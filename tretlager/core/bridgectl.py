"""Sensor-Bridge aus dem Kern steuern – über D-Bus mit `gdbus` (gibt es im Flatpak und auf jedem
System mit GLib; `busctl` und `systemctl` fehlen in der Sandbox).

Synchron und ohne zusätzliche Python-Pakete, damit die Oberfläche es aus Threads nutzen kann.

Lebenszyklus: Im Flatpak startet der Sitzungsbus die Bridge per D-Bus-Aktivierung als eigene
Instanz (Dienstdatei `de.linuxundich.Tretlager.Bridge.service`), unabhängig vom Fenster; beendet
wird sie über die Methode `Quit`. *Beim Anmelden starten* läuft über das Background-Portal. Aus
dem Quellbaum (ohne Dienstdatei) startet Tretlager die Bridge als losgelösten Prozess.
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
    """Python-Wert als GVariant-Text für gdbus."""
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
        raise BridgeError(_("gdbus fehlt (Paket libglib2.0-bin bzw. glib2)")) from None
    if r.returncode != 0:
        applog.warning("gdbus %s: %s", args[-1] if args else "", r.stderr.strip())
        raise BridgeError(describe_dbus_error(r.stderr))
    return r.stdout.strip()


def describe_dbus_error(stderr: str) -> str:
    """D-Bus-Fehler von gdbus als Satz für Nutzer; die Rohmeldung steht im Protokoll (applog)."""
    if "org.bluez.Error.NotReady" in stderr or "not powered" in stderr.lower():
        return _("Bluetooth ist ausgeschaltet. Bluetooth einschalten und erneut versuchen.")
    if "org.bluez.Error.InProgress" in stderr:
        return _("Bluetooth ist gerade beschäftigt. In ein paar Sekunden erneut versuchen.")
    if "org.bluez" in stderr and ("NoSuchAdapter" in stderr or "UnknownObject" in stderr):
        return _("Kein Bluetooth-Adapter gefunden. Adapter einstecken bzw. einschalten.")
    if any(k in stderr for k in ("ServiceUnknown", "NameHasNoOwner", "NoReply", "Timeout", "TimedOut")):
        return _("Die Sensor-Bridge antwortet nicht. Sie startet beim nächsten Versuch neu.")
    return _("Die Sensor-Bridge meldet einen Fehler. Details stehen im Protokoll.")


def _call(method: str, *args, timeout: int = 10, run=subprocess.run):
    """Methode der Bridge aufrufen; liefert das erste Rückgabeelement (bei uns ein String/Bool)."""
    out = _gdbus(["--dest", BRIDGE_BUS_NAME, "--object-path", BRIDGE_OBJECT_PATH,
                  "--method", f"{BRIDGE_BUS_NAME}.{method}", *[_gvariant(a) for a in args]], timeout, run)
    if out in ("(true,)", "(false,)"):
        return out == "(true,)"
    try:  # GVariant-Text eines Strings ist ein Python-Literal: ('…',)
        result = ast.literal_eval(out) if out else ()
    except (ValueError, SyntaxError):
        raise BridgeError(_("Unerwartete Antwort der Bridge")) from None
    return result[0] if result else None


def status(run=subprocess.run) -> dict | None:
    """Zustand der Bridge; None, wenn sie nicht läuft (startet sie nicht)."""
    if not is_running(run):
        return None
    try:
        return json.loads(_call("GetStatus", run=run))
    except (BridgeError, subprocess.TimeoutExpired, ValueError, TypeError):
        return None


def scan(seconds: int = 10, run=subprocess.run) -> list[dict]:
    # Ein laufender Verbindungsaufbau kann die BlueZ-Sperre bis zu 40 s halten.
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
    """Bluetooth-Adapter per Adresse wählen; leer = Standardadapter von BlueZ."""
    _call("SetAdapter", address, timeout=60, run=run)


def unit_installed(run=subprocess.run) -> bool:
    """Die Bridge gehört zu Tretlager und ist immer vorhanden (früher: systemd-Dienst des Pakets)."""
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
    try:  # D-Bus-Aktivierung (Flatpak bzw. installierte Dienstdatei)
        _gdbus([*DBUS, "org.freedesktop.DBus.StartServiceByName", _gvariant(BRIDGE_BUS_NAME), "uint32 0"], 30, run)
        return
    except BridgeError:
        if IN_FLATPAK:
            raise
    # Aus dem Quellbaum: losgelöster Prozess, überlebt das Fenster
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[2]))
    popen([sys.executable, "-m", "tretlager.bridge"], env=env, start_new_session=True,
          stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def restart_if_outdated(version: str, run=subprocess.run, sleep=None) -> bool:
    """Läuft noch eine Bridge aus einer älteren Version (nach einem Update), neu starten.
    True, wenn neu gestartet wurde. Nur aufrufen, solange Zwift nicht läuft."""
    import time
    st = status(run)
    if st is None or st.get("version") == version:
        return False
    set_running(False, run)
    for _attempt in range(50):  # Quit trennt die Geräte sauber, das dauert ein paar Sekunden
        if not is_running(run):
            break
        (sleep or time.sleep)(0.2)
    set_running(True, run)
    return True


def autostart(run=subprocess.run) -> bool:
    return bool(state.load().get("bridge", {}).get("autostart"))


def set_autostart(on: bool, run=subprocess.run) -> None:
    """Bridge beim Anmelden starten – über das Background-Portal (legt den Autostart-Eintrag an
    bzw. entfernt ihn). Außerhalb des Flatpaks nur gemerkt."""
    if IN_FLATPAK:
        options = ("{'reason': <%s>, 'autostart': <%s>, 'commandline': <['tretlager-bridge']>, "
                   "'dbus-activatable': <false>}") % (_gvariant(_("Sensoren beim Anmelden bereithalten")),
                                                       "true" if on else "false")
        _gdbus(["--dest", "org.freedesktop.portal.Desktop", "--object-path", "/org/freedesktop/portal/desktop",
                "--method", "org.freedesktop.portal.Background.RequestBackground", "''", options], 30, run)
    state.update("bridge", autostart=on)

