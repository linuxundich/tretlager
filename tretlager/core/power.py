"""Stromversorgung und NVIDIA-Fehler rund um eine Fahrt.

Befund auf tinytin (2026-10-30): Zwift im Netzbetrieb gestartet, während des Starts das Netzteil
gezogen bzw. gesteckt – kurz danach meldete der NVIDIA-Treiber für Zwifts Prozess Dutzende
„Xid 69“ (Fehler der Grafik-Engine), Zwift hing. Die Grafik wechselt dabei nicht auf den
Intel-Chip (PRIME-Offload bleibt), das TCC-Profil war für Netz und Akku gleich; vermutlich stellt
nvidia-powerd (Dynamic Boost) beim Wechsel der Stromquelle das Leistungsbudget um, während Zwift
seine Grafik aufbaut. Tretlager warnt deshalb vor dem Start im Akkubetrieb, bemerkt einen Wechsel
während Start und Fahrt und meldet danach NVIDIA-Fehler aus dem Kernel-Journal.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

POWER_SUPPLY = Path("/sys/class/power_supply")
XID_RE = re.compile(r"NVRM: Xid \([^)]*\): (\d+)")


def on_ac(root: Path = POWER_SUPPLY) -> bool | None:
    """True am Netz, False auf Akku, None ohne Netzteil-Eintrag (z. B. Desktop-PC)."""
    mains = []
    for dev in root.glob("*"):
        try:
            if (dev / "type").read_text().strip() == "Mains":
                mains.append((dev / "online").read_text().strip() == "1")
        except OSError:
            continue
    if not mains:
        return None
    return any(mains)


def nvidia_xids(since: float, run=subprocess.run) -> list[int]:
    """Xid-Codes des NVIDIA-Treibers seit `since` (Unix-Zeit) aus dem Kernel-Journal.

    Braucht Lesezugriff aufs Journal (Gruppe systemd-journal oder adm, unter Debian/TUXEDO OS für
    den ersten Benutzer üblich); ohne Zugriff kommt eine leere Liste.
    """
    try:
        res = run(["journalctl", "-k", "--no-pager", "-o", "cat", "--since", f"@{int(since)}", "-g", "NVRM: Xid"],
                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return []
    return [int(m.group(1)) for m in XID_RE.finditer(res.stdout or "")]


def describe_xids(codes: list[int]) -> str:
    """Kurzfassung für die Oberfläche, z. B. „Xid 69 (58×)“."""
    counts: dict[int, int] = {}
    for c in codes:
        counts[c] = counts.get(c, 0) + 1
    return ", ".join(f"Xid {c}" + (f" ({n}×)" if n > 1 else "") for c, n in sorted(counts.items()))


def notify(summary: str, body: str, run=subprocess.run) -> None:
    """Desktop-Benachrichtigung (org.freedesktop.Notifications) über gdbus; Fehler bleiben still."""
    if not shutil.which("gdbus"):
        return
    try:
        run(["gdbus", "call", "--session", "--dest", "org.freedesktop.Notifications",
             "--object-path", "/org/freedesktop/Notifications",
             "--method", "org.freedesktop.Notifications.Notify",
             "Tretlager", "0", "de.linuxundich.Tretlager", summary, body, "[]",
             "{'urgency': <byte 2>, 'desktop-entry': <'de.linuxundich.Tretlager'>}", "-1"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        pass
