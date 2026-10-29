import io
import json
import urllib.error
import urllib.parse

import pytest

from tretlager.core import login

BACK = "https://launcher.zwift.com/launcher?state=abc&session_state=x&iss=y&code=CODE123"


def test_auth_url_contains_parameters():
    url = login.auth_url("abc")
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    assert q["client_id"] == ["Game_Launcher"] and q["state"] == ["abc"]
    assert q["redirect_uri"] == ["https://launcher.zwift.com/launcher"]


def test_parse_redirect_ok_and_state():
    assert login.parse_redirect(BACK, "abc") == "CODE123"
    assert login.parse_redirect("  " + BACK + "\n") == "CODE123"
    with pytest.raises(login.LoginError, match="älteren"):
        login.parse_redirect(BACK, "other")


@pytest.mark.parametrize("url,msg", [
    ("https://example.com/launcher?code=x", "nicht die Adresse"),
    ("https://launcher.zwift.com/launcher?state=abc", "fehlt"),
    ("https://launcher.zwift.com/launcher?error=access_denied", "Fehler"),
])
def test_parse_redirect_errors(url, msg):
    with pytest.raises(login.LoginError, match=msg):
        login.parse_redirect(url)


def test_status_states():
    t = {"obtained_at": 1000, "expires_in": 21600, "refresh_expires_in": 691200, "refresh_token": "r"}
    assert login.status(t, now=1000)["state"] == "valid"
    assert login.status(t, now=1000 + 21600)["state"] == "refreshable"
    assert login.status(t, now=1000 + 691200)["state"] == "expired"
    assert login.status(None)["state"] == "none"


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def opener_returning(payload, seen=None):
    def opener(req, timeout=0):
        if seen is not None:
            seen.append(urllib.parse.parse_qs(req.data.decode()))
        return FakeResponse(json.dumps(payload).encode())
    return opener


def test_exchange_code_posts_form_and_stamps_time():
    seen = []
    token = login.exchange_code("CODE123", opener_returning({"access_token": "a", "expires_in": 21600}, seen))
    assert token["access_token"] == "a" and token["obtained_at"] > 0
    assert seen[0]["grant_type"] == ["authorization_code"] and seen[0]["code"] == ["CODE123"]


def test_exchange_rejected_code():
    def opener(req, timeout=0):
        raise urllib.error.HTTPError(req.full_url, 400, "bad", {}, io.BytesIO(b""))
    with pytest.raises(login.LoginError, match="abgelehnt"):
        login.exchange_code("x", opener)


class FakeKeyring:
    def __init__(self, token):
        self.token = token
        self.saved = None

    def load(self):
        return self.token

    def save(self, token):
        self.saved = token


def test_valid_token_refreshes_when_needed():
    import time
    old = {"obtained_at": int(time.time()) - 22000, "expires_in": 21600, "refresh_expires_in": 691200,
           "refresh_token": "r"}
    kr = FakeKeyring(old)
    seen = []
    new = login.valid_token(kr, opener_returning({"access_token": "neu", "expires_in": 21600,
                                                  "refresh_expires_in": 691200, "refresh_token": "r2"}, seen))
    assert new["access_token"] == "neu" and kr.saved is new
    assert seen[0]["grant_type"] == ["refresh_token"] and seen[0]["refresh_token"] == ["r"]


def test_valid_token_none_when_expired():
    assert login.valid_token(FakeKeyring(None)) is None
    expired = {"obtained_at": 0, "expires_in": 1, "refresh_expires_in": 1, "refresh_token": "r"}
    assert login.valid_token(FakeKeyring(expired)) is None
