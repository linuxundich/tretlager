"""Start Zwift: bridge, sign-in, update, launch, window, cleanup.

Procedures from the tests on tinytin (FEASIBILITY.md, T2b/T3, poc/token-login/start.sh):
- Zwift only starts as a child of the launcher; otherwise ZwiftApp.exe calls the launcher again.
- NVIDIA on hybrid laptops only via GLX + PRIME offload (decided by the graphics step).
- Zwift does not maximise itself to fit the Plasma panel → KWin script.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Callable

from . import bridgectl, debug, display, login, paths, setup, state, wine
from .manifest import UpdateProgress, remote_version  # noqa: F401 (also for callers of launch)
from ..i18n import _, ngettext

RFP_SRC = Path(__file__).resolve().parent.parent / "data" / "RunFromProcess.cs"
UPDATE_TIMEOUT = 15 * 60
# Wine's output of the launcher and ZwiftApp; the previous launch's log is kept as zwift-wine.old.log.
# Zwift's own crash handler does not work under Wine, so this is the only trace of a crash. Errors
# only, in debug mode also exceptions; TRETLAGER_WINE_DEBUG sets the WINEDEBUG channels directly.
WINE_LOG = paths.STATE / "zwift-wine.log"
WINE_LOG_DEBUG = "-all,err+all"


def wine_log_env(env: dict) -> dict:
    """env with the WINEDEBUG channels for the Zwift launch (in debug mode also exceptions)."""
    channels = os.environ.get("TRETLAGER_WINE_DEBUG") or (debug.WINE_CHANNELS if debug.enabled() else WINE_LOG_DEBUG)
    return dict(env, WINEDEBUG=channels)


class NeedLogin(Exception):
    """No valid token left: sign-in in the browser required."""


class LaunchError(Exception):
    """Error with a sentence for the user."""


def wine_tasks(env: dict) -> dict[str, int]:
    """Running Windows processes in the prefix: name → PID."""
    r = subprocess.run(["wine", "tasklist"], capture_output=True, text=True, env=env, timeout=30)
    out = {}
    for line in r.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0].lower().endswith(".exe") and parts[1].isdigit():
            out.setdefault(parts[0], int(parts[1]))
    return out


def process_running(name: str, proc: Path = Path("/proc")) -> bool:
    """Is a Windows program with this name running? Cheaper and more robust than `wine tasklist`,
    which would have to start a Wine program every few seconds and blocks if wineserver hangs.

    argv[0] is what counts: Wine puts the Windows path there (`C:\\…\\ZwiftApp.exe`). The process
    name (comm) is useless – Zwift names its main thread "main", and comm is truncated to
    15 characters (measured on tinytin, 2026-10-30). Only read up to the first null byte: the
    remaining arguments contain the Zwift token.
    """
    want = name.lower()
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            with open(entry / "cmdline", "rb") as f:
                argv0 = f.read(4096).split(b"\0", 1)[0].decode(errors="replace")
        except OSError:
            continue  # process has exited in the meantime
        if re.split(r"[\\/]", argv0)[-1].lower() == want:
            return True
    return False


ZWIFT_WINDOW = """(w) => (w.resourceClass || "").toLowerCase() === "zwiftapp.exe" && w.normalWindow"""
# Tretlager listens here while Zwift runs; the KWin watch script reports the window's monitor.
WINDOW_BUS_NAME = "de.linuxundich.Tretlager"
WINDOW_OBJECT_PATH = "/de/linuxundich/Tretlager/ZwiftWindow"
WINDOW_INTERFACE = "de.linuxundich.Tretlager.ZwiftWindow"


def maximize_script(output: str | None) -> str:
    """KWin script: move the Zwift window to `output` (the monitor of the last ride), else maximise.

    Moving and maximising happen in separate runs (wait_and_maximize runs it several times):
    two resizes in quick succession leave Zwift's picture at the old size (two monitors with
    different scales, tinytin 2026-11-01).
    """
    return f"""
