"""Bridge-Dienst: Geräte verwalten und über D-Bus (Session-Bus) steuerbar machen.

Schnittstelle de.linuxundich.Tretlager.Bridge unter /de/linuxundich/Tretlager/Bridge.
Zustände gehen als JSON-Zeichenkette hinaus; so bleibt die Schnittstelle schlank und die
Oberfläche (GLib/Gio) braucht keine eigenen D-Bus-Typen.
"""

# Kein `from __future__ import annotations`: dbus-fast liest die Signaturen ("s", "u", …) aus
# den Annotationen.
import asyncio
import json
import logging
import signal

from bleak import BleakScanner
from bleak.exc import BleakDBusError
from dbus_fast.aio import MessageBus
from dbus_fast.service import ServiceInterface, method, signal as dbus_signal

from .. import BRIDGE_BUS_NAME, BRIDGE_OBJECT_PATH
from . import gatt
from .config import BridgeConfig
from .device import BridgedDevice, connect_lock
from .mdns import Announcer

log = logging.getLogger(__name__)

TICK = 1.0  # Sekunden zwischen Live-Aktualisierungen


class Bridge(ServiceInterface):
    def __init__(self) -> None:
        super().__init__(BRIDGE_BUS_NAME)
        self.config = BridgeConfig.load()
        self.announcer = Announcer()
        self.devices: dict[str, BridgedDevice] = {}
        self.scanning = False
        self._dirty = True

    # --- Lebenszyklus ---

    def start_devices(self) -> None:
        for cfg in self.config.devices:
            if cfg.enabled:
                self._start(cfg.address)

    def _start(self, address: str) -> None:
        cfg = self.config.find(address)
        if cfg and address not in self.devices:
            dev = BridgedDevice(cfg, self.announcer, self._mark_dirty, local_only=self.config.local_only)
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
            live = any(d.state == "verbunden" for d in self.devices.values())
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
                                "enabled": cfg.enabled, "port": cfg.port, "state": "aus",
                                "error": "", "services": [], "zwift_clients": 0, "values": {}})
        return json.dumps({"running": True, "scanning": self.scanning, "devices": devices})

    # --- D-Bus ---

    @method()
    def GetStatus(self) -> "s":
        return self._status_json()

    @method()
    async def Scan(self, seconds: "u") -> "s":
        """BLE-Geräte in Reichweite suchen, die einen überbrückbaren Dienst ankündigen."""
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
        # Gleiche Sperre wie beim Verbinden: BlueZ scannt und verbindet nicht parallel.
        for attempt in range(3):
            try:
                async with connect_lock:
                    return await BleakScanner.discover(timeout=seconds, return_adv=True)
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

    @dbus_signal()
    def Changed(self, status: "s") -> "s":
        return status


async def run() -> None:
    bridge = Bridge()
    bus = await MessageBus().connect()
    bus.export(BRIDGE_OBJECT_PATH, bridge)
    await bus.request_name(BRIDGE_BUS_NAME)
    log.info("Bridge bereit, %d Gerät(e) konfiguriert", len(bridge.config.devices))
    bridge.start_devices()

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set)
    ticker = asyncio.create_task(bridge.tick())
    await stop.wait()
    ticker.cancel()
    await bridge.shutdown()
    bus.disconnect()
    log.info("Bridge beendet")
