import re
import sys
from pathlib import Path

from tretlager import i18n

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "build-aux"))
import msgfmt  # noqa: E402


def test_language_selection(tmp_path):
    (tmp_path / "en" / "LC_MESSAGES").mkdir(parents=True)
    (tmp_path / "en" / "LC_MESSAGES" / "tretlager.mo").write_bytes(b"")
    assert i18n.ui_language({"LANG": "de_DE.UTF-8"}, tmp_path) == "de"
    assert i18n.ui_language({"LANG": "en_GB.UTF-8"}, tmp_path) == "en"
    assert i18n.ui_language({"LANG": "fr_FR.UTF-8"}, tmp_path) == "en"  # ohne Katalog: Englisch
    assert i18n.ui_language({"LANGUAGE": "de:en", "LANG": "en_US"}, tmp_path) == "de"
    assert i18n.ui_language({"LANG": "C"}, tmp_path) == "en"
    assert i18n.ui_language({"LANG": "de_DE", "TRETLAGER_LANG": "en"}, tmp_path) == "en"


def _placeholders(text: str) -> set[str]:
    return set(re.findall(r"%\d|\{\w+\}", text))


def test_english_catalog_complete_and_consistent():
    pot = (ROOT / "po" / "tretlager.pot").read_text()
    entries = msgfmt.parse(ROOT / "po" / "en.po")
    ids = {k.split("\x00")[0] for k in entries if k}
    pot_ids = {m for m in re.findall(r'^msgid "(.+)"$', pot, re.M)}
    missing = [m for m in pot_ids if m.replace('\\"', '"').replace("\\n", "\n") not in ids]
    assert not missing, missing[:5]
    for key, value in entries.items():
        if not key:
            continue
        src = key.split("\x00")[0]
        for translated in value.split("\x00"):
            # Plural: die Einzahl darf die Zahl ausschreiben („einen Tag“ → „one more day“)
            if "\x00" in key:
                assert _placeholders(translated) <= _placeholders(key.replace("\x00", " ")), key
            else:
                assert _placeholders(translated) == _placeholders(src), src


def test_msgfmt_roundtrip(tmp_path):
    import gettext
    out = tmp_path / "en.mo"
    msgfmt.write(msgfmt.parse(ROOT / "po" / "en.po"), out)
    t = gettext.GNUTranslations(out.open("rb"))
    assert t.gettext("Sensoren in der Nähe") == "Sensors nearby"
    assert t.ngettext(", Erneuerung noch {n} Tag", ", Erneuerung noch {n} Tage", 2) == ", renewal for {n} more days"


def test_english_help_matches_structure():
    from tretlager.core import helpdoc
    de = helpdoc.parse((ROOT / "tretlager" / "data" / "hilfe.md").read_text())
    en = helpdoc.parse((ROOT / "tretlager" / "data" / "hilfe.en.md").read_text())
    assert [len(s["items"]) for s in de] == [len(s["items"]) for s in en]
    assert [s["icon"] for s in de] == [s["icon"] for s in en]
    assert [s["wide"] for s in de] == [s["wide"] for s in en]
