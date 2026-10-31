"""System check before the setup – read-only, without root.

Each check returns a `Check` with a traffic light (ok, warn, fail) and a sentence for the user.
Where possible, structured sources are read (sysfs, os-release, busctl --json), not the
human-readable output of tools.
"""

from __future__ import annotations

import json
import re
import os
import platform
import shutil
import socket
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import btcompat, dbusutil, paths, wine
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
    action: str = ""  # ID of a remedy the interface can offer as a button

    def to_dict(self) -> dict:
        return asdict(self)


# --- individual checks; `root` allows tests against a mock file system ---

def read_os_release(root: Path = Path("/")) -> dict:
    """The host's os-release; in the Flatpak it is under /run/host (otherwise we would see the runtime)."""
    out = {}
    host = root / "run/host/os-release"
    source = host if host.exists() else root / "etc/os-release"
    for line in source.read_text().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k] = v.strip().strip('"')
    return out


def check_system(root: Path = Path("/"), machine: str | None = None) -> Check:
    machine = machine or platform.machine()
    try:
        osr = read_os_release(root)
    except OSError:
        return Check("system", _("System"), FAIL, _("Operating system not recognised"))
    name = osr.get("PRETTY_NAME", "Linux")
    codename = osr.get("VERSION_CODENAME", "")
    details = [f"{name}, {codename or _("no codename")}, {machine}"]
    if machine != "x86_64":
        return Check("system", _("System"), FAIL, _("{machine} is not supported (Zwift needs x86-64)").format(machine=machine), details)
    # Tretlager runs as a Flatpak on all modern distributions; the system is only displayed.
    return Check("system", _("System"), OK, name, details)


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
            continue  # connectors such as card1-eDP-1
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
        pass
    try:  # /sys/module is missing in the Flatpak, /proc/driver/nvidia is visible
        m = re.search(r"Kernel Module.*?\s(\d+\.\d+(?:\.\d+)?)\s", (root / "proc/driver/nvidia/version").read_text())
        return m.group(1) if m else ""
    except OSError:
        return ""


def nvidia_gl_extension_missing(version: str, root: Path = Path("/")) -> bool:
    """In the Flatpak: is the GL extension for the NVIDIA driver (org.freedesktop.Platform.GL.nvidia-…) missing?

    Flatpak only installs it if the driver is loaded during `flatpak update`. Anyone who switches to
    the NVIDIA card only after the installation (envycontrol, nvidia-prime) does not have it; then
    there is no OpenGL on the NVIDIA card inside the sandbox.
    """
    if not (root / ".flatpak-info").exists() or not version:
        return False
    return not (root / "usr/lib/x86_64-linux-gnu/GL" / ("nvidia-" + version.replace(".", "-"))).is_dir()


def nvidia_usable(root: Path = Path("/")) -> bool:
    """Can Zwift render on the NVIDIA card: driver loaded and (in the Flatpak) GL extension present."""
    gpus = list_gpus(root)
    if not any(g.vendor == "NVIDIA" and g.driver == "nvidia" for g in gpus):
        return False
    version = nvidia_driver_version(root)
    return bool(version) and not nvidia_gl_extension_missing(version, root)


def gpu_signature(root: Path = Path("/")) -> list[str]:
    """Graphics chips with driver and NVIDIA usability; if this changes, the graphics test runs again."""
    return sorted(f"{g.vendor}:{g.device}:{g.driver}" for g in list_gpus(root)) + (
        ["nvidia-usable"] if nvidia_usable(root) else [])


def secure_boot_enabled(root: Path = Path("/")) -> bool | None:
    var = root / "sys/firmware/efi/efivars" / SECURE_BOOT_VAR
    try:
        return var.read_bytes()[-1] == 1
    except OSError:
        return None


