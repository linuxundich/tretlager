"""Systemprüfung vor der Einrichtung – nur lesend, ohne root.

Jede Prüfung liefert ein `Check` mit Ampel (ok, warn, fail) und einem Satz für den Nutzer.
Wo möglich werden strukturierte Quellen gelesen (sysfs, os-release, busctl --json), nicht die
menschenlesbare Ausgabe von Werkzeugen.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import socket
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import btcompat, paths
from ..i18n import _

OK, WARN, FAIL = "ok", "warn", "fail"

VENDORS = {"0x10de": "NVIDIA", "0x8086": "Intel", "0x1002": "AMD"}
SECURE_BOOT_VAR = "SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c"


@dataclass
class Check:
    id: str
    title: str
    status: str  # ok, warn, fail
    summary: str
    details: list[str] = field(default_factory=list)
    action: str = ""  # Kennung einer Abhilfe, die die Oberfläche als Knopf anbieten kann

    def to_dict(self) -> dict:
        return asdict(self)


# --- einzelne Prüfungen; `root` erlaubt Tests gegen ein nachgebautes Dateisystem ---

def read_os_release(root: Path = Path("/")) -> dict:
    out = {}
    for line in (root / "etc/os-release").read_text().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k] = v.strip().strip('"')
    return out


def check_system(root: Path = Path("/"), machine: str | None = None) -> Check:
    machine = machine or platform.machine()
    try:
        osr = read_os_release(root)
    except OSError:
        return Check("system", _("System"), FAIL, _("Betriebssystem nicht erkannt"))
    name = osr.get("PRETTY_NAME", "Linux")
    codename = osr.get("VERSION_CODENAME", "")
    details = [f"{name}, {codename or _('ohne Codename')}, {machine}"]
    if machine != "x86_64":
        return Check("system", _("System"), FAIL, _("{machine} wird nicht unterstützt (Zwift braucht x86-64)").format(machine=machine), details)
    is_debian = osr.get("ID") == "debian" or "debian" in osr.get("ID_LIKE", "")
    if osr.get("ID") == "tuxedo" and codename == "forky":
        return Check("system", _("System"), OK, f"{name}, forky", details)
    if is_debian and codename == "forky":
        return Check("system", _("System"), WARN, _("{name}: Debian testing, nicht TUXEDO OS – nicht getestet").format(name=name), details)
    return Check("system", _("System"), WARN, _("{name} ist nicht das Zielsystem (TUXEDO OS forky)").format(name=name), details)


@dataclass
class Gpu:
    vendor: str
    device: str
    driver: str
    boot_vga: bool


def list_gpus(root: Path = Path("/")) -> list[Gpu]:
    gpus = []
    for card in sorted((root / "sys/class/drm").glob("card[0-9]*")):
        if "-" in card.name:
            continue  # Anschlüsse wie card1-eDP-1
        dev = card / "device"
        try:
            vendor = (dev / "vendor").read_text().strip()
            device = (dev / "device").read_text().strip()
        except OSError:
            continue
        driver = os.path.basename(os.path.realpath(dev / "driver")) if (dev / "driver").exists() else ""
        try:
            boot_vga = (dev / "boot_vga").read_text().strip() == "1"
        except OSError:
            boot_vga = False
        gpus.append(Gpu(VENDORS.get(vendor, vendor), device, driver, boot_vga))
    return gpus


def nvidia_driver_version(root: Path = Path("/")) -> str:
    try:
        return (root / "sys/module/nvidia/version").read_text().strip()
    except OSError:
        return ""


def secure_boot_enabled(root: Path = Path("/")) -> bool | None:
    var = root / "sys/firmware/efi/efivars" / SECURE_BOOT_VAR
    try:
        return var.read_bytes()[-1] == 1
    except OSError:
        return None


def check_graphics(root: Path = Path("/")) -> list[Check]:
    gpus = list_gpus(root)
    if not gpus:
        return [Check("graphics", _("Grafik"), FAIL, _("Keine Grafikkarte gefunden"))]
    details = [_("{vendor} {device} (Treiber {driver})").format(vendor=g.vendor, device=g.device, driver=g.driver or _("keiner"))
               + (_(" – Anzeige") if g.boot_vga else "")
               for g in gpus]
    nvidia = [g for g in gpus if g.vendor == "NVIDIA"]
    others = [g for g in gpus if g.vendor != "NVIDIA"]
    checks = []
    if nvidia:
        version = nvidia_driver_version(root)
        if nvidia[0].driver == "nvidia" and version:
            checks.append(Check("graphics", _("Grafik"), OK, _("NVIDIA-Treiber {version} geladen").format(version=version), details))
        else:
            sb = secure_boot_enabled(root)
            hint = (" " + _("Secure Boot ist an; das Kernelmodul muss signiert sein (TUXEDO-Anleitung).")
                    if sb else "")
            checks.append(Check("graphics", _("Grafik"), FAIL,
                                _("NVIDIA-Karte gefunden, aber der proprietäre Treiber ist nicht geladen.") + hint,
                                details, action="nvidia-help"))
        if others:
            checks.append(Check("hybrid", _("Hybrid-Grafik"), OK,
                                _("Notebook mit zwei Grafikchips – Zwift wird auf die NVIDIA-Karte gelegt"),
                                [_("Anzeige über {vendor}, Zwift per PRIME-Offload (GLX)").format(
                                    vendor=next((g.vendor for g in gpus if g.boot_vga), others[0].vendor))]))
    else:
        g = gpus[0]
        checks.append(Check("graphics", _("Grafik"), WARN,
                            _("{vendor}-Grafik (Mesa): Zwift läuft, aber mit weniger Bildrate als mit NVIDIA").format(vendor=g.vendor),
                            details))
    return checks


def bluez_adapter(run=subprocess.run) -> dict | None:
    """Eigenschaften von hci0 über busctl im JSON-Format, None ohne Adapter."""
    props = {}
    for prop in ("Powered", "Name", "Address"):
        r = run(["busctl", "--system", "--json=short", "get-property", "org.bluez", "/org/bluez/hci0",
                 "org.bluez.Adapter1", prop], capture_output=True, text=True, timeout=5)
        if r.returncode != 0:
            return None
        props[prop] = json.loads(r.stdout)["data"]
    return props


def rfkill_blocked(root: Path = Path("/")) -> bool:
    for dev in (root / "sys/class/rfkill").glob("rfkill*"):
        try:
            if (dev / "type").read_text().strip() == "bluetooth" and (dev / "soft").read_text().strip() == "1":
                return True
        except OSError:
            continue
    return False


def check_bluetooth(root: Path = Path("/"), run=subprocess.run) -> Check:
    try:
        adapter = bluez_adapter(run)
    except (OSError, subprocess.TimeoutExpired, ValueError):
        adapter = None
    if adapter is None:
        return Check("bluetooth", _("Bluetooth"), WARN,
                     _("Kein Bluetooth-Adapter gefunden – Sensoren lassen sich erst mit Adapter verbinden"))
    details = [f"{adapter['Name']} ({adapter['Address']})"]
    chip = btcompat.adapter_chip(root=root / "sys/class/bluetooth")
    if chip:
        details.append(_("Chip: {name}").format(name=chip.name))
    if rfkill_blocked(root) or not adapter["Powered"]:
        return Check("bluetooth", _("Bluetooth"), WARN, _("Bluetooth ist ausgeschaltet"), details,
                     action="bluetooth-on")
    return Check("bluetooth", _("Bluetooth"), OK, _("Bluetooth bereit für Trainer und Pulsgurt"), details)


def check_disk(path: Path | None = None) -> Check:
    path = path or Path.home()
    free = shutil.disk_usage(path).free
    gb = free / 10**9
    details = [_("{gb} GB frei in {path}").format(gb=f"{gb:.0f}", path=path), _("Bedarf: etwa 11 GB (Wine 1,8 GB, Zwift mit Umgebung 8,6 GB)")]
    if free >= paths.RECOMMENDED_BYTES:
        return Check("disk", _("Speicherplatz"), OK, _("{gb} GB frei").format(gb=f"{gb:.0f}"), details)
    if free >= paths.REQUIRED_BYTES:
        return Check("disk", _("Speicherplatz"), WARN, _("Nur {gb} GB frei – reicht knapp").format(gb=f"{gb:.0f}"), details)
    return Check("disk", _("Speicherplatz"), FAIL, _("Nur {gb} GB frei, nötig sind etwa 11 GB").format(gb=f"{gb:.0f}"), details)


NETWORK_HOSTS = [("cdn.zwift.com", 443), ("dl.winehq.org", 443)]


def check_network(hosts=NETWORK_HOSTS, timeout: float = 4.0) -> Check:
    """Nur ein Verbindungsaufbau zu den Quellen, die die Einrichtung braucht; keine Daten."""
    bad = []
    for host, port in hosts:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                pass
        except OSError:
            bad.append(host)
    details = [f"{h}: {_('nicht erreichbar') if h in bad else _('erreichbar')}" for h, _port in hosts]
    if bad:
        return Check("network", _("Internet"), FAIL, _("Download-Quellen nicht erreichbar"), details)
    return Check("network", _("Internet"), OK, _("Zwift und WineHQ erreichbar"), details)


def wine_version(run=subprocess.run) -> str:
    if not shutil.which("wine"):
        return ""
    try:
        return run(["wine", "--version"], capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def check_wine(root: Path = Path("/"), run=subprocess.run) -> Check:
    version = wine_version(run)
    source = any((root / "etc/apt/sources.list.d").glob("winehq-*.sources"))
    details = [_("WineHQ-Paketquelle: {state}").format(state=_("eingerichtet") if source else _("fehlt")),
               _("Wine: {version}").format(version=version or _("nicht installiert"))]
    if version:
        return Check("wine", "Wine", OK, _("{version} installiert").format(version=version), details)
    return Check("wine", "Wine", WARN, _("Wird im nächsten Schritt eingerichtet (WineHQ, etwa 290 MB)"), details)


def check_existing(zwift_dir: Path | None = None) -> Check:
    zwift_dir = zwift_dir or paths.ZWIFT_DIR
    if (zwift_dir / "ZwiftLauncher.exe").exists():
        game = (zwift_dir / "ZwiftApp.exe").exists()
        return Check("existing", "Zwift", OK,
                     _("Zwift ist schon eingerichtet") if game else _("Launcher vorhanden, Spiel fehlt noch"),
                     [str(zwift_dir)])
    return Check("existing", "Zwift", OK, _("Noch nicht eingerichtet – das übernimmt Tretlager"), [])


def run_all() -> list[Check]:
    checks = [check_system()]
    checks += check_graphics()
    checks += [check_bluetooth(), check_disk(), check_network(), check_wine(), check_existing()]
    return checks


def overall(checks: list[Check]) -> str:
    if any(c.status == FAIL for c in checks):
        return FAIL
    if any(c.status == WARN for c in checks):
        return WARN
    return OK
