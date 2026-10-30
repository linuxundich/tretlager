"""Bildschirmskalierung an Wine weitergeben (DPI der Windows-Fenster).

Wine zeichnet seine Fenster mit 96 DPI, solange in der Registry nichts anderes steht. Auf
HiDPI-Bildschirmen mit „X11-Anwendungen skalieren selbst“ (Plasma, `Xwayland Scale`) erscheinen
Installer, .NET-Einrichtung und Wine-Dialoge dann winzig. Tretlager setzt deshalb
`HKCU\\Control Panel\\Desktop\\LogPixels` auf 96 × Skalierung, bei der Einrichtung und vor jedem
Start; die Oberfläche meldet die Skalierung über `set_scale` (Qt kennt sie auch unter Wayland).
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
    """Skalierung des Bildschirms, auf dem Tretlager läuft (von der Oberfläche gesetzt)."""
    global _scale
    _scale = scale if scale and scale > 0 else None


def _kwin_xwayland_scale(config_home: Path) -> float | None:
    """Skalierung, die KWin für XWayland-Programme ansetzt (Plasma: [Xwayland] Scale in kwinrc)."""
    cfg = configparser.ConfigParser(strict=False)
    try:
        cfg.read(config_home / "kwinrc")
        return float(cfg["Xwayland"]["Scale"])
    except (KeyError, ValueError, configparser.Error):
        return None


def wine_dpi(env=os.environ) -> int:
    """DPI für Wine: TRETLAGER_DPI, sonst 96 × Skalierung, sonst 96.

    Die Skalierung kommt bevorzugt aus der XWayland-Einstellung von KWin – auf sie richten sich die
    X11-Programme aus, unter denen Wine läuft. Sonst aus der Oberfläche (Fensterskalierung).
    """
    forced = env.get("TRETLAGER_DPI", "")
    if forced.isdigit():
        return int(forced)
    # Im Flatpak zeigt XDG_CONFIG_HOME in die Sandbox; kwinrc des Rechners liegt (mit Freigabe
    # xdg-config/kwinrc:ro) unter ~/.config.
    scale = (_kwin_xwayland_scale(Path(env.get("XDG_CONFIG_HOME") or Path.home() / ".config"))
             or _kwin_xwayland_scale(Path(env.get("HOME") or Path.home()) / ".config") or _scale)
    if not scale or scale < 1:
        return BASE_DPI
    return round(BASE_DPI * scale)


def current_dpi(prefix: Path) -> int | None:
    """LogPixels aus user.reg des Präfixes, None ohne Eintrag."""
    try:
        text = (prefix / "user.reg").read_text(errors="replace")
    except OSError:
        return None
    m = re.search(r'\[Control Panel\\\\Desktop\][^\[]*?"LogPixels"=dword:([0-9a-fA-F]{8})', text)
    return int(m.group(1), 16) if m else None


def ensure_dpi(prefix: Path, run: Callable[[list[str]], int], dpi: int | None = None) -> int | None:
    """LogPixels setzen, falls es abweicht; gibt den neuen Wert zurück (None: nichts geändert)."""
    dpi = dpi or wine_dpi()
    if current_dpi(prefix) == dpi or not (prefix / "user.reg").exists():
        return None
    run(["wine", "reg", "add", REG_KEY, "/v", "LogPixels", "/t", "REG_DWORD", "/d", str(dpi), "/f"])
    return dpi
