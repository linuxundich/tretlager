"""Translation of the user interface (gettext, domain "tretlager").

The source language is English. German comes from po/de.po; if there is no catalog for the
system language, Tretlager shows English. Catalogs live as `po/<language>.po` in the source tree
and are compiled into `data/locale` at build time (build-aux/msgfmt.py). `TRETLAGER_LANG=en` or
`de` forces a language.
"""

from __future__ import annotations

import gettext
import os
from pathlib import Path

DOMAIN = "tretlager"
LOCALEDIR = Path(__file__).resolve().parent / "data" / "locale"
SOURCE_LANGUAGE = "en"


def system_languages(env=os.environ) -> list[str]:
    """Languages in the order gettext evaluates them as well (LANGUAGE, LC_ALL, LC_MESSAGES, LANG)."""
    for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = env.get(var, "")
        if value:
            return [v.split(".")[0].split("@")[0] for v in value.split(":") if v]
    return []


def ui_language(env=os.environ, localedir: Path = LOCALEDIR) -> str:
    """Short code of the UI language: a language with a catalog (or the source language), else "en"."""
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
    """Only marks text for translation; it is translated when displayed (e.g. bridge texts that
    reach the UI as state over D-Bus and stay untranslated in the journal)."""
    return text
