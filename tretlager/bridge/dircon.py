"""Wahoo Direct Connect (DIRCON): GATT über TCP.

Wahoo veröffentlicht keine Spezifikation. Das Format folgt dem Verhalten echter Geräte, wie es
qdomyos-zwift (src/devices/dircon/, GPL-3.0) nachbildet:

    Kopf (6 Byte): Version (1) | Nachricht | Sequenz | Antwortcode | Länge (uint16, Big Endian)
    Nutzdaten:     UUIDs immer als 16 Byte (128 Bit), gefolgt von nachrichtenabhängigen Daten

Dieses Modul kennt nur das Format und die Antwortlogik; woher die GATT-Werte kommen, entscheidet
der Aufrufer über die Schnittstelle `GattBackend`.
"""

from __future__ import annotations

import asyncio
import fcntl
import logging
import socket
import struct
import uuid as uuidlib
from dataclasses import dataclass, field
from typing import Protocol

log = logging.getLogger(__name__)

HEADER = struct.Struct(">BBBBH")
VERSION = 1

MSG_DISCOVER_SERVICES = 0x01
MSG_DISCOVER_CHARACTERISTICS = 0x02
MSG_READ_CHARACTERISTIC = 0x03
MSG_WRITE_CHARACTERISTIC = 0x04
MSG_ENABLE_NOTIFICATIONS = 0x05
MSG_NOTIFICATION = 0x06
MSG_UNKNOWN_07 = 0x07

RESP_SUCCESS = 0x00
RESP_UNKNOWN_MESSAGE = 0x01
RESP_UNEXPECTED_ERROR = 0x02
RESP_SERVICE_NOT_FOUND = 0x03
RESP_CHARACTERISTIC_NOT_FOUND = 0x04
RESP_OPERATION_NOT_SUPPORTED = 0x05
RESP_WRITE_FAILED = 0x06

PROP_READ = 0x01
PROP_WRITE = 0x02
PROP_NOTIFY = 0x04
PROP_INDICATE = 0x08

BLUETOOTH_BASE = "0000{:04x}-0000-1000-8000-00805f9b34fb"

ADDRESS_CHECK_INTERVAL = 3.0
MAX_SEND_BUFFER = 64 * 1024  # Bytes; Messwert-Pakete sind 20–30 Bytes groß
SIOCGIFADDR = 0x8915


def local_ipv4_addresses() -> set[str]:
    """IPv4-Adressen aller Schnittstellen (ohne externe Werkzeuge, per ioctl)."""
    out = set()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        for _index, name in socket.if_nameindex():
            try:
                req = struct.pack("256s", name.encode()[:15])
                out.add(socket.inet_ntoa(fcntl.ioctl(s.fileno(), SIOCGIFADDR, req)[20:24]))
            except OSError:
                pass  # Schnittstelle ohne IPv4-Adresse
    return out


def full_uuid(value: str | int) -> str:
    """Kurze (0x2AD2, "2ad2") oder lange UUID in die kleingeschriebene 128-Bit-Form bringen."""
    if isinstance(value, int):
        return BLUETOOTH_BASE.format(value)
    v = value.strip().lower()
    if v.startswith("0x"):
        v = v[2:]
    if len(v) <= 4:
        return BLUETOOTH_BASE.format(int(v, 16))
    return str(uuidlib.UUID(v))


def uuid_bytes(value: str) -> bytes:
    return uuidlib.UUID(full_uuid(value)).bytes


def uuid_from_bytes(raw: bytes) -> str:
    return str(uuidlib.UUID(bytes=bytes(raw[:16])))


@dataclass
class Packet:
    message: int
    sequence: int = 0
    response: int = RESP_SUCCESS
    payload: bytes = b""

    def encode(self) -> bytes:
        return HEADER.pack(VERSION, self.message, self.sequence & 0xFF, self.response, len(self.payload)) + self.payload


def parse_packets(buf: bytearray) -> list[Packet]:
    """Vollständige Pakete aus `buf` lösen; unvollständige Reste bleiben im Puffer."""
    out = []
    while len(buf) >= HEADER.size:
        version, message, sequence, response, length = HEADER.unpack_from(buf)
        if len(buf) < HEADER.size + length:
            break
        payload = bytes(buf[HEADER.size:HEADER.size + length])
        del buf[:HEADER.size + length]
        if version != VERSION:
            log.warning("DIRCON-Version %d unbekannt, Paket verworfen", version)
            continue
        out.append(Packet(message, sequence, response, payload))
    return out


