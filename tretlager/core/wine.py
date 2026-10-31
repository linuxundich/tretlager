"""Which Wine starts Zwift: the bundled one or the previous, proven version (docs/updates.md).

Tretlager keeps exactly one copy of Wine in the data directory: the last proven version. If a
Tretlager update brings a new Wine, the copy of the old version stays; if the new Wine causes
problems, Zwift can be started with the copy. Once the new Wine has managed two rides, it replaces
the copy. A copy takes a good 500 MB and is created in a second.

Flatpak only: outside it, Tretlager does not bring its own Wine.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path

from . import paths, state

BUNDLED = Path("/app/wine")
KEPT = paths.DATA / "wine-kept"
_OLD_KEPT = paths.DATA / "wine-bewaehrt"  # name up to 0.9.x
VERSION_FILE = "tretlager-wine-version"
GOOD_RIDES = 2  # number of rides until a new Wine counts as proven
GOOD_RIDE_SECONDS = 5 * 60


def _version(bin_dir: Path) -> str:
    try:
        return subprocess.run([str(bin_dir / "wine"), "--version"], capture_output=True, text=True,
                              timeout=10).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def _adopt_old_copy() -> None:
    """Keep the proven Wine copy of installations from before the directory was renamed."""
    try:
        if _OLD_KEPT.is_dir() and not KEPT.exists():
            _OLD_KEPT.rename(KEPT)
    except OSError:
        pass


_adopt_old_copy()


def available() -> bool:
    return (BUNDLED / "bin" / "wine").exists()


@lru_cache(maxsize=1)  # /app does not change while Tretlager is running
def bundled_version() -> str:
    return _version(BUNDLED / "bin") if available() else ""


def kept_version() -> str:
    try:
        return (KEPT / VERSION_FILE).read_text().strip()
    except OSError:
        return ""


def _info() -> dict:
    return state.load().get("wine", {})


def use_kept() -> bool:
    """Is Zwift currently started with the previous version? Only if it exists and differs."""
    info = _info()
    kept = kept_version()
    return bool(info.get("use_kept")) and bool(kept) and kept != bundled_version()


def bin_dir() -> Path | None:
    """Directory of the Wine Tretlager works with; None = `wine` from PATH (outside the Flatpak)."""
    if use_kept():
        return KEPT / "bin"
    return BUNDLED / "bin" if available() else None


def env_path(base: str | None = None) -> str:
    """PATH with the selected Wine first."""
    base = base if base is not None else os.environ.get("PATH", "/usr/bin")
    b = bin_dir()
    return f"{b}:{base}" if b else base


def set_use_kept(on: bool) -> None:
    state.update("wine", use_kept=on, for_bundled=bundled_version())


def check_after_update() -> bool:
    """After a Tretlager update with yet another new Wine, reset the "previous version" choice:
    the new Wine may have fixed the problem. True if it was reset."""
    info = _info()
    if info.get("use_kept") and info.get("for_bundled") != bundled_version():
        state.update("wine", use_kept=False)
        return True
    return False


def _copy_bundled() -> None:
    tmp = KEPT.with_name(KEPT.name + ".new")
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.copytree(BUNDLED, tmp, symlinks=True)
    (tmp / VERSION_FILE).write_text(bundled_version() + "\n")
    shutil.rmtree(KEPT, ignore_errors=True)
    tmp.rename(KEPT)


def record_ride(seconds: float) -> str:
    """After a ride: once the bundled Wine has proven itself, it becomes the kept copy.
    Returns a line for the log or ""."""
    if not available() or use_kept() or seconds < GOOD_RIDE_SECONDS:
        return ""
    bundled = bundled_version()
    if kept_version() == bundled:
        return ""
    info = _info()
    rides = (info.get("rides", 0) if info.get("rides_for") == bundled else 0) + 1
    state.update("wine", rides=rides, rides_for=bundled)
    # The very first copy right away (otherwise there would be nothing to go back to at the first
    # update); an existing older one only once the new version has proven itself.
    if kept_version() and rides < GOOD_RIDES:
        return ""
    _copy_bundled()
    return bundled
