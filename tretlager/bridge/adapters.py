"""Bluetooth-Adapter der Bridge auswählen.

Gespeichert wird die Adresse des Adapters, nicht der Name hciN: Die Nummer hängt von der
Reihenfolge ab, in der die Adapter erscheinen, und ändert sich etwa beim Umstecken eines
USB-Sticks. Beim Start und bei jeder Änderung wird die Adresse auf den aktuellen hciN-Namen
aufgelöst. Ohne Auswahl oder wenn der gewählte Adapter fehlt, nutzt die Bridge den
Standardadapter von BlueZ.
"""

from __future__ import annotations

from dbus_fast import BusType, Message, MessageType
from dbus_fast.aio import MessageBus


async def bluez_adapters() -> dict[str, str]:
    """Adapter laut BlueZ als {"hci0": "AA:BB:…"}; leer, wenn BlueZ nicht antwortet."""
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
            if adapter and "Address" in adapter:
                out[path.rsplit("/", 1)[-1]] = adapter["Address"].value.upper()
        return dict(sorted(out.items()))
    finally:
        bus.disconnect()


def resolve(wanted: str, adapters: dict[str, str]) -> tuple[str, bool]:
    """hciN für die gewünschte Adresse; ("", True), wenn sie gewählt ist, aber fehlt."""
    if not wanted:
        return "", False
    for hci, address in adapters.items():
        if address == wanted.upper():
            return hci, False
    return "", True
