import asyncio

import pytest

from tretlager.bridge import dircon
from tretlager.bridge.dircon import (Characteristic, Packet, Service, Session, full_uuid, parse_packets,
                                     uuid_bytes)

FTMS = full_uuid(0x1826)
CP = full_uuid(0x2AD9)
BIKE_DATA = full_uuid(0x2AD2)
FEATURE = full_uuid(0x2ACC)


class FakeBackend:
    def __init__(self):
        self.written = []
        self.notify = []

    def services(self):
        return [Service(FTMS, [Characteristic(FEATURE, dircon.PROP_READ),
                               Characteristic(BIKE_DATA, dircon.PROP_NOTIFY),
                               Characteristic(CP, dircon.PROP_WRITE | dircon.PROP_INDICATE)])]

    async def read(self, uuid):
        return b"\x01\x02"

    async def write(self, uuid, data):
        self.written.append((uuid, data))

    async def set_notify(self, uuid, enabled):
        self.notify.append((uuid, enabled))


def run(coro):
    return asyncio.run(coro)


def test_full_uuid_forms():
    assert full_uuid(0x1826) == "00001826-0000-1000-8000-00805f9b34fb"
    assert full_uuid("0x2AD2") == full_uuid("2ad2") == full_uuid(0x2AD2)
    assert full_uuid("A026E005-0A7D-4AB3-97FA-F1500F9FEB8B") == "a026e005-0a7d-4ab3-97fa-f1500f9feb8b"


def test_uuid_bytes_layout_matches_dircon():
    # Kurze UUID steht in Byte 2 und 3, Rest ist die Bluetooth-Basis-UUID.
    raw = uuid_bytes(FTMS)
    assert len(raw) == 16 and raw[2:4] == b"\x18\x26" and raw[4:] == bytes.fromhex("0000100080000080" "5f9b34fb")


def test_packet_roundtrip_and_partial_buffer():
    a = Packet(dircon.MSG_READ_CHARACTERISTIC, 7, 0, uuid_bytes(FEATURE)).encode()
    b = Packet(dircon.MSG_DISCOVER_SERVICES, 8).encode()
    buf = bytearray(a + b[:3])
    pkts = parse_packets(buf)
    assert [p.sequence for p in pkts] == [7] and bytes(buf) == b[:3]
    buf += b[3:]
    assert [p.message for p in parse_packets(buf)] == [dircon.MSG_DISCOVER_SERVICES] and not buf


def test_discover_services_and_characteristics():
    s = Session(FakeBackend(), None)
    r = run(s.handle(Packet(dircon.MSG_DISCOVER_SERVICES, 1)))
    assert r.response == 0 and r.payload == uuid_bytes(FTMS) and r.sequence == 1
    r = run(s.handle(Packet(dircon.MSG_DISCOVER_CHARACTERISTICS, 2, 0, uuid_bytes(FTMS))))
    assert r.payload[:16] == uuid_bytes(FTMS)
    assert len(r.payload) == 16 + 3 * 17
    assert r.payload[16 + 16] == dircon.PROP_READ
    assert r.payload[16 + 2 * 17 + 16] == dircon.PROP_WRITE | dircon.PROP_INDICATE


def test_unknown_service_and_characteristic():
    s = Session(FakeBackend(), None)
    r = run(s.handle(Packet(dircon.MSG_DISCOVER_CHARACTERISTICS, 3, 0, uuid_bytes(full_uuid(0x180D)))))
    assert r.response == dircon.RESP_SERVICE_NOT_FOUND
    r = run(s.handle(Packet(dircon.MSG_READ_CHARACTERISTIC, 4, 0, uuid_bytes(full_uuid(0x2A37)))))
    assert r.response == dircon.RESP_CHARACTERISTIC_NOT_FOUND


