"""Step "Set up Zwift": installer, Wine environment, components, launcher, game, graphics.

Each step checks with `done()` on the real system whether it is already done; this way the setup
can be cancelled and resumed at any time. Procedures and timings come from the tests on tinytin
(FEASIBILITY.md, T1–T3).
"""

from __future__ import annotations

import hashlib
import os
import re
import selectors
import shutil
import subprocess
import threading
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from . import display, manifest, paths, state, systemcheck, wine
from ..i18n import _

INSTALLER_URL = "https://cdn.zwift.com/app/ZwiftSetup.exe"
# Expected signer (EV certificate); the leaf certificate expires in 2027, hence subject instead of fingerprint.
SIGNER_REQUIRED = ["CN=Zwift\\, Inc.", "serialNumber=5463328"]
CA_BUNDLE = "/etc/ssl/certs/ca-certificates.crt"

WINETRICKS_COMMIT = "f3890f670867b5ffbc3938726db45c0f7d16c8ba"  # provides the webview2 verb
WINETRICKS_URL = f"https://raw.githubusercontent.com/Winetricks/winetricks/{WINETRICKS_COMMIT}/src/winetricks"
WINETRICKS_SHA256 = "672a1ff4442e8691a3ffc0e6860137e201a1d1227e9b3044245f1731e9e9837e"
VERBS = ["corefonts", "dotnet48", "d3dcompiler_47", "webview2"]
VERB_WEIGHT = {"corefonts": 15, "dotnet48": 60, "d3dcompiler_47": 5, "webview2": 20}

GAME_SIZE_BYTES = 4_900_000_000  # Zwift 1.124 on tinytin
GAME_TIMEOUT = 45 * 60
WINEBOOT_TIMEOUT = 5 * 60  # creating ≈ 30 s, adapting to a new Wine is quicker
# Zwift in fullscreen changed the panel resolution despite UseXRandR=N (tinytin, M5); XVidMode
# is the second way Wine switches modes.
WINE_DISPLAY_KEYS = ["UseXRandR", "UseXVidMode"]
GLTEST_SRC = Path(__file__).resolve().parent.parent / "data" / "gltest" / "GLTest.cs"
CSC = r"C:\windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
# Context.run(): how long output is still collected after the command exited, and how often
# cancellation and the time limit are checked.
OUTPUT_GRACE = 2.0
POLL_INTERVAL = 0.2


class SetupError(Exception):
    """Error with a sentence for the user."""


