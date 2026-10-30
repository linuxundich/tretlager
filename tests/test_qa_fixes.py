"""Regressionstests zu den Befunden des QA-Audits vom 2026-10-30 (docs/qa-audit-2026-10-30.md)."""

import io
import json
import urllib.error

import pytest

from tretlager.bridge.config import BridgeConfig
from tretlager.core import bridgectl, launch, login


def test_dbus_error_texts():
    assert "ausgeschaltet" in bridgectl.describe_dbus_error(
        "Error: GDBus.Error:org.bluez.Error.NotReady: Resource Not Ready")
    assert "antwortet nicht" in bridgectl.describe_dbus_error(
        "Error: GDBus.Error:org.freedesktop.DBus.Error.NoReply: Timeout was reached")
    assert "GDBus" not in bridgectl.describe_dbus_error("Error: GDBus.Error:x.y.Z: kaputt")


# --- B-02: kaputte bridge.json legt die Bridge nicht lahm ---

def test_corrupt_config_is_set_aside(tmp_path):
    path = tmp_path / "bridge.json"
    path.write_text('{"devices": [ {"address": ')
    cfg = BridgeConfig.load(path)
    assert cfg.devices == [] and not path.exists()
    assert (tmp_path / "bridge.defekt").exists()


def test_config_ignores_unknown_fields(tmp_path):
    path = tmp_path / "bridge.json"
    path.write_text(json.dumps({"devices": [{"address": "AA:BB", "name": "x", "role": "trainer",
                                             "port": 36866, "neu_in_spaeterer_version": 1}]}))
    assert BridgeConfig.load(path).devices[0].address == "AA:BB"


# --- Z-01: Zwift-Prozess über /proc statt wine tasklist ---

def test_process_running(tmp_path):
    # Zwift wie auf tinytin: comm „main“, argv[0] Windows-Pfad, das Token als eigenes Argument.
    for pid, argv in (("1", [b"/sbin/init"]), ("self", [b"x"]),
                      ("42", [b"C:\\Program Files (x86)\\Zwift\\ZwiftApp.exe", b"--token={geheim ZwiftLauncher.exe}"]),
                      ("43", [b"C:\\windows\\system32\\services.exe"])):
        (tmp_path / pid).mkdir()
        (tmp_path / pid / "cmdline").write_bytes(b"\0".join(argv) + b"\0")
    assert launch.process_running("ZwiftApp.exe", tmp_path)
    assert launch.process_running("zwiftapp.exe", tmp_path)
    assert not launch.process_running("ZwiftLauncher.exe", tmp_path)  # steht nur im Token-Argument


# --- L-01: offline heißt nicht „neu anmelden“ ---

class FakeKeyring:
    def __init__(self, token):
        self.token = token

    def load(self):
        return self.token

    def save(self, token):
        self.token = token


def test_valid_token_offline_raises_instead_of_login():
    old = {"obtained_at": 0, "expires_in": 60, "refresh_expires_in": 10**10, "refresh_token": "r"}

    def offline(*_a, **_kw):
        raise urllib.error.URLError("Name or service not known")
    with pytest.raises(login.LoginUnavailable, match="Internetverbindung"):
        login.valid_token(FakeKeyring(old), offline)


def test_valid_token_rejected_refresh_means_login():
    old = {"obtained_at": 0, "expires_in": 60, "refresh_expires_in": 10**10, "refresh_token": "r"}

    def rejected(req, **_kw):
        raise urllib.error.HTTPError(req.full_url, 400, "Bad Request", {}, io.BytesIO(b"{}"))
    assert login.valid_token(FakeKeyring(old), rejected) is None