def check_graphics(root: Path = Path("/")) -> list[Check]:
    gpus = list_gpus(root)
    if not gpus:
        return [Check("graphics", _("Graphics"), FAIL, _("No graphics card found"))]
    details = [_("{vendor} {device} (driver {driver})").format(vendor=g.vendor, device=g.device, driver=g.driver or _("none"))
               + (_(" – display") if g.boot_vga else "")
               for g in gpus]
    nvidia = [g for g in gpus if g.vendor == "NVIDIA"]
    others = [g for g in gpus if g.vendor != "NVIDIA"]
    checks = []
    if nvidia:
        version = nvidia_driver_version(root)
        if nvidia[0].driver == "nvidia" and version and nvidia_gl_extension_missing(version, root):
            checks.append(Check("graphics", _("Graphics"), FAIL,
                                _("NVIDIA driver {version} is loaded, but the Flatpak lacks "
                                  "the matching extension. Run “flatpak update” in a terminal "
                                  "and restart Tretlager.").format(version=version),
                                details + [f"org.freedesktop.Platform.GL.nvidia-{version.replace('.', '-')}"]))
        elif nvidia[0].driver == "nvidia" and version:
            checks.append(Check("graphics", _("Graphics"), OK, _("NVIDIA driver {version} loaded").format(version=version), details))
        else:
            sb = secure_boot_enabled(root)
            hint = (" " + _("Secure Boot is on; the kernel module must be signed (see the TUXEDO guide).")
                    if sb else "")
            checks.append(Check("graphics", _("Graphics"), FAIL,
                                _("NVIDIA card found, but the proprietary driver is not loaded.") + hint,
                                details, action="nvidia-help"))
        if others:
            display_vendor = next((g.vendor for g in gpus if g.boot_vga), others[0].vendor)
            if nvidia_usable(root):
                checks.append(Check("hybrid", _("Hybrid graphics"), OK,
                                    _("Laptop with two graphics chips – Zwift runs on the NVIDIA card"),
                                    [_("Display via {vendor}, Zwift via PRIME offload (GLX)").format(vendor=display_vendor)]))
            else:
                checks.append(Check("hybrid", _("Hybrid graphics"), WARN,
                                    _("Laptop with two graphics chips – Zwift runs on {vendor} until the NVIDIA card is usable").format(
                                        vendor=display_vendor)))
    else:
        g = gpus[0]
        checks.append(Check("graphics", _("Graphics"), WARN,
                            _("{vendor} graphics (Mesa): Zwift runs, but at a lower frame rate than with NVIDIA").format(vendor=g.vendor),
                            details + [_("Laptop with the NVIDIA card switched off (e.g. "
                                         "envycontrol “integrated”)? Then Tretlager cannot see "
                                         "it; see Help, “Zwift on the NVIDIA card”.")]))
    return checks


def bluez_adapter(run=subprocess.run, adapter: str = "hci0") -> dict | None:
    """Properties of a BlueZ adapter (via gdbus), None without an adapter."""
    props = dbusutil.get_all("system", "org.bluez", f"/org/bluez/{adapter}", "org.bluez.Adapter1", run)
    if not props or "Address" not in props:
        return None
    props.setdefault("Name", adapter)
    props.setdefault("Powered", False)
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
                     _("No Bluetooth adapter found – sensors can only be connected with an adapter"))
    details = [f"{adapter['Name']} ({adapter['Address']})"]
    chip = btcompat.adapter_chip(root=root / "sys/class/bluetooth")
    if chip:
        details.append(_("Chip: {name}").format(name=chip.name))
    if rfkill_blocked(root) or not adapter["Powered"]:
        return Check("bluetooth", _("Bluetooth"), WARN, _("Bluetooth is turned off"), details,
                     action="bluetooth-on")
    return Check("bluetooth", _("Bluetooth"), OK, _("Bluetooth ready for trainer and heart rate strap"), details)


