"""Regression tests for the findings of the QA audit of 2026-10-30 (docs/qa-audit-2026-10-30.md)."""

import io
import json
import urllib.error

import pytest

from tretlager.bridge.config import BridgeConfig
from tretlager.core import bridgectl, launch, login


def test_dbus_error_texts():
    assert "switched off" in bridgectl.describe_dbus_error(
        "Error: GDBus.Error:org.bluez.Error.NotReady: Resource Not Ready")
    assert "not responding" in bridgectl.describe_dbus_error(
        "Error: GDBus.Error:org.freedesktop.DBus.Error.NoReply: Timeout was reached")
    assert "GDBus" not in bridgectl.describe_dbus_error("Error: GDBus.Error:x.y.Z: broken")


# --- B-02: a corrupt bridge.json does not cripple the bridge ---

def test_corrupt_config_is_set_aside(tmp_path):
    path = tmp_path / "bridge.json"
    path.write_text('{"devices": [ {"address": ')
    cfg = BridgeConfig.load(path)
    assert cfg.devices == [] and not path.exists()
    assert (tmp_path / "bridge.broken").exists()


def test_config_ignores_unknown_fields(tmp_path):
    path = tmp_path / "bridge.json"
    path.write_text(json.dumps({"devices": [{"address": "AA:BB", "name": "x", "role": "trainer",
                                             "port": 36866, "added_in_later_version": 1}]}))
    assert BridgeConfig.load(path).devices[0].address == "AA:BB"


# --- Z-01: Zwift process via /proc instead of wine tasklist ---

def test_process_running(tmp_path):
    # Zwift as on tinytin: comm "main", argv[0] a Windows path, the token as a separate argument.
    for pid, argv in (("1", [b"/sbin/init"]), ("self", [b"x"]),
                      ("42", [b"C:\\Program Files (x86)\\Zwift\\ZwiftApp.exe", b"--token={secret ZwiftLauncher.exe}"]),
                      ("43", [b"C:\\windows\\system32\\services.exe"])):
        (tmp_path / pid).mkdir()
        (tmp_path / pid / "cmdline").write_bytes(b"\0".join(argv) + b"\0")
    assert launch.process_running("ZwiftApp.exe", tmp_path)
    assert launch.process_running("zwiftapp.exe", tmp_path)
    assert not launch.process_running("ZwiftLauncher.exe", tmp_path)  # appears only in the token argument


# --- L-01: offline does not mean "sign in again" ---

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
    with pytest.raises(login.LoginUnavailable, match="internet connection"):
        login.valid_token(FakeKeyring(old), offline)


def test_valid_token_rejected_refresh_means_login():
    old = {"obtained_at": 0, "expires_in": 60, "refresh_expires_in": 10**10, "refresh_token": "r"}

    def rejected(req, **_kw):
        raise urllib.error.HTTPError(req.full_url, 400, "Bad Request", {}, io.BytesIO(b"{}"))
    assert login.valid_token(FakeKeyring(old), rejected) is None


# --- C-01: the timeout applies even without output ---

def test_context_run_times_out_without_output():
    import time
    from tretlager.core import setup
    ctx = setup.Context()
    start = time.monotonic()
    rc = ctx.run(["sleep", "30"], env={"PATH": "/usr/bin:/bin"}, timeout=1)
    assert rc != 0 and time.monotonic() - start < 5


def test_context_run_cancel_without_output():
    import threading
    import time
    from tretlager.core import setup
    ctx = setup.Context()
    threading.Timer(0.5, ctx.cancel.set).start()
    start = time.monotonic()
    ctx.run(["sleep", "30"], env={"PATH": "/usr/bin:/bin"})
    assert time.monotonic() - start < 5


# --- C-02: DIRCON drops readings when the client does not read ---

def test_dircon_drops_when_buffer_full():
    from types import SimpleNamespace
    from tretlager.bridge import dircon
    written = []
    transport = SimpleNamespace(get_write_buffer_size=lambda: dircon.MAX_SEND_BUFFER + 1)
    writer = SimpleNamespace(transport=transport, write=written.append)
    dircon.Session(None, writer).notify("00002a37-0000-1000-8000-00805f9b34fb", b"\x00\x40")
    assert written == []
    transport.get_write_buffer_size = lambda: 0
    dircon.Session(None, writer).notify("00002a37-0000-1000-8000-00805f9b34fb", b"\x00\x40")
    assert len(written) == 1
