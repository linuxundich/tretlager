"""Appearance outside Plasma in the Flatpak: Breeze, but light/dark and font from the desktop.

In the Flatpak the Plasma platform theme reads colors and font through the Settings portal
(`org.kde.kdeglobals.*`). Only Plasma provides those; under GNOME Tretlager would always stay
Breeze Light with Noto Sans. The desktop's settings also come through the portal
(`org.freedesktop.appearance color-scheme`, `org.gnome.desktop.interface font-name`). Tretlager sets
the color scheme like KColorSchemeManager: the `KDE_COLOR_SCHEME_PATH` property (Kirigami and the
desktop style read their colors from it) plus a matching application palette (triggers the repaint).
When the setting changes, Tretlager follows immediately.
"""

from __future__ import annotations

import configparser
import os
import re
from pathlib import Path

from PySide6.QtCore import SLOT, QObject, Slot
from PySide6.QtDBus import QDBusConnection, QDBusMessage, QDBusVariant
from PySide6.QtGui import QColor, QFont, QGuiApplication, QPalette

from ..core import applog

COLOR_SCHEMES = Path("/usr/share/color-schemes")
PORTAL = ("org.freedesktop.portal.Desktop", "/org/freedesktop/portal/desktop", "org.freedesktop.portal.Settings")
APPEARANCE = ("org.freedesktop.appearance", "color-scheme")
GNOME_FONT = ("org.gnome.desktop.interface", "font-name")


def wanted(env=os.environ, in_flatpak: bool = False) -> bool:
    """Only in the Flatpak and not under Plasma (there the portal provides the real KDE settings)."""
    return in_flatpak and "KDE" not in env.get("XDG_CURRENT_DESKTOP", "").upper()


def scheme_name(color_scheme) -> str:
    """Portal value color-scheme (0 no preference, 1 dark, 2 light) → Breeze color scheme."""
    return "BreezeDark" if color_scheme == 1 else "BreezeLight"


def parse_font(value) -> tuple[str, float] | None:
    """GNOME font setting "Adwaita Sans 12" or "Cantarell Bold 11" → (family, size in pt)."""
    m = re.fullmatch(r"\s*(.+?)\s+(\d+(?:\.\d+)?)\s*", value or "")
    if not m:
        return None
    family = re.sub(r"\s+(Regular|Bold|Italic|Medium|Light|Semi-Bold|Oblique)$", "", m.group(1))
    return family, float(m.group(2))


def read_colors(path: Path) -> dict[str, dict[str, tuple[int, int, int]]]:
    """[Colors:*] groups of a .colors file as {group: {key: (r, g, b)}}."""
    cp = configparser.ConfigParser(interpolation=None, strict=False)
    cp.optionxform = str
    cp.read(path, encoding="utf-8")
    colors = {}
    for section in cp.sections():
        if section.startswith("Colors:") and "][" not in section:
            colors[section[len("Colors:"):]] = {
                k: tuple(int(x) for x in v.split(",")[:3]) for k, v in cp[section].items() if v.count(",") >= 2}
    return colors


def palette(colors) -> QPalette:
    """Application palette like KColorScheme::createApplicationPalette (simplified)."""
    def c(group, key):
        return QColor(*colors[group][key])
    p = QPalette()
    for grp in (QPalette.Active, QPalette.Inactive, QPalette.Disabled):
        fg = "ForegroundInactive" if grp == QPalette.Disabled else "ForegroundNormal"
        for role, (group, key) in {
            QPalette.Window: ("Window", "BackgroundNormal"), QPalette.WindowText: ("Window", fg),
            QPalette.Base: ("View", "BackgroundNormal"), QPalette.AlternateBase: ("View", "BackgroundAlternate"),
            QPalette.Text: ("View", fg), QPalette.Button: ("Button", "BackgroundNormal"),
            QPalette.ButtonText: ("Button", fg), QPalette.Highlight: ("Selection", "BackgroundNormal"),
            QPalette.HighlightedText: ("Selection", "ForegroundNormal"),
            QPalette.ToolTipBase: ("Tooltip", "BackgroundNormal"), QPalette.ToolTipText: ("Tooltip", "ForegroundNormal"),
            QPalette.Link: ("View", "ForegroundLink"), QPalette.LinkVisited: ("View", "ForegroundVisited"),
            QPalette.PlaceholderText: ("View", "ForegroundInactive"),
        }.items():
            p.setColor(grp, role, c(group, key))
        button = c("Button", "BackgroundNormal")
        p.setColor(grp, QPalette.Light, button.lighter(150))
        p.setColor(grp, QPalette.Midlight, button.lighter(120))
        p.setColor(grp, QPalette.Mid, button.darker(130))
        p.setColor(grp, QPalette.Dark, button.darker(200))
        p.setColor(grp, QPalette.Shadow, QColor(0, 0, 0))
    return p


def _value(v):
    while isinstance(v, QDBusVariant):
        v = v.variant()
    return v


def read_setting(namespace: str, key: str):
    msg = QDBusMessage.createMethodCall(*PORTAL, "ReadOne")
    msg.setArguments([namespace, key])
    reply = QDBusConnection.sessionBus().call(msg, timeout=2000)
    if reply.type() != QDBusMessage.ReplyMessage or not reply.arguments():
        return None
    return _value(reply.arguments()[0])


class DesktopStyle(QObject):
    """Applies color scheme and font and follows changes on the desktop."""

    def __init__(self, app: QGuiApplication):
        super().__init__(app)
        self.app = app
        self.scheme = ""

    def start(self) -> None:
        self.apply_scheme(read_setting(*APPEARANCE))
        self.apply_font(read_setting(*GNOME_FONT))
        QDBusConnection.sessionBus().connect(*PORTAL, "SettingChanged", self, SLOT("changed(QDBusMessage)"))

    def apply_scheme(self, color_scheme) -> None:
        name = scheme_name(color_scheme)
        path = COLOR_SCHEMES / f"{name}.colors"
        if name == self.scheme or not path.exists():
            return
        self.scheme = name
        self.app.setProperty("KDE_COLOR_SCHEME_PATH", str(path))
        self.app.setPalette(palette(read_colors(path)))
        applog.info("Color scheme %s (desktop outside Plasma)", name)

    def apply_font(self, value) -> None:
        font = parse_font(value) if isinstance(value, str) else None
        if font:
            f = QFont(font[0])
            f.setPointSizeF(font[1])
            self.app.setFont(f)

    @Slot(QDBusMessage)
    def changed(self, msg: QDBusMessage) -> None:
        namespace, key, value = (_value(a) for a in msg.arguments()[:3])
        if (namespace, key) == APPEARANCE:
            self.apply_scheme(value)
        elif (namespace, key) == GNOME_FONT:
            self.apply_font(value)
