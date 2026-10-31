"""Control the sensor bridge from the core – over D-Bus with `gdbus` (available in the Flatpak and on
every system with GLib; `busctl` and `systemctl` are missing in the sandbox).

Synchronous and without extra Python packages, so the interface can use it from threads.

Lifecycle: in the Flatpak the session bus starts the bridge via D-Bus activation as a separate
instance (service file `de.linuxundich.Tretlager.Bridge.service`), independent of the window; it is
stopped via the `Quit` method. *Start at login* goes through the Background portal. From the source
tree (no service file) Tretlager starts the bridge as a detached process.
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path

from .. import BRIDGE_BUS_NAME, BRIDGE_OBJECT_PATH
from ..i18n import _
from . import applog, state

IN_FLATPAK = Path("/.flatpak-info").exists()
DBUS = ["--dest", "org.freedesktop.DBus", "--object-path", "/org/freedesktop/DBus", "--method"]


class BridgeError(Exception):
    pass


def _gvariant(value) -> str:
    """Python value as GVariant text for gdbus."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return f"uint32 {value}"
    return "'" + str(value).replace("\\", "\\\\").replace("'", "\\'") + "'"


def _gdbus(args: list[str], timeout: int, run) -> str:
    cmd = ["gdbus", "call", "--session", f"--timeout={timeout}", *args]
    try:
        r = run(cmd, capture_output=True, text=True, timeout=timeout + 5)
    except FileNotFoundError:
        raise BridgeError(_("gdbus is missing (package libglib2.0-bin or glib2)")) from None
    if r.returncode != 0:
        applog.warning("gdbus %s: %s", args[-1] if args else "", r.stderr.strip())
        raise BridgeError(describe_dbus_error(r.stderr))
    return r.stdout.strip()


def describe_dbus_error(stderr: str) -> str:
    """gdbus D-Bus error as a sentence for the user; the raw message goes to the log (applog)."""
    if "org.bluez.Error.NotReady" in stderr or "not powered" in stderr.lower():
        return _("Bluetooth is switched off. Switch on Bluetooth and try again.")
    if "org.bluez.Error.InProgress" in stderr:
        return _("Bluetooth is busy. Try again in a few seconds.")
    if "org.bluez" in stderr and ("NoSuchAdapter" in stderr or "UnknownObject" in stderr):
        return _("No Bluetooth adapter found. Plug in or switch on the adapter.")
    if any(k in stderr for k in ("ServiceUnknown", "NameHasNoOwner", "NoReply", "Timeout", "TimedOut")):
        return _("The sensor bridge is not responding. It restarts on the next attempt.")
    return _("The sensor bridge reported an error. Details are in the log.")


def _call(method: str, *args, timeout: int = 10, run=subprocess.run):
    """Call a bridge method; returns the first return element (a string/bool in our case)."""
    out = _gdbus(["--dest", BRIDGE_BUS_NAME, "--object-path", BRIDGE_OBJECT_PATH,
                  "--method", f"{BRIDGE_BUS_NAME}.{method}", *[_gvariant(a) for a in args]], timeout, run)
    if out in ("(true,)", "(false,)"):
        return out == "(true,)"
    try:  # GVariant text of a string is a Python literal: ('…',)
        result = ast.literal_eval(out) if out else ()
    except (ValueError, SyntaxError):
        raise BridgeError(_("Unexpected response from the bridge")) from None
    return result[0] if result else None


def status(run=subprocess.run) -> dict | None:
    """Bridge status; None if it is not running (does not start it)."""
    if not is_running(run):
        return None
    try:
        return json.loads(_call("GetStatus", run=run))
    except (BridgeError, subprocess.TimeoutExpired, ValueError, TypeError):
        return None


def scan(seconds: int = 10, run=subprocess.run) -> list[dict]:
    # A connection attempt in progress can hold the BlueZ lock for up to 40 s.
    return json.loads(_call("Scan", seconds, timeout=seconds + 60, run=run))


def add_device(address: str, name: str, role: str, run=subprocess.run) -> None:
    _call("AddDevice", address, name, role, run=run)


def remove_device(address: str, run=subprocess.run) -> None:
    _call("RemoveDevice", address, run=run)


def set_device_enabled(address: str, enabled: bool, run=subprocess.run) -> None:
    _call("SetDeviceEnabled", address, enabled, run=run)


def set_local_only(local_only: bool, run=subprocess.run) -> None:
    _call("SetLocalOnly", local_only, run=run)


def set_adapter(address: str, run=subprocess.run) -> None:
    """Select the Bluetooth adapter by address; empty = BlueZ default adapter."""
    _call("SetAdapter", address, timeout=60, run=run)


def unit_installed(run=subprocess.run) -> bool:
    """The bridge is part of Tretlager and always present (formerly: the package's systemd service)."""
    return True


def is_running(run=subprocess.run) -> bool:
    try:
        out = _gdbus([*DBUS, "org.freedesktop.DBus.NameHasOwner", _gvariant(BRIDGE_BUS_NAME)], 5, run)
    except (BridgeError, subprocess.TimeoutExpired):
        return False
    return "true" in out


def set_running(on: bool, run=subprocess.run, popen=subprocess.Popen) -> None:
    if not on:
        if is_running(run):
            _call("Quit", run=run)
        return
    if is_running(run):
        return
    try:  # D-Bus activation (Flatpak or installed service file)
        _gdbus([*DBUS, "org.freedesktop.DBus.StartServiceByName", _gvariant(BRIDGE_BUS_NAME), "uint32 0"], 30, run)
        return
    except BridgeError:
        if IN_FLATPAK:
            raise
    # From the source tree: detached process, outlives the window
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[2]))
    popen([sys.executable, "-m", "tretlager.bridge"], env=env, start_new_session=True,
          stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def restart_if_outdated(version: str, run=subprocess.run, sleep=None) -> bool:
    """Restart the bridge if one from an older version is still running (after an update).
    True if it was restarted. Only call while Zwift is not running."""
    import time
    st = status(run)
    if st is None or st.get("version") == version:
        return False
    set_running(False, run)
    for _attempt in range(50):  # Quit disconnects the devices cleanly; that takes a few seconds
        if not is_running(run):
            break
        (sleep or time.sleep)(0.2)
    set_running(True, run)
    return True


def autostart(run=subprocess.run) -> bool:
    return bool(state.load().get("bridge", {}).get("autostart"))


def set_autostart(on: bool, run=subprocess.run) -> None:
    """Start the bridge at login – via the Background portal (creates or removes the autostart
    entry). Outside the Flatpak it is only remembered."""
    if IN_FLATPAK:
        options = ("{'reason': <%s>, 'autostart': <%s>, 'commandline': <['tretlager-bridge']>, "
                   "'dbus-activatable': <false>}") % (_gvariant(_("Keep sensors ready at login")),
                                                       "true" if on else "false")
        _gdbus(["--dest", "org.freedesktop.portal.Desktop", "--object-path", "/org/freedesktop/portal/desktop",
                "--method", "org.freedesktop.portal.Background.RequestBackground", "''", options], 30, run)
    state.update("bridge", autostart=on)

