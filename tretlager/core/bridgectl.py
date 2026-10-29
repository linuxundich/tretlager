"""Sensor-Bridge aus dem Kern steuern: D-Bus über `busctl --json`, Dienst über `systemctl --user`.

Synchron und ohne zusätzliche Python-Pakete, damit Kirigami- und GTK-Oberfläche es aus Threads
nutzen können.
"""

from __future__ import annotations

import json
import subprocess

from .. import BRIDGE_BUS_NAME, BRIDGE_OBJECT_PATH, BRIDGE_UNIT


class BridgeError(Exception):
    pass


def _busctl(method: str, signature: str = "", *args, timeout: int = 10, run=subprocess.run):
    cmd = ["busctl", "--user", "--json=short", f"--timeout={timeout}", "call", BRIDGE_BUS_NAME,
           BRIDGE_OBJECT_PATH, BRIDGE_BUS_NAME, method]
    if signature:
        cmd += [signature, *[str(a).lower() if isinstance(a, bool) else str(a) for a in args]]
    r = run(cmd, capture_output=True, text=True, timeout=timeout + 5)
    if r.returncode != 0:
        raise BridgeError(r.stderr.strip() or "Bridge antwortet nicht")
    return json.loads(r.stdout)["data"][0]


def status(run=subprocess.run) -> dict | None:
    """Zustand der Bridge; None, wenn sie nicht läuft."""
    try:
        return json.loads(_busctl("GetStatus", run=run))
    except (BridgeError, subprocess.TimeoutExpired, ValueError):
        return None


def scan(seconds: int = 10, run=subprocess.run) -> list[dict]:
    # Ein laufender Verbindungsaufbau kann die BlueZ-Sperre bis zu 40 s halten.
    return json.loads(_busctl("Scan", "u", seconds, timeout=seconds + 60, run=run))


def add_device(address: str, name: str, role: str, run=subprocess.run) -> None:
    _busctl("AddDevice", "sss", address, name, role, run=run)


def remove_device(address: str, run=subprocess.run) -> None:
    _busctl("RemoveDevice", "s", address, run=run)


def set_device_enabled(address: str, enabled: bool, run=subprocess.run) -> None:
    _busctl("SetDeviceEnabled", "sb", address, enabled, run=run)


def _systemctl(*args, run=subprocess.run) -> subprocess.CompletedProcess:
    return run(["systemctl", "--user", *args, BRIDGE_UNIT], capture_output=True, text=True, timeout=30)


def unit_installed(run=subprocess.run) -> bool:
    r = run(["systemctl", "--user", "cat", BRIDGE_UNIT], capture_output=True, text=True, timeout=10)
    return r.returncode == 0


def is_running(run=subprocess.run) -> bool:
    return _systemctl("is-active", "--quiet", run=run).returncode == 0


def set_running(on: bool, run=subprocess.run) -> None:
    r = _systemctl("start" if on else "stop", run=run)
    if r.returncode != 0:
        raise BridgeError(r.stderr.strip() or "systemctl fehlgeschlagen")


def autostart(run=subprocess.run) -> bool:
    return _systemctl("is-enabled", "--quiet", run=run).returncode == 0


def set_autostart(on: bool, run=subprocess.run) -> None:
    r = _systemctl("enable" if on else "disable", run=run)
    if r.returncode != 0:
        raise BridgeError(r.stderr.strip() or "systemctl fehlgeschlagen")
