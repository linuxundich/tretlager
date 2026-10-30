"""Regressionstests zu den Befunden des QA-Audits vom 2026-10-30 (docs/qa-audit-2026-10-30.md)."""

import asyncio

import pytest

pytest.importorskip("bleak")
from bleak.exc import BleakDBusError, BleakDeviceNotFoundError, BleakError  # noqa: E402

from tretlager.bridge import device  # noqa: E402


# --- B-01: abwesendes Gerät hält die BlueZ-Sperre nicht 40 s ---

def test_find_timeout_short_and_separate():
    assert device.FIND_TIMEOUT <= 10 < device.CONNECT_TIMEOUT


# --- B-03: verständliche Fehlertexte der Bridge ---

@pytest.mark.parametrize("exc,text,not_found", [
    (BleakDeviceNotFoundError("AA", "Device with address AA was not found."), "Nicht in Reichweite", True),
    (BleakError("failed to discover services, device disconnected"), "Gerät schläft", True),
    (asyncio.TimeoutError(), "Zeitüberschreitung", False),
    (BleakDBusError("org.bluez.Error.NotReady", ["Resource Not Ready"]), "Bluetooth ist aus", False),
    (BleakDBusError("org.bluez.Error.InProgress", ["Operation already in progress"]), "beschäftigt", False),
    (BleakDBusError("org.bluez.Error.Failed", ["le-connection-abort-by-local"]), "abgebrochen", False),
    (RuntimeError("Verbindung zum Gerät verloren"), "Verbindung zum Gerät verloren", False),
    (BleakError("something odd"), "Verbindung fehlgeschlagen", False),
])
def test_describe_error(exc, text, not_found):
    got, nf = device.describe_error(exc)
    assert text in got and nf is not_found
    assert "org.bluez" not in got