const isZwift = {ZWIFT_WINDOW};
const target = workspace.screens.find((s) => s.name === {json.dumps(output)});
for (const w of workspace.windowList()) {{
    if (!isZwift(w)) continue;
    if (target && w.output !== target) {{
        workspace.sendClientToScreen(w, target);
    }} else {{
        w.setMaximize(true, true);
    }}
}}
"""


WATCH_SCRIPT = f"""
const isZwift = {ZWIFT_WINDOW};
function report(w) {{
    if (w.output) {{
        callDBus("{WINDOW_BUS_NAME}", "{WINDOW_OBJECT_PATH}", "{WINDOW_INTERFACE}", "SetOutput", w.output.name);
    }}
}}
function watch(w) {{
    if (!isZwift(w)) return;
    w.outputChanged.connect(() => report(w));
    report(w);
}}
workspace.windowList().forEach(watch);
workspace.windowAdded.connect(watch);
"""
WATCH_SCRIPT_NAME = "tretlager-watch"
# Zwift writes this once its interface is up. Resizes before that only reach Zwift once the world
# has loaded, and its picture can stay at the window's first size (tinytin 2026-11-01).
UI_READY = "noesisGUI->OnResize end"
UI_TIMEOUT = 120


def zwift_ui_ready(since: float, prefix: Path | None = None) -> bool:
    """Has the Zwift log written since `since` (time.time()) reported the interface as ready?"""
    for log in (prefix or paths.PREFIX).glob("drive_c/users/*/AppData/Local/Zwift/Logs/Log.txt"):
        try:
            if log.stat().st_mtime < since:
                continue  # previous ride's log, Zwift has not rotated it yet
            if UI_READY in log.read_text(errors="replace"):
                return True
        except OSError:
            continue
    return False


def _host_visible_tmpdir() -> str | None:
    """Directory for files KWin has to read. In the Flatpak /tmp is private; the host sees
    $XDG_RUNTIME_DIR/app/<ID> under the same path. Otherwise the normal temp directory (None)."""
    app_id = os.environ.get("FLATPAK_ID")
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    if app_id and runtime:
        path = Path(runtime) / "app" / app_id
        path.mkdir(parents=True, exist_ok=True)
        return str(path)
    return None


def kwin_available() -> bool:
    return "KDE" in os.environ.get("XDG_CURRENT_DESKTOP", "") and bool(shutil.which("gdbus"))


def _kwin_call(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["gdbus", "call", "--session", "--dest", "org.kde.KWin", *args],
                          capture_output=True, text=True, timeout=10)


def unload_kwin_script(name: str) -> None:
    if kwin_available():
        _kwin_call("--object-path", "/Scripting", "--method", "org.kde.kwin.Scripting.unloadScript", name)


def run_kwin_script(name: str, source: str, log: Callable[[str], None], keep: bool = False) -> bool:
    """Run a KWin script; keep=True leaves it loaded (until unload_kwin_script). False outside KDE."""
    if not kwin_available():
        return False
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, dir=_host_visible_tmpdir()) as f:
        f.write(source)
        script = f.name
    try:
        unload_kwin_script(name)
        r = _kwin_call("--object-path", "/Scripting", "--method", "org.kde.kwin.Scripting.loadScript", script, name)
        sid = r.stdout.strip().strip("(),")
        if not sid.lstrip("-").isdigit() or int(sid) < 0:
            log(_("Could not load the KWin script"))
            return False
        _kwin_call("--object-path", f"/Scripting/Script{sid}", "--method", "org.kde.kwin.Script.run")
        if not keep:
            unload_kwin_script(name)
        return True
    finally:
        os.unlink(script)


def maximize_window_kde(log: Callable[[str], None]) -> bool:
    """Maximise the Zwift window under KWin (above the Plasma panel), on the monitor of the last ride."""
    output = state.load().get("window", {}).get("output")
    return run_kwin_script("tretlager-maximize", maximize_script(output), log)


class Launcher:
    """Performs a launch; progress(text) for the status line, log(text) for the log."""

    def __init__(self, progress: Callable[..., None], log: Callable[[str], None]):
        """progress(text, percent=-1): status line, percent 0–100 or -1 without a progress bar."""
        self.progress = progress
        self.log = log
        self.ctx = setup.Context(log=log, progress=lambda _step, pct, text: progress(text, pct) if text else None)

    @property
    def env(self) -> dict:
        # Fresh every time: the choice of Wine (core/wine.py) can change during reconciliation.
        return self.ctx.wine_env

    def run(self) -> None:
        self.progress(_("Checking the sensor bridge"))
        self.ensure_bridge()
        self.progress(_("Checking the sign-in"))
        token = login.valid_token()
        if token is None:
            raise NeedLogin()
        self.reconcile()
        self.update_if_needed()
        dpi = display.ensure_dpi(paths.PREFIX, self.ctx.run)
        if dpi:
            self.log(_("Wine DPI adjusted to the screen: {dpi}").format(dpi=dpi))
        self.progress(_("Start Zwift"))
        started = time.time()
        self.start(token)
        self.progress(_("Adjusting the window"))
        self.wait_and_maximize(started)
        self.progress(_("Zwift is running"))

    def ensure_bridge(self) -> None:
        if not bridgectl.unit_installed():
            self.log(_("Sensor bridge not installed, starting without sensors"))
            return
        if not bridgectl.is_running():
            bridgectl.set_running(True)
            self.log(_("Sensor bridge started"))

    def reconcile(self) -> None:
        """Reconcile the setup with this Tretlager (docs/updates.md).

        Each step checks on the real system whether it is done; normally this takes under a
        second. After a Tretlager update with a new Wine this adapts the Zwift environment
        (`wineboot -u`) and repeats the graphics test; if a new Tretlager version requires more
        Windows components, they are added here; if something is missing, it is repaired.
        """
        shutil.rmtree(paths.DATA / "snapshots", ignore_errors=True)  # snapshots up to 0.8.x
        if wine.check_after_update():
            self.log(_("New Wine with Tretlager: back to the bundled version"))
        titles = {s.id: s.title for s in setup.STEPS}
        errors: list[str] = []

        def on_step(step_id: str, status: str, text: str) -> None:
            if status == "running":
                self.progress(_("Completing setup: {step}").format(step=titles.get(step_id, step_id)))
                self.log(_("Completing setup: {step}").format(step=titles.get(step_id, step_id)))
            elif status == "error":
                errors.append(text)

        self.progress(_("Check setup"))
        if not setup.run_setup(self.ctx, on_step):
            raise LaunchError(errors[0] if errors else _("The setup could not be checked."))

    def update_if_needed(self) -> None:
        local = setup.game_version()
        try:
            remote = remote_version()
        except OSError as e:
            self.log(_("Could not check for updates: {error}").format(error=e))
            return
        state.update("game", local=local, remote=remote, checked=int(time.time()))
        if not remote or remote == local:
            return
        # Zwift updates itself through its own launcher; Tretlager only starts it invisibly and
        # waits until the new version is on disk.
        title = _("Updating Zwift ({old} → {new})").format(old=local, new=remote)
        self.progress(title)
        tracker = UpdateProgress()
        if tracker.total:
            self.log(_("Zwift update: {gb} GB to download").format(gb=f"{tracker.total / 10**9:.1f}"))
        self.ctx.wineserver_kill()
        subprocess.Popen(["wine", "start", "/d", r"C:\Program Files (x86)\Zwift", "ZwiftLauncher.exe", "SilentLaunch"],
                         env=self.env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        started = time.monotonic()
        deadline = started + UPDATE_TIMEOUT
        try:
            while time.monotonic() < deadline:
                time.sleep(3)
                pct = tracker.percent()
                if pct >= 0:
                    done = tracker.loaded()
                    self.progress(_("{title}: {done} of {total} GB").format(
                        title=title, done=f"{done / 10**9:.1f}", total=f"{tracker.total / 10**9:.1f}"), pct)
                else:
                    minutes = int((time.monotonic() - started) // 60)
                    self.progress(ngettext("{title}, for {n} minute", "{title}, for {n} minutes", minutes)
                                  .format(title=title, n=minutes) if minutes else title)
                if setup.game_version() == remote:
                    self.log(_("Zwift updated to {version}").format(version=remote))
                    time.sleep(10)
                    return
            raise LaunchError(_("The Zwift update did not finish. Tretlager continues it on the next start."))
        finally:
            self.ctx.wineserver_kill()

    def run_from_process(self) -> Path:
        work = paths.CACHE / "rfp"
        exe = work / "RunFromProcess.exe"
        src = work / "RunFromProcess.cs"
        # Recompile if the bundled source has changed.
        if not exe.exists() or not src.exists() or src.read_bytes() != RFP_SRC.read_bytes():
            work.mkdir(parents=True, exist_ok=True)
            exe.unlink(missing_ok=True)
            shutil.copy(RFP_SRC, src)
            self.ctx.run(["wine", setup.CSC, "/nologo", "/target:exe", "/platform:x64", "/out:RunFromProcess.exe",
                          "RunFromProcess.cs"], cwd=work)
            if not exe.exists():
                raise LaunchError(_("Could not compile the start helper."))
        return exe

    def ensure_display_settings(self) -> None:
        """Block resolution changes on every launch, also for prefixes from older Tretlager versions."""
        reg = r"HKCU\Software\Wine\X11 Driver"
        for value in setup.WINE_DISPLAY_KEYS:
            subprocess.run(["wine", "reg", "add", reg, "/v", value, "/t", "REG_SZ", "/d", "N", "/f"],
                           env=self.env, capture_output=True, timeout=60)

    def start(self, token: dict) -> None:
        rfp = self.run_from_process()
        self.ensure_display_settings()
        self.ctx.wineserver_kill()
        # A file, not a pipe: Zwift inherits the descriptor and keeps it open until it exits.
        WINE_LOG.parent.mkdir(parents=True, exist_ok=True)
        if WINE_LOG.exists():  # keep the previous ride's log (a crash is often noticed only afterwards)
            WINE_LOG.replace(WINE_LOG.with_suffix(".old.log"))
        wine_log = open(WINE_LOG, "wb")
        try:
            self._start(token, rfp, wine_log)
        finally:
            wine_log.close()

    def _start(self, token: dict, rfp: Path, wine_log) -> None:
        subprocess.Popen(["wine", "start", "/d", r"C:\Program Files (x86)\Zwift", "ZwiftLauncher.exe", "SilentLaunch"],
                         env=wine_log_env(self.env), stdout=wine_log, stderr=subprocess.STDOUT)
        pid = None
        for _attempt in range(30):
            time.sleep(1)
            pid = wine_tasks(self.env).get("ZwiftLauncher.exe")
            if pid:
                break
        if not pid:
            raise LaunchError(_("The Zwift launcher does not start."))
        time.sleep(5)
        gfx = state.load().get("graphics", {})
        env = wine_log_env(dict(self.env, **setup.graphics_env(gfx)))
        # Never put the token on a Linux command line or in a log: it goes via a file only the user can
        # read (tmpfs), RunFromProcess inserts it itself; the file is deleted afterwards.
        tok_file = Path(os.environ.get("XDG_RUNTIME_DIR") or tempfile.gettempdir()) / "tretlager-start.json"
        fd = os.open(tok_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(json.dumps(token))
        try:
            win_path = "Z:" + str(tok_file).replace("/", "\\")
            # No pipe: otherwise Zwift inherits the output and keeps it open (timeout).
            proc = subprocess.run(["wine", str(rfp), str(pid), "ZwiftApp.exe", "--token=@" + win_path],
                                  cwd=paths.ZWIFT_DIR, env=env, stdout=wine_log,
                                  stderr=subprocess.STDOUT, timeout=60, check=False)
            if proc.returncode != 0:
                raise LaunchError(_("Could not start Zwift (RunFromProcess, code {code}).").format(code=proc.returncode))
            time.sleep(15)
        except subprocess.TimeoutExpired:
            raise LaunchError(_("Could not start Zwift (timed out).")) from None
        finally:
            tok_file.unlink(missing_ok=True)
        for name in ("ZwiftLauncher.exe", "ZwiftWindowsCrashHandler.exe"):
            subprocess.run(["wine", "taskkill", "/f", "/im", name], env=self.env, capture_output=True, timeout=30)

    def wait_and_maximize(self, started: float) -> None:
        deadline = time.monotonic() + UI_TIMEOUT
        while time.monotonic() < deadline and not zwift_ui_ready(started):
            time.sleep(2)
        # First run moves the window to the remembered monitor, the next one maximises it;
        # maximising more than once does no harm.
        for _attempt in range(3):
            if not maximize_window_kde(self.log):
                return
            time.sleep(4)
        # From now on KWin reports which monitor the window is on (remembered for the next start).
        run_kwin_script(WATCH_SCRIPT_NAME, WATCH_SCRIPT, self.log, keep=True)

    def running(self) -> bool:
        return process_running("ZwiftApp.exe")

    def after_exit(self) -> None:
        """After exit: kill leftovers, stop the bridge unless it is set to autostart."""
        unload_kwin_script(WATCH_SCRIPT_NAME)
        self.ctx.wineserver_kill()
        try:
            if bridgectl.is_running() and not bridgectl.autostart():
                bridgectl.set_running(False)
                self.log(_("Sensor bridge stopped"))
        except bridgectl.BridgeError as e:
            self.log(str(e))
