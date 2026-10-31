from pathlib import Path

from tretlager.core import helpdoc

DATA = Path(__file__).resolve().parents[1] / "tretlager" / "data" / "help.md"


def test_parse_sections_and_items():
    text = """## Title
<!-- icon: help-about; wide -->

A *short* sentence
across two lines.

- [view-refresh] **Keyword**: Text with `code` and a
  continuation line.
- **No icon**: text only
"""
    (s,) = helpdoc.parse(text)
    assert s["title"] == "Title" and s["icon"] == "help-about" and s["wide"] is True
    assert s["intro"] == ["A <i>short</i> sentence across two lines."]
    assert s["items"][0] == {"icon": "view-refresh", "title": "Keyword",
                             "text": "Text with <code>code</code> and a continuation line."}
    assert s["items"][1]["icon"] == "" and s["items"][1]["text"] == "text only"


def test_inline_escapes_html():
    assert helpdoc.inline("a < b **bold**") == "a &lt; b <b>bold</b>"


def test_real_help_file_layout():
    sections = helpdoc.layout(helpdoc.parse(DATA.read_text()))
    titles = [s["title"] for s in sections]
    assert "Sensors" in titles and "Troubleshooting" in titles
    assert all(s["items"] for s in sections)
    wide = [s for s in sections if s["column"] == 2]
    assert len(wide) == 1 and len(wide[0]["items"]) % 2 == 0  # two columns without a gap
    assert {s["column"] for s in sections if not s["wide"]} == {0, 1}
