"""„Zwift starten“: Bridge, Anmeldung, Update, Start, Fenster, Aufräumen.

Abläufe aus den Tests auf tinytin (FEASIBILITY.md, T2b/T3, poc/token-login/start.sh):
- Zwift startet nur als Kind des Launchers; sonst ruft ZwiftApp.exe den Launcher erneut auf.
- NVIDIA auf Hybrid-Notebooks nur über GLX + PRIME-Offload (Grafikschritt legt das fest).
- Zwift maximiert sich nicht von selbst passend zur Plasma-Leiste → KWin-Skript.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Callable

from . import bridgectl, login, paths, setup, state

VER_CUR_URL = "https://cdn.zwift.com/gameassets/Zwift_Updates_Root/Zwift_ver_cur.xml"
RFP_SRC = Path(__file__).resolve().parent.parent / "data" / "RunFromProcess.cs"
UPDATE_TIMEOUT = 15 * 60
KEEP_SNAPSHOTS = 2


class NeedLogin(Exception):
    """Kein gültiges Token mehr: Anmeldung im Browser nötig."""


class LaunchError(Exception):
    """Fehler mit einem Satz für den Nutzer."""


def remote_version(opener=urllib.request.urlopen) -> str:
    req = urllib.request.Request(VER_CUR_URL, headers={"User-Agent": "Tretlager"})
    with opener(req, timeout=20) as r:  # noqa: S310 (feste https-URL)
        text = r.read().decode(errors="ignore")
    m = re.search(r'sversion="([^"]+)"', text)
    return m.group(1) if m else ""


def wine_tasks(env: dict) -> dict[str, int]:
    """Laufende Windows-Prozesse im Prefix: Name → PID."""
    r = subprocess.run(["wine", "tasklist"], capture_output=True, text=True, env=env, timeout=30)
    out = {}
    for line in r.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0].lower().endswith(".exe") and parts[1].isdigit():
            out.setdefault(parts[0], int(parts[1]))
    return out


def snapshot_prefix(log: Callable[[str], None]) -> Path | None:
    """Kopie des Prefix vor einem Update; auf Btrfs per Reflink in Sekundenbruchteilen."""
    if not paths.PREFIX.exists():
        return None
    paths.SNAPSHOTS.mkdir(parents=True, exist_ok=True)
    dest = paths.SNAPSHOTS / datetime.now().strftime("prefix-%Y%m%d-%H%M%S")
    r = subprocess.run(["cp", "-a", "--reflink=auto", str(paths.PREFIX), str(dest)], capture_output=True, text=True)
    if r.returncode != 0:
        log("Schnappschuss fehlgeschlagen: " + r.stderr.strip())
        shutil.rmtree(dest, ignore_errors=True)
        return None
    for old in sorted(paths.SNAPSHOTS.glob("prefix-*"))[:-KEEP_SNAPSHOTS]:
        shutil.rmtree(old, ignore_errors=True)
    return dest


KWIN_SCRIPT = """
for (const w of workspace.windowList()) {
    if ((w.resourceClass || "").toLowerCase() === "zwiftapp.exe") {
        w.setMaximize(true, true);
    }
}
"""


def maximize_window_kde(log: Callable[[str], None]) -> bool:
    """Zwift-Fenster unter KWin maximieren (über der Plasma-Leiste). False außerhalb von KDE."""
    if "KDE" not in os.environ.get("XDG_CURRENT_DESKTOP", "") or not shutil.which("gdbus"):
        return False
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(KWIN_SCRIPT)
        script = f.name
    try:
        name = "tretlager-maximize"
        call = ["gdbus", "call", "--session", "--dest", "org.kde.KWin"]
        subprocess.run(call + ["--object-path", "/Scripting", "--method", "org.kde.kwin.Scripting.unloadScript", name],
                       capture_output=True, timeout=10)
        r = subprocess.run(call + ["--object-path", "/Scripting", "--method", "org.kde.kwin.Scripting.loadScript",
                                   script, name], capture_output=True, text=True, timeout=10)
        sid = r.stdout.strip().strip("(),")
        if not sid.lstrip("-").isdigit() or int(sid) < 0:
            log("KWin-Skript ließ sich nicht laden")
            return False
        subprocess.run(call + ["--object-path", f"/Scripting/Script{sid}", "--method", "org.kde.kwin.Script.run"],
                       capture_output=True, timeout=10)
        subprocess.run(call + ["--object-path", "/Scripting", "--method", "org.kde.kwin.Scripting.unloadScript", name],
                       capture_output=True, timeout=10)
        return True
    finally:
        os.unlink(script)


class Launcher:
    """Führt einen Start durch; progress(text) für die Statuszeile, log(text) fürs Protokoll."""

    def __init__(self, progress: Callable[[str], None], log: Callable[[str], None]):
        self.progress = progress
        self.log = log
        self.ctx = setup.Context(log=log)
        self.env = self.ctx.wine_env

    def run(self) -> None:
        self.progress("Sensor-Bridge prüfen")
        self.ensure_bridge()
        self.progress("Anmeldung prüfen")
        token = login.valid_token()
        if token is None:
            raise NeedLogin()
        self.update_if_needed()
        self.progress("Zwift starten")
        self.start(token)
        self.progress("Fenster anpassen")
        self.wait_and_maximize()
        self.progress("Zwift läuft")

    def ensure_bridge(self) -> None:
        if not bridgectl.unit_installed():
            self.log("Sensor-Bridge nicht installiert, Start ohne Sensoren")
            return
        if not bridgectl.is_running():
            bridgectl.set_running(True)
            self.log("Sensor-Bridge gestartet")

    def update_if_needed(self) -> None:
        local = setup.game_version()
        try:
            remote = remote_version()
        except OSError as e:
            self.log(f"Update-Prüfung nicht möglich: {e}")
            return
        state.update("game", local=local, remote=remote, checked=int(time.time()))
        if not remote or remote == local:
            return
        self.progress(f"Zwift wird aktualisiert ({local} → {remote})")
        snap = snapshot_prefix(self.log)
        if snap:
            self.log(f"Schnappschuss vor dem Update: {snap}")
        self.ctx.wineserver_kill()
        subprocess.Popen(["wine", "start", "/d", r"C:\Program Files (x86)\Zwift", "ZwiftLauncher.exe", "SilentLaunch"],
                         env=self.env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        deadline = time.monotonic() + UPDATE_TIMEOUT
        try:
            while time.monotonic() < deadline:
                time.sleep(5)
                if setup.game_version() == remote:
                    self.log(f"Zwift aktualisiert auf {remote}")
                    time.sleep(10)
                    return
            raise LaunchError("Das Zwift-Update wurde nicht fertig. Der Schnappschuss davor ist erhalten.")
        finally:
            self.ctx.wineserver_kill()

    def run_from_process(self) -> Path:
        work = paths.CACHE / "rfp"
        exe = work / "RunFromProcess.exe"
        if not exe.exists():
            work.mkdir(parents=True, exist_ok=True)
            shutil.copy(RFP_SRC, work / "RunFromProcess.cs")
            self.ctx.run(["wine", setup.CSC, "/nologo", "/target:exe", "/platform:x64", "/out:RunFromProcess.exe",
                          "RunFromProcess.cs"], cwd=work)
            if not exe.exists():
                raise LaunchError("Hilfsprogramm zum Starten ließ sich nicht übersetzen.")
        return exe

    def start(self, token: dict) -> None:
        rfp = self.run_from_process()
        self.ctx.wineserver_kill()
        subprocess.Popen(["wine", "start", "/d", r"C:\Program Files (x86)\Zwift", "ZwiftLauncher.exe", "SilentLaunch"],
                         env=self.env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        pid = None
        for _ in range(30):
            time.sleep(1)
            pid = wine_tasks(self.env).get("ZwiftLauncher.exe")
            if pid:
                break
        if not pid:
            raise LaunchError("Der Zwift-Launcher startet nicht.")
        time.sleep(5)
        gfx = state.load().get("graphics", {})
        env = dict(self.env, **setup.graphics_env(gfx))
        # Token als Argument; es liegt nur im Speicher dieses Prozesses und im Schlüsselbund.
        r = subprocess.run(["wine", str(rfp), str(pid), "ZwiftApp.exe", "--token=" + json.dumps(token)],
                           cwd=paths.ZWIFT_DIR, env=env, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            raise LaunchError("Zwift ließ sich nicht starten: " + (r.stderr or r.stdout).strip()[-200:])
        time.sleep(15)
        for name in ("ZwiftLauncher.exe", "ZwiftWindowsCrashHandler.exe"):
            subprocess.run(["wine", "taskkill", "/f", "/im", name], env=self.env, capture_output=True, timeout=30)

    def wait_and_maximize(self) -> None:
        # Das Skript weiß nicht, ob das Fenster schon da ist; mehrfaches Maximieren schadet nicht.
        for _ in range(3):
            if not maximize_window_kde(self.log):
                return
            time.sleep(4)

    def running(self) -> bool:
        return "ZwiftApp.exe" in wine_tasks(self.env)

    def after_exit(self) -> None:
        """Nach dem Beenden: Reste beenden, Bridge stoppen, wenn sie nicht im Autostart ist."""
        self.ctx.wineserver_kill()
        try:
            if bridgectl.is_running() and not bridgectl.autostart():
                bridgectl.set_running(False)
                self.log("Sensor-Bridge gestoppt")
        except bridgectl.BridgeError as e:
            self.log(str(e))
