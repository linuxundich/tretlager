#!/usr/bin/env python3
"""Passive Bluetooth observer for sensor problems; runs inside the Tretlager Flatpak.

Writes JSON lines (wall-clock time "t", kind "k") with:
- BlueZ events of the bridged sensors: Connected, ServicesResolved, RSSI, Disconnected(reason)
- adapter events: Powered, Discovering, adapters appearing and disappearing
- bridge state per device (only changes) and the heart rate once per second
- optionally advertising seen on a second adapter (observer scan): tells "strap advertises but
  the bridge cannot connect" apart from "strap is silent"

It never connects to anything itself.
"""

import argparse
import asyncio
import json
import time

from dbus_fast import BusType, Message, MessageType, Variant
from dbus_fast.aio import MessageBus

BRIDGE = ("de.linuxundich.Tretlager.Bridge", "/de/linuxundich/Tretlager/Bridge", "de.linuxundich.Tretlager.Bridge")
OBSERVE_CYCLE = 10.0  # restart discovery so BlueZ reports every advertising device again

out = None


def emit(kind: str, **kw) -> None:
    out.write(json.dumps({"t": round(time.time(), 3), "k": kind, **kw}, default=str) + "\n")


def plain(v):
    if isinstance(v, Variant):
        return plain(v.value)
    if isinstance(v, (bytes, bytearray)):
        return bytes(v).hex()
    if isinstance(v, dict):
        return {k: plain(x) for k, x in v.items()}
    if isinstance(v, list):
        return [plain(x) for x in v]
    return v


def split_path(path: str):
    """/org/bluez/hci1/dev_AA_BB…[/service…] → ("hci1", "AA:BB:…" or "", rest)."""
    parts = path.split("/")
    hci = parts[3] if len(parts) > 3 else ""
    dev = parts[4][4:].replace("_", ":") if len(parts) > 4 and parts[4].startswith("dev_") else ""
    return hci, dev, "/".join(parts[5:])


