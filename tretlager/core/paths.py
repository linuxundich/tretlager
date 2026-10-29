"""Orte, an denen Tretlager Daten ablegt (XDG)."""

from __future__ import annotations

import os
from pathlib import Path


def _xdg(var: str, default: str) -> Path:
    return Path(os.environ.get(var) or Path.home() / default)


DATA = _xdg("XDG_DATA_HOME", ".local/share") / "tretlager"
STATE = _xdg("XDG_STATE_HOME", ".local/state") / "tretlager"
CACHE = _xdg("XDG_CACHE_HOME", ".cache") / "tretlager"

PREFIX = DATA / "prefix"
SNAPSHOTS = DATA / "snapshots"
ZWIFT_DIR = PREFIX / "drive_c" / "Program Files (x86)" / "Zwift"

# Ablagebedarf laut Messung auf tinytin: 1,8 GB System (Wine) + 8,6 GB Prefix mit Spiel.
REQUIRED_BYTES = 11 * 10**9
RECOMMENDED_BYTES = 15 * 10**9
