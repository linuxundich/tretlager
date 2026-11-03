"""Regression tests for the findings of the QA audit of 2026-10-30 (docs/qa-audit-2026-10-30.md)."""

import asyncio

import pytest

pytest.importorskip("bleak")
from bleak.exc import BleakDBusError, BleakDeviceNotFoundError, BleakError  # noqa: E402

from tretlager.bridge import device  # noqa: E402


# --- B-01: an absent device does not hold the BlueZ lock for 40 s ---

def test_find_timeout_short_and_separate():
    assert device.FIND_TIMEOUT <= 10 < device.CONNECT_TIMEOUT


def test_connect_timeout_long_only_for_slow_sensors():
    assert device.connect_timeout("TICKR 9029") == device.CONNECT_TIMEOUT == 20.0
    assert device.connect_timeout("HRM-Pro+:123456") == device.SLOW_CONNECT_TIMEOUT
    assert device.connect_timeout("") == device.CONNECT_TIMEOUT


# --- B-03: understandable error texts of the bridge ---

@pytest.mark.parametrize("exc,text,not_found", [
    (BleakDeviceNotFoundError("AA", "Device with address AA was not found."), "Out of range", True),
    (BleakError("failed to discover services, device disconnected"), "Device is asleep", True),
    (asyncio.TimeoutError(), "timed out", False),
    (BleakDBusError("org.bluez.Error.NotReady", ["Resource Not Ready"]), "Bluetooth is off", False),
    (BleakDBusError("org.bluez.Error.InProgress", ["Operation already in progress"]), "busy", False),
    (BleakDBusError("org.bluez.Error.Failed", ["le-connection-abort-by-local"]), "aborted", False),
    (RuntimeError("Connection to the device lost"), "Connection to the device lost", False),
    (BleakError("something odd"), "Connection failed", False),
])
def test_describe_error(exc, text, not_found):
    got, nf = device.describe_error(exc)
    assert text in got and nf is not_found
    assert "org.bluez" not in got


# --- B-04: grace period after a BLE dropout ---

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
        dev = device.BridgedDevice(DeviceConfig("AA:BB:CC:DD:EE:FF", "Strap", "heartrate", 0), ann, lambda: None)
        dev.start()
        await asyncio.sleep(0.1)
        assert dev.state == "connected" and ann.published == 1 and dev._server.running
        FakeClient.instances[-1].drop()  # short dropout: the device stays announced
        await asyncio.sleep(0.2)
        assert dev.state == "connected" and len(FakeClient.instances) == 2
        assert ann.published == 1 and ann.withdrawn == 0 and dev._server.running
        assert gatt.HR_MEASUREMENT in FakeClient.instances[-1].notified  # data flows again
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
        dev = device.BridgedDevice(DeviceConfig("AA:BB:CC:DD:EE:FF", "Strap", "heartrate", 0), ann, lambda: None)
        dev.start()
        await asyncio.sleep(0.1)
        monkeypatch.setattr(device.BleakScanner, "find_device_by_address", missing)  # device is gone
        FakeClient.instances[-1].drop()
        await asyncio.sleep(0.1)
        assert dev._server.running and ann.withdrawn == 0  # still within the grace period
        await asyncio.sleep(0.3)
        assert not dev._server.running and ann.withdrawn == 1
        await dev.stop()

    asyncio.run(scenario())


# --- Stuck controller (2026-11-03): connection timeouts in a row of a device that is found ---

def test_stuck_controller_resets_adapter(monkeypatch):
    class TimingOutClient(FakeClient):
        async def connect(self):
            raise asyncio.TimeoutError()

    async def found(*_a, **_kw):
        return object()

    async def no_disconnect(*_a, **_kw):
        pass
    resets = []

    async def reset(adapter, bridged):
        resets.append((adapter, list(bridged)))
        monkeypatch.setattr(device, "BleakClient", FakeClient)  # after the reset the strap connects
        return ""
    monkeypatch.setattr(device.BleakScanner, "find_device_by_address", found)
    monkeypatch.setattr(device, "BleakClient", TimingOutClient)
    monkeypatch.setattr(device, "bluez_disconnect", no_disconnect)
    monkeypatch.setattr(device, "reset_adapter", reset)
    monkeypatch.setattr(device, "RECONNECT_DELAY", 0.01)
    monkeypatch.setattr(device, "MAX_RECONNECT_DELAY", 0.01)

    async def scenario():
        dev = device.BridgedDevice(DeviceConfig("AA:BB:CC:DD:EE:FF", "TICKR", "heartrate", 0), FakeAnnouncer(),
                                   lambda: None, adapter="hci0", bridged=lambda: ["AA:BB:CC:DD:EE:FF"])
        dev.start()
        await asyncio.sleep(0.3)
        assert resets == [("hci0", ["AA:BB:CC:DD:EE:FF"])]
        assert dev.state == "connected"
        await dev.stop()

    asyncio.run(scenario())


def test_reset_rate_limited(monkeypatch):
    monkeypatch.setattr(device, "_last_reset", {"hci0": device.time.monotonic()})
    reason = asyncio.run(device.reset_adapter("", []))
    assert "stuck" in reason


# --- Other devices on the bridge's adapter (headphones crowd out the sensors, 2026-11-03) ---

def test_foreign_devices_on_adapter():
    from dbus_fast import Variant

    def dev(addr, connected, icon="", uuids=(), alias=""):
        return {"org.bluez.Device1": {"Address": Variant("s", addr), "Connected": Variant("b", connected),
                                      "Icon": Variant("s", icon), "UUIDs": Variant("as", list(uuids)),
                                      "Alias": Variant("s", alias)}}
    objects = {
        "/org/bluez/hci0": {"org.bluez.Adapter1": {}},
        "/org/bluez/hci0/dev_DC_1E": dev("DC:1E:D3:39:2C:8D", True, alias="TICKR 9029"),  # bridged
        "/org/bluez/hci0/dev_20_74": dev("20:74:CF:A9:29:10", True, "audio-headset", alias="Headphones"),
        "/org/bluez/hci0/dev_AA_BB": dev("AA:BB:CC:00:00:01", True,
                                        uuids=["0000110b-0000-1000-8000-00805f9b34fb"]),
        "/org/bluez/hci0/dev_AA_CC": dev("AA:BB:CC:00:00:02", False, "audio-headset"),  # not connected
        "/org/bluez/hci1/dev_AA_DD": dev("AA:BB:CC:00:00:03", True, "audio-headset"),  # other adapter
    }
    got = device.foreign_devices(objects, "", ["dc:1e:d3:39:2c:8d"])
    assert got == [{"name": "Headphones", "address": "20:74:CF:A9:29:10", "audio": True},
                   {"name": "AA:BB:CC:00:00:01", "address": "AA:BB:CC:00:00:01", "audio": True}]
    assert [d["address"] for d in device.foreign_devices(objects, "hci1", [])] == ["AA:BB:CC:00:00:03"]
