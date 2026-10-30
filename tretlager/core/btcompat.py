"""Bekannte Problemkombinationen aus Bluetooth-Chip und Sensor.

Manche Sensoren vertragen sich mit bestimmten Bluetooth-Chips nicht, ohne dass Reichweite oder
Batterie schuld sind. Befund auf tinytin (2026-10-29): Der Garmin HRM-Pro Plus wird am
eingebauten Intel AX201 (Firmware 202-5.26) gefunden, die GATT-Dienstsuche nach dem Verbinden
hängt aber jedes Mal; am Intel AX200 (smokki) und am USB-Stick
TP-Link UB500 (Realtek RTL8761BU, tinytin, 30.10.) läuft derselbe Gurt. Vermutet wird ein Problem mit
LE 2M. Tretlager erkennt den Chip an der USB-Kennung und warnt beim Hinzufügen und in der
Übersicht, statt den Gurt endlos „Verbindet …“ zeigen zu lassen.

Neue Fälle als Eintrag in KNOWN_ISSUES ergänzen – nur mit echtem Befund.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from ..i18n import _
from . import dbusutil

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
    # Realtek RTL8761B(U): Chip der meisten günstigen Bluetooth-5-Sticks
    "0bda:8771": "Realtek RTL8761B",
    "2357:0604": "TP-Link UB500 (Realtek RTL8761BU)",
    "2550:8761": "Realtek RTL8761BU",
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
    text: str  # Warnung am eingerichteten Gerät
    short: str  # eine Zeile in den Suchergebnissen


KNOWN_ISSUES = [
    Issue(
        chips=frozenset({"8087:0026"}),
        device=re.compile(r"^HRM-?Pro", re.IGNORECASE),  # „HRM-Pro:…“, „HRMPro+:…“
        device_name="Garmin HRM-Pro",
        text=_("Der Garmin HRM-Pro verbindet sich nicht mit dem Bluetooth-Chip dieses Rechners ({chip}). "
               "Er wird zwar gefunden, die Verbindung kommt aber nie zustande; an Reichweite oder "
               "Batterie liegt das nicht. Abhilfe: einen USB-Bluetooth-Stick anschließen und unter "
               "Sensoren als Bluetooth-Adapter wählen (getestet: TP-Link UB500) oder einen anderen "
               "Pulsgurt nutzen, etwa einen Wahoo TICKR."),
        short=_("Verbindet sich nicht mit diesem Bluetooth-Chip ({chip}). Abhilfe: USB-Bluetooth-Stick"),
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
    return Chip(usb_id, CHIP_NAMES.get(usb_id, f"USB {usb_id}" if usb_id else _("unbekannter Chip")))


def list_adapters(root: Path = BLUETOOTH, run=subprocess.run) -> list[dict]:
    """Alle Bluetooth-Adapter: hciN, Adresse (von BlueZ) und Chip; zur Auswahl in der Oberfläche."""
    out = []
    for hci in sorted(p.name for p in root.glob("hci*")):
        chip = adapter_chip(hci, root)
        props = dbusutil.get_all("system", "org.bluez", f"/org/bluez/{hci}", "org.bluez.Adapter1", run) or {}
        address = str(props.get("Address", "")).upper()
        if address:
            out.append({"hci": hci, "address": address, "chip": chip.name if chip else "unbekannter Chip",
                        "usb_id": chip.usb_id if chip else ""})
    return out


def find_issue(chip: Chip | None, device_name: str) -> Issue | None:
    if chip is None or not chip.usb_id:
        return None
    for issue in KNOWN_ISSUES:
        if chip.usb_id in issue.chips and issue.device.search(device_name or ""):
            return issue
    return None


def issue_for(chip: Chip | None, device_name: str, short: bool = False) -> str:
    """Warntext für eine bekannte Problemkombination, sonst leer."""
    issue = find_issue(chip, device_name)
    if issue is None:
        return ""
    return (issue.short if short else issue.text).format(chip=chip.name)


def annotate(devices: list[dict], chip: Chip | None) -> list[dict]:
    """Gerätelisten der Bridge (eingerichtet oder gefunden) um `compat` und `compat_short` ergänzen."""
    return [dict(d, compat=issue_for(chip, d.get("name", "")),
                 compat_short=issue_for(chip, d.get("name", ""), short=True),
                 # Fehlertexte der Bridge kommen deutsch (N_) und werden hier übersetzt
                 **({"error": _(d["error"])} if d.get("error") else {})) for d in devices]
