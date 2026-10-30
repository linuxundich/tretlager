"""Anmeldung bei Zwift über den Browser (Entscheidung E2, nur mit ausdrücklicher Zustimmung).

Die offizielle Anmeldung im Launcher 1.2 funktioniert unter Wine nicht (WebView2CompositionControl
braucht Windows.UI.Composition, siehe FEASIBILITY.md T2). Ersatz:
  1. Die Anmeldeseite von secure.zwift.com erscheint in einem eingebetteten, privaten
     Browserfenster (QtWebEngine), wie im offiziellen Launcher. Tretlager liest die Seite nicht aus.
     Ausweichweg: der eigene Browser (Passwortmanager, Anmeldung mit Google oder Apple).
  2. Zwift springt auf launcher.zwift.com/launcher?…&code=… zurück; andere Rücksprungadressen
     (localhost usw.) lehnt Zwift ab (geprüft 2026-10-30). Das eingebettete Fenster fängt diese
     Adresse ab, bevor die Seite („Bad Request“) lädt. Im eigenen Browser kopiert der Nutzer sie.
  3. Tretlager tauscht den Code gegen ein Token und erneuert es später selbst.
Das nutzt die nicht dokumentierte Launcher-Anmeldung (client_id Game_Launcher) und widerspricht
§5 der Zwift-Nutzungsbedingungen; deshalb nur nach Zustimmung und mit Hinweis.

Das Token liegt nur im Schlüsselbund (Secret Service, unter Plasma ksecretd), nie in Dateien oder
Protokollen. Gültigkeit laut Zwift: Zugriff 6 h, Erneuerung 8 Tage.
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
MARGIN = 5 * 60  # so viel Restlaufzeit muss ein Zugriffstoken für einen Start haben
KEYRING_ATTRS = {"application": "tretlager", "kind": "zwift-token"}


class LoginError(Exception):
    """Fehler mit einem Satz für den Nutzer."""


class LoginUnavailable(LoginError):
    """Zwift-Anmeldung nicht erreichbar (offline, Serverfehler): kein Grund, sich neu anzumelden."""


def new_state() -> str:
    return pysecrets.token_hex(16)


def auth_url(state_value: str, language: str = "") -> str:
    """Adresse der Anmeldeseite; `language` (z. B. „de“) wählt die Sprache der Zwift-Seite."""
    params = {"response_type": "code", "client_id": CLIENT_ID, "redirect_uri": REDIRECT,
              "scope": "openid", "login": "true", "state": state_value}
    if language:
        params["ui_locales"] = language
    q = urllib.parse.urlencode(params)
    return f"{REALM}/auth?{q}"


# Fehlercodes aus OAuth/OpenID Connect als Satz für den Nutzer
ERROR_TEXT = {
    "access_denied": _("Die Anmeldung wurde abgebrochen."),
    "login_required": _("Zwift verlangt eine Anmeldung mit E-Mail und Passwort. Bitte erneut anmelden."),
    "interaction_required": _("Zwift verlangt eine Anmeldung mit E-Mail und Passwort. Bitte erneut anmelden."),
    "temporarily_unavailable": _("Die Zwift-Anmeldung ist gerade nicht erreichbar. Bitte später erneut versuchen."),
    "server_error": _("Bei der Zwift-Anmeldung ist ein Fehler aufgetreten. Bitte später erneut versuchen."),
}


def _error_text(code: str) -> str:
    return ERROR_TEXT.get(code, _("Zwift hat die Anmeldung nicht abgeschlossen (Fehler „{code}“). Bitte erneut anmelden.").format(code=code))


def parse_redirect(url: str, expected_state: str | None = None) -> str:
    """Code aus der Rücksprungadresse holen; prüft Ziel und (falls bekannt) state."""
    url = url.strip()
    parsed = urllib.parse.urlparse(url)
    if parsed.netloc != "launcher.zwift.com" or not parsed.path.startswith("/launcher"):
        raise LoginError(_("Das ist nicht die Adresse nach der Zwift-Anmeldung (launcher.zwift.com/launcher?…)."))
    q = urllib.parse.parse_qs(parsed.query)
    if "error" in q:
        raise LoginError(_error_text(q["error"][0]))
    code = (q.get("code") or [""])[0]
    if not code:
        raise LoginError(_("In der Adresse fehlt der Anmeldecode (code=…)."))
    if expected_state and (q.get("state") or [""])[0] != expected_state:
        raise LoginError(_("Die Adresse gehört zu einer älteren Anmeldung. Bitte erneut im Browser anmelden."))
    return code


def _post(form: dict, opener=urllib.request.urlopen) -> dict:
    data = urllib.parse.urlencode(form).encode()
    req = urllib.request.Request(f"{REALM}/token", data=data, headers={"User-Agent": "Tretlager"})
    try:
        with opener(req, timeout=30) as r:  # noqa: S310 (feste https-URL)
            token = json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code in (400, 401):
            raise LoginError(_("Zwift hat die Anmeldung abgelehnt (Code abgelaufen oder bereits benutzt).")) from None
        raise LoginUnavailable(_("Zwift-Anmeldung nicht erreichbar (HTTP {code}).").format(code=e.code)) from None
    except (urllib.error.URLError, TimeoutError):
        raise LoginUnavailable(_("Zwift-Anmeldung nicht erreichbar. Besteht eine Internetverbindung?")) from None
    if "access_token" not in token:
        raise LoginError(_("Unerwartete Antwort von Zwift."))
    token["obtained_at"] = int(time.time())
    return token


def exchange_code(code: str, opener=urllib.request.urlopen) -> dict:
    return _post({"client_id": CLIENT_ID, "redirect_uri": REDIRECT, "code": code,
                  "grant_type": "authorization_code", "scope": "openid"}, opener)


def refresh(token: dict, opener=urllib.request.urlopen) -> dict:
    return _post({"client_id": CLIENT_ID, "grant_type": "refresh_token",
                  "refresh_token": token["refresh_token"]}, opener)


def logout_remote(token: dict, opener=urllib.request.urlopen) -> None:
    """Sitzung bei Zwift beenden (Keycloak-Logout); das Erneuerungs-Token wird damit ungültig."""
    data = urllib.parse.urlencode({"client_id": CLIENT_ID, "refresh_token": token["refresh_token"]}).encode()
    req = urllib.request.Request(f"{REALM}/logout", data=data, headers={"User-Agent": "Tretlager"})
    try:
        with opener(req, timeout=30):  # noqa: S310 (feste https-URL)
            pass
    except urllib.error.HTTPError as e:
        raise LoginError(_("Abmelden bei Zwift fehlgeschlagen (HTTP {code}).").format(code=e.code)) from None
    except (urllib.error.URLError, TimeoutError):
        raise LoginError(_("Zwift-Anmeldung nicht erreichbar; lokal abgemeldet.")) from None


def lifetimes(token: dict, now: float | None = None) -> tuple[int, int]:
    """Restlaufzeit (Sekunden) von Zugriffs- und Erneuerungstoken."""
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


# --- Schlüsselbund ---

class Keyring:
    """Token im Secret Service; ohne Bibliothek oder Dienst eine klare Fehlermeldung."""

    def _collection(self):
        try:
            import secretstorage
        except ImportError as e:
            raise LoginError(_("python3-secretstorage fehlt; ohne Schlüsselbund speichert Tretlager kein Token.")) from e
        try:
            conn = secretstorage.dbus_init()
            coll = secretstorage.get_default_collection(conn)
            if coll.is_locked():
                coll.unlock()
                if coll.is_locked():
                    raise LoginError(_("Der Schlüsselbund ist gesperrt. Zum Starten von Zwift den Schlüsselbund entsperren."))
        except secretstorage.exceptions.SecretStorageException:
            # Kein Secret Service (manche Desktops starten keinen) oder Entsperren abgelehnt
            raise LoginError(_("Kein Schlüsselbund erreichbar. Tretlager speichert die Zwift-Sitzung im "
                               "Schlüsselbund des Desktops (KWallet bzw. GNOME Schlüsselbund); dieser muss "
                               "laufen und entsperrt sein.")) from None
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
        coll.create_item("Tretlager: Zwift-Sitzung", KEYRING_ATTRS, json.dumps(token).encode(), replace=True)

    def delete(self) -> None:
        coll = self._collection()
        for item in coll.search_items(KEYRING_ATTRS):
            item.delete()


def consent_given() -> bool:
    return state.load().get("login", {}).get("consent") is True


def give_consent() -> None:
    state.update("login", consent=True)


def valid_token(keyring: Keyring | None = None, opener=urllib.request.urlopen) -> dict | None:
    """Ein für den Start brauchbares Token, notfalls erneuert; None = Anmeldung im Browser nötig."""
    keyring = keyring or Keyring()
    token = keyring.load()
    st = status(token)["state"]
    if st == "valid":
        return token
    if st == "refreshable":
        try:
            token = refresh(token, opener)
        except LoginUnavailable:
            raise  # offline o. Ä.: melden statt zur Neuanmeldung schicken
        except LoginError:
            return None
        keyring.save(token)
        return token
    return None
