"""Known GATT services and decoders for the live display.

The bridge passes raw data to Zwift unchanged. The decoders here only serve the display in the
user interface and diagnostics; they do not alter the data stream.
"""

from __future__ import annotations

import struct

from .dircon import full_uuid

FTMS = full_uuid(0x1826)
CYCLING_POWER = full_uuid(0x1818)
CSC = full_uuid(0x1816)
HEART_RATE = full_uuid(0x180D)

INDOOR_BIKE_DATA = full_uuid(0x2AD2)
CP_MEASUREMENT = full_uuid(0x2A63)
CSC_MEASUREMENT = full_uuid(0x2A5B)
HR_MEASUREMENT = full_uuid(0x2A37)

# Services Zwift uses over DIRCON. Vendor-specific services (e.g. Wahoo EE01…) stay out so that
# Zwift takes the standard FTMS path.
BRIDGED_SERVICES = [FTMS, CYCLING_POWER, CSC, HEART_RATE]

SERVICE_NAMES = {
    FTMS: "Fitness Machine (FTMS)",
    CYCLING_POWER: "Cycling Power",
    CSC: "Cycling Speed and Cadence",
    HEART_RATE: "Heart Rate",
}


def role_for(services: list[str]) -> str:
    """Device class from the offered services: trainer, power, cadence, heartrate, other."""
    s = set(services)
    if FTMS in s:
        return "trainer"
    if CYCLING_POWER in s:
        return "power"
    if CSC in s:
        return "cadence"
    if HEART_RATE in s:
        return "heartrate"
    return "other"


def decode_heart_rate(data: bytes) -> dict:
    if not data:
        return {}
    flags = data[0]
    hr = struct.unpack_from("<H", data, 1)[0] if flags & 0x01 else data[1]
    return {"heart_rate": hr}


def decode_indoor_bike_data(data: bytes) -> dict:
    """FTMS Indoor Bike Data (0x2AD2), only the fields needed for the display."""
    if len(data) < 2:
        return {}
    flags = struct.unpack_from("<H", data, 0)[0]
    pos = 2
    out: dict = {}
    if not flags & 0x0001:  # bit 0 "More Data" = 0 -> instantaneous speed present
        out["speed_kmh"] = struct.unpack_from("<H", data, pos)[0] / 100
        pos += 2
    if flags & 0x0002:  # average speed
        pos += 2
    if flags & 0x0004:
        out["cadence"] = struct.unpack_from("<H", data, pos)[0] / 2
        pos += 2
    if flags & 0x0008:  # average cadence
        pos += 2
    if flags & 0x0010:  # total distance (uint24)
        pos += 3
    if flags & 0x0020:  # resistance level
        pos += 2
    if flags & 0x0040:
        out["power"] = struct.unpack_from("<h", data, pos)[0]
        pos += 2
    if flags & 0x0080:  # average power
        pos += 2
    if flags & 0x0100:  # energy: total, per hour, per minute
        pos += 5
    if flags & 0x0200:
        out["heart_rate"] = data[pos]
    return out


def decode_cycling_power(data: bytes) -> dict:
    """Cycling Power Measurement (0x2A63): only the instantaneous power."""
    if len(data) < 4:
        return {}
    return {"power": struct.unpack_from("<h", data, 2)[0]}


DECODERS = {
    HR_MEASUREMENT: decode_heart_rate,
    INDOOR_BIKE_DATA: decode_indoor_bike_data,
    CP_MEASUREMENT: decode_cycling_power,
}
