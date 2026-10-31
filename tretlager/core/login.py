"""Signing in to Zwift via the browser (decision E2, only with explicit consent).

The official sign-in in launcher 1.2 does not work under Wine (WebView2CompositionControl needs
Windows.UI.Composition, see FEASIBILITY.md T2). Replacement:
  1. The sign-in page of secure.zwift.com appears in an embedded, private browser window
     (QtWebEngine), as in the official launcher. Tretlager does not read the page.
     Fallback: the user's own browser (password manager, sign-in with Google or Apple).
  2. Zwift redirects back to launcher.zwift.com/launcher?…&code=…; Zwift rejects other redirect
     addresses (localhost etc.) (checked 2026-10-30). The embedded window intercepts this address
     before the page ("Bad Request") loads. In their own browser the user copies it.
  3. Tretlager exchanges the code for a token and later refreshes it itself.
This uses the undocumented launcher sign-in (client_id Game_Launcher) and contradicts §5 of the
Zwift terms of service; hence only after consent and with a notice.

The token is only kept in the keyring (Secret Service, ksecretd under Plasma), never in files or
logs. Validity according to Zwift: access 6 h, refresh 8 days.
"""

from __future__ import annotations

import json
import secrets as pysecrets
import time
import urllib.error
import urllib.parse
import urllib.request

from . import state
from ..i18n import _

REALM = "https://secure.zwift.com/auth/realms/zwift/protocol/openid-connect"
CLIENT_ID = "Game_Launcher"
REDIRECT = "https://launcher.zwift.com/launcher"
MARGIN = 5 * 60  # remaining lifetime an access token needs for a launch
KEYRING_ATTRS = {"application": "tretlager", "kind": "zwift-token"}


class LoginError(Exception):
    """Error with a sentence for the user."""


class LoginUnavailable(LoginError):
    """Zwift sign-in unreachable (offline, server error): no reason to sign in again."""


def new_state() -> str:
    return pysecrets.token_hex(16)


def auth_url(state_value: str, language: str = "") -> str:
    """Address of the sign-in page; `language` (e.g. "de") selects the language of the Zwift page."""
    params = {"response_type": "code", "client_id": CLIENT_ID, "redirect_uri": REDIRECT,
              "scope": "openid", "login": "true", "state": state_value}
    if language:
        params["ui_locales"] = language
    q = urllib.parse.urlencode(params)
    return f"{REALM}/auth?{q}"


# OAuth/OpenID Connect error codes as a sentence for the user
ERROR_TEXT = {
    "access_denied": _("The sign-in was cancelled."),
    "login_required": _("Zwift requires signing in with email and password. Please sign in again."),
    "interaction_required": _("Zwift requires signing in with email and password. Please sign in again."),
    "temporarily_unavailable": _("Zwift sign-in is unavailable right now. Please try again later."),
    "server_error": _("Zwift sign-in reported an error. Please try again later."),
}


def _error_text(code: str) -> str:
    return ERROR_TEXT.get(code, _("Zwift did not complete the sign-in (error “{code}”). Please sign in again.").format(code=code))


def parse_redirect(url: str, expected_state: str | None = None) -> str:
    """Extract the code from the redirect address; checks the target and (if known) the state."""
    url = url.strip()
    parsed = urllib.parse.urlparse(url)
    if parsed.netloc != "launcher.zwift.com" or not parsed.path.startswith("/launcher"):
        raise LoginError(_("This is not the address shown after signing in to Zwift (launcher.zwift.com/launcher?…)."))
    q = urllib.parse.parse_qs(parsed.query)
    if "error" in q:
        raise LoginError(_error_text(q["error"][0]))
    code = (q.get("code") or [""])[0]
    if not code:
        raise LoginError(_("The address is missing the sign-in code (code=…)."))
    if expected_state and (q.get("state") or [""])[0] != expected_state:
        raise LoginError(_("The address belongs to an earlier sign-in. Please sign in again in the browser."))
    return code


def _post(form: dict, opener=urllib.request.urlopen) -> dict:
    data = urllib.parse.urlencode(form).encode()
    req = urllib.request.Request(f"{REALM}/token", data=data, headers={"User-Agent": "Tretlager"})
    try:
        with opener(req, timeout=30) as r:  # noqa: S310 (fixed https URL)
            token = json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code in (400, 401):
            raise LoginError(_("Zwift rejected the sign-in (code expired or already used).")) from None
        raise LoginUnavailable(_("Zwift sign-in unreachable (HTTP {code}).").format(code=e.code)) from None
    except (urllib.error.URLError, TimeoutError):
        raise LoginUnavailable(_("Zwift sign-in unreachable. Is there an internet connection?")) from None
    if "access_token" not in token:
        raise LoginError(_("Unexpected response from Zwift."))
    token["obtained_at"] = int(time.time())
    return token


