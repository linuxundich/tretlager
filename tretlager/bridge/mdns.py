"""Announce DIRCON devices via mDNS through avahi-daemon (system D-Bus).

IPv4 only, as in qdomyos-zwift: the TCP server listens on 0.0.0.0, and an AAAA record with a
link-local address makes some clients connect to nowhere.
"""

from __future__ import annotations

import logging

from dbus_fast import BusType, Message, MessageType
from dbus_fast.aio import MessageBus

log = logging.getLogger(__name__)

AVAHI = "org.freedesktop.Avahi"
IF_UNSPEC = -1
PROTO_INET = 0
SERVICE_TYPE = "_wahoo-fitness-tnp._tcp"
PUBLISH_NO_REVERSE = 16  # no PTR record for 127.0.0.1
LOOPBACK = "127.0.0.1"


class Announcer:
    def __init__(self) -> None:
        self._bus: MessageBus | None = None
        self._groups: dict[int, str] = {}  # port -> EntryGroup path

    async def _call(self, path: str, interface: str, member: str, signature: str = "", body=None):
        if self._bus is None:
            self._bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
        reply = await self._bus.call(Message(destination=AVAHI, path=path, interface=interface,
                                             member=member, signature=signature, body=body or []))
        if reply.message_type == MessageType.ERROR:
            raise RuntimeError(f"avahi {member}: {reply.error_name} {reply.body}")
        return reply.body

    async def publish(self, name: str, port: int, service_uuids: list[str], mac: str, serial: str,
                      local_only: bool = True) -> None:
        """Announce a device.

        local_only: Zwift runs on the same computer. The announcement then points to 127.0.0.1;
        that address never goes away, not even when switching between cable and Wi-Fi. With a
        LAN address Zwift would otherwise remember the old address and not find the device again.
        """
        await self.withdraw(port)
        (group,) = await self._call("/", f"{AVAHI}.Server", "EntryGroupNew")
        txt = [f"ble-service-uuids={','.join(u.upper() for u in service_uuids)}".encode(),
               f"mac-address={mac}".encode(),
               f"serial-number={serial}".encode()]
        host = ""
        if local_only:
            host = f"tretlager-{port}.local"
            await self._call(group, f"{AVAHI}.EntryGroup", "AddAddress", "iiuss",
                             [IF_UNSPEC, PROTO_INET, PUBLISH_NO_REVERSE, host, LOOPBACK])
        await self._call(group, f"{AVAHI}.EntryGroup", "AddService", "iiussssqaay",
                         [IF_UNSPEC, PROTO_INET, 0, name, SERVICE_TYPE, "", host, port, txt])
        await self._call(group, f"{AVAHI}.EntryGroup", "Commit")
        self._groups[port] = group
        log.info("mDNS: \"%s\" announced on port %d (%s)", name, port,
                 f"{host} → {LOOPBACK}" if local_only else "LAN addresses")

    async def withdraw(self, port: int) -> None:
        group = self._groups.pop(port, None)
        if group:
            try:
                await self._call(group, f"{AVAHI}.EntryGroup", "Free")
            except Exception as e:
                log.debug("mDNS withdraw port %d: %s", port, e)

    async def close(self) -> None:
        for port in list(self._groups):
            await self.withdraw(port)
        if self._bus:
            self._bus.disconnect()
            self._bus = None
