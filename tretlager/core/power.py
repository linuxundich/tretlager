"""Power supply and NVIDIA errors around a ride.

Finding on tinytin (2026-10-30): Zwift started on AC power, power adapter unplugged or plugged in
during the start – shortly afterwards the NVIDIA driver reported dozens of "Xid 69" (graphics
engine error) for Zwift's process, and Zwift hung. The graphics do not switch to the Intel chip
(PRIME offload stays), and the TCC profile was the same for AC and battery; presumably
nvidia-powerd (Dynamic Boost) changes the power budget when the power source changes while Zwift
is setting up its graphics. Tretlager therefore warns before starting on battery, notices a change
during start and ride, and afterwards reports NVIDIA errors from the kernel journal.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

POWER_SUPPLY = Path("/sys/class/power_supply")
XID_RE = re.compile(r"NVRM: Xid \([^)]*\): (\d+)")


def on_ac(root: Path = POWER_SUPPLY) -> bool | None:
    """True on AC, False on battery, None without a mains entry (e.g. desktop PC)."""
    mains = []
    for dev in root.glob("*"):
        try:
            if (dev / "type").read_text().strip() == "Mains":
                mains.append((dev / "online").read_text().strip() == "1")
        except OSError:
            continue
    if not mains:
        return None
    return any(mains)


def nvidia_xids(since: float, run=subprocess.run) -> list[int]:
    """Xid codes of the NVIDIA driver since `since` (Unix time) from the kernel journal.

    Needs read access to the journal (group systemd-journal or adm, usual for the first user on
    Debian/TUXEDO OS); without access the list is empty.
    """
    try:
        res = run(["journalctl", "-k", "--no-pager", "-o", "cat", "--since", f"@{int(since)}", "-g", "NVRM: Xid"],
                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return []
    return [int(m.group(1)) for m in XID_RE.finditer(res.stdout or "")]


def describe_xids(codes: list[int]) -> str:
    """Short summary for the interface, e.g. "Xid 69 (58×)"."""
    counts: dict[int, int] = {}
    for c in codes:
        counts[c] = counts.get(c, 0) + 1
    return ", ".join(f"Xid {c}" + (f" ({n}×)" if n > 1 else "") for c, n in sorted(counts.items()))


def notify(summary: str, body: str, run=subprocess.run) -> None:
    """Desktop notification (org.freedesktop.Notifications) via gdbus; errors are silent."""
    if not shutil.which("gdbus"):
        return
    try:
        run(["gdbus", "call", "--session", "--dest", "org.freedesktop.Notifications",
             "--object-path", "/org/freedesktop/Notifications",
             "--method", "org.freedesktop.Notifications.Notify",
             "Tretlager", "0", "de.linuxundich.Tretlager", summary, body, "[]",
             "{'urgency': <byte 2>, 'desktop-entry': <'de.linuxundich.Tretlager'>}", "-1"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        pass
