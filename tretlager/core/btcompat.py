"""Known problem combinations of Bluetooth chip and sensor.

Some sensors might not get along with certain Bluetooth chips, without range or battery being the
cause. Tretlager recognises the chip by its USB ID and warns when adding the device and in the
overview. The first case (Garmin HRM-Pro Plus on the Intel AX201, 2026-10-29: service discovery
"hung every time") was really the slow connection interval Linux remembers for a strap; the
bridge has waited long enough since 0.11.2 and the entry is gone.

Add new cases as an entry in KNOWN_ISSUES – only with a real finding.
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

# USB IDs (vendor:product) of common built-in chips, only for readable names.
CHIP_NAMES = {
    "8087:0025": "Intel Wireless-AC 9260/9560",
    "8087:0026": "Intel Wi-Fi 6 AX201",
    "8087:0029": "Intel Wi-Fi 6 AX200",
    "8087:0032": "Intel Wi-Fi 6E AX210",
    "8087:0033": "Intel Wi-Fi 6E AX211",
    "8087:0036": "Intel Wi-Fi 7 BE200",
    "8087:0aaa": "Intel Wireless-AC 9560",
    # Realtek RTL8761B(U): chip of most cheap Bluetooth 5 dongles
    "0bda:8771": "Realtek RTL8761B",
    "2357:0604": "TP-Link UB500 (Realtek RTL8761BU)",
    "2550:8761": "Realtek RTL8761BU",
}


@dataclass(frozen=True)
class Chip:
    usb_id: str  # e.g. 8087:0026, empty for chips without a USB connection
    name: str


@dataclass(frozen=True)
class Issue:
    chips: frozenset[str]  # USB IDs
    device: re.Pattern  # matches the sensor's BLE name
    device_name: str
    text: str  # warning on the configured device
    short: str  # one line in the scan results


# Empty since 0.11.2: the only entry, Garmin HRM-Pro x Intel AX201 (8087:0026), turned out to be
# the slow connection interval the kernel remembers (see bridge/device.py, DISCOVERY_TIMEOUT); with
# 0.11.2 the strap connects through the AX201 in 7 to 12 s (tinytin, 2026-11-06).
KNOWN_ISSUES: list[Issue] = []


def adapter_chip(adapter: str = "hci0", root: Path = BLUETOOTH) -> Chip | None:
    """Chip of the Bluetooth adapter the bridge uses; None without an adapter."""
    dev = root / adapter / "device"
    if not dev.exists():
        return None
    usb_id = ""
    # btusb is bound to the USB interface; idVendor/idProduct sit one level up on the USB device.
    for d in (dev, dev / ".."):
        try:
            usb_id = f"{(d / 'idVendor').read_text().strip()}:{(d / 'idProduct').read_text().strip()}".lower()
            break
        except OSError:
            continue
    return Chip(usb_id, CHIP_NAMES.get(usb_id, f"USB {usb_id}" if usb_id else _("unknown chip")))


def list_adapters(root: Path = BLUETOOTH, run=subprocess.run) -> list[dict]:
    """All Bluetooth adapters: hciN, address (from BlueZ) and chip; for selection in the interface."""
    out = []
    for hci in sorted(p.name for p in root.glob("hci*")):
        chip = adapter_chip(hci, root)
        props = dbusutil.get_all("system", "org.bluez", f"/org/bluez/{hci}", "org.bluez.Adapter1", run) or {}
        address = str(props.get("Address", "")).upper()
        if address:
            out.append({"hci": hci, "address": address, "chip": chip.name if chip else _("unknown chip"),
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
    """Warning text for a known problem combination, otherwise empty."""
    issue = find_issue(chip, device_name)
    if issue is None:
        return ""
    return (issue.short if short else issue.text).format(chip=chip.name)


def annotate(devices: list[dict], chip: Chip | None) -> list[dict]:
    """Add `compat` and `compat_short` to the bridge's device lists (configured or found)."""
    return [dict(d, compat=issue_for(chip, d.get("name", "")),
                 compat_short=issue_for(chip, d.get("name", ""), short=True),
                 # The bridge sends error texts untranslated (N_ msgids); they are translated here
                 **({"error": _(d["error"])} if d.get("error") else {})) for d in devices]
