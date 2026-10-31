import json
import subprocess
from pathlib import Path

from tretlager.core import systemcheck as sc


def make_root(tmp_path: Path, os_release: str, gpus: list[tuple], nvidia_version: str = "",
              secure_boot: int | None = None, rfkill_soft: str | None = None) -> Path:
    (tmp_path / "etc").mkdir(parents=True)
    (tmp_path / "etc/os-release").write_text(os_release)
    drm = tmp_path / "sys/class/drm"
    drivers = tmp_path / "sys/bus/pci/drivers"
    for i, (vendor, device, driver, boot) in enumerate(gpus):
        dev = tmp_path / f"sys/devices/pci/{i}"
        dev.mkdir(parents=True)
        (dev / "vendor").write_text(vendor + "\n")
        (dev / "device").write_text(device + "\n")
        (dev / "boot_vga").write_text("1\n" if boot else "0\n")
        if driver:
            (drivers / driver).mkdir(parents=True, exist_ok=True)
            (dev / "driver").symlink_to(drivers / driver)
        (drm / f"card{i}").mkdir(parents=True)
        (drm / f"card{i}" / "device").symlink_to(dev)
        (drm / f"card{i}-eDP-1").mkdir()
    if nvidia_version:
        (tmp_path / "sys/module/nvidia").mkdir(parents=True)
        (tmp_path / "sys/module/nvidia/version").write_text(nvidia_version + "\n")
    if secure_boot is not None:
        efi = tmp_path / "sys/firmware/efi/efivars"
        efi.mkdir(parents=True)
        (efi / sc.SECURE_BOOT_VAR).write_bytes(bytes([6, 0, 0, 0, secure_boot]))
    if rfkill_soft is not None:
        rf = tmp_path / "sys/class/rfkill/rfkill0"
        rf.mkdir(parents=True)
        (rf / "type").write_text("bluetooth\n")
        (rf / "soft").write_text(rfkill_soft + "\n")
    return tmp_path


TUXEDO_FORKY = 'NAME="TUXEDO OS"\nID=tuxedo\nID_LIKE="debian"\nPRETTY_NAME="TUXEDO OS (Debian base)"\nVERSION_CODENAME=forky\n'
TINYTIN_GPUS = [("0x8086", "0x46a6", "i915", True), ("0x10de", "0x25a0", "nvidia", False)]


def test_tinytin_like_system(tmp_path):
    root = make_root(tmp_path, TUXEDO_FORKY, TINYTIN_GPUS, nvidia_version="580.178.04", secure_boot=0)
    assert sc.check_system(root, "x86_64").status == sc.OK
    checks = sc.check_graphics(root)
    assert [c.id for c in checks] == ["graphics", "hybrid"]
    assert checks[0].status == sc.OK and "580.178.04" in checks[0].summary
    assert "Intel" in checks[1].details[0]


def test_nvidia_without_driver_and_secure_boot(tmp_path):
    root = make_root(tmp_path, TUXEDO_FORKY, [("0x10de", "0x25a0", "nouveau", True)], secure_boot=1)
    (c,) = sc.check_graphics(root)
    assert c.status == sc.FAIL and "Secure Boot" in c.summary and c.action == "nvidia-help"


def test_intel_only_is_warning(tmp_path):
    root = make_root(tmp_path, TUXEDO_FORKY, [("0x8086", "0x9a49", "i915", True)])
    (c,) = sc.check_graphics(root)
    assert c.status == sc.WARN and "Intel" in c.summary


def test_other_systems(tmp_path):
    root = make_root(tmp_path, 'ID=fedora\nPRETTY_NAME="Fedora Linux 45 (KDE Plasma)"\n', [])
    c = sc.check_system(root, "x86_64")
    assert c.status == sc.OK and c.summary == "Fedora Linux 45 (KDE Plasma)"  # nur angezeigt, nicht bewertet
    assert sc.check_system(root, "aarch64").status == sc.FAIL


def test_os_release_of_host_inside_flatpak(tmp_path):
    root = make_root(tmp_path, 'ID=org.kde.Platform\nPRETTY_NAME="KDE Flatpak runtime"\n', [])
    (root / "run/host").mkdir(parents=True)
    (root / "run/host/os-release").write_text('ID=tuxedo\nPRETTY_NAME="TUXEDO OS"\n')
    assert sc.check_system(root, "x86_64").summary == "TUXEDO OS"


def test_nvidia_version_from_proc(tmp_path):
    (tmp_path / "proc/driver/nvidia").mkdir(parents=True)
    (tmp_path / "proc/driver/nvidia/version").write_text(
        "NVRM version: NVIDIA UNIX Open Kernel Module for x86_64  580.178.04  Release Build  (pbuilder)\n")
    assert sc.nvidia_driver_version(tmp_path) == "580.178.04"


