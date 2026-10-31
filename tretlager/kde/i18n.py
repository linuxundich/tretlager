"""Replacement for KLocalizedContext: i18n functions for QML that Kirigami Addons calls.

In C++ programs KI18n sets these functions as the QML engine's context object. PySide has no
binding for it; without it, labels stay empty, e.g. on the About page. gettext reads the
translations from the catalogs of the respective domain (e.g. kirigami-addons6); i18n() without
a domain uses Tretlager's own catalog.
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
    """Replace the KDE placeholders %1 … %9 (from the back, so that %1 does not hit %10)."""
    for i in range(len(args), 0, -1):
        text = text.replace(f"%{i}", str(args[i - 1]))
    return text


def _args(*values):
    return [v for v in values if v is not None]


class LocalizedContext(QObject):
    """Context object of the QML engine. Up to three placeholders per call suffice for Kirigami Addons."""

    # --- with domain ---
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

    # --- without domain: Tretlager's own texts (domain "tretlager", see tretlager/i18n.py) ---
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
