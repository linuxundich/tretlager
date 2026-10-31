"""Pass the screen scaling on to Wine (DPI of the Windows windows).

Wine draws its windows at 96 DPI unless the registry says otherwise. On HiDPI screens with
"Apply scaling themselves" for X11 applications (Plasma, `Xwayland Scale`), the installer, .NET
setup and Wine dialogs then appear tiny. Tretlager therefore sets
`HKCU\\Control Panel\\Desktop\\LogPixels` to 96 × scale, during setup and before every launch;
the interface reports the scale via `set_scale` (Qt knows it under Wayland, too).
"""

from __future__ import annotations

import configparser
import os
import re
from pathlib import Path
from typing import Callable

BASE_DPI = 96
REG_KEY = r"HKCU\Control Panel\Desktop"
_scale: float | None = None


def set_scale(scale: float) -> None:
    """Scale of the screen Tretlager runs on (set by the interface)."""
    global _scale
    _scale = scale if scale and scale > 0 else None


def _kwin_xwayland_scale(config_home: Path) -> float | None:
    """Scale KWin applies to XWayland programs (Plasma: [Xwayland] Scale in kwinrc)."""
    cfg = configparser.ConfigParser(strict=False)
    try:
        cfg.read(config_home / "kwinrc")
        return float(cfg["Xwayland"]["Scale"])
    except (KeyError, ValueError, configparser.Error):
        return None


def wine_dpi(env=os.environ) -> int:
    """DPI for Wine: TRETLAGER_DPI, else 96 × scale, else 96.

    The scale preferably comes from KWin's XWayland setting – X11 programs, which is what Wine
    runs as, follow it. Otherwise from the interface (window scale).
    """
    forced = env.get("TRETLAGER_DPI", "")
    if forced.isdigit():
        return int(forced)
    # In the Flatpak XDG_CONFIG_HOME points into the sandbox; the host's kwinrc is under
    # ~/.config (with the permission xdg-config/kwinrc:ro).
    scale = (_kwin_xwayland_scale(Path(env.get("XDG_CONFIG_HOME") or Path.home() / ".config"))
             or _kwin_xwayland_scale(Path(env.get("HOME") or Path.home()) / ".config") or _scale)
    if not scale or scale < 1:
        return BASE_DPI
    return round(BASE_DPI * scale)


def current_dpi(prefix: Path) -> int | None:
    """LogPixels from the prefix's user.reg, None without an entry."""
    try:
        text = (prefix / "user.reg").read_text(errors="replace")
    except OSError:
        return None
    m = re.search(r'\[Control Panel\\\\Desktop\][^\[]*?"LogPixels"=dword:([0-9a-fA-F]{8})', text)
    return int(m.group(1), 16) if m else None


def ensure_dpi(prefix: Path, run: Callable[[list[str]], int], dpi: int | None = None) -> int | None:
    """Set LogPixels if it differs; returns the new value (None: nothing changed)."""
    dpi = dpi or wine_dpi()
    if current_dpi(prefix) == dpi or not (prefix / "user.reg").exists():
        return None
    run(["wine", "reg", "add", REG_KEY, "/v", "LogPixels", "/t", "REG_DWORD", "/d", str(dpi), "/f"])
    return dpi
