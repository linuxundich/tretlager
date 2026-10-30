"""Bekannte Problemkombinationen aus Bluetooth-Chip und Sensor.

Manche Sensoren vertragen sich mit bestimmten Bluetooth-Chips nicht, ohne dass Reichweite oder
Batterie schuld sind. Befund auf tinytin (2026-10-29): Der Garmin HRM-Pro Plus wird am
eingebauten Intel AX201 (Firmware 202-5.26) gefunden, die GATT-Dienstsuche nach dem Verbinden
hängt aber jedes Mal; am Intel AX200 (smokki) läuft derselbe Gurt. Vermutet wird ein Problem mit
LE 2M. Tretlager erkennt den Chip an der USB-Kennung und warnt beim Hinzufügen und in der
Übersicht, statt den Gurt endlos „Verbindet …“ zeigen zu lassen.

Neue Fälle als Eintrag in KNOWN_ISSUES ergänzen – nur mit echtem Befund.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

BLUETOOTH = Path("/sys/class/bluetooth")

# USB-Kennungen (Hersteller:Produkt) gängiger eingebauter Chips, nur für lesbare Namen.
CHIP_NAMES = {
    "8087:0025": "Intel Wireless-AC 9260/9560",
    "8087:0026": "Intel Wi-Fi 6 AX201",
    "8087:0029": "Intel Wi-Fi 6 AX200",
    "8087:0032": "Intel Wi-Fi 6E AX210",
    "8087:0033": "Intel Wi-Fi 6E AX211",
    "8087:0036": "Intel Wi-Fi 7 BE200",
    "8087:0aaa": "Intel Wireless-AC 9560",
}


@dataclass(frozen=True)
class Chip:
    usb_id: str  # z. B. 8087:0026, leer bei Chips ohne USB-Anbindung
    name: str


@dataclass(frozen=True)
class Issue:
    chips: frozenset[str]  # USB-Kennungen
    device: re.Pattern  # passt auf den BLE-Namen des Sensors
    device_name: str
    text: str


KNOWN_ISSUES = [
    Issue(
        chips=frozenset({"8087:0026"}),
        device=re.compile(r"^HRM-?Pro", re.IGNORECASE),  # „HRM-Pro:…“, „HRMPro+:…“
        device_name="Garmin HRM-Pro",
        text="Der Garmin HRM-Pro verträgt sich nicht mit dem Bluetooth-Chip dieses Rechners ({chip}): "
             "Er wird gefunden, aber die Verbindung kommt nie zustande. Das liegt nicht an Reichweite "
             "oder Batterie. Abhilfe: einen anderen Pulsgurt nutzen, zum Beispel einen Wahoo TICKR. "
             "Mit anderen Chips (getestet: Intel AX200) funktioniert der Gurt.",
    ),
]


def adapter_chip(adapter: str = "hci0", root: Path = BLUETOOTH) -> Chip | None:
    """Chip des Bluetooth-Adapters, den die Bridge nutzt; None ohne Adapter."""
    dev = root / adapter / "device"
    if not dev.exists():
        return None
    usb_id = ""
    # btusb hängt am USB-Interface, idVendor/idProduct stehen eine Ebene höher am USB-Gerät.
    for d in (dev, dev / ".."):
        try:
            usb_id = f"{(d / 'idVendor').read_text().strip()}:{(d / 'idProduct').read_text().strip()}".lower()
            break
        except OSError:
            continue
    return Chip(usb_id, CHIP_NAMES.get(usb_id, f"USB {usb_id}" if usb_id else "unbekannter Chip"))


def issue_for(chip: Chip | None, device_name: str) -> str:
    """Warntext für eine bekannte Problemkombination, sonst leer."""
    if chip is None or not chip.usb_id:
        return ""
    for issue in KNOWN_ISSUES:
        if chip.usb_id in issue.chips and issue.device.search(device_name or ""):
            return issue.text.format(chip=chip.name)
    return ""


def annotate(devices: list[dict], chip: Chip | None) -> list[dict]:
    """Gerätelisten der Bridge (eingerichtet oder gefunden) um das Feld `compat` ergänzen."""
    return [dict(d, compat=issue_for(chip, d.get("name", ""))) for d in devices]
