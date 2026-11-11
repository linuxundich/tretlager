"""GNOME: stop the "program is not responding" dialog while Zwift runs.

Mutter asks every window now and then whether its program is alive. Zwift under Wine does not
answer while it loads the world, so GNOME offers to force quit it although nothing is wrong
(`org.gnome.mutter check-alive-timeout`). While Zwift runs, Tretlager sets the timeout to 0
(check off) and puts the old value back afterwards. The old value is kept in the state file, so a
crash cannot leave the setting changed: the next start of Tretlager restores it.
Not in the Flatpak (the sandbox cannot reach the GNOME settings): there, set it yourself with
`gsettings set org.gnome.mutter check-alive-timeout 0`.
"""

from __future__ import annotations

import os
import shutil
import subprocess

from . import bridgectl, state

SCHEMA, KEY = "org.gnome.mutter", "check-alive-timeout"
SECTION = "gnome_alive"


def available() -> bool:
    return ("GNOME" in os.environ.get("XDG_CURRENT_DESKTOP", "").upper() and not bridgectl.IN_FLATPAK
            and bool(shutil.which("gsettings")))


def _gsettings(*args: str) -> str | None:
    try:
        r = subprocess.run(["gsettings", *args], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def parse_value(text: str | None) -> int | None:
    """`uint32 5000` or `5000` → 5000."""
    try:
        return int((text or "").split()[-1])
    except (ValueError, IndexError):
        return None


def disable() -> bool:
    """Switch the alive check off for the ride, remembering the old value. True if it is off now."""
    if not available():
        return False
    saved = state.load().get(SECTION, {}).get("value")
    if saved is None:  # not when a previous run was cut short: that value is the real one
        current = parse_value(_gsettings("get", SCHEMA, KEY))
        if current is None:
            return False
        state.update(SECTION, value=current)
    return _gsettings("set", SCHEMA, KEY, "0") is not None


def restore() -> None:
    """Put the remembered value back (no-op if nothing was changed)."""
    if not available():
        return
    data = state.load()
    value = data.get(SECTION, {}).get("value")
    if value is None:
        return
    if _gsettings("set", SCHEMA, KEY, str(value)) is not None:
        data.pop(SECTION, None)
        state.save(data)
