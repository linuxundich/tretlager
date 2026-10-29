"""Bekannte GATT-Dienste und Decoder für die Live-Anzeige.

Die Bridge reicht Rohdaten unverändert an Zwift weiter. Die Decoder hier dienen nur der Anzeige in
der Oberfläche und der Diagnose; sie verändern nichts am Datenstrom.
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

# Dienste, die Zwift über DIRCON nutzt. Herstellereigene Dienste (z. B. Wahoo EE01…) bleiben
# draußen, damit Zwift den Standardweg FTMS nimmt.
BRIDGED_SERVICES = [FTMS, CYCLING_POWER, CSC, HEART_RATE]

SERVICE_NAMES = {
    FTMS: "Fitness Machine (FTMS)",
    CYCLING_POWER: "Cycling Power",
    CSC: "Geschwindigkeit/Trittfrequenz",
    HEART_RATE: "Herzfrequenz",
}


def role_for(services: list[str]) -> str:
    """Geräteklasse aus den angebotenen Diensten: trainer, power, cadence, heartrate, other."""
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
    """FTMS Indoor Bike Data (0x2AD2), nur die Felder für die Anzeige."""
    if len(data) < 2:
        return {}
    flags = struct.unpack_from("<H", data, 0)[0]
    pos = 2
    out: dict = {}
    if not flags & 0x0001:  # Bit 0 „More Data“ = 0 → Momentangeschwindigkeit vorhanden
        out["speed_kmh"] = struct.unpack_from("<H", data, pos)[0] / 100
        pos += 2
    if flags & 0x0002:  # Durchschnittsgeschwindigkeit
        pos += 2
    if flags & 0x0004:
        out["cadence"] = struct.unpack_from("<H", data, pos)[0] / 2
        pos += 2
    if flags & 0x0008:  # Durchschnittstrittfrequenz
        pos += 2
    if flags & 0x0010:  # Gesamtstrecke (uint24)
        pos += 3
    if flags & 0x0020:  # Widerstandsstufe
        pos += 2
    if flags & 0x0040:
        out["power"] = struct.unpack_from("<h", data, pos)[0]
        pos += 2
    if flags & 0x0080:  # Durchschnittsleistung
        pos += 2
    if flags & 0x0100:  # Energie: gesamt, pro Stunde, pro Minute
        pos += 5
    if flags & 0x0200:
        out["heart_rate"] = data[pos]
    return out


def decode_cycling_power(data: bytes) -> dict:
    """Cycling Power Measurement (0x2A63): nur die Momentanleistung."""
    if len(data) < 4:
        return {}
    return {"power": struct.unpack_from("<h", data, 2)[0]}


DECODERS = {
    HR_MEASUREMENT: decode_heart_rate,
    INDOOR_BIKE_DATA: decode_indoor_bike_data,
    CP_MEASUREMENT: decode_cycling_power,
}
