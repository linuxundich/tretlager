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
from pathlib import Path
from typing import Callable

from . import bridgectl, display, login, paths, setup, state
from ..i18n import _

VER_CUR_URL = "https://cdn.zwift.com/gameassets/Zwift_Updates_Root/Zwift_ver_cur.xml"
RFP_SRC = Path(__file__).resolve().parent.parent / "data" / "RunFromProcess.cs"
UPDATE_TIMEOUT = 15 * 60


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


def process_running(name: str, proc: Path = Path("/proc")) -> bool:
    """Läuft ein Windows-Programm dieses Namens? Billiger und robuster als `wine tasklist`, das
    alle paar Sekunden ein Wine-Programm starten müsste und bei hängendem wineserver blockiert.

    Maßgeblich ist argv[0]: Wine setzt dort den Windows-Pfad (`C:\\…\\ZwiftApp.exe`). Der
    Prozessname (comm) taugt nicht – Zwift benennt seinen Hauptthread „main“, und comm ist auf
    15 Zeichen gekürzt (gemessen auf tinytin, 30.10.). Gelesen wird nur bis zum ersten Nullbyte:
    Die weiteren Argumente enthalten das Zwift-Token.
    """
    want = name.lower()
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            with open(entry / "cmdline", "rb") as f:
                argv0 = f.read(4096).split(b"\0", 1)[0].decode(errors="replace")
        except OSError:
            continue  # Prozess inzwischen beendet
        if re.split(r"[\\/]", argv0)[-1].lower() == want:
            return True
    return False


KWIN_SCRIPT = """
for (const w of workspace.windowList()) {
    if ((w.resourceClass || "").toLowerCase() === "zwiftapp.exe") {
        w.setMaximize(true, true);
    }
}
"""


def _host_visible_tmpdir() -> str | None:
    """Ordner für Dateien, die KWin lesen muss. Im Flatpak ist /tmp privat; $XDG_RUNTIME_DIR/app/<ID>
    sieht der Rechner unter demselben Pfad. Sonst das normale Temp-Verzeichnis (None)."""
    app_id = os.environ.get("FLATPAK_ID")
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    if app_id and runtime:
        path = Path(runtime) / "app" / app_id
        path.mkdir(parents=True, exist_ok=True)
        return str(path)
    return None


