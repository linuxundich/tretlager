"""Ersatz für KLocalizedContext: i18n-Funktionen für QML, die Kirigami Addons aufruft.

In C++-Programmen setzt KI18n diese Funktionen als Kontextobjekt der QML-Engine. PySide hat dafür
keine Bindung; ohne sie bleiben z. B. auf der Infoseite die Beschriftungen leer. Die Übersetzungen
liest gettext aus den Katalogen der jeweiligen Domain (etwa kirigami-addons6); i18n() ohne Domain
nutzt Tretlagers eigenen Katalog.
"""

from __future__ import annotations

import gettext
from functools import lru_cache

from PySide6.QtCore import QObject, Slot

from ..i18n import _t as own


@lru_cache(maxsize=None)
def _catalog(domain: str) -> gettext.NullTranslations:
    return gettext.translation(domain, fallback=True)


def _fill(text: str, args) -> str:
    """KDE-Platzhalter %1 … %9 ersetzen (von hinten, damit %1 nicht in %10 greift)."""
    for i in range(len(args), 0, -1):
        text = text.replace(f"%{i}", str(args[i - 1]))
    return text


def _args(*values):
    return [v for v in values if v is not None]


class LocalizedContext(QObject):
    """Kontextobjekt der QML-Engine. Bis zu drei Platzhalter je Aufruf genügen für Kirigami Addons."""

    # --- mit Domain ---
    @Slot(str, str, result=str)
    @Slot(str, str, "QVariant", result=str)
    @Slot(str, str, "QVariant", "QVariant", result=str)
    @Slot(str, str, "QVariant", "QVariant", "QVariant", result=str)
    def i18nd(self, domain, text, a1=None, a2=None, a3=None):
        return _fill(_catalog(domain).gettext(text), _args(a1, a2, a3))

    @Slot(str, str, str, result=str)
    @Slot(str, str, str, "QVariant", result=str)
    @Slot(str, str, str, "QVariant", "QVariant", result=str)
    def i18ndc(self, domain, context, text, a1=None, a2=None):
        return _fill(_catalog(domain).pgettext(context, text), _args(a1, a2))

    @Slot(str, str, str, "QVariant", result=str)
    @Slot(str, str, str, "QVariant", "QVariant", result=str)
    @Slot(str, str, str, "QVariant", "QVariant", "QVariant", result=str)
    def i18ndp(self, domain, singular, plural, n, a1=None, a2=None):
        count = int(n) if n is not None else 0
        return _fill(_catalog(domain).ngettext(singular, plural, count), _args(n, a1, a2))

    @Slot(str, str, str, str, "QVariant", result=str)
    @Slot(str, str, str, str, "QVariant", "QVariant", result=str)
    def i18ndcp(self, domain, context, singular, plural, n, a1=None):
        count = int(n) if n is not None else 0
        return _fill(_catalog(domain).npgettext(context, singular, plural, count), _args(n, a1))

    # --- ohne Domain: Texte von Tretlager selbst (Domain „tretlager“, siehe tretlager/i18n.py) ---
    @Slot(str, result=str)
    @Slot(str, "QVariant", result=str)
    @Slot(str, "QVariant", "QVariant", result=str)
    @Slot(str, "QVariant", "QVariant", "QVariant", result=str)
    def i18n(self, text, a1=None, a2=None, a3=None):
        return _fill(own.gettext(text), _args(a1, a2, a3))

    @Slot(str, str, result=str)
    @Slot(str, str, "QVariant", result=str)
    @Slot(str, str, "QVariant", "QVariant", result=str)
    def i18nc(self, context, text, a1=None, a2=None):
        return _fill(own.pgettext(context, text), _args(a1, a2))

    @Slot(str, str, "QVariant", result=str)
    @Slot(str, str, "QVariant", "QVariant", result=str)
    def i18np(self, singular, plural, n, a1=None):
        return _fill(own.ngettext(singular, plural, int(n)), _args(n, a1))
