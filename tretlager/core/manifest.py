"""Zwift manifest from the CDN: what belongs to a Zwift version and how much of it is still missing.

`Zwift_ver_cur.xml` names the current version and its manifest (`Zwift_<Version>_<Hash>_manifest.xml`,
same directory, ≈ 5 MB). The manifest lists every file with path (backslashes) and size. From it,
the first installation (`setup.Game`) and the update (`launch.Launcher`) compute their progress.
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
    with opener(req, timeout=timeout) as r:  # noqa: S310 (fixed https URL on the Zwift CDN)
        return r.read().decode(errors="ignore")


def _attr(text: str, name: str) -> str:
    m = re.search(rf'{name}="([^"]+)"', text)
    return m.group(1) if m else ""


def remote_version(opener=urllib.request.urlopen) -> str:
    return _attr(_fetch(VER_CUR_URL, opener), "sversion")


def manifest_files(manifest: str) -> list[tuple[str, int]]:
    """Files per the Zwift manifest: (path relative to the Zwift directory, size in bytes)."""
    return [(path.replace("\\", "/"), int(length)) for path, length in
            re.findall(r"<path>([^<]+)</path>\s*<length>(\d+)</length>", manifest)]


def missing_files(files: list[tuple[str, int]], zwift_dir: Path) -> list[tuple[Path, int]]:
    """What the Zwift directory lacks for the new version: files that are missing or differ in size.
    Changed files of the same size go undetected; that is good enough for the display."""
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
    """How much of the missing files is now present at full size."""
    done = 0
    for path, length in missing:
        try:
            if path.stat().st_size == length:
                done += length
        except OSError:
            pass
    return done


def staging_dirs(prefix: Path | None = None) -> list[Path]:
    """Staging directories of the Zwift launcher: it downloads everything to Temp\\Zwift\\Downloads and
    only moves it into the Zwift directory at the end (measured on tinytin, 2026-10-30: 5.1 GB in
    ~9 min, then ~15 s)."""
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
    """Progress of downloading Zwift (first installation and update) from the manifest of the current
    version (cdn.zwift.com): what is in the launcher's staging directory plus what has already
    arrived complete in the Zwift directory."""

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
            pass  # without a manifest, only elapsed time is shown
        # leftovers of an interrupted download do not count
        self.staged_before = dir_bytes(staging_dirs(self.prefix)) if self.total else 0

    def loaded(self) -> int:
        staged = max(dir_bytes(staging_dirs(self.prefix)) - self.staged_before, 0)
        return min(staged + loaded_bytes(self.missing), self.total)

    def percent(self) -> float:
        """0–100, or -1 if unknown."""
        if not self.total:
            return -1
        return min(99.0, 100 * self.loaded() / self.total)
