"""Bridge service: manage devices and make them controllable over D-Bus (session bus).

Interface de.linuxundich.Tretlager.Bridge at /de/linuxundich/Tretlager/Bridge.
State goes out as a JSON string; this keeps the interface lean and the user interface
(GLib/Gio) needs no D-Bus types of its own.
"""

# No `from __future__ import annotations`: dbus-fast reads the signatures ("s", "u", …) from
# the annotations.
import asyncio
import json
import logging
import signal

from bleak import BleakScanner
from bleak.exc import BleakDBusError
from dbus_fast.aio import MessageBus
from dbus_fast.service import ServiceInterface, method, signal as dbus_signal

from .. import BRIDGE_BUS_NAME, BRIDGE_OBJECT_PATH, __version__
from . import adapters, gatt
from .config import BridgeConfig
from .device import BridgedDevice, connect_lock
from .mdns import Announcer

log = logging.getLogger(__name__)

TICK = 1.0  # seconds between live updates


class Bridge(ServiceInterface):
    def __init__(self) -> None:
        super().__init__(BRIDGE_BUS_NAME)
        self.config = BridgeConfig.load()
        self.announcer = Announcer()
        self.devices: dict[str, BridgedDevice] = {}
        self.scanning = False
        self._dirty = True
        self.stop_event = asyncio.Event()
        self.adapters: dict[str, str] = {}  # hciN -> address according to BlueZ
        self.hci = ""  # resolved adapter, empty = default
        self.adapter_missing = False
        self._adapter_check = 0

    async def resolve_adapter(self) -> bool:
        """Resolve the selected adapter; True if the adapter in use has changed."""
        self.adapters = await adapters.bluez_adapters()
        hci, missing = adapters.resolve(self.config.adapter, self.adapters)
        changed = hci != self.hci
        newly_missing = missing and not self.adapter_missing
        self.hci, self.adapter_missing = hci, missing
        if newly_missing:
            log.warning("adapter %s missing, using default adapter", self.config.adapter)
        if changed:
            log.info("adapter: %s", hci or "default")
        return changed

    async def restart_devices(self) -> None:
        for address in list(self.devices):
            await self._stop(address)
        self.start_devices()
        self._mark_dirty()

    # --- Lifecycle ---

    def start_devices(self) -> None:
        # Trainer first: connections are made one after another, and a sleeping strap should not
        # hold up the trainer.
        for cfg in sorted(self.config.devices, key=lambda c: c.role != "trainer"):
            if cfg.enabled:
                self._start(cfg.address)

    def _start(self, address: str) -> None:
        cfg = self.config.find(address)
        if cfg and address not in self.devices:
            dev = BridgedDevice(cfg, self.announcer, self._mark_dirty, local_only=self.config.local_only,
                                adapter=self.hci)
            self.devices[address] = dev
            dev.start()

    async def _stop(self, address: str) -> None:
        dev = self.devices.pop(address, None)
        if dev:
            await dev.stop()

    async def shutdown(self) -> None:
        for address in list(self.devices):
            await self._stop(address)
        await self.announcer.close()

    async def tick(self) -> None:
        while True:
            await asyncio.sleep(TICK)
            # If an adapter is selected, check every ten seconds whether it is still present and
            # powered (USB dongle unplugged or switched off), or has come back.
            self._adapter_check += 1
            if self.config.adapter and self._adapter_check % 10 == 0:
                if await self.resolve_adapter():
                    await self.restart_devices()
            live = any(d.state == "connected" for d in self.devices.values())
            if self._dirty or live:
                self._dirty = False
                self.Changed(self._status_json())

    def _mark_dirty(self) -> None:
        self._dirty = True

    def _status_json(self) -> str:
        devices = []
        for cfg in self.config.devices:
            dev = self.devices.get(cfg.address)
            if dev:
                devices.append(dev.status())
            else:
                devices.append({"address": cfg.address, "name": cfg.name, "role": cfg.role,
                                "enabled": cfg.enabled, "port": cfg.port, "state": "paused",
                                "error": "", "services": [], "zwift_clients": 0, "values": {}})
        return json.dumps({"running": True, "version": __version__, "scanning": self.scanning,
                           "local_only": self.config.local_only,
                           "adapter": self.config.adapter, "adapter_hci": self.hci or next(iter(self.adapters), ""),
                           "adapter_missing": self.adapter_missing, "devices": devices})

    # --- D-Bus ---

    @method()
    def GetStatus(self) -> "s":
        return self._status_json()

    @method()
    async def Scan(self, seconds: "u") -> "s":
        """Scan for BLE devices in range that advertise a service the bridge can relay."""
        self.scanning = True
        self._mark_dirty()
        try:
            found = await self._discover(float(min(max(seconds, 3), 30)))
        finally:
            self.scanning = False
            self._mark_dirty()
        out = []
        for address, (device, adv) in found.items():
            uuids = [u.lower() for u in adv.service_uuids]
            bridged = [u for u in uuids if u in gatt.BRIDGED_SERVICES]
            if not bridged:
                continue
            out.append({"address": address.upper(), "name": adv.local_name or device.name or address,
                        "rssi": adv.rssi, "services": bridged, "role": gatt.role_for(bridged),
                        "configured": self.config.find(address) is not None})
        out.sort(key=lambda d: -d["rssi"])
        return json.dumps(out)

    async def _discover(self, seconds: float) -> dict:
        # Same lock as for connecting: BlueZ does not scan and connect in parallel.
        for attempt in range(3):
            try:
                async with connect_lock:
                    return await BleakScanner.discover(timeout=seconds, return_adv=True,
                                                       bluez={"adapter": self.hci} if self.hci else {})
            except BleakDBusError as e:
                if "InProgress" not in e.dbus_error or attempt == 2:
                    raise
                await asyncio.sleep(2)
        return {}

    @method()
    def AddDevice(self, address: "s", name: "s", role: "s") -> "s":
        cfg = self.config.add(address, name, role)
        self.config.save()
        self._start(cfg.address)
        self._mark_dirty()
        return self._status_json()

    @method()
    async def RemoveDevice(self, address: "s") -> "b":
        address = address.upper()
        await self._stop(address)
        removed = self.config.remove(address)
        self.config.save()
        self._mark_dirty()
        return removed

    @method()
    async def SetDeviceEnabled(self, address: "s", enabled: "b") -> "b":
        cfg = self.config.find(address)
        if not cfg:
            return False
        cfg.enabled = enabled
        self.config.save()
        if enabled:
            self._start(cfg.address)
        else:
            await self._stop(cfg.address)
        self._mark_dirty()
        return True

    @method()
    async def SetLocalOnly(self, local_only: "b") -> "b":
        """Only for Zwift on this computer (True) or also in the network (False); re-announce devices."""
        if self.config.local_only == local_only:
            return True
        self.config.local_only = local_only
        self.config.save()
        await self.restart_devices()
        return True

    @method()
    async def SetAdapter(self, address: "s") -> "b":
        """Select the Bluetooth adapter by address (empty = default); reconnect devices through it."""
        address = address.upper()
        if address == self.config.adapter:
            return True
        self.config.adapter = address
        self.config.save()
        await self.resolve_adapter()
        await self.restart_devices()
        return True

    @method()
    def Quit(self) -> "b":
        """Quit the bridge (replaces `systemctl stop`; devices are disconnected cleanly)."""
        log.info("quit requested over D-Bus")
        self.stop_event.set()
        return True

    @dbus_signal()
    def Changed(self, status: "s") -> "s":
        return status


async def run() -> None:
    bridge = Bridge()
    bus = await MessageBus().connect()
    bus.export(BRIDGE_OBJECT_PATH, bridge)
    await bus.request_name(BRIDGE_BUS_NAME)
    log.info("bridge ready, %d device(s) configured", len(bridge.config.devices))
    await bridge.resolve_adapter()
    bridge.start_devices()

    stop = bridge.stop_event
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set)
    ticker = asyncio.create_task(bridge.tick())
    await stop.wait()
    ticker.cancel()
    await bridge.shutdown()
    bus.disconnect()
    log.info("bridge stopped")