def exchange_code(code: str, opener=urllib.request.urlopen) -> dict:
    return _post({"client_id": CLIENT_ID, "redirect_uri": REDIRECT, "code": code,
                  "grant_type": "authorization_code", "scope": "openid"}, opener)


def refresh(token: dict, opener=urllib.request.urlopen) -> dict:
    return _post({"client_id": CLIENT_ID, "grant_type": "refresh_token",
                  "refresh_token": token["refresh_token"]}, opener)


def logout_remote(token: dict, opener=urllib.request.urlopen) -> None:
    """End the session at Zwift (Keycloak logout); this invalidates the refresh token."""
    data = urllib.parse.urlencode({"client_id": CLIENT_ID, "refresh_token": token["refresh_token"]}).encode()
    req = urllib.request.Request(f"{REALM}/logout", data=data, headers={"User-Agent": "Tretlager"})
    try:
        with opener(req, timeout=30):  # noqa: S310 (fixed https URL)
            pass
    except urllib.error.HTTPError as e:
        raise LoginError(_("Signing out of Zwift failed (HTTP {code}).").format(code=e.code)) from None
    except (urllib.error.URLError, TimeoutError):
        raise LoginError(_("Zwift sign-in unreachable; signed out locally.")) from None


def lifetimes(token: dict, now: float | None = None) -> tuple[int, int]:
    """Remaining lifetime (seconds) of access and refresh token."""
    now = now if now is not None else time.time()
    got = token.get("obtained_at", 0)
    return (int(got + token.get("expires_in", 0) - now), int(got + token.get("refresh_expires_in", 0) - now))


def status(token: dict | None, now: float | None = None) -> dict:
    if not token:
        return {"state": "none", "access_left": 0, "refresh_left": 0}
    access, refresh_left = lifetimes(token, now)
    if access > MARGIN:
        st = "valid"
    elif refresh_left > MARGIN and token.get("refresh_token"):
        st = "refreshable"
    else:
        st = "expired"
    return {"state": st, "access_left": max(access, 0), "refresh_left": max(refresh_left, 0)}


# --- Keyring ---

class Keyring:
    """Token in the Secret Service; a clear error message without library or service."""

    def _collection(self):
        try:
            import secretstorage
        except ImportError as e:
            raise LoginError(_("python3-secretstorage is missing; without a keyring Tretlager does not store a token.")) from e
        try:
            conn = secretstorage.dbus_init()
            coll = secretstorage.get_default_collection(conn)
            if coll.is_locked():
                coll.unlock()
                if coll.is_locked():
                    raise LoginError(_("The keyring is locked. Unlock the keyring to start Zwift."))
        except secretstorage.exceptions.SecretStorageException:
            # No Secret Service (some desktops do not start one) or unlocking was refused
            raise LoginError(_("No keyring available. Tretlager keeps the Zwift session in the "
                               "desktop keyring (KWallet or GNOME Keyring), which must be "
                               "running and unlocked.")) from None
        return coll

    def load(self) -> dict | None:
        coll = self._collection()
        for item in coll.search_items(KEYRING_ATTRS):
            try:
                return json.loads(item.get_secret())
            except (json.JSONDecodeError, ValueError):
                return None
        return None

    def save(self, token: dict) -> None:
        coll = self._collection()
        coll.create_item("Tretlager: Zwift session", KEYRING_ATTRS, json.dumps(token).encode(), replace=True)

    def delete(self) -> None:
        coll = self._collection()
        for item in coll.search_items(KEYRING_ATTRS):
            item.delete()


def consent_given() -> bool:
    return state.load().get("login", {}).get("consent") is True


def give_consent() -> None:
    state.update("login", consent=True)


def valid_token(keyring: Keyring | None = None, opener=urllib.request.urlopen) -> dict | None:
    """A token usable for a launch, refreshed if necessary; None = sign-in in the browser required."""
    keyring = keyring or Keyring()
    token = keyring.load()
    st = status(token)["state"]
    if st == "valid":
        return token
    if st == "refreshable":
        try:
            token = refresh(token, opener)
        except LoginUnavailable:
            raise  # offline or similar: report instead of asking to sign in again
        except LoginError:
            return None
        keyring.save(token)
        return token
    return None
