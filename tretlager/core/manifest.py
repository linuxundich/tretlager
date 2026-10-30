"""Zwift-Manifest vom CDN: was zu einer Zwift-Version gehört und wie viel davon noch fehlt.

`Zwift_ver_cur.xml` nennt die aktuelle Version und ihr Manifest (`Zwift_<Version>_<Hash>_manifest.xml`,
gleicher Ordner, ≈ 5 MB). Das Manifest führt jede Datei mit Pfad (Backslash) und Größe. Daraus
berechnen Erstinstallation (`setup.Game`) und Update (`launch.Launcher`) ihren Fortschritt.
"""

from __future__ import annotations

import os
import re
import urllib.request
from pathlib import Path

from . import paths

VER_CUR_URL = "https://cdn.zwift.com/gameassets/Zwift_Updates_Root/Zwift_ver_cur.xml"
MANIFEST_BASE = "https://cdn.zwift.com/gameassets/Zwift_Updates_Root/"


def _fetch(url: str, opener=urllib.request.urlopen, timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Tretlager"})
    with opener(req, timeout=timeout) as r:  # noqa: S310 (feste https-URL beim Zwift-CDN)
        return r.read().decode(errors="ignore")


def _attr(text: str, name: str) -> str:
    m = re.search(rf'{name}="([^"]+)"', text)
    return m.group(1) if m else ""


def remote_version(opener=urllib.request.urlopen) -> str:
    return _attr(_fetch(VER_CUR_URL, opener), "sversion")


def manifest_files(manifest: str) -> list[tuple[str, int]]:
    """Dateien laut Zwift-Manifest: (Pfad relativ zum Zwift-Ordner, Größe in Byte)."""
    return [(path.replace("\\", "/"), int(length)) for path, length in
            re.findall(r"<path>([^<]+)</path>\s*<length>(\d+)</length>", manifest)]


def missing_files(files: list[tuple[str, int]], zwift_dir: Path) -> list[tuple[Path, int]]:
    """Was dem Zwift-Ordner zur neuen Version fehlt: Dateien, die fehlen oder anders groß sind.
    Gleich große, aber geänderte Dateien bleiben unerkannt; für die Anzeige genügt das."""
    out = []
    for rel, length in files:
        path = zwift_dir / rel
        try:
            if path.stat().st_size == length:
                continue
        except OSError:
            pass
        out.append((path, length))
    return out


def loaded_bytes(missing: list[tuple[Path, int]]) -> int:
    """Wie viel der fehlenden Dateien inzwischen in voller Größe da ist."""
    done = 0
    for path, length in missing:
        try:
            if path.stat().st_size == length:
                done += length
        except OSError:
            pass
    return done


def staging_dirs(prefix: Path | None = None) -> list[Path]:
    """Zwischenordner des Zwift-Launchers: Er lädt alles nach Temp\\Zwift\\Downloads und verschiebt es
    erst am Ende in den Zwift-Ordner (gemessen auf tinytin, 30.10.: 5,1 GB in ~9 min, dann ~15 s)."""
    return sorted((prefix or paths.PREFIX).glob("drive_c/users/*/AppData/Local/Temp/Zwift/Downloads"))


def dir_bytes(dirs: list[Path]) -> int:
    total = 0
    for d in dirs:
        for root, _dirs, files in os.walk(d):
            for f in files:
                try:
                    total += os.lstat(os.path.join(root, f)).st_size
                except OSError:
                    pass
    return total


class UpdateProgress:
    """Fortschritt beim Laden von Zwift (Erstinstallation und Update) aus dem Manifest der aktuellen
    Version (cdn.zwift.com): was im Zwischenordner des Launchers liegt plus was schon fertig im
    Zwift-Ordner angekommen ist."""

    def __init__(self, opener=urllib.request.urlopen, zwift_dir: Path | None = None,
                 prefix: Path | None = None):
        self.missing: list[tuple[Path, int]] = []
        self.total = 0
        self.prefix = prefix
        self.staged_before = 0
        try:
            name = _attr(_fetch(VER_CUR_URL, opener), "manifest")
            if name and re.fullmatch(r"[\w.\-]+\.xml", name):
                manifest = _fetch(MANIFEST_BASE + name, opener, timeout=60)
                self.missing = missing_files(manifest_files(manifest), zwift_dir or paths.ZWIFT_DIR)
                self.total = sum(length for _p, length in self.missing)
        except (OSError, ValueError):
            pass  # ohne Manifest bleibt es bei der Zeitanzeige
        # Reste eines abgebrochenen Ladens zählen nicht mit
        self.staged_before = dir_bytes(staging_dirs(self.prefix)) if self.total else 0

    def loaded(self) -> int:
        staged = max(dir_bytes(staging_dirs(self.prefix)) - self.staged_before, 0)
        return min(staged + loaded_bytes(self.missing), self.total)

    def percent(self) -> float:
        """0–100, oder -1, wenn unbekannt."""
        if not self.total:
            return -1
        return min(99.0, 100 * self.loaded() / self.total)