@dataclass
class Characteristic:
    uuid: str
    properties: int  # PROP_*


@dataclass
class Service:
    uuid: str
    characteristics: list[Characteristic] = field(default_factory=list)


class GattBackend(Protocol):
    """Was der DIRCON-Server von der Gegenseite (dem echten BLE-Gerät) braucht."""

    def services(self) -> list[Service]: ...

    async def read(self, char_uuid: str) -> bytes: ...

    async def write(self, char_uuid: str, data: bytes) -> bytes | None:
        """Schreiben; bei Control Points die Antwort des Geräts (Indication) zurückgeben."""
        ...

    async def set_notify(self, char_uuid: str, enabled: bool) -> None: ...


class Session:
    """Eine TCP-Verbindung eines DIRCON-Clients (Zwift)."""

    def __init__(self, backend: GattBackend, writer: asyncio.StreamWriter | None):
        self.backend = backend
        self.writer = writer
        self.subscribed: set[str] = set()

    def _find_char(self, char_uuid: str) -> Characteristic | None:
        for s in self.backend.services():
            for c in s.characteristics:
                if c.uuid == char_uuid:
                    return c
        return None

    async def handle(self, pkt: Packet) -> Packet | None:
        """Antwort auf eine Anfrage berechnen (None = keine Antwort senden)."""
        if pkt.response != RESP_SUCCESS:
            return None  # Antworten oder Fehler der Gegenseite ignorieren wir
        m = pkt.message
        reply = Packet(m, pkt.sequence)

        if m == MSG_DISCOVER_SERVICES:
            reply.payload = b"".join(uuid_bytes(s.uuid) for s in self.backend.services())
            return reply

        if m == MSG_UNKNOWN_07:
            return reply

        if len(pkt.payload) < 16:
            reply.response = RESP_UNEXPECTED_ERROR
            return reply
        target = uuid_from_bytes(pkt.payload)
        data = pkt.payload[16:]

        if m == MSG_DISCOVER_CHARACTERISTICS:
            for s in self.backend.services():
                if s.uuid == target:
                    reply.payload = uuid_bytes(s.uuid) + b"".join(
                        uuid_bytes(c.uuid) + bytes([c.properties]) for c in s.characteristics)
                    return reply
            reply.response = RESP_SERVICE_NOT_FOUND
            return reply

        char = self._find_char(target)
        if char is None:
            reply.response = RESP_CHARACTERISTIC_NOT_FOUND
            return reply

        if m == MSG_READ_CHARACTERISTIC:
            if not char.properties & PROP_READ:
                reply.response = RESP_OPERATION_NOT_SUPPORTED
                return reply
            try:
                reply.payload = uuid_bytes(target) + await self.backend.read(target)
            except Exception as e:  # BLE-Fehler werden zu DIRCON-Fehlern
                log.warning("Lesen %s fehlgeschlagen: %s", target, e)
                reply.response = RESP_UNEXPECTED_ERROR
            return reply

        if m == MSG_WRITE_CHARACTERISTIC:
            if not char.properties & PROP_WRITE:
                reply.response = RESP_OPERATION_NOT_SUPPORTED
                return reply
            try:
                answer = await self.backend.write(target, data)
                # Bei Control Points erwartet Zwift die Antwort des Geräts (z. B. FTMS 0x80,
                # Befehl, Ergebnis) direkt in der Schreib-Antwort, wie bei qdomyos-zwift; sonst
                # wiederholt Zwift den Befehl und setzt den Trainer zurück. Ohne Antwort: Echo.
                reply.payload = uuid_bytes(target) + (answer if answer is not None else data)
            except Exception as e:
                log.warning("Schreiben %s fehlgeschlagen: %s", target, e)
                reply.response = RESP_WRITE_FAILED
            return reply

        if m == MSG_ENABLE_NOTIFICATIONS:
            if not char.properties & (PROP_NOTIFY | PROP_INDICATE):
                reply.response = RESP_OPERATION_NOT_SUPPORTED
                return reply
            enable = bool(data[0]) if data else True
            if enable:
                self.subscribed.add(target)
            else:
                self.subscribed.discard(target)
            try:
                await self.backend.set_notify(target, enable)
            except Exception as e:
                log.warning("Benachrichtigung %s fehlgeschlagen: %s", target, e)
                reply.response = RESP_UNEXPECTED_ERROR
                return reply
            reply.payload = uuid_bytes(target)
            return reply

        reply.response = RESP_UNKNOWN_MESSAGE
        reply.payload = b""
        return reply

    def notify(self, char_uuid: str, value: bytes, strict: bool = False) -> None:
        # Wie qdomyos-zwift (Standard): Benachrichtigungen gehen an jeden Client, auch ohne
        # Abo. Zwift verlässt sich darauf, z. B. für die Antworten des Control Points.
        if self.writer is None or (strict and char_uuid not in self.subscribed):
            return
        # Liest der Client nicht mehr (Zwift hängt), Messwerte verwerfen statt den Puffer
        # unbegrenzt wachsen zu lassen; veraltete Werte nützen ohnehin niemandem.
        transport = getattr(self.writer, "transport", None)
        if transport is not None and transport.get_write_buffer_size() > MAX_SEND_BUFFER:
            return
        self.writer.write(Packet(MSG_NOTIFICATION, 0, RESP_SUCCESS, uuid_bytes(char_uuid) + value).encode())