def check_disk(path: Path | None = None) -> Check:
    # Measure where the Zwift environment ends up: in the Flatpak ~ is only a small tmpfs, the data
    # lives under ~/.var/app/<ID>/data (XDG_DATA_HOME).
    if path is None:
        path = paths.DATA
        while not path.exists() and path != path.parent:
            path = path.parent
    free = shutil.disk_usage(path).free
    gb = free / 10**9
    details = [_("{gb} GB free in {path}").format(gb=f"{gb:.0f}", path=path), _("Required: about 11 GB (Wine 1.8 GB, Zwift with environment 8.6 GB)")]
    if free >= paths.RECOMMENDED_BYTES:
        return Check("disk", _("Disk space"), OK, _("{gb} GB free").format(gb=f"{gb:.0f}"), details)
    if free >= paths.REQUIRED_BYTES:
        return Check("disk", _("Disk space"), WARN, _("Only {gb} GB free – just enough").format(gb=f"{gb:.0f}"), details)
    return Check("disk", _("Disk space"), FAIL, _("Only {gb} GB free, about 11 GB are needed").format(gb=f"{gb:.0f}"), details)


# Zwift (installer, game) and GitHub (winetricks); WineHQ only for the old Debian package.
NETWORK_HOSTS = [("cdn.zwift.com", 443), ("raw.githubusercontent.com", 443)]


def check_network(hosts=NETWORK_HOSTS, timeout: float = 4.0) -> Check:
    """Only a connection attempt to the sources the setup needs; no data."""
    bad = []
    for host, port in hosts:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                pass
        except OSError:
            bad.append(host)
    details = [f"{h}: {_("unreachable") if h in bad else _("reachable")}" for h, _port in hosts]
    if bad:
        return Check("network", _("Internet"), FAIL, _("Download sources unreachable"), details)
    return Check("network", _("Internet"), OK, _("Zwift and GitHub reachable"), details)


def wine_version(run=subprocess.run) -> str:
    """Version of the Wine Tretlager starts Zwift with (bundled or previous, core/wine.py)."""
    exe = shutil.which("wine", path=wine.env_path())
    if not exe:
        return ""
    try:
        return run([exe, "--version"], capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def check_wine(root: Path = Path("/"), run=subprocess.run) -> Check:
    version = wine_version(run)
    if (root / ".flatpak-info").exists():
        if version:
            return Check("wine", "Wine", OK, _("{version}, included in the Flatpak").format(version=version))
        return Check("wine", "Wine", FAIL, _("Wine is missing from the Flatpak – reinstall Tretlager"))
    source = any((root / "etc/apt/sources.list.d").glob("winehq-*.sources"))
    details = [_("WineHQ package source: {state}").format(state=_("set up") if source else _("missing")),
               _("Wine: {version}").format(version=version or _("not installed"))]
    if version:
        return Check("wine", "Wine", OK, _("{version} installed").format(version=version), details)
    return Check("wine", "Wine", WARN, _("Will be set up in the next step (WineHQ, about 290 MB)"), details)


def check_existing(zwift_dir: Path | None = None) -> Check:
    zwift_dir = zwift_dir or paths.ZWIFT_DIR
    if (zwift_dir / "ZwiftLauncher.exe").exists():
        game = (zwift_dir / "ZwiftApp.exe").exists()
        return Check("existing", "Zwift", OK,
                     _("Zwift is already set up") if game else _("Launcher present, game still missing"),
                     [str(zwift_dir)])
    return Check("existing", "Zwift", OK, _("Not set up yet – Tretlager takes care of it"), [])


def check_avahi(run=subprocess.run) -> Check:
    """Avahi announces the sensors to Zwift (mDNS); without it, Zwift finds no devices."""
    if dbusutil.name_has_owner("system", "org.freedesktop.Avahi", run) or \
            dbusutil.activatable("system", "org.freedesktop.Avahi", run):
        return Check("avahi", _("Device announcement"), OK, _("Avahi is running, Zwift can find the sensors"))
    return Check("avahi", _("Device announcement"), WARN,
                 _("Avahi is not running – Zwift will not find the sensors. Remedy: install "
                   "the avahi package and start the avahi-daemon service."))


def run_all() -> list[Check]:
    checks = [check_system()]
    checks += check_graphics()
    checks += [check_bluetooth(), check_avahi(), check_disk(), check_network(), check_wine(), check_existing()]
    return checks


def overall(checks: list[Check]) -> str:
    if any(c.status == FAIL for c in checks):
        return FAIL
    if any(c.status == WARN for c in checks):
        return WARN
    return OK
