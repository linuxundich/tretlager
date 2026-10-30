"""Übersetzung der Oberfläche (gettext, Domain „tretlager“).

Quellsprache ist Deutsch. Gibt es für die Systemsprache keinen Katalog, zeigt Tretlager Englisch:
Für alle, die kein Deutsch eingestellt haben, ist Englisch die verständlichere Wahl. Kataloge
liegen als `po/<sprache>.po` im Quellbaum und werden beim Bauen nach `data/locale` übersetzt
(build-aux/msgfmt.py). `TRETLAGER_LANG=en` bzw. `de` erzwingt eine Sprache.
"""

from __future__ import annotations

import gettext
import os
from pathlib import Path

DOMAIN = "tretlager"
LOCALEDIR = Path(__file__).resolve().parent / "data" / "locale"
SOURCE_LANGUAGE = "de"


def system_languages(env=os.environ) -> list[str]:
    """Sprachen in der Reihenfolge, die auch gettext auswertet (LANGUAGE, LC_ALL, LC_MESSAGES, LANG)."""
    for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = env.get(var, "")
        if value:
            return [v.split(".")[0].split("@")[0] for v in value.split(":") if v]
    return []


def ui_language(env=os.environ, localedir: Path = LOCALEDIR) -> str:
    """Kurzcode der Oberflächensprache: „de“, eine Sprache mit Katalog oder sonst „en“."""
    forced = env.get("TRETLAGER_LANG", "")
    for lang in ([forced] if forced else []) + system_languages(env):
        code = lang.split("_")[0].lower()
        if code == SOURCE_LANGUAGE or (localedir / code / "LC_MESSAGES" / f"{DOMAIN}.mo").exists():
            return code
        if code in ("c", "posix"):
            break
    return "en"


def translation(language: str | None = None, localedir: Path = LOCALEDIR) -> gettext.NullTranslations:
    language = language or ui_language(localedir=localedir)
    if language == SOURCE_LANGUAGE:
        return gettext.NullTranslations()
    return gettext.translation(DOMAIN, localedir, languages=[language], fallback=True)


LANGUAGE = ui_language()
_t = translation(LANGUAGE)
_ = _t.gettext
ngettext = _t.ngettext
pgettext = _t.pgettext


def N_(text: str) -> str:
    """Nur Markierung für die Übersetzung, übersetzt wird beim Anzeigen (etwa Texte der Bridge,
    die als Zustand über D-Bus zur Oberfläche gehen und im Journal deutsch bleiben)."""
    return text
