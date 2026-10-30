#!/usr/bin/env python3
"""Minimaler msgfmt: .po → .mo, nur Standardbibliothek (auf tinytin fehlt gettext).

Unterstützt msgctxt, msgid_plural/msgstr[n] und mehrzeilige Zeichenketten; leere und als
„fuzzy“ markierte Übersetzungen werden ausgelassen (dann gilt der deutsche Text).
    build-aux/msgfmt.py po/en.po tretlager/data/locale/en/LC_MESSAGES/tretlager.mo
"""

import ast
import struct
import sys
from pathlib import Path


def parse(path: Path) -> dict[str, str]:
    entries, cur, key, fuzzy = {}, {}, None, False

    def flush():
        nonlocal cur, fuzzy
        if "msgid" in cur and not fuzzy:
            mid = cur["msgid"]
            if "msgctxt" in cur:
                mid = cur["msgctxt"] + "\x04" + mid
            if "msgid_plural" in cur:
                mid += "\x00" + cur["msgid_plural"]
                strs = [cur[k] for k in sorted(k for k in cur if k.startswith("msgstr["))]
                if all(strs):
                    entries[mid] = "\x00".join(strs)
            elif cur.get("msgstr") or not cur["msgid"]:
                entries[mid] = cur.get("msgstr", "")
        cur, fuzzy = {}, False

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("#,") and "fuzzy" in line:
            if "msgid" in cur:
                flush()
            fuzzy = True
            continue
        if not line or line.startswith("#"):
            # Leerzeile beendet einen Eintrag erst, wenn seine Übersetzung schon gelesen ist
            if not line and "msgid" in cur and any(k.startswith("msgstr") for k in cur):
                flush()
            continue
        if line.startswith('"'):
            cur[key] += ast.literal_eval(line)
            continue
        word, _, rest = line.partition(" ")
        if word in ("msgctxt", "msgid") and "msgid" in cur and ("msgstr" in cur or "msgstr[0]" in cur):
            flush()
        key = word
        cur[key] = ast.literal_eval(rest)
    flush()
    return entries


def write(entries: dict[str, str], out: Path) -> None:
    keys = sorted(entries)
    ids = b"".join(k.encode() + b"\0" for k in keys)
    strs = b"".join(entries[k].encode() + b"\0" for k in keys)
    n = len(keys)
    start = 7 * 4 + 16 * n
    offs, o = [], 0
    for k in keys:
        offs.append((len(k.encode()), start + o)); o += len(k.encode()) + 1
    toffs, o = [], 0
    for k in keys:
        v = entries[k].encode()
        toffs.append((len(v), start + len(ids) + o)); o += len(v) + 1
    data = struct.pack("Iiiiiii", 0x950412de, 0, n, 7 * 4, 7 * 4 + 8 * n, 0, 0)
    data += b"".join(struct.pack("ii", *p) for p in offs)
    data += b"".join(struct.pack("ii", *p) for p in toffs)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data + ids + strs)


if __name__ == "__main__":
    write(parse(Path(sys.argv[1])), Path(sys.argv[2]))