def test_avahi_check():
    def run_with(owner):
        def run(cmd, **_kw):
            method = cmd[cmd.index("--method") + 1]
            out = {"org.freedesktop.DBus.NameHasOwner": "(%s,)" % ("true" if owner else "false"),
                   "org.freedesktop.DBus.ListActivatableNames": "(['org.freedesktop.DBus'],)"}[method]
            return subprocess.CompletedProcess(cmd, 0, out, "")
        return run
    assert sc.check_avahi(run_with(True)).status == sc.OK
    assert sc.check_avahi(run_with(False)).status == sc.WARN


def fake_busctl(powered=True, missing=False):
    """gdbus Properties.GetAll eines BlueZ-Adapters (Name historisch)."""
    def run(cmd, **_kw):
        if missing:
            return subprocess.CompletedProcess(cmd, 1, "", "no adapter")
        out = ("({'Address': <'68:54:5A:AC:2E:15'>, 'AddressType': <'public'>, 'Name': <'tinytin'>, "
               "'Powered': <%s>, 'Class': <uint32 7078156>, 'UUIDs': <['0000110e-0000-1000-8000-00805f9b34fb']>},)"
               % ("true" if powered else "false"))
        return subprocess.CompletedProcess(cmd, 0, out, "")
    return run


def test_bluetooth_states(tmp_path):
    root = make_root(tmp_path, TUXEDO_FORKY, [], rfkill_soft="0")
    assert sc.check_bluetooth(root, fake_busctl()).status == sc.OK
    off = sc.check_bluetooth(root, fake_busctl(powered=False))
    assert off.status == sc.WARN and off.action == "bluetooth-on"
    assert sc.check_bluetooth(root, fake_busctl(missing=True)).status == sc.WARN


def test_rfkill_soft_block_counts_as_off(tmp_path):
    root = make_root(tmp_path, TUXEDO_FORKY, [], rfkill_soft="1")
    assert sc.check_bluetooth(root, fake_busctl()).action == "bluetooth-on"


def test_existing_installation(tmp_path):
    assert "Noch nicht" in sc.check_existing(tmp_path).summary
    (tmp_path / "ZwiftLauncher.exe").touch()
    assert "Spiel fehlt" in sc.check_existing(tmp_path).summary
    (tmp_path / "ZwiftApp.exe").touch()
    assert "schon eingerichtet" in sc.check_existing(tmp_path).summary


def test_network_unreachable_host():
    c = sc.check_network([("127.0.0.1", 9)], timeout=0.5)
    assert c.status == sc.FAIL


def test_overall():
    mk = lambda s: sc.Check("x", "x", s, "")  # noqa: E731
    assert sc.overall([mk(sc.OK), mk(sc.WARN)]) == sc.WARN
    assert sc.overall([mk(sc.OK), mk(sc.FAIL), mk(sc.WARN)]) == sc.FAIL
    assert sc.overall([mk(sc.OK)]) == sc.OK


def test_nvidia_in_flatpak_without_gl_extension(tmp_path):
    root = make_root(tmp_path, TUXEDO_FORKY, TINYTIN_GPUS, nvidia_version="580.196.07")
    (root / ".flatpak-info").write_text("[Application]\n")
    checks = sc.check_graphics(root)
    assert checks[0].status == sc.FAIL and "flatpak update" in checks[0].summary
    assert checks[1].status == sc.WARN  # Hybrid-Zeile verspricht die NVIDIA nicht
    assert not sc.nvidia_usable(root)
    (root / "usr/lib/x86_64-linux-gnu/GL/nvidia-580-196-07").mkdir(parents=True)
    assert sc.check_graphics(root)[0].status == sc.OK
    assert sc.nvidia_usable(root)


def test_gpu_signature_changes_when_nvidia_appears(tmp_path):
    intel = make_root(tmp_path / "a", TUXEDO_FORKY, [("0x8086", "0x591b", "i915", True)])
    hybrid = make_root(tmp_path / "b", TUXEDO_FORKY, [("0x8086", "0x591b", "i915", True),
                                                       ("0x10de", "0x1c8d", "nvidia", False)], nvidia_version="580.196.07")
    assert sc.gpu_signature(intel) == ["Intel:0x591b:i915"]
    assert sc.gpu_signature(hybrid)[-1] == "nvidia-usable"


def test_intel_only_mentions_switched_off_nvidia(tmp_path):
    root = make_root(tmp_path, TUXEDO_FORKY, [("0x8086", "0x591b", "i915", True)])
    (c,) = sc.check_graphics(root)
    assert any("envycontrol" in d for d in c.details)
