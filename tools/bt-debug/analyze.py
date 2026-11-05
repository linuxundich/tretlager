#!/usr/bin/env python3
"""Merge a bt-debug recording into one timeline and summarise drops and reconnects.

    analyze.py RUNDIR [--since 10m] [--full]

Sources: marks.log, events.jsonl (probe), bridge.log (debug), kernel.log, bluetoothd.log.
Only the standard library; runs on the test computer or after copying the folder.
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

NAMES = {}
HR_GAP = 3.0  # seconds without a heart rate notification that count as a gap


def ts(s: str) -> float:
    s = s.strip()
    if "T" in s:
        return datetime.fromisoformat(s).timestamp()
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").timestamp()


def hm(t: float) -> str:
    return datetime.fromtimestamp(t).strftime("%H:%M:%S")


def name(addr: str) -> str:
    return NAMES.get(addr.upper(), addr)


def load(run: Path):
    ev = []  # (t, source, text, extra)
    for line in (run / "marks.log").read_text().splitlines() if (run / "marks.log").exists() else []:
        t, _, text = line.partition(" ")
        ev.append((ts(t), "MARK", f">>> {text}", None))
    adv_state = {}
    for line in (run / "events.jsonl").read_text().splitlines() if (run / "events.jsonl").exists() else []:
        try:
            e = json.loads(line)
        except ValueError:
            continue
        t, k = e.pop("t"), e.pop("k")
        if k == "bstate":
            NAMES[e["dev"]] = (e.get("name") or e["dev"]).split(":")[0]
            ev.append((t, "bridge", f"{name(e['dev'])}: {e['state']}" + (f" – {e['error']}" if e.get("error") else "")
                       + (" [unstable]" if e.get("unstable") else ""), e))
        elif k == "hr":
            ev.append((t, "hr", "", e))
        elif k == "adv":
            seen = e["n"] > 0
            prev = adv_state.get(e["dev"])
            if prev is None or prev != seen:
                txt = (f"{name(e['dev'])} advertising, RSSI {e['min']}..{e['max']}" if seen
                       else f"{name(e['dev'])} NOT advertising")
                ev.append((t, f"adv@{e['hci']}", txt, e))
            adv_state[e["dev"]] = seen
            ev.append((t, "advraw", "", e))
        elif k == "dev":
            keep = {x: y for x, y in e.items() if x not in ("hci", "dev")}
            if set(keep) == {"RSSI"}:
                ev.append((t, "rssi", "", e))  # advertising heard while the bridge scans
                continue
            ev.append((t, f"bluez@{e['hci']}", f"{name(e['dev'])}: {keep}", e))
        elif k == "disconnected":
            ev.append((t, f"bluez@{e['hci']}", f"{name(e['dev'])}: DISCONNECTED reason={e['reason']} {e.get('message', '')}", e))
        elif k in ("adapter", "adapter-added", "adapter-removed", "observer", "other", "bridge", "probe-error",
                   "dev-added", "dev-removed"):
            ev.append((t, k, json.dumps(e), e))
    hr_notes = {}
    for line in (run / "bridge.log").read_text(errors="replace").splitlines() if (run / "bridge.log").exists() else []:
        m = re.match(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) (\w+) (\S+): (.*)$", line)
        if not m:
            continue
        t, level, logger, msg = ts(m[1]), m[2], m[3], m[4]
        hrm = re.match(r"([0-9A-F:]{17}) 2a37: ", msg)
        if hrm:
            hr_notes.setdefault(hrm[1], []).append(t)
            continue
        if "control point" in msg or level == "DEBUG" or "DIRCON" in msg or "mDNS" in msg:
            continue
        for a, n in NAMES.items():
            msg = msg.replace(a, n)
        ev.append((t, "bridge.log", f"{level} {msg}", None))
    for fname, src in (("kernel.log", "kernel"), ("bluetoothd.log", "bluetoothd")):
        p = run / fname
        for line in p.read_text(errors="replace").splitlines() if p.exists() else []:
            m = re.match(r"^(\S+) \S+ ([^:]+): (.*)$", line)
            if not m or line.startswith("--"):
                continue
            msg = m[3]
            if src == "kernel" and not re.search(r"Bluetooth|hci\d|usb \d", msg):
                continue
            if src == "bluetoothd" and re.search(r"Endpoint (un)?registered|Player (un)?registered", msg):
                continue
            ev.append((ts(m[1]), src, msg, None))
    ev.sort(key=lambda x: x[0])
    return ev, hr_notes


def hr_gaps(notes: list[float]):
    gaps = []
    for a, b in zip(notes, notes[1:]):
        if b - a > HR_GAP:
            gaps.append((a, b))
    return gaps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", type=Path)
    ap.add_argument("--since", help="only the last N minutes, e.g. 10m")
    ap.add_argument("--full", action="store_true", help="also every advertising window")
    args = ap.parse_args()
    ev, hr_notes = load(args.run)
    if not ev:
        sys.exit("empty recording")
    start = ev[0][0]
    if args.since:
        start = ev[-1][0] - float(args.since.rstrip("m")) * 60
    gaps = {a: hr_gaps(n) for a, n in hr_notes.items()}
    for addr, gl in gaps.items():
        for a, b in gl:
            ev.append((a, "hr-gap", f"{name(addr)}: no heart rate {b - a:.0f} s (until {hm(b)})", None))
    ev.sort(key=lambda x: x[0])

    print("== timeline")
    last_txt = {}
    for t, src, txt, extra in ev:
        if t < start or src in ("hr", "rssi") or (src == "advraw" and not args.full):
            continue
        if src == "advraw":
            txt = f"{name(extra['dev'])} n={extra['n']} rssi={extra.get('min')}..{extra.get('max')}"
        key = (src, re.sub(r"\d+", "#", txt))
        if last_txt.get(src) == key and src in ("bridge.log", "bluetoothd", "kernel"):
            continue  # identical repeats
        last_txt[src] = key
        print(f"{hm(t)} {src:13} {txt}")

    print("\n== heart rate")
    for addr, n in hr_notes.items():
        if not n:
            continue
        span = n[-1] - n[0]
        lost = sum(b - a for a, b in gaps[addr])
        print(f"{name(addr)}: notifications {hm(n[0])}–{hm(n[-1])}, {len(n)} received, "
              f"{len(gaps[addr])} gaps > {HR_GAP:.0f} s, {lost:.0f} s without heart rate ({100 * lost / max(span, 1):.1f} %)")
        for a, b in gaps[addr]:
            print(f"   gap {hm(a)}–{hm(b)} {b - a:5.0f} s")

    print("\n== drops (BlueZ) and time until connected again")
    conn = {}
    for t, src, txt, e in ev:
        if not e or not src.startswith("bluez@"):
            continue
        d = e.get("dev")
        if "reason" in e:
            conn[d] = ("down", t, e["reason"])
        elif e.get("Connected") is True and d in conn and conn[d][0] == "down":
            print(f"{name(d)}: down {hm(conn[d][1])} ({conn[d][2]}), back {hm(t)} after {t - conn[d][1]:.0f} s")
            conn[d] = ("up", t, "")
    for d, (st, t, r) in conn.items():
        if st == "down":
            print(f"{name(d)}: down since {hm(t)} ({r}), not back")


if __name__ == "__main__":
    main()
