"""Welches Wine Zwift startet: das mitgelieferte oder die vorige, bewährte Version (docs/updates.md).

Tretlager behält genau eine Kopie von Wine im Datenordner: die zuletzt bewährte Version. Bringt ein
Tretlager-Update ein neues Wine, bleibt die Kopie der alten Version stehen; macht das neue Wine
Probleme, lässt sich Zwift mit der Kopie starten. Hat das neue Wine zwei Fahrten geschafft, ersetzt
es die Kopie. Eine Kopie kostet gut 500 MB und ist in einer Sekunde angelegt.

Nur im Flatpak: Außerhalb bringt Tretlager kein eigenes Wine mit.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path

from . import paths, state

BUNDLED = Path("/app/wine")
KEPT = paths.DATA / "wine-bewaehrt"
VERSION_FILE = "tretlager-wine-version"
GOOD_RIDES = 2  # so viele Fahrten, bis ein neues Wine als bewährt gilt
GOOD_RIDE_SECONDS = 5 * 60


def _version(bin_dir: Path) -> str:
    try:
        return subprocess.run([str(bin_dir / "wine"), "--version"], capture_output=True, text=True,
                              timeout=10).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def available() -> bool:
    return (BUNDLED / "bin" / "wine").exists()


@lru_cache(maxsize=1)  # /app ändert sich nicht, solange Tretlager läuft
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
    """Startet Zwift gerade mit der vorigen Version? Nur, wenn sie da ist und sich unterscheidet."""
    info = _info()
    kept = kept_version()
    return bool(info.get("use_kept")) and bool(kept) and kept != bundled_version()


def bin_dir() -> Path | None:
    """Ordner des Wine, mit dem Tretlager arbeitet; None = `wine` aus PATH (außerhalb des Flatpaks)."""
    if use_kept():
        return KEPT / "bin"
    return BUNDLED / "bin" if available() else None


def env_path(base: str | None = None) -> str:
    """PATH mit dem gewählten Wine vorn."""
    base = base if base is not None else os.environ.get("PATH", "/usr/bin")
    b = bin_dir()
    return f"{b}:{base}" if b else base


def set_use_kept(on: bool) -> None:
    state.update("wine", use_kept=on, for_bundled=bundled_version())


def check_after_update() -> bool:
    """Nach einem Tretlager-Update mit wieder neuem Wine die Wahl „vorige Version“ zurücksetzen:
    Das neue Wine kann das Problem behoben haben. True, wenn zurückgesetzt wurde."""
    info = _info()
    if info.get("use_kept") and info.get("for_bundled") != bundled_version():
        state.update("wine", use_kept=False)
        return True
    return False


def _copy_bundled() -> None:
    tmp = KEPT.with_name(KEPT.name + ".neu")
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.copytree(BUNDLED, tmp, symlinks=True)
    (tmp / VERSION_FILE).write_text(bundled_version() + "\n")
    shutil.rmtree(KEPT, ignore_errors=True)
    tmp.rename(KEPT)


def record_ride(seconds: float) -> str:
    """Nach einer Fahrt: Bewährt sich das mitgelieferte Wine, wird es zur aufbewahrten Kopie.
    Liefert eine Zeile fürs Protokoll oder ""."""
    if not available() or use_kept() or seconds < GOOD_RIDE_SECONDS:
        return ""
    bundled = bundled_version()
    if kept_version() == bundled:
        return ""
    info = _info()
    rides = (info.get("rides", 0) if info.get("rides_for") == bundled else 0) + 1
    state.update("wine", rides=rides, rides_for=bundled)
    # Erste Kopie überhaupt sofort (sonst gäbe es beim ersten Update nichts zum Zurückgehen),
    # eine vorhandene ältere erst, wenn sich die neue Version bewährt hat.
    if kept_version() and rides < GOOD_RIDES:
        return ""
    _copy_bundled()
    return bundled
