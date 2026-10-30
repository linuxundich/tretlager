#!/usr/bin/env python3
"""Python-Pakete der Bridge für das Flatpak festschreiben: lädt passende Wheels (CPython 3.13,
manylinux x86_64 – die Python-Version der KDE-Laufzeit 6.11) und schreibt python-deps.json mit
festen URLs und Prüfsummen. Der Bau läuft damit ohne Netz.
    build-aux/flatpak/gen-python-deps.py
"""

import hashlib
import json
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

REQUIREMENTS = ["bleak", "dbus-fast", "secretstorage"]
HERE = Path(__file__).resolve().parent

with tempfile.TemporaryDirectory() as tmp:
    subprocess.run([sys.executable, "-m", "pip", "download", "--quiet", "--dest", tmp, "--only-binary=:all:",
                    "--python-version", "3.13", "--implementation", "cp", "--abi", "cp313", "--abi", "abi3",
                    "--abi", "none", "--platform", "manylinux_2_28_x86_64", "--platform", "manylinux_2_17_x86_64",
                    "--platform", "manylinux2014_x86_64", "--platform", "any", *REQUIREMENTS], check=True)
    sources, names = [], []
    for wheel in sorted(Path(tmp).glob("*.whl")):
        name, version = wheel.name.split("-")[:2]
        sha = hashlib.sha256(wheel.read_bytes()).hexdigest()
        with urllib.request.urlopen(f"https://pypi.org/pypi/{name}/{version}/json", timeout=30) as r:
            urls = [u for u in json.load(r)["urls"] if u["filename"] == wheel.name]
        if not urls or urls[0]["digests"]["sha256"] != sha:
            sys.exit(f"{wheel.name}: nicht auf PyPI gefunden oder Prüfsumme weicht ab")
        sources.append({"type": "file", "url": urls[0]["url"], "sha256": sha})
        names.append(name)
        print(wheel.name)

module = {
    "name": "python-deps",
    "buildsystem": "simple",
    "build-commands": ["pip3 install --no-index --no-build-isolation --find-links=. --prefix=${FLATPAK_DEST} "
                       + " ".join(REQUIREMENTS)],
    "sources": sources,
}
(HERE / "python-deps.json").write_text(json.dumps(module, indent=2) + "\n")
print(f"→ {HERE / 'python-deps.json'} ({len(sources)} Wheels)")