def test_read_and_unsupported_read():
    s = Session(FakeBackend(), None)
    r = run(s.handle(Packet(dircon.MSG_READ_CHARACTERISTIC, 5, 0, uuid_bytes(FEATURE))))
    assert r.response == 0 and r.payload == uuid_bytes(FEATURE) + b"\x01\x02"
    r = run(s.handle(Packet(dircon.MSG_READ_CHARACTERISTIC, 6, 0, uuid_bytes(BIKE_DATA))))
    assert r.response == dircon.RESP_OPERATION_NOT_SUPPORTED


def test_write_control_point_echoes_data():
    backend = FakeBackend()
    s = Session(backend, None)
    cmd = bytes([0x05, 0xC8, 0x00])  # FTMS: Zielleistung 200 W
    r = run(s.handle(Packet(dircon.MSG_WRITE_CHARACTERISTIC, 9, 0, uuid_bytes(CP) + cmd)))
    assert r.response == 0 and r.payload == uuid_bytes(CP) + cmd
    assert backend.written == [(CP, cmd)]


def test_enable_notifications_and_filtering():
    class Writer:
        def __init__(self):
            self.data = b""

        def write(self, d):
            self.data += d

    backend = FakeBackend()
    w = Writer()
    s = Session(backend, w)
    s.notify(BIKE_DATA, b"\x44\x00")
    assert w.data == b""  # nicht abonniert → nichts senden
    r = run(s.handle(Packet(dircon.MSG_ENABLE_NOTIFICATIONS, 10, 0, uuid_bytes(BIKE_DATA) + b"\x01")))
    assert r.response == 0 and r.payload == uuid_bytes(BIKE_DATA)
    assert backend.notify == [(BIKE_DATA, True)]
    s.notify(BIKE_DATA, b"\x44\x00")
    pkts = parse_packets(bytearray(w.data))
    assert pkts[0].message == dircon.MSG_NOTIFICATION and pkts[0].sequence == 0
    assert pkts[0].payload == uuid_bytes(BIKE_DATA) + b"\x44\x00"


def test_unknown_07_answered_empty():
    r = run(Session(FakeBackend(), None).handle(Packet(dircon.MSG_UNKNOWN_07, 11)))
    assert r.message == 7 and r.payload == b"" and r.response == 0


@pytest.mark.parametrize("msg", [dircon.MSG_READ_CHARACTERISTIC, dircon.MSG_WRITE_CHARACTERISTIC])
def test_short_payload_is_error(msg):
    r = run(Session(FakeBackend(), None).handle(Packet(msg, 12, 0, b"\x00\x01")))
    assert r.response == dircon.RESP_UNEXPECTED_ERROR


def test_server_end_to_end_over_tcp():
    async def scenario():
        backend = FakeBackend()
        server = dircon.Server(backend, host="127.0.0.1", port=0)
        server._server = await asyncio.start_server(server._client, "127.0.0.1", 0)
        port = server._server.sockets[0].getsockname()[1]
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.write(Packet(dircon.MSG_DISCOVER_SERVICES, 1).encode())
        writer.write(Packet(dircon.MSG_ENABLE_NOTIFICATIONS, 2, 0, uuid_bytes(BIKE_DATA) + b"\x01").encode())
        await writer.drain()
        buf = bytearray()
        while len(parse_packets(bytearray(buf))) < 2:
            buf += await reader.read(1024)
        server.notify(BIKE_DATA, b"\x40\x00\xc8\x00")
        await asyncio.sleep(0.05)
        buf += await reader.read(1024)
        pkts = parse_packets(buf)
        writer.close()
        await server.stop()
        return pkts, server.client_count

    pkts, clients = run(scenario())
    assert [p.message for p in pkts] == [1, 5, 6]
    assert pkts[2].payload.endswith(b"\x40\x00\xc8\x00")
    assert clients == 0


def test_local_ipv4_addresses_include_loopback():
    assert "127.0.0.1" in dircon.local_ipv4_addresses()
