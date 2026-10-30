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


# --- B-04: Schonfrist nach einem BLE-Abbruch ---

from types import SimpleNamespace  # noqa: E402

from tretlager.bridge import gatt  # noqa: E402
from tretlager.bridge.config import DeviceConfig  # noqa: E402


class FakeServices(list):
    def get_characteristic(self, uuid):
        for s in self:
            for c in s.characteristics:
                if c.uuid == uuid:
                    return c
        return None


class FakeClient:
    instances = []

    def __init__(self, device, disconnected_callback=None, **_kw):
        self.on_disconnect = disconnected_callback
        self.is_connected = False
        hr = SimpleNamespace(uuid=gatt.HR_MEASUREMENT, properties=["notify"])
        self.services = FakeServices([SimpleNamespace(uuid=gatt.HEART_RATE, characteristics=[hr])])
        self.notified = []
        FakeClient.instances.append(self)

    async def connect(self):
        self.is_connected = True

    async def disconnect(self):
        self.is_connected = False

    async def start_notify(self, uuid, _cb):
        self.notified.append(uuid)

    def drop(self):
        self.is_connected = False
        self.on_disconnect(self)


class FakeAnnouncer:
    def __init__(self):
        self.published, self.withdrawn = 0, 0

    async def publish(self, *_a, **_kw):
        self.published += 1

    async def withdraw(self, _port):
        self.withdrawn += 1


def test_grace_keeps_device_for_zwift(monkeypatch):
    async def found(*_a, **_kw):
        return object()

    async def no_disconnect(*_a, **_kw):
        pass
    monkeypatch.setattr(device.BleakScanner, "find_device_by_address", found)
    monkeypatch.setattr(device, "BleakClient", FakeClient)
    monkeypatch.setattr(device, "bluez_disconnect", no_disconnect)
    monkeypatch.setattr(device, "RECONNECT_DELAY", 0.05)
    monkeypatch.setattr(device, "GRACE", 0.5)
    FakeClient.instances.clear()

    async def scenario():
        ann = FakeAnnouncer()
        dev = device.BridgedDevice(DeviceConfig("AA:BB:CC:DD:EE:FF", "Gurt", "heartrate", 0), ann, lambda: None)
        dev.start()
        await asyncio.sleep(0.1)
        assert dev.state == "verbunden" and ann.published == 1 and dev._server.running
        FakeClient.instances[-1].drop()  # kurzer Abbruch: Gerät bleibt angekündigt
        await asyncio.sleep(0.2)
        assert dev.state == "verbunden" and len(FakeClient.instances) == 2
        assert ann.published == 1 and ann.withdrawn == 0 and dev._server.running
        assert gatt.HR_MEASUREMENT in FakeClient.instances[-1].notified  # Daten fließen wieder
        await dev.stop()
        assert ann.withdrawn >= 1 and not dev._server.running

    asyncio.run(scenario())


def test_grace_expires_and_withdraws(monkeypatch):
    async def missing(*_a, **_kw):
        return None

    async def no_disconnect(*_a, **_kw):
        pass
    monkeypatch.setattr(device, "BleakClient", FakeClient)
    monkeypatch.setattr(device, "bluez_disconnect", no_disconnect)
    monkeypatch.setattr(device, "GRACE", 0.2)
    monkeypatch.setattr(device, "NOT_FOUND_DELAY", 0.05)

    async def found(*_a, **_kw):
        return object()
    monkeypatch.setattr(device.BleakScanner, "find_device_by_address", found)
    FakeClient.instances.clear()

    async def scenario():
        ann = FakeAnnouncer()
        dev = device.BridgedDevice(DeviceConfig("AA:BB:CC:DD:EE:FF", "Gurt", "heartrate", 0), ann, lambda: None)
        dev.start()
        await asyncio.sleep(0.1)
        monkeypatch.setattr(device.BleakScanner, "find_device_by_address", missing)  # Gerät ist weg
        FakeClient.instances[-1].drop()
        await asyncio.sleep(0.1)
        assert dev._server.running and ann.withdrawn == 0  # noch in der Schonfrist
        await asyncio.sleep(0.3)
        assert not dev._server.running and ann.withdrawn == 1
        await dev.stop()

    asyncio.run(scenario())
