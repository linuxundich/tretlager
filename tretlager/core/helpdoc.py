"""Split the help from `data/hilfe.md` into sections and entries.

The help page shows no running text but one card with entries (keyword and sentence) per
section, like the other pages. File format:

    ## Title
    <!-- icon: iconname; wide -->         optional; wide = full width, entries in two columns
    Introductory paragraph                optional
    - [icon] **Keyword**: text            icon optional; continuation lines indented

Emphasis (**bold**, *italic*, `code`) becomes simple rich text for Qt labels.
"""

from __future__ import annotations

import html
import math
import re

ITEM_RE = re.compile(r"^-\s+(?:\[(?P<icon>[\w.-]+)\]\s+)?\*\*(?P<title>.+?)\*\*:?\s*(?P<text>.*)$")
META_RE = re.compile(r"^<!--\s*(?P<meta>.*?)\s*-->$")


def inline(text: str) -> str:
    """Turn Markdown emphasis into rich text, escape everything else."""
    out = html.escape(text, quote=False)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", out)
    out = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", out)
    return out


def parse(text: str) -> list[dict]:
    sections: list[dict] = []
    current: dict | None = None
    para: list[str] = []
    item: dict | None = None

    def flush_para():
        if current is not None and para:
            current["intro"].append(" ".join(para))
        para.clear()

    for raw in text.splitlines():
        line = raw.strip()
        if raw.startswith("## "):
            flush_para()
            item = None
            current = {"title": raw[3:].strip(), "icon": "", "wide": False, "intro": [], "items": []}
            sections.append(current)
            continue
        if current is None:
            continue
        m = META_RE.match(line)
        if m:
            for part in (p.strip() for p in m.group("meta").split(";")):
                if part.startswith("icon:"):
                    current["icon"] = part[5:].strip()
                elif part == "wide":
                    current["wide"] = True
            continue
        m = ITEM_RE.match(line)
        if m:
            flush_para()
            item = {"icon": m.group("icon") or "", "title": m.group("title"), "text": m.group("text")}
            current["items"].append(item)
            continue
        if not line:
            flush_para()
            item = None
            continue
        if item is not None and raw.startswith("  "):
            item["text"] = (item["text"] + " " + line).strip()
        else:
            para.append(line)
    flush_para()

    for s in sections:
        s["intro"] = [inline(p) for p in s["intro"]]
        for it in s["items"]:
            it["title"] = inline(it["title"])
            it["text"] = inline(it["text"])
    return sections


def layout(sections: list[dict]) -> list[dict]:
    """Assign a column to each section: 0 left, 1 right, 2 at the bottom across the full width.

    In order, into whichever column is shorter, estimated from entries and text length, so both
    columns end up about the same length and the reading order is preserved.
    """
    heights = [0.0, 0.0]
    out = []
    for s in sections:
        if s["wide"]:
            out.append(dict(s, column=2))
            continue
        # In line heights: header about 2; entry = padding and title (about 2.2) plus text lines of
        # roughly 65 characters. Measured on tinytin: short path 68 px, three text lines 110 px.
        def lines(t: str) -> int:
            return math.ceil(len(re.sub("<[^>]+>", "", t)) / 65)
        weight = 2 + sum(lines(p) + 0.8 for p in s["intro"]) + sum(2.2 + lines(it["text"]) for it in s["items"])
        col = 0 if heights[0] <= heights[1] else 1
        heights[col] += weight
        out.append(dict(s, column=col))
    return out
