"""Zugriff der Oberfläche auf den Bridge-Dienst und auf systemd (beides Session-Bus, Gio)."""

from __future__ import annotations

import json
from typing import Callable

from gi.repository import Gio, GLib, GObject

from .. import BRIDGE_BUS_NAME, BRIDGE_OBJECT_PATH, BRIDGE_UNIT

SYSTEMD = "org.freedesktop.systemd1"
SYSTEMD_PATH = "/org/freedesktop/systemd1"
SYSTEMD_MANAGER = "org.freedesktop.systemd1.Manager"


class BridgeClient(GObject.Object):
    """Beobachtet den Dienst und meldet Zustandswechsel als GObject-Signale."""

    __gsignals__ = {
        "status": (GObject.SignalFlags.RUN_FIRST, None, (object,)),  # dict oder None (Dienst aus)
        "error": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self) -> None:
        super().__init__()
        self.bus = Gio.bus_get_sync(Gio.BusType.SESSION)
        self.status: dict | None = None
        self._sub = self.bus.signal_subscribe(BRIDGE_BUS_NAME, BRIDGE_BUS_NAME, "Changed", BRIDGE_OBJECT_PATH,
                                              None, Gio.DBusSignalFlags.NONE, self._on_changed)
        Gio.bus_watch_name_on_connection(self.bus, BRIDGE_BUS_NAME, Gio.BusNameWatcherFlags.NONE,
                                         self._on_appeared, self._on_vanished)

    # --- Dienst ---

    def _call(self, dest: str, path: str, iface: str, member: str, args: GLib.Variant | None,
              reply: str | None, done: Callable | None = None, timeout_ms: int = 5000) -> None:
        def finish(bus, res):
            try:
                result = bus.call_finish(res)
            except GLib.Error as e:
                self.emit("error", e.message)
                if done:
                    done(None)
                return
            if done:
                done(result.unpack() if result is not None else None)
        self.bus.call(dest, path, iface, member, args,
                      GLib.VariantType(reply) if reply else None,
                      Gio.DBusCallFlags.NONE, timeout_ms, None, finish)

    def bridge_call(self, member: str, args: GLib.Variant | None, reply: str, done: Callable | None = None,
                    timeout_ms: int = 5000) -> None:
        self._call(BRIDGE_BUS_NAME, BRIDGE_OBJECT_PATH, BRIDGE_BUS_NAME, member, args, reply, done, timeout_ms)

    def refresh(self) -> None:
        self.bridge_call("GetStatus", None, "(s)", lambda r: r and self._set_status(json.loads(r[0])))

    def scan(self, seconds: int, done: Callable[[list | None], None]) -> None:
        self.bridge_call("Scan", GLib.Variant("(u)", (seconds,)), "(s)",
                         lambda r: done(json.loads(r[0]) if r else None),
                         # Ein laufender Verbindungsaufbau (bis 40 s) hält dieselbe BlueZ-Sperre.
                         timeout_ms=(seconds + 60) * 1000)

    def add_device(self, address: str, name: str, role: str) -> None:
        self.bridge_call("AddDevice", GLib.Variant("(sss)", (address, name, role)), "(s)",
                         lambda r: r and self._set_status(json.loads(r[0])))

    def remove_device(self, address: str) -> None:
        self.bridge_call("RemoveDevice", GLib.Variant("(s)", (address,)), "(b)", lambda _r: self.refresh())

    def set_device_enabled(self, address: str, enabled: bool) -> None:
        self.bridge_call("SetDeviceEnabled", GLib.Variant("(sb)", (address, enabled)), "(b)",
                         lambda _r: self.refresh())

    # --- systemd ---

    def set_running(self, running: bool) -> None:
        self._call(SYSTEMD, SYSTEMD_PATH, SYSTEMD_MANAGER, "StartUnit" if running else "StopUnit",
                   GLib.Variant("(ss)", (BRIDGE_UNIT, "replace")), "(o)")

    def get_autostart(self, done: Callable[[bool], None]) -> None:
        self._call(SYSTEMD, SYSTEMD_PATH, SYSTEMD_MANAGER, "GetUnitFileState", GLib.Variant("(s)", (BRIDGE_UNIT,)),
                   "(s)", lambda r: done(bool(r) and r[0] == "enabled"))

    def set_autostart(self, enabled: bool, done: Callable | None = None) -> None:
        if enabled:
            self._call(SYSTEMD, SYSTEMD_PATH, SYSTEMD_MANAGER, "EnableUnitFiles",
                       GLib.Variant("(asbb)", ([BRIDGE_UNIT], False, True)), "(ba(sss))", done)
        else:
            self._call(SYSTEMD, SYSTEMD_PATH, SYSTEMD_MANAGER, "DisableUnitFiles",
                       GLib.Variant("(asb)", ([BRIDGE_UNIT], False)), "(a(sss))", done)

    # --- Signale ---

    def _set_status(self, status: dict | None) -> None:
        self.status = status
        self.emit("status", status)

    def _on_changed(self, _bus, _sender, _path, _iface, _signal, params) -> None:
        self._set_status(json.loads(params.unpack()[0]))

    def _on_appeared(self, _bus, _name, _owner) -> None:
        self.refresh()

    def _on_vanished(self, _bus, _name) -> None:
        self._set_status(None)
