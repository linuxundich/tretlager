"""Error report for testers: one ZIP file with system information, logs and configuration.

Contents: report.txt (versions, system, graphics, screens, Wine, bridge, checks), the logs of the
interface, the bridge, Wine and Zwift, state.json and the bridge's device list. Sign-in data never
goes in: the token is only in the keyring and in a temporary file, and everything that looks like a
token, password or e-mail address is masked in all files before packing (`scrub`).
"""

from __future__ import annotations

import json
import os
import platform
import re
import time
import zipfile
from pathlib import Path
from typing import Callable

from .. import __version__, build_id
from . import bridgectl, debug, display, paths, power, setup, state, systemcheck, wine

# Large logs: keep the beginning (configuration, start) and above all the end (crash).
MAX_BYTES = 6_000_000
HEAD_BYTES = 1_000_000

_SECRETS = [
    (re.compile(r"eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"), "[token]"),
    (re.compile(r'("(?:access|refresh|id)_token"\s*:\s*")[^"]*'), r"\1[token]"),
    (re.compile(r"(--token=)\S+"), r"\1[removed]"),
    (re.compile(r"(Bearer\s+)\S+", re.IGNORECASE), r"\1[token]"),
    (re.compile(r"(\b(?:password|passwd|client_secret|secret)[\"']?\s*[:=]\s*[\"']?)[^\s\"',;&]+",
                re.IGNORECASE), r"\1[removed]"),
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}"), "[e-mail]"),
]


def scrub(text: str) -> str:
    """Mask tokens, passwords and e-mail addresses."""
    for pattern, repl in _SECRETS:
        text = pattern.sub(repl, text)
    return text


def _read(path: Path) -> str:
    """File as text, shortened in the middle if it is larger than MAX_BYTES."""
    size = path.stat().st_size
    with open(path, "rb") as f:
        if size <= MAX_BYTES:
            data = f.read()
        else:
            head = f.read(HEAD_BYTES)
            f.seek(size - (MAX_BYTES - HEAD_BYTES))
            cut = f"\n\n[… {size - MAX_BYTES} bytes left out by Tretlager …]\n\n".encode()
            data = head + cut + f.read()
    return data.decode("utf-8", errors="replace")


def zwift_log_dirs(prefix: Path | None = None) -> list[Path]:
    return sorted((prefix or paths.PREFIX).glob("drive_c/users/*/AppData/Local/Zwift/Logs"))


def collect_files(prefix: Path | None = None, state_dir: Path | None = None,
                  bridge_config: Path | None = None) -> dict[str, Path]:
    """Name in the ZIP → file on disk (only files that exist)."""
    state_dir = state_dir or paths.STATE
    files: dict[str, Path] = {}
    for name in ("tretlager.log", "tretlager.log.1", "bridge.log", "bridge.log.1", "zwift-wine.log",
                 "zwift-wine.old.log", "state.json"):
        files[f"tretlager/{name}"] = state_dir / name
    if bridge_config is None:
        from ..bridge import config
        bridge_config = config.config_path()
    files["tretlager/bridge.json"] = bridge_config
    for logs in zwift_log_dirs(prefix):
        for name in ("Log.txt", "Log (old 1).txt", "Log (old 2).txt", "Log (old 3).txt",
                     "Launcher_log.txt", "Launcher_log (old 1).txt"):
            files[f"zwift/{name}"] = logs / name
    return {k: v for k, v in files.items() if v.is_file()}


def _safe(fn: Callable, default="?"):
    try:
        return fn()
    except Exception as e:  # the report is collected best effort; one failing source must not stop it
        return f"{default} ({type(e).__name__})"


def _flatpak_info() -> str:
    try:
        return Path("/.flatpak-info").read_text()
    except OSError:
        return ""


def system_report(screens: list[dict] | None = None) -> str:
    """report.txt: everything that helps to understand a problem, in readable form."""
    lines: list[str] = []

    def section(title: str) -> None:
        lines.extend(["", f"== {title}"])

    def item(key: str, value) -> None:
        lines.append(f"{key}: {value}")

    lines.append(f"Tretlager error report, {time.strftime('%Y-%m-%d %H:%M:%S %z')}")
    section("Tretlager")
    item("Version", __version__)
    item("Build", build_id() or "–")
    item("Flatpak", bridgectl.IN_FLATPAK)
    item("Debug mode", _safe(debug.enabled))

    section("System")
    osr = _safe(systemcheck.read_os_release, {})
    item("OS", osr.get("PRETTY_NAME", osr) if isinstance(osr, dict) else osr)
    item("Kernel", platform.release())
    item("Machine", platform.machine())
    for var in ("XDG_CURRENT_DESKTOP", "XDG_SESSION_TYPE", "DESKTOP_SESSION", "LANG", "QT_QPA_PLATFORMTHEME",
                "WAYLAND_DISPLAY", "DISPLAY"):
        item(var, os.environ.get(var, "–"))
    item("On AC power", _safe(power.on_ac))

    section("Screens")
    for s in screens or []:
        item(s.get("name", "?"), f"{s.get('x')},{s.get('y')} {s.get('width')}×{s.get('height')} scale {s.get('scale')}")
    item("KWin XWayland scale", _safe(lambda: display._kwin_xwayland_scale(Path.home() / ".config")))
    item("Wine DPI (LogPixels)", _safe(lambda: display.current_dpi(paths.PREFIX)))
    item("Remembered Zwift monitor", _safe(lambda: state.load().get("window", {}).get("output", "–")))

    section("Graphics")
    for gpu in _safe(systemcheck.list_gpus, []) or []:
        item("GPU", f"{gpu.vendor} {gpu.device}, driver {gpu.driver}{', boot' if gpu.boot_vga else ''}"
             if isinstance(gpu, systemcheck.Gpu) else gpu)
    item("NVIDIA driver", _safe(systemcheck.nvidia_driver_version) or "–")
    item("Secure Boot", _safe(systemcheck.secure_boot_enabled))
    item("Graphics test", json.dumps(_safe(lambda: state.load().get("graphics", {}), {}), ensure_ascii=False))

    section("Wine and Zwift")
    item("Wine in use", _safe(systemcheck.wine_version))
    item("Wine bundled", _safe(wine.bundled_version))
    item("Wine kept", _safe(wine.kept_version) or "–")
    item("Zwift version", _safe(setup.game_version) or "–")

    section("Sensor bridge")
    status = _safe(bridgectl.status, None)
    lines.append(json.dumps(status, indent=2, ensure_ascii=False) if status else "not running")

    section("System check")
    for check in _safe(systemcheck.run_all, []) or []:
        lines.append(f"[{check.status}] {check.title}: {check.summary}")
        lines.extend(f"    {d}" for d in check.details)

    info = _flatpak_info()
    if info:
        section("Flatpak")
        lines.append(info.strip())
    return "\n".join(lines) + "\n"


def default_name(now: float | None = None) -> str:
    return time.strftime("tretlager-report-%Y-%m-%d-%H%M.zip", time.localtime(now))


def build(dest: Path, screens: list[dict] | None = None, files: dict[str, Path] | None = None,
          summary: str | None = None) -> list[str]:
    """Write the report to `dest`; returns the names in the ZIP."""
    files = collect_files() if files is None else files
    summary = system_report(screens) if summary is None else summary
    names = ["report.txt"]
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("report.txt", scrub(summary))
        for name, path in files.items():
            try:
                z.writestr(name, scrub(_read(path)))
                names.append(name)
            except OSError:
                continue
    return names