@dataclass
class Context:
    """What the steps need to work; the interface hooks in via the callbacks."""

    progress: Callable[[str, float, str], None] = lambda step, pct, text: None
    log: Callable[[str], None] = lambda text: None
    cancel: threading.Event = field(default_factory=threading.Event)

    @property
    def wine_env(self) -> dict:
        # PATH: bundled Wine or the kept previous version (core/wine.py)
        return dict(os.environ, WINEPREFIX=str(paths.PREFIX), WINEDEBUG="-all", PATH=wine.env_path())

    def run(self, cmd: list[str], env: dict | None = None, cwd: Path | None = None, timeout: int = 3600) -> int:
        """Run a command, output goes to the log line by line.

        Waits for the PROCESS, not for the end of its output. Wine starts helpers (wineserver,
        services.exe, explorer.exe, rpcss.exe …) that inherit our pipe and outlive the command, so the
        pipe only reaches end-of-file much later or never. Reading until then froze the setup: after the
        .NET installation "Installing dotnet48" stood still for half an hour while winetricks was already
        a zombie, and only the one-hour limit would have ended it (measured on tinytin, 2026-11-13).
        """
        self.log("$ " + " ".join(cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                env=env or self.wine_env, cwd=cwd)
        assert proc.stdout
        rest = b""

        def emit(raw: bytes) -> None:
            line = raw.decode("utf-8", "replace").rstrip()
            if line and "libEGL warning" not in line and "pci id for fd" not in line:
                self.log(line)

        sel = selectors.DefaultSelector()
        sel.register(proc.stdout, selectors.EVENT_READ)
        deadline = time.monotonic() + timeout
        rc: int | None = None
        exited: float | None = None          # when the command itself finished
        try:
            while True:
                for _ in sel.select(POLL_INTERVAL):
                    try:
                        chunk = os.read(proc.stdout.fileno(), 65536)
                    except OSError:
                        chunk = b""
                    if not chunk:            # end of file: nobody holds the pipe any more
                        sel.unregister(proc.stdout)
                        break
                    rest += chunk
                    *lines, rest = rest.split(b"\n")
                    for raw in lines:
                        emit(raw)
                if rc is None:
                    rc = proc.poll()
                    if rc is not None:
                        exited = time.monotonic()
                if self.cancel.is_set() or time.monotonic() > deadline:
                    proc.kill()
                    rc = proc.wait()
                    break
                if not sel.get_map():        # pipe closed and command finished
                    if rc is not None:
                        break
                elif exited is not None and time.monotonic() - exited > OUTPUT_GRACE:
                    # Helpers still hold the pipe; stop collecting instead of waiting for them
                    self.log(f"(output ends here, Wine helpers keep the pipe open; rc {rc})")
                    break
        finally:
            sel.close()
            if rest:
                emit(rest)
            proc.stdout.close()
        return rc if rc is not None else proc.wait()

    def wineserver_kill(self) -> None:
        subprocess.run(["wineserver", "-k"], env=self.wine_env, capture_output=True)

    def wineserver_wait(self) -> None:
        subprocess.run(["wineserver", "-w"], env=self.wine_env, capture_output=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: Path, ctx: Context, step: str, text: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": "Tretlager"})
    with urllib.request.urlopen(req, timeout=60) as r, open(part, "wb") as f:  # noqa: S310 (fixed https URL)
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        while chunk := r.read(1 << 16):
            if ctx.cancel.is_set():
                raise SetupError(_("Cancelled"))
            f.write(chunk)
            done += len(chunk)
            if total:
                ctx.progress(step, 100 * done / total, _("{text} ({done} of {total} MB)").format(text=text, done=done // 10**6, total=total // 10**6))
    part.replace(dest)


# --- Steps ---

class Step:
    id = ""
    title = ""

    def done(self, ctx: Context) -> bool:
        raise NotImplementedError

    def run(self, ctx: Context) -> None:
        raise NotImplementedError


def parse_signer(output: str) -> str:
    """First "Signer #0" subject from `osslsigncode verify`."""
    m = re.search(r"Signer #0:\s*\n\s*Subject: (.+)", output)
    return m.group(1).strip() if m else ""


class Installer(Step):
    id = "installer"
    title = _("Download the Zwift installer and verify its signature")
    path = paths.CACHE / "ZwiftSetup.exe"

    def done(self, ctx: Context) -> bool:
        # Only the "launcher" step needs the installer; if the launcher exists, do not download it again.
        if (paths.ZWIFT_DIR / "ZwiftLauncher.exe").exists():
            return True
        info = state.load().get("installer", {})
        return self.path.exists() and info.get("sha256") == sha256(self.path) and info.get("verified") is True

    def run(self, ctx: Context) -> None:
        download(INSTALLER_URL, self.path, ctx, self.id, _("Downloading the installer"))
        ctx.progress(self.id, 100, _("Verifying the signature"))
        r = subprocess.run(["osslsigncode", "verify", "-in", str(self.path), "-CAfile", CA_BUNDLE,
                            "-TSA-CAfile", CA_BUNDLE], capture_output=True, text=True)
        ctx.log(r.stdout[-3000:])
        signer = parse_signer(r.stdout)
        if r.returncode != 0 or "Succeeded" not in r.stdout:
            self.path.unlink(missing_ok=True)
            raise SetupError(_("The Zwift installer's signature is invalid; the file was discarded."))
        if not all(part in signer for part in SIGNER_REQUIRED):
            self.path.unlink(missing_ok=True)
            raise SetupError(_("The installer is not signed by Zwift, Inc. ({signer}).").format(signer=signer or _("unknown")))
        state.update("installer", sha256=sha256(self.path), verified=True, signer=signer, url=INSTALLER_URL)


class Prefix(Step):
    id = "prefix"
    title = _("Create the Wine environment")

    @staticmethod
    def exists() -> bool:
        return (paths.PREFIX / "system.reg").exists() and (paths.PREFIX / "drive_c").is_dir()

    @staticmethod
    def wine_of_prefix() -> str:
        """Wine version the environment was last created or adapted with."""
        st = state.load()
        # Environments up to 0.8.x have no entry of their own; the graphics test ran with the same Wine.
        return st.get("prefix", {}).get("wine") or st.get("graphics", {}).get("wine", "")

    def done(self, ctx: Context) -> bool:
        return self.exists() and self.wine_of_prefix() == systemcheck.wine_version()

    def run(self, ctx: Context) -> None:
        paths.PREFIX.parent.mkdir(parents=True, exist_ok=True)
        # New Wine (Tretlager update): adapt the environment to the new version, which Wine would
        # otherwise do unprompted on the next program start, in the middle of starting Zwift.
        ctx.progress(self.id, 0, _("Wine is adapting the environment to the new version") if self.exists()
                     else _("Wine is setting up the environment"))
        # Only for wineboot: do not fetch Mono and Gecko. Without the variable wineboot opens an
        # install dialog and waits (on tinytin `wineboot -u` hung there for over 10 min). .NET and
        # WebView2 come via winetricks; set permanently, the variable would disable .NET.
        env = dict(ctx.wine_env, WINEDLLOVERRIDES="mscoree,mshtml=")
        if ctx.run(["wine", "wineboot", "-u"], env=env, timeout=WINEBOOT_TIMEOUT) != 0:
            raise SetupError(_("Wine could not adapt the environment.") if self.exists()
                             else _("Wine could not create the environment."))
        ctx.wineserver_wait()
        state.update("prefix", wine=systemcheck.wine_version())
        # From now on at screen scale: otherwise installer and .NET setup are tiny on HiDPI
        display.ensure_dpi(paths.PREFIX, ctx.run)


class Winetricks:
    path = paths.CACHE / "winetricks"

    def ensure(self, ctx: Context) -> Path:
        if not (self.path.exists() and sha256(self.path) == WINETRICKS_SHA256):
            download(WINETRICKS_URL, self.path, ctx, Components.id, _("Downloading winetricks"))
            if sha256(self.path) != WINETRICKS_SHA256:
                self.path.unlink(missing_ok=True)
                raise SetupError(_("winetricks does not have the expected checksum; download discarded."))
            self.path.chmod(0o755)
        return self.path

    @staticmethod
    def installed(ctx: Context) -> set[str]:
        """Installed verbs. winetricks records them in winetricks.log in the prefix; reading it directly
        equals `winetricks list-installed`, just without 2 s startup time (reconciled before every launch)."""
        try:
            return set((paths.PREFIX / "winetricks.log").read_text(errors="ignore").split())
        except OSError:
            return set()


class Components(Step):
    id = "components"
    title = _("Microsoft components (fonts, .NET 4.8, WebView2)")

    def done(self, ctx: Context) -> bool:
        return set(VERBS) <= Winetricks().installed(ctx)

    def run(self, ctx: Context) -> None:
        wt = Winetricks()
        tool = wt.ensure(ctx)
        have = wt.installed(ctx)
        base = 0.0
        for verb in VERBS:
            if verb not in have:
                ctx.progress(self.id, base, _("Installing {verb}").format(verb=verb))
                if ctx.run([str(tool), "-q", verb], cwd=paths.CACHE) != 0:
                    raise SetupError(_("winetricks could not install “{verb}”.").format(verb=verb))
                ctx.wineserver_wait()
            base += VERB_WEIGHT[verb]


class Launcher(Step):
    id = "launcher"
    title = _("Install the Zwift launcher")

    def done(self, ctx: Context) -> bool:
        return (paths.ZWIFT_DIR / "ZwiftLauncher.exe").exists()

    def run(self, ctx: Context) -> None:
        ctx.progress(self.id, 0, _("Installer is running unattended"))
        ctx.run(["wine", str(Installer.path), "/SP-", "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/NOCANCEL"])
        time.sleep(5)
        # Otherwise launcher 1.2 crashes on its first start (netbrain/zwift#420).
        ctx.wineserver_kill()
        if not self.done(ctx):
            raise SetupError(_("The Zwift launcher was not installed."))


def dir_size(path: Path) -> int:
    total = 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            try:
                total += os.lstat(os.path.join(root, f)).st_size
            except OSError:
                pass
    return total


def game_version(zwift_dir: Path | None = None) -> str:
    """Version from the version file; the launcher renames it and records the name (UTF-16)."""
    zwift_dir = zwift_dir or paths.ZWIFT_DIR
    ref = zwift_dir / "Zwift_ver_cur_filename.txt"
    try:
        name = ref.read_bytes().replace(b"\0", b"").decode().strip()
        text = (zwift_dir / name).read_text(errors="ignore")
    except OSError:
        return ""
    m = re.search(r'sversion="([^"]+)"', text)
    return m.group(1) if m else ""


class Game(Step):
    id = "game"
    title = _("Download Zwift (about 5 GB)")

    def done(self, ctx: Context) -> bool:
        return (paths.ZWIFT_DIR / "ZwiftApp.exe").exists() and bool(game_version())

    def run(self, ctx: Context) -> None:
        # Progress from the Zwift manifest (as for updates); without a manifest it is estimated from
        # the size of the Zwift directory.
        tracker = manifest.UpdateProgress()
        if tracker.total:
            ctx.log(_("Zwift: {gb} GB to download").format(gb=f"{tracker.total / 10**9:.1f}"))
        start_size = 0 if tracker.total else dir_size(paths.ZWIFT_DIR)
        ctx.log("$ wine start ZwiftLauncher.exe SilentLaunch")
        subprocess.Popen(["wine", "start", "/d", r"C:\Program Files (x86)\Zwift", "ZwiftLauncher.exe", "SilentLaunch"],
                         env=ctx.wine_env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        deadline = time.monotonic() + GAME_TIMEOUT
        last, stable_since = -1, time.monotonic()
        try:
            while time.monotonic() < deadline:
                if ctx.cancel.is_set():
                    raise SetupError(_("Cancelled"))
                time.sleep(3)
                if tracker.total:
                    loaded = size = tracker.loaded()
                    text = _("{loaded} of {total} GB")
                    total = tracker.total
                else:
                    size = dir_size(paths.ZWIFT_DIR)
                    loaded, total = max(size - start_size, 0), GAME_SIZE_BYTES
                    text = _("{loaded} of about {total} GB")
                ctx.progress(self.id, min(99, 100 * loaded / total),
                             text.format(loaded=f"{loaded / 10**9:.1f}", total=f"{total / 10**9:.1f}"))
                if size != last:
                    last, stable_since = size, time.monotonic()
                if self.done(ctx) and time.monotonic() - stable_since > 15:
                    ctx.log(_("Zwift {version} downloaded").format(version=game_version()))
                    return
            raise SetupError(_("Zwift was not fully downloaded (timed out)."))
        finally:
            ctx.wineserver_kill()


def graphics_env(info: dict) -> dict:
    """Environment variables for the launch, derived from the graphics test."""
    if info.get("offload"):
        return {"__NV_PRIME_RENDER_OFFLOAD": "1", "__GLX_VENDOR_LIBRARY_NAME": "nvidia"}
    return {}


def parse_gltest(output: str) -> dict:
    out = {}
    for key in ("GL_VENDOR", "GL_RENDERER", "GL_VERSION"):
        m = re.search(rf"{key}:\s+(.+)", output)
        if m:
            out[key.lower()] = m.group(1).strip()
    return out


class Graphics(Step):
    id = "graphics"
    title = _("Set up graphics")

    def done(self, ctx: Context) -> bool:
        info = state.load().get("graphics", {})
        # Redo if Wine or the graphics change (e.g. NVIDIA switched on via envycontrol)
        return (bool(info.get("gl_renderer")) and info.get("wine") == systemcheck.wine_version()
                and info.get("gpus") == systemcheck.gpu_signature())

    def run(self, ctx: Context) -> None:
        gpus = systemcheck.list_gpus()
        # NVIDIA only if Zwift can actually use it (driver + GL extension in the Flatpak)
        nvidia = systemcheck.nvidia_usable()
        hybrid = nvidia and any(g.vendor != "NVIDIA" for g in gpus)
        reg = r"HKCU\Software\Wine\X11 Driver"
        # T3: with NVIDIA under XWayland only GLX provides a context on the NVIDIA card.
        if nvidia:
            ctx.run(["wine", "reg", "add", reg, "/v", "UseEGL", "/t", "REG_SZ", "/d", "N", "/f"])
        # Zwift must not change the desktop resolution (neither via XRandR nor via XVidMode).
        for value in WINE_DISPLAY_KEYS:
            ctx.run(["wine", "reg", "add", reg, "/v", value, "/t", "REG_SZ", "/d", "N", "/f"])
        ctx.progress(self.id, 40, _("Compiling the graphics test"))
        work = paths.CACHE / "gltest"
        work.mkdir(parents=True, exist_ok=True)
        shutil.copy(GLTEST_SRC, work / "GLTest.cs")
        ctx.run(["wine", CSC, "/nologo", "/target:exe", "/platform:x64", "/out:GLTest.exe",
                 "/r:System.Windows.Forms.dll", "GLTest.cs"], cwd=work)
        ctx.progress(self.id, 70, _("Running the graphics test"))
        info = {"offload": hybrid}
        env = dict(ctx.wine_env, **graphics_env(info))
        r = subprocess.run(["wine", "GLTest.exe"], cwd=work, env=env, capture_output=True, text=True, timeout=120)
        ctx.wineserver_kill()
        result = parse_gltest(r.stdout)
        ctx.log(r.stdout.strip())
        if not result.get("gl_renderer"):
            raise SetupError(_("Wine gets no OpenGL context; Zwift would not start."))
        if nvidia and "NVIDIA" not in result.get("gl_vendor", ""):
            ctx.log(_("Warning: NVIDIA present, but OpenGL does not run on it"))
        state.update("graphics", **info, **result, wine=systemcheck.wine_version(), gpus=systemcheck.gpu_signature())


STEPS: list[Step] = [Installer(), Prefix(), Components(), Launcher(), Game(), Graphics()]


def run_setup(ctx: Context, on_step: Callable[[str, str, str], None]) -> bool:
    """All steps in order; on_step(id, status, text) with status running/done/skipped/error."""
    # Resumed setup: adapt the DPI of the existing environment to the screen
    display.ensure_dpi(paths.PREFIX, ctx.run)
    for step in STEPS:
        if ctx.cancel.is_set():
            return False
        try:
            if step.done(ctx):
                on_step(step.id, "skipped", _("already done"))
                continue
            on_step(step.id, "running", "")
            step.run(ctx)
            on_step(step.id, "done", "")
        except SetupError as e:
            on_step(step.id, "error", str(e))
            return False
        except Exception as e:  # unexpected: still report it understandably, details go to the log
            ctx.log(f"{type(e).__name__}: {e}")
            on_step(step.id, "error", _("Unexpected error: {error}").format(error=e))
            return False
    return True