def maximize_window_kde(log: Callable[[str], None]) -> bool:
    """Zwift-Fenster unter KWin maximieren (über der Plasma-Leiste). False außerhalb von KDE."""
    if "KDE" not in os.environ.get("XDG_CURRENT_DESKTOP", "") or not shutil.which("gdbus"):
        return False
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, dir=_host_visible_tmpdir()) as f:
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
            log(_("KWin-Skript ließ sich nicht laden"))
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
        self.ctx = setup.Context(log=log, progress=lambda _step, _pct, text: progress(text) if text else None)
        self.env = self.ctx.wine_env

    def run(self) -> None:
        self.progress(_("Sensor-Bridge prüfen"))
        self.ensure_bridge()
        self.progress(_("Anmeldung prüfen"))
        token = login.valid_token()
        if token is None:
            raise NeedLogin()
        self.reconcile()
        self.update_if_needed()
        dpi = display.ensure_dpi(paths.PREFIX, self.ctx.run)
        if dpi:
            self.log(_("Wine-DPI an den Bildschirm angepasst: {dpi}").format(dpi=dpi))
        self.progress(_("Zwift starten"))
        self.start(token)
        self.progress(_("Fenster anpassen"))
        self.wait_and_maximize()
        self.progress(_("Zwift läuft"))

    def ensure_bridge(self) -> None:
        if not bridgectl.unit_installed():
            self.log(_("Sensor-Bridge nicht installiert, Start ohne Sensoren"))
            return
        if not bridgectl.is_running():
            bridgectl.set_running(True)
            self.log(_("Sensor-Bridge gestartet"))

    def reconcile(self) -> None:
        """Einrichtung mit diesem Tretlager abgleichen (docs/updates.md).

        Jeder Schritt prüft am echten System, ob er erledigt ist; im Normalfall dauert das unter
        einer Sekunde. Nach einem Tretlager-Update mit neuem Wine passt das die Zwift-Umgebung an
        (`wineboot -u`) und wiederholt den Grafiktest; verlangt eine neue Tretlager-Version
        weitere Windows-Komponenten, kommen sie hier dazu; fehlt etwas, wird es repariert.
        """
        shutil.rmtree(paths.DATA / "snapshots", ignore_errors=True)  # Schnappschüsse bis 0.8.x
        titles = {s.id: s.title for s in setup.STEPS}
        errors: list[str] = []

        def on_step(step_id: str, status: str, text: str) -> None:
            if status == "running":
                self.progress(_("Einrichtung ergänzen: {step}").format(step=titles.get(step_id, step_id)))
                self.log(_("Einrichtung ergänzen: {step}").format(step=titles.get(step_id, step_id)))
            elif status == "error":
                errors.append(text)

        self.progress(_("Einrichtung prüfen"))
        if not setup.run_setup(self.ctx, on_step):
            raise LaunchError(errors[0] if errors else _("Die Einrichtung ließ sich nicht abgleichen."))

    def update_if_needed(self) -> None:
        local = setup.game_version()
        try:
            remote = remote_version()
        except OSError as e:
            self.log(_("Update-Prüfung nicht möglich: {error}").format(error=e))
            return
        state.update("game", local=local, remote=remote, checked=int(time.time()))
        if not remote or remote == local:
            return
        # Zwift aktualisiert sich über den eigenen Launcher; Tretlager startet ihn nur unsichtbar und
        # wartet, bis die neue Version auf der Platte steht.
        self.progress(_("Zwift wird aktualisiert ({old} → {new})").format(old=local, new=remote))
        self.ctx.wineserver_kill()
        subprocess.Popen(["wine", "start", "/d", r"C:\Program Files (x86)\Zwift", "ZwiftLauncher.exe", "SilentLaunch"],
                         env=self.env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        deadline = time.monotonic() + UPDATE_TIMEOUT
        try:
            while time.monotonic() < deadline:
                time.sleep(5)
                if setup.game_version() == remote:
                    self.log(_("Zwift aktualisiert auf {version}").format(version=remote))
                    time.sleep(10)
                    return
            raise LaunchError(_("Das Zwift-Update wurde nicht fertig. Beim nächsten Start setzt Tretlager es fort."))
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
                raise LaunchError(_("Hilfsprogramm zum Starten ließ sich nicht übersetzen."))
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
        for _attempt in range(30):
            time.sleep(1)
            pid = wine_tasks(self.env).get("ZwiftLauncher.exe")
            if pid:
                break
        if not pid:
            raise LaunchError(_("Der Zwift-Launcher startet nicht."))
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
                raise LaunchError(_("Zwift ließ sich nicht starten (RunFromProcess, Code {code}).").format(code=proc.returncode))
            time.sleep(15)
        except subprocess.TimeoutExpired:
            raise LaunchError(_("Zwift ließ sich nicht starten (Zeitüberschreitung).")) from None
        finally:
            tok_file.unlink(missing_ok=True)
        for name in ("ZwiftLauncher.exe", "ZwiftWindowsCrashHandler.exe"):
            subprocess.run(["wine", "taskkill", "/f", "/im", name], env=self.env, capture_output=True, timeout=30)

    def wait_and_maximize(self) -> None:
        # Das Skript weiß nicht, ob das Fenster schon da ist; mehrfaches Maximieren schadet nicht.
        for _attempt in range(3):
            if not maximize_window_kde(self.log):
                return
            time.sleep(4)

    def running(self) -> bool:
        return process_running("ZwiftApp.exe")

    def after_exit(self) -> None:
        """Nach dem Beenden: Reste beenden, Bridge stoppen, wenn sie nicht im Autostart ist."""
        self.ctx.wineserver_kill()
        try:
            if bridgectl.is_running() and not bridgectl.autostart():
                bridgectl.set_running(False)
                self.log(_("Sensor-Bridge gestoppt"))
        except bridgectl.BridgeError as e:
            self.log(str(e))
