"""Select the bridge's Bluetooth adapter.

The adapter's address is stored, not its hciN name: the number depends on the order in which
the adapters appear and changes, for example, when a USB dongle is replugged. On start and on
every change the address is resolved to the current hciN name. Without a selection, or if the
selected adapter is missing, the bridge uses the BlueZ default adapter. Powered-off adapters
count as missing.
"""

from __future__ import annotations

from dbus_fast import BusType, Message, MessageType
from dbus_fast.aio import MessageBus


async def bluez_adapters() -> dict[str, str]:
    """Powered adapters according to BlueZ as {"hci0": "AA:BB:…"}; empty if BlueZ does not answer."""
    try:
        bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
    except Exception:
        return {}
    try:
        reply = await bus.call(Message(destination="org.bluez", path="/",
                                       interface="org.freedesktop.DBus.ObjectManager",
                                       member="GetManagedObjects"))
        if reply.message_type == MessageType.ERROR:
            return {}
        out = {}
        for path, ifaces in reply.body[0].items():
            adapter = ifaces.get("org.bluez.Adapter1")
            # Powered-off adapters count as missing: no connection can be made through them.
            if adapter and "Address" in adapter and adapter.get("Powered") and adapter["Powered"].value:
                out[path.rsplit("/", 1)[-1]] = adapter["Address"].value.upper()
        return dict(sorted(out.items()))
    finally:
        bus.disconnect()


def resolve(wanted: str, adapters: dict[str, str]) -> tuple[str, bool]:
    """hciN for the wanted address; ("", True) if it is selected but missing."""
    if not wanted:
        return "", False
    for hci, address in adapters.items():
        if address == wanted.upper():
            return hci, False
    return "", True