class Server:
    """TCP-Server für ein Gerät; mehrere Clients gleichzeitig sind erlaubt."""

    def __init__(self, backend: GattBackend, host: str = "0.0.0.0", port: int = 36866):
        self.backend = backend
        self.host = host
        self.port = port
        self.sessions: set[Session] = set()
        self._server: asyncio.base_events.Server | None = None
        self._watchdog: asyncio.Task | None = None

    async def start(self) -> None:
        self._server = await asyncio.start_server(self._client, self.host, self.port)
        self._watchdog = asyncio.create_task(self._watch_addresses())
        log.info("DIRCON lauscht auf %s:%d", self.host, self.port)

    async def _watch_addresses(self) -> None:
        """Verbindungen schließen, deren lokale Adresse verschwunden ist (Kabel ab, WLAN-Wechsel).

        TCP merkt das sonst erst nach Minuten; Zwift wartet so lange auf Daten, die nie kommen,
        statt sich über die neue Adresse wieder zu verbinden.
        """
        while True:
            await asyncio.sleep(ADDRESS_CHECK_INTERVAL)
            current = local_ipv4_addresses()
            for s in list(self.sessions):
                local = s.writer.get_extra_info("sockname") if s.writer else None
                if local and local[0] not in current and not local[0].startswith("127."):
                    log.info("DIRCON: lokale Adresse %s ist weg, Verbindung wird geschlossen", local[0])
                    s.writer.transport.abort()

    async def stop(self) -> None:
        if self._watchdog:
            self._watchdog.cancel()
            self._watchdog = None
        if self._server:
            self._server.close()
            for s in list(self.sessions):
                if s.writer:
                    s.writer.close()
            await self._server.wait_closed()
            self._server = None

    def notify(self, char_uuid: str, value: bytes) -> None:
        for s in list(self.sessions):
            s.notify(char_uuid, value)

    @property
    def running(self) -> bool:
        return self._server is not None

    def subscribed(self) -> set[str]:
        """Merkmale, die mindestens ein Client abonniert hat."""
        return set().union(*(s.subscribed for s in self.sessions)) if self.sessions else set()

    @property
    def client_count(self) -> int:
        return len(self.sessions)

    async def _client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername")
        session = Session(self.backend, writer)
        self.sessions.add(session)
        log.info("DIRCON-Client verbunden: %s", peer)
        buf = bytearray()
        try:
            while data := await reader.read(4096):
                buf += data
                for pkt in parse_packets(buf):
                    reply = await session.handle(pkt)
                    if reply is not None:
                        writer.write(reply.encode())
                await writer.drain()
        except (ConnectionError, asyncio.IncompleteReadError):
            pass
        finally:
            self.sessions.discard(session)
            for char_uuid in session.subscribed:
                if not any(char_uuid in s.subscribed for s in self.sessions):
                    try:
                        await self.backend.set_notify(char_uuid, False)
                    except Exception:
                        pass
            writer.close()
            log.info("DIRCON-Client getrennt: %s", peer)