class Probe:
    def __init__(self, args):
        self.args = args
        self.watch: set[str] = {a.upper() for a in args.address}
        self.bridge_hci = ""
        self.observer = ""
        self.last_bridge: dict[str, tuple] = {}
        self.last_hr: dict[str, tuple] = {}
        self.adv: dict[tuple, list] = {}  # (hci, address) -> [count, last rssi, min, max]

    def watched(self, address: str) -> bool:
        return self.args.all or address.upper() in self.watch

    # --- BlueZ signals ---

    def on_message(self, msg: Message):
        if msg.message_type != MessageType.SIGNAL or not (msg.path or "").startswith("/org/bluez"):
            return
        hci, dev, rest = split_path(msg.path)
        if msg.member == "PropertiesChanged":
            iface, changed, invalidated = msg.body
            changed = {k: plain(v) for k, v in changed.items()}
            if iface == "org.bluez.Adapter1":
                keep = {k: v for k, v in changed.items() if k in ("Powered", "Discovering", "PowerState", "Connectable")}
                if keep:
                    emit("adapter", hci=hci, **keep)
            elif iface == "org.bluez.Device1" and dev and not rest:
                if hci == self.observer and hci != self.bridge_hci:
                    if "RSSI" in changed and self.watched(dev):
                        a = self.adv.setdefault((hci, dev), [0, None, 999, -999])
                        rssi = changed["RSSI"]
                        a[0] += 1
                        a[1] = rssi
                        a[2] = min(a[2], rssi)
                        a[3] = max(a[3], rssi)
                    return
                if not self.watched(dev):
                    if "Connected" in changed:  # other devices (headphones) still matter
                        emit("other", hci=hci, dev=dev, Connected=changed["Connected"])
                    return
                keep = {k: v for k, v in changed.items() if k not in ("ManufacturerData", "ServiceData", "AdvertisingFlags")}
                if keep or invalidated:
                    emit("dev", hci=hci, dev=dev, **keep, **({"invalidated": invalidated} if invalidated else {}))
            elif iface == "org.bluez.GattCharacteristic1" and dev and self.watched(dev) and "Value" in changed:
                emit("notify", hci=hci, dev=dev, char=rest, value=changed["Value"])
        elif msg.member == "Disconnected" and msg.interface == "org.bluez.Device1":
            if dev and (self.watched(dev) or hci != self.observer):
                emit("disconnected", hci=hci, dev=dev, reason=plain(msg.body[0]) if msg.body else "",
                     message=plain(msg.body[1]) if len(msg.body) > 1 else "")
        elif msg.member == "InterfacesAdded":
            path, ifaces = msg.body
            hci, dev, rest = split_path(path)
            if "org.bluez.Adapter1" in ifaces:
                emit("adapter-added", hci=hci, address=plain(ifaces["org.bluez.Adapter1"].get("Address")))
            elif "org.bluez.Device1" in ifaces and dev and self.watched(dev) and hci != self.observer:
                p = ifaces["org.bluez.Device1"]
                emit("dev-added", hci=hci, dev=dev, RSSI=plain(p.get("RSSI")), Connected=plain(p.get("Connected")))
        elif msg.member == "InterfacesRemoved":
            path, ifaces = msg.body
            hci, dev, rest = split_path(path)
            if "org.bluez.Adapter1" in ifaces:
                emit("adapter-removed", hci=hci)
            elif "org.bluez.Device1" in ifaces and dev and self.watched(dev) and hci != self.observer:
                emit("dev-removed", hci=hci, dev=dev)

    # --- Bridge state ---

    async def poll_bridge(self, session: MessageBus, once: bool = False):
        while True:
            try:
                reply = await session.call(Message(destination=BRIDGE[0], path=BRIDGE[1], interface=BRIDGE[2],
                                                   member="GetStatus"))
                if reply.message_type == MessageType.ERROR:
                    if self.last_bridge.get("_") != ("down",):
                        emit("bridge", running=False, error=reply.error_name)
                        self.last_bridge["_"] = ("down",)
                else:
                    self.on_bridge(json.loads(reply.body[0]))
            except Exception as e:  # keep observing whatever happens
                emit("probe-error", where="bridge", error=repr(e))
            if once:
                return
            await asyncio.sleep(1.0)

    def on_bridge(self, st: dict):
        top = ("up", st.get("version"), st.get("adapter_hci"), st.get("adapter_missing"),
               json.dumps(st.get("other_devices")))
        if self.last_bridge.get("_") != top:
            emit("bridge", running=True, version=st.get("version"), adapter_hci=st.get("adapter_hci"),
                 adapter_missing=st.get("adapter_missing"), other_devices=st.get("other_devices"))
            self.last_bridge["_"] = top
        self.bridge_hci = st.get("adapter_hci") or self.bridge_hci
        for d in st.get("devices", []):
            addr = d["address"].upper()
            self.watch.add(addr)
            key = (d.get("state"), d.get("error"), d.get("unstable"), d.get("zwift_clients"), d.get("enabled"))
            if self.last_bridge.get(addr) != key:
                emit("bstate", dev=addr, name=d.get("name"), state=d.get("state"), error=d.get("error"),
                     unstable=d.get("unstable"), zwift=d.get("zwift_clients"), enabled=d.get("enabled"))
                self.last_bridge[addr] = key
            hr = (d.get("values") or {}).get("heart_rate")
            if d.get("role") == "heartrate":
                # every second while values come in, once when they stop
                if hr is not None or self.last_hr.get(addr) != (None,):
                    emit("hr", dev=addr, bpm=hr)
                self.last_hr[addr] = (hr,)

    # --- Observer scan on a second adapter ---

    async def observe(self, system: MessageBus):
        await asyncio.sleep(3.0)  # let the bridge state tell us its adapter first
        adapters = await self.adapters(system)
        if self.args.observe == "auto":
            others = [h for h in adapters if h != self.bridge_hci]
            self.observer = others[0] if others and self.bridge_hci else ""
        elif self.args.observe != "none":
            self.observer = self.args.observe
        if not self.observer:
            emit("observer", hci="", note="no second adapter, observer scan off")
            return
        if self.observer == self.bridge_hci:
            emit("observer", hci=self.observer, note="same adapter as the bridge, observer scan off")
            self.observer = ""
            return
        emit("observer", hci=self.observer, address=adapters.get(self.observer))
        path = f"/org/bluez/{self.observer}"
        await system.call(Message(destination="org.bluez", path=path, interface="org.bluez.Adapter1",
                                  member="SetDiscoveryFilter", signature="a{sv}",
                                  body=[{"Transport": Variant("s", "le"), "DuplicateData": Variant("b", True)}]))
        while True:
            for member in ("StartDiscovery",):
                reply = await system.call(Message(destination="org.bluez", path=path,
                                                  interface="org.bluez.Adapter1", member=member))
                if reply.message_type == MessageType.ERROR and "InProgress" not in (reply.error_name or ""):
                    emit("probe-error", where="observer", error=f"{reply.error_name}: {reply.body}")
            await asyncio.sleep(OBSERVE_CYCLE)
            await system.call(Message(destination="org.bluez", path=path, interface="org.bluez.Adapter1",
                                      member="StopDiscovery"))
            seen = {dev for (h, dev) in self.adv}
            for (h, dev), (n, rssi, lo, hi) in sorted(self.adv.items()):
                emit("adv", hci=h, dev=dev, n=n, rssi=rssi, min=lo, max=hi, window=OBSERVE_CYCLE)
            for dev in sorted(self.watch - seen):
                emit("adv", hci=self.observer, dev=dev, n=0, window=OBSERVE_CYCLE)
            self.adv.clear()
            await asyncio.sleep(0.5)

    async def adapters(self, system: MessageBus) -> dict:
        reply = await system.call(Message(destination="org.bluez", path="/",
                                          interface="org.freedesktop.DBus.ObjectManager", member="GetManagedObjects"))
        out = {}
        if reply.message_type != MessageType.ERROR:
            for path, ifaces in reply.body[0].items():
                if "org.bluez.Adapter1" in ifaces:
                    out[path.split("/")[-1]] = plain(ifaces["org.bluez.Adapter1"]["Address"])
        return out

    async def snapshot(self, system: MessageBus):
        """Initial state of adapters and watched devices."""
        reply = await system.call(Message(destination="org.bluez", path="/",
                                          interface="org.freedesktop.DBus.ObjectManager", member="GetManagedObjects"))
        if reply.message_type == MessageType.ERROR:
            emit("probe-error", where="snapshot", error=reply.error_name)
            return
        for path, ifaces in sorted(reply.body[0].items()):
            hci, dev, rest = split_path(path)
            if "org.bluez.Adapter1" in ifaces:
                a = ifaces["org.bluez.Adapter1"]
                emit("snap-adapter", hci=hci, **{k: plain(a[k]) for k in ("Address", "Name", "Powered", "Discovering")
                                                  if k in a})
            elif "org.bluez.Device1" in ifaces and dev:
                d = ifaces["org.bluez.Device1"]
                if self.watched(dev) or plain(d.get("Connected")):
                    emit("snap-dev", hci=hci, dev=dev, **{k: plain(d[k]) for k in
                                                         ("Alias", "Connected", "ServicesResolved", "Paired",
                                                          "Trusted", "Bonded", "AddressType", "RSSI") if k in d})

    async def run(self):
        system = await MessageBus(bus_type=BusType.SYSTEM).connect()
        session = await MessageBus(bus_type=BusType.SESSION).connect()
        for rule in ("type='signal',sender='org.bluez',interface='org.freedesktop.DBus.Properties',member='PropertiesChanged'",
                     "type='signal',sender='org.bluez',interface='org.freedesktop.DBus.ObjectManager'",
                     "type='signal',sender='org.bluez',interface='org.bluez.Device1'"):
            await system.call(Message(destination="org.freedesktop.DBus", path="/org/freedesktop/DBus",
                                      interface="org.freedesktop.DBus", member="AddMatch", signature="s", body=[rule]))
        system.add_message_handler(self.on_message)
        await self.poll_bridge(session, once=True)  # learn the sensor addresses first
        emit("probe-start", watch=sorted(self.watch), observe=self.args.observe)
        await self.snapshot(system)
        await asyncio.gather(self.poll_bridge(session), self.observe(system))


def main():
    global out
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--observe", default="auto", help="auto, none or hciN (never the bridge's adapter)")
    ap.add_argument("--address", action="append", default=[], help="extra sensor address to watch")
    ap.add_argument("--all", action="store_true", help="log every BlueZ device, not only the sensors")
    args = ap.parse_args()
    out = open(args.out, "a", buffering=1, encoding="utf-8")
    try:
        asyncio.run(Probe(args).run())
    except KeyboardInterrupt:
        pass
    finally:
        emit("probe-stop")


if __name__ == "__main__":
    main()
