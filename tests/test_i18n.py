import re
import sys
from pathlib import Path

from tretlager import i18n

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "build-aux"))
import msgfmt  # noqa: E402


def test_language_selection(tmp_path):
    (tmp_path / "de" / "LC_MESSAGES").mkdir(parents=True)
    (tmp_path / "de" / "LC_MESSAGES" / "tretlager.mo").write_bytes(b"")
    assert i18n.ui_language({"LANG": "de_DE.UTF-8"}, tmp_path) == "de"
    assert i18n.ui_language({"LANG": "en_GB.UTF-8"}, tmp_path) == "en"
    assert i18n.ui_language({"LANG": "fr_FR.UTF-8"}, tmp_path) == "en"  # no catalog: English
    assert i18n.ui_language({"LANGUAGE": "de:en", "LANG": "en_US"}, tmp_path) == "de"
    assert i18n.ui_language({"LANG": "C"}, tmp_path) == "en"
    assert i18n.ui_language({"LANG": "de_DE", "TRETLAGER_LANG": "en"}, tmp_path) == "en"


def _placeholders(text: str) -> set[str]:
    return set(re.findall(r"%\d|\{\w+\}", text))


def test_german_catalog_complete_and_consistent():
    pot = (ROOT / "po" / "tretlager.pot").read_text()
    entries = msgfmt.parse(ROOT / "po" / "de.po")
    ids = {k.split("\x00")[0] for k in entries if k}
    pot_ids = {m for m in re.findall(r'^msgid "(.+)"$', pot, re.M)}
    missing = [m for m in pot_ids if m.replace('\\"', '"').replace("\\n", "\n") not in ids]
    assert not missing, missing[:5]
    for key, value in entries.items():
        if not key:
            continue
        src = key.split("\x00")[0]
        for translated in value.split("\x00"):
            # Plural: the singular may spell out the number ("einen Tag" for "one more day")
            if "\x00" in key:
                assert _placeholders(translated) <= _placeholders(key.replace("\x00", " ")), key
            else:
                assert _placeholders(translated) == _placeholders(src), src


def test_msgfmt_roundtrip(tmp_path):
    import gettext
    out = tmp_path / "de.mo"
    msgfmt.write(msgfmt.parse(ROOT / "po" / "de.po"), out)
    t = gettext.GNUTranslations(out.open("rb"))
    assert t.gettext("Sensors nearby") == "Sensoren in der Nähe"
    assert t.ngettext(", renewal for {n} more day", ", renewal for {n} more days", 2) == ", Erneuerung noch {n} Tage"


def test_german_help_matches_structure():
    from tretlager.core import helpdoc
    de = helpdoc.parse((ROOT / "tretlager" / "data" / "help.de.md").read_text())
    en = helpdoc.parse((ROOT / "tretlager" / "data" / "help.md").read_text())
    assert [len(s["items"]) for s in de] == [len(s["items"]) for s in en]
    assert [s["icon"] for s in de] == [s["icon"] for s in en]
    assert [s["wide"] for s in de] == [s["wide"] for s in en]
