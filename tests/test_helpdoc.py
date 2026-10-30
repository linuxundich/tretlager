from pathlib import Path

from tretlager.core import helpdoc

DATA = Path(__file__).resolve().parents[1] / "tretlager" / "data" / "hilfe.md"


def test_parse_sections_and_items():
    text = """## Titel
<!-- icon: help-about; wide -->

Ein *kurzer* Satz
über zwei Zeilen.

- [view-refresh] **Stichwort**: Text mit `code` und
  Folgezeile.
- **Ohne Symbol**: nur Text
"""
    (s,) = helpdoc.parse(text)
    assert s["title"] == "Titel" and s["icon"] == "help-about" and s["wide"] is True
    assert s["intro"] == ["Ein <i>kurzer</i> Satz über zwei Zeilen."]
    assert s["items"][0] == {"icon": "view-refresh", "title": "Stichwort",
                             "text": "Text mit <code>code</code> und Folgezeile."}
    assert s["items"][1]["icon"] == "" and s["items"][1]["text"] == "nur Text"


def test_inline_escapes_html():
    assert helpdoc.inline("a < b **fett**") == "a &lt; b <b>fett</b>"


def test_real_help_file_layout():
    sections = helpdoc.layout(helpdoc.parse(DATA.read_text()))
    titles = [s["title"] for s in sections]
    assert "Sensoren" in titles and "Wenn etwas nicht klappt" in titles
    assert all(s["items"] for s in sections)
    wide = [s for s in sections if s["column"] == 2]
    assert len(wide) == 1 and len(wide[0]["items"]) % 2 == 0  # zwei Spalten ohne Lücke
    assert {s["column"] for s in sections if not s["wide"]} == {0, 1}
