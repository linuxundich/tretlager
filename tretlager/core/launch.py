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
        src = work / "RunFromProcess.cs"
        # Neu übersetzen, wenn die mitgelieferte Quelle sich geändert hat.
        if not exe.exists() or not src.exists() or src.read_bytes() != RFP_SRC.read_bytes():
            work.mkdir(parents=True, exist_ok=True)
            exe.unlink(missing_ok=True)
            shutil.copy(RFP_SRC, src)
            self.ctx.run(["wine", setup.CSC, "/nologo", "/target:exe", "/platform:x64", "/out:RunFromProcess.exe",
                          "RunFromProcess.cs"], cwd=work)
            if not exe.exists():
                raise LaunchError("Hilfsprogramm zum Starten ließ sich nicht übersetzen.")
        return exe

    def ensure_display_settings(self) -> None:
        """Auflösungswechsel bei jedem Start sperren, auch für Prefixe aus älteren Tretlager-Versionen."""
        reg = r"HKCU\Software\Wine\X11 Driver"
        for value in setup.WINE_DISPLAY_KEYS:
            subprocess.run(["wine", "reg", "add", reg, "/v", value, "/t", "REG_SZ", "/d", "N", "/f"],
                           env=self.env, capture_output=True, timeout=60)

    def start(self, token: dict) -> None:
        rfp = self.run_from_process()
        self.ensure_display_settings()
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
        # Das Token nie in eine Linux-Befehlszeile oder ein Protokoll: Es geht über eine Datei, die nur
        # der Benutzer lesen kann (tmpfs), RunFromProcess setzt es selbst ein; danach wird sie gelöscht.
        tok_file = Path(os.environ.get("XDG_RUNTIME_DIR") or tempfile.gettempdir()) / "tretlager-start.json"
        fd = os.open(tok_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(json.dumps(token))
        try:
            win_path = "Z:" + str(tok_file).replace("/", "\\")
            # Ohne Pipe: Zwift erbt sonst die Ausgabe und hält sie offen (Zeitüberschreitung).
            proc = subprocess.run(["wine", str(rfp), str(pid), "ZwiftApp.exe", "--token=@" + win_path],
                                  cwd=paths.ZWIFT_DIR, env=env, stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL, timeout=60, check=False)
            if proc.returncode != 0:
                raise LaunchError(f"Zwift ließ sich nicht starten (RunFromProcess, Code {proc.returncode}).")
            time.sleep(15)
        except subprocess.TimeoutExpired:
            raise LaunchError("Zwift ließ sich nicht starten (Zeitüberschreitung).") from None
        finally:
            tok_file.unlink(missing_ok=True)
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
