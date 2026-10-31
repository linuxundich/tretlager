"""Step "Prepare the system": WineHQ source and packages.

Planning without root: APT works through the installation in a temp directory (WineHQ list
downloaded there, system lists only linked). This way the user sees the exact package list before
the single password prompt. The fixed helper `setup-system` does the work via pkexec.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable
from ..i18n import _

WINEHQ_FPR = "D43F640145369C51D786DDEA76F1A20FF987672F"
WINEHQ_URI = "https://dl.winehq.org/wine-builds/debian"
WINEHQ_SUITE = "forky"
# What Tretlager needs; cabextract for winetricks, osslsigncode for the signature check.
PACKAGES = ["winehq-devel", "cabextract", "osslsigncode"]

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
KEY_PATH = DATA_DIR / "winehq.key"
HELPER = "/usr/libexec/tretlager/setup-system"
SYSTEM_SOURCES = Path("/etc/apt/sources.list.d")
SYSTEM_LISTS = Path("/var/lib/apt/lists")


def sources_text(key_path: str | Path) -> str:
    return (f"Types: deb\nURIs: {WINEHQ_URI}\nSuites: {WINEHQ_SUITE}\nComponents: main\n"
            f"Architectures: amd64\nSigned-By: {key_path}\n")


def winehq_source_present(sources_dir: Path = SYSTEM_SOURCES) -> bool:
    return any(sources_dir.glob("winehq-*.sources")) or any(
        WINEHQ_URI in p.read_text(errors="ignore") for p in sources_dir.glob("*") if p.is_file())


@dataclass
class Package:
    name: str
    version: str
    origin: str
    size: int = 0  # download in bytes


@dataclass
class Plan:
    add_source: bool
    packages: list[Package] = field(default_factory=list)
    error: str = ""
    removals: list[str] = field(default_factory=list)  # anything APT would have to remove is listed here

    @property
    def nothing_to_do(self) -> bool:
        return not self.add_source and not self.packages and not self.error

    @property
    def download_bytes(self) -> int:
        return sum(p.size for p in self.packages)

    def to_dict(self) -> dict:
        return {"add_source": self.add_source, "nothing_to_do": self.nothing_to_do, "error": self.error,
                "download_bytes": self.download_bytes, "fingerprint": WINEHQ_FPR, "uri": WINEHQ_URI,
                "packages": [p.__dict__ for p in self.packages], "removals": self.removals}


INST_RE = re.compile(r"^Inst (\S+) (?:\[\S+\] )?\((\S+) (.+?) \[")
REMV_RE = re.compile(r"^Remv (\S+)")


def parse_removals(output: str) -> list[str]:
    return [m.group(1) for line in output.splitlines() if (m := REMV_RE.match(line))]


def parse_simulation(output: str) -> list[Package]:
    """Parse `apt-get -s install`: "Inst wine-devel (11.20~forky-1 winehq:testing [amd64])"."""
    out = []
    for line in output.splitlines():
        m = INST_RE.match(line)
        if m:
            out.append(Package(m.group(1), m.group(2), m.group(3)))
    return out


def parse_sizes(apt_cache_show: str) -> dict[str, int]:
    sizes, name = {}, None
    for line in apt_cache_show.splitlines():
        if line.startswith("Package: "):
            name = line.split(": ", 1)[1].strip()
        elif line.startswith("Size: ") and name and name not in sizes:
            sizes[name] = int(line.split(": ", 1)[1])
    return sizes


def _apt_opts(tmp: Path, sourceparts: Path) -> list[str]:
    return ["-o", f"Dir::State::lists={tmp}/lists", "-o", f"Dir::Cache={tmp}/cache",
            "-o", "Dir::Etc::sourcelist=/dev/null", "-o", f"Dir::Etc::sourceparts={sourceparts}",
            "-o", "Debug::NoLocking=1", "-o", "APT::Get::List-Cleanup=0"]


def _run(cmd: list[str], timeout: int = 180) -> subprocess.CompletedProcess:
    env = dict(os.environ, LC_ALL="C.UTF-8", LANG="C.UTF-8")
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)


def plan(packages: list[str] | None = None, force_temp_source: bool = False) -> Plan:
    packages = packages or PACKAGES
    add_source = force_temp_source or not winehq_source_present()
    with tempfile.TemporaryDirectory(prefix="tretlager-apt-") as d:
        tmp = Path(d)
        for sub in ("lists/partial", "cache/archives/partial", "wine-only", "all"):
            (tmp / sub).mkdir(parents=True)
        if add_source:
            key = tmp / "winehq.key"
            key.write_bytes(KEY_PATH.read_bytes())
            text = sources_text(key)
            (tmp / "wine-only" / "winehq.sources").write_text(text)
            (tmp / "all" / "winehq.sources").write_text(text)
            r = _run(["apt-get", "-q", *_apt_opts(tmp, tmp / "wine-only"), "update"])
            if r.returncode != 0:
                return Plan(add_source, error=_("Could not load the WineHQ package list: {error}").format(error=r.stderr.strip()[-300:] or r.stdout[-300:]))
        # Add system sources and lists, only linked.
        for src in SYSTEM_SOURCES.glob("*"):
            if src.suffix not in (".sources", ".list") or (tmp / "all" / src.name).exists():
                continue
            if add_source and WINEHQ_URI in src.read_text(errors="ignore"):
                continue  # otherwise two Signed-By for the same source
            (tmp / "all" / src.name).symlink_to(src)
        for lst in SYSTEM_LISTS.iterdir():
            if lst.is_file() and lst.name != "lock" and not (tmp / "lists" / lst.name).exists():
                (tmp / "lists" / lst.name).symlink_to(lst)
        opts = _apt_opts(tmp, tmp / "all")
        r = _run(["apt-get", "-s", *opts, "install", "--install-recommends", *packages])
        if r.returncode != 0:
            return Plan(add_source, error=_("Package planning failed: {error}").format(error=r.stderr.strip()[-300:]))
        result = parse_simulation(r.stdout)
        if result:
            show = _run(["apt-cache", *opts, "show", "--no-all-versions", *[p.name for p in result]])
            sizes = parse_sizes(show.stdout)
            for p in result:
                p.size = sizes.get(p.name, 0)
        return Plan(add_source, result, removals=parse_removals(r.stdout))


def run_helper(on_event: Callable[[dict], None], cmd: list[str] | None = None) -> int:
    """Start the helper via pkexec and pass on its JSON lines. Returns the exit code."""
    cmd = cmd or ["pkexec", HELPER, "install"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    assert proc.stdout
    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue
        try:
            on_event(json.loads(line))
        except json.JSONDecodeError:
            on_event({"event": "log", "text": line})
    rc = proc.wait()
    if rc in (126, 127):  # pkexec: refused or not authorised
        on_event({"event": "error", "text": _("Cancelled or permission not granted")})
    return rc
