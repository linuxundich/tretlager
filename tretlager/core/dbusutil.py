"""Small D-Bus queries via `gdbus` (system and session bus), without `busctl` and without
extra Python packages – the Flatpak only has gdbus."""

from __future__ import annotations

import re
import subprocess


def _gdbus(bus: str, args: list[str], run=subprocess.run, timeout: int = 5) -> str | None:
    try:
        r = run(["gdbus", "call", f"--{bus}", f"--timeout={timeout}", *args],
                capture_output=True, text=True, timeout=timeout + 5)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def _value(text: str):
    """GVariant value from gdbus output: 'str' / "str", true/false, numbers (with type prefix)."""
    text = text.strip()
    if text in ("true", "false"):
        return text == "true"
    if text[:1] in "'\"" and text[-1:] == text[:1]:
        return text[1:-1].replace("\\'", "'").replace('\\"', '"').replace("\\\\", "\\")
    num = re.sub(r"^(byte|int16|uint16|int32|uint32|int64|uint64|double)\s+", "", text)
    try:
        return int(num)
    except ValueError:
        return text


def get_all(bus: str, dest: str, path: str, interface: str, run=subprocess.run) -> dict | None:
    """All properties of an object as {name: value} (simple values); None on error."""
    out = _gdbus(bus, ["--dest", dest, "--object-path", path, "--method",
                       "org.freedesktop.DBus.Properties.GetAll", interface], run)
    if out is None:
        return None
    return {m.group(1): _value(m.group(2))
            for m in re.finditer(r"'(\w+)': <((?:'[^']*'|\"[^\"]*\"|[^<>,{}\[\]])+)>", out)}


def name_has_owner(bus: str, name: str, run=subprocess.run) -> bool:
    out = _gdbus(bus, ["--dest", "org.freedesktop.DBus", "--object-path", "/org/freedesktop/DBus",
                       "--method", "org.freedesktop.DBus.NameHasOwner", name], run)
    return bool(out) and "true" in out


def activatable(bus: str, name: str, run=subprocess.run) -> bool:
    out = _gdbus(bus, ["--dest", "org.freedesktop.DBus", "--object-path", "/org/freedesktop/DBus",
                       "--method", "org.freedesktop.DBus.ListActivatableNames"], run)
    return bool(out) and f"'{name}'" in out
