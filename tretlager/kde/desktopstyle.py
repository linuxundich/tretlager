"""Aussehen außerhalb von Plasma im Flatpak: Breeze, aber Hell/Dunkel und Schrift vom Desktop.

Im Flatpak liest das Plasma-Plattformthema Farben und Schrift über das Settings-Portal
(`org.kde.kdeglobals.*`). Das liefert nur Plasma; unter GNOME bliebe Tretlager immer Breeze Light mit
Noto Sans. Die Einstellungen des Desktops kommen ebenfalls übers Portal
(`org.freedesktop.appearance color-scheme`, `org.gnome.desktop.interface font-name`). Das Farbschema
setzt Tretlager wie KColorSchemeManager: Eigenschaft `KDE_COLOR_SCHEME_PATH` (Kirigami und der
Desktop-Stil lesen ihre Farben daraus) plus passende Anwendungspalette (löst das Neuzeichnen aus).
Ändert sich die Einstellung, folgt Tretlager sofort.
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
    """Nur im Flatpak und nicht unter Plasma (dort liefert das Portal die echten KDE-Einstellungen)."""
    return in_flatpak and "KDE" not in env.get("XDG_CURRENT_DESKTOP", "").upper()


def scheme_name(color_scheme) -> str:
    """Portal-Wert color-scheme (0 egal, 1 dunkel, 2 hell) → Breeze-Farbschema."""
    return "BreezeDark" if color_scheme == 1 else "BreezeLight"


def parse_font(value) -> tuple[str, float] | None:
    """GNOME-Schriftangabe „Adwaita Sans 12“ bzw. „Cantarell Bold 11“ → (Familie, Größe in pt)."""
    m = re.fullmatch(r"\s*(.+?)\s+(\d+(?:\.\d+)?)\s*", value or "")
    if not m:
        return None
    family = re.sub(r"\s+(Regular|Bold|Italic|Medium|Light|Semi-Bold|Oblique)$", "", m.group(1))
    return family, float(m.group(2))


def read_colors(path: Path) -> dict[str, dict[str, tuple[int, int, int]]]:
    """[Colors:*]-Gruppen einer .colors-Datei als {Gruppe: {Schlüssel: (r, g, b)}}."""
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
    """Anwendungspalette wie KColorScheme::createApplicationPalette (vereinfacht)."""
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
    """Wendet Farbschema und Schrift an und folgt Änderungen am Desktop."""

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
        applog.info("Farbschema %s (Desktop außerhalb von Plasma)", name)

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
