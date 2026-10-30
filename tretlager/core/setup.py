"""Schritt „Zwift einrichten“: Installer, Wine-Umgebung, Komponenten, Launcher, Spiel, Grafik.

Jeder Schritt prüft mit `done()` am echten System, ob er schon erledigt ist; so lässt sich die
Einrichtung jederzeit abbrechen und fortsetzen. Abläufe und Zeiten stammen aus den Tests auf
tinytin (FEASIBILITY.md, T1–T3).
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import threading
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from . import display, paths, state, systemcheck
from ..i18n import _

INSTALLER_URL = "https://cdn.zwift.com/app/ZwiftSetup.exe"
# Erwarteter Signierer (EV-Zertifikat); das Blatt-Zertifikat läuft 2027 ab, daher Subject statt Fingerabdruck.
SIGNER_REQUIRED = ["CN=Zwift\\, Inc.", "serialNumber=5463328"]
CA_BUNDLE = "/etc/ssl/certs/ca-certificates.crt"

WINETRICKS_COMMIT = "f3890f670867b5ffbc3938726db45c0f7d16c8ba"  # bringt das Verb webview2 mit
WINETRICKS_URL = f"https://raw.githubusercontent.com/Winetricks/winetricks/{WINETRICKS_COMMIT}/src/winetricks"
WINETRICKS_SHA256 = "672a1ff4442e8691a3ffc0e6860137e201a1d1227e9b3044245f1731e9e9837e"
VERBS = ["corefonts", "dotnet48", "d3dcompiler_47", "webview2"]
VERB_WEIGHT = {"corefonts": 15, "dotnet48": 60, "d3dcompiler_47": 5, "webview2": 20}

GAME_SIZE_BYTES = 4_900_000_000  # Zwift 1.124 auf tinytin
GAME_TIMEOUT = 45 * 60
# Zwift im Vollbild stellte trotz UseXRandR=N die Panel-Auflösung um (tinytin, M5); XVidMode
# ist der zweite Weg, über den Wine Modi wechselt.
WINE_DISPLAY_KEYS = ["UseXRandR", "UseXVidMode"]
GLTEST_SRC = Path(__file__).resolve().parent.parent / "data" / "gltest" / "GLTest.cs"
CSC = r"C:\windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"


class SetupError(Exception):
    """Fehler mit einem Satz für den Nutzer."""


@dataclass
class Context:
    """Was die Schritte zum Arbeiten brauchen; die Oberfläche hängt sich über die Rückrufe an."""

    progress: Callable[[str, float, str], None] = lambda step, pct, text: None
    log: Callable[[str], None] = lambda text: None
    cancel: threading.Event = field(default_factory=threading.Event)

    @property
    def wine_env(self) -> dict:
        return dict(os.environ, WINEPREFIX=str(paths.PREFIX), WINEDEBUG="-all")

    def run(self, cmd: list[str], env: dict | None = None, cwd: Path | None = None, timeout: int = 3600) -> int:
        """Befehl ausführen, Ausgabe zeilenweise ins Protokoll."""
        self.log("$ " + " ".join(cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                env=env or self.wine_env, cwd=cwd, errors="replace")
        assert proc.stdout
        start = time.monotonic()
        for line in proc.stdout:
            line = line.rstrip()
            if line and "libEGL warning" not in line and "pci id for fd" not in line:
                self.log(line)
            if self.cancel.is_set() or time.monotonic() - start > timeout:
                proc.kill()
                break
        return proc.wait()

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
    with urllib.request.urlopen(req, timeout=60) as r, open(part, "wb") as f:  # noqa: S310 (feste https-URL)
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        while chunk := r.read(1 << 16):
            if ctx.cancel.is_set():
                raise SetupError(_("Abgebrochen"))
            f.write(chunk)
            done += len(chunk)
            if total:
                ctx.progress(step, 100 * done / total, _("{text} ({done} von {total} MB)").format(text=text, done=done // 10**6, total=total // 10**6))
    part.replace(dest)


# --- Schritte ---

class Step:
    id = ""
    title = ""

    def done(self, ctx: Context) -> bool:
        raise NotImplementedError

    def run(self, ctx: Context) -> None:
        raise NotImplementedError


def parse_signer(output: str) -> str:
    """Erstes „Signer #0“-Subject aus `osslsigncode verify`."""
    m = re.search(r"Signer #0:\s*\n\s*Subject: (.+)", output)
    return m.group(1).strip() if m else ""


class Installer(Step):
    id = "installer"
    title = _("Zwift-Installer laden und Signatur prüfen")
    path = paths.CACHE / "ZwiftSetup.exe"

    def done(self, ctx: Context) -> bool:
        info = state.load().get("installer", {})
        return self.path.exists() and info.get("sha256") == sha256(self.path) and info.get("verified") is True

    def run(self, ctx: Context) -> None:
        download(INSTALLER_URL, self.path, ctx, self.id, _("Installer laden"))
        ctx.progress(self.id, 100, _("Signatur prüfen"))
        r = subprocess.run(["osslsigncode", "verify", "-in", str(self.path), "-CAfile", CA_BUNDLE,
                            "-TSA-CAfile", CA_BUNDLE], capture_output=True, text=True)
        ctx.log(r.stdout[-3000:])
        signer = parse_signer(r.stdout)
        if r.returncode != 0 or "Succeeded" not in r.stdout:
            self.path.unlink(missing_ok=True)
            raise SetupError(_("Die Signatur des Zwift-Installers ist ungültig; die Datei wurde verworfen."))
        if not all(part in signer for part in SIGNER_REQUIRED):
            self.path.unlink(missing_ok=True)
            raise SetupError(_("Der Installer ist nicht von Zwift, Inc. signiert ({signer}).").format(signer=signer or _("unbekannt")))
        state.update("installer", sha256=sha256(self.path), verified=True, signer=signer, url=INSTALLER_URL)


class Prefix(Step):
    id = "prefix"
    title = _("Wine-Umgebung anlegen")

    def done(self, ctx: Context) -> bool:
        return (paths.PREFIX / "system.reg").exists() and (paths.PREFIX / "drive_c").is_dir()

    def run(self, ctx: Context) -> None:
        paths.PREFIX.parent.mkdir(parents=True, exist_ok=True)
        ctx.progress(self.id, 0, _("Wine richtet die Umgebung ein"))
        # Nur hier: Mono und Gecko nicht nachladen, .NET und WebView2 kommen über winetricks.
        # Später gesetzt würde die Variable .NET abschalten (winetricks dotnet48, csc.exe).
        env = dict(ctx.wine_env, WINEDLLOVERRIDES="mscoree,mshtml=")
        if ctx.run(["wine", "wineboot", "-u"], env=env) != 0:
            raise SetupError(_("Wine konnte die Umgebung nicht anlegen."))
        ctx.wineserver_wait()
        # Ab jetzt in Bildschirmgröße: Installer und .NET-Einrichtung sonst winzig auf HiDPI
        display.ensure_dpi(paths.PREFIX, ctx.run)


class Winetricks:
    path = paths.CACHE / "winetricks"

    def ensure(self, ctx: Context) -> Path:
        if not (self.path.exists() and sha256(self.path) == WINETRICKS_SHA256):
            download(WINETRICKS_URL, self.path, ctx, Components.id, "winetricks laden")
            if sha256(self.path) != WINETRICKS_SHA256:
                self.path.unlink(missing_ok=True)
                raise SetupError(_("winetricks hat nicht die erwartete Prüfsumme; Download verworfen."))
            self.path.chmod(0o755)
        return self.path

    def installed(self, ctx: Context) -> set[str]:
        if not self.path.exists():
            return set()
        r = subprocess.run([str(self.path), "list-installed"], capture_output=True, text=True,
                           env=ctx.wine_env, timeout=120)
        return set(r.stdout.split())


class Components(Step):
    id = "components"
    title = _("Komponenten von Microsoft (Schriften, .NET 4.8, WebView2)")

    def done(self, ctx: Context) -> bool:
        return set(VERBS) <= Winetricks().installed(ctx)

    def run(self, ctx: Context) -> None:
        wt = Winetricks()
        tool = wt.ensure(ctx)
        have = wt.installed(ctx)
        base = 0.0
        for verb in VERBS:
            if verb not in have:
                ctx.progress(self.id, base, f"{verb} installieren")
                if ctx.run([str(tool), "-q", verb], cwd=paths.CACHE) != 0:
                    raise SetupError(_("winetricks konnte „{verb}“ nicht installieren.").format(verb=verb))
                ctx.wineserver_wait()
            base += VERB_WEIGHT[verb]


class Launcher(Step):
    id = "launcher"
    title = _("Zwift-Launcher installieren")

    def done(self, ctx: Context) -> bool:
        return (paths.ZWIFT_DIR / "ZwiftLauncher.exe").exists()

    def run(self, ctx: Context) -> None:
        ctx.progress(self.id, 0, _("Installer läuft unbeaufsichtigt"))
        ctx.run(["wine", str(Installer.path), "/SP-", "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/NOCANCEL"])
        time.sleep(5)
        # Launcher 1.2 stürzt sonst beim ersten Start ab (netbrain/zwift#420).
        ctx.wineserver_kill()
        if not self.done(ctx):
            raise SetupError(_("Der Zwift-Launcher wurde nicht installiert."))


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
    """Version aus der Versionsdatei; der Launcher benennt sie um und vermerkt den Namen (UTF-16)."""
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
    title = _("Zwift laden (etwa 5 GB)")

    def done(self, ctx: Context) -> bool:
        return (paths.ZWIFT_DIR / "ZwiftApp.exe").exists() and bool(game_version())

    def run(self, ctx: Context) -> None:
        start_size = dir_size(paths.ZWIFT_DIR)
        ctx.log("$ wine start ZwiftLauncher.exe SilentLaunch")
        subprocess.Popen(["wine", "start", "/d", r"C:\Program Files (x86)\Zwift", "ZwiftLauncher.exe", "SilentLaunch"],
                         env=ctx.wine_env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        deadline = time.monotonic() + GAME_TIMEOUT
        last, stable_since = -1, time.monotonic()
        try:
            while time.monotonic() < deadline:
                if ctx.cancel.is_set():
                    raise SetupError(_("Abgebrochen"))
                time.sleep(3)
                size = dir_size(paths.ZWIFT_DIR)
                loaded = max(size - start_size, 0)
                ctx.progress(self.id, min(99, 100 * loaded / GAME_SIZE_BYTES),
                             f"{loaded / 10**9:.1f} von etwa {GAME_SIZE_BYTES / 10**9:.1f} GB")
                if size != last:
                    last, stable_since = size, time.monotonic()
                if self.done(ctx) and time.monotonic() - stable_since > 15:
                    ctx.log(_("Zwift {version} geladen").format(version=game_version()))
                    return
            raise SetupError(_("Zwift wurde nicht vollständig geladen (Zeitüberschreitung)."))
        finally:
            ctx.wineserver_kill()


def graphics_env(info: dict) -> dict:
    """Umgebungsvariablen für den Start, abgeleitet aus dem Grafiktest."""
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
    title = _("Grafik einrichten")

    def done(self, ctx: Context) -> bool:
        info = state.load().get("graphics", {})
        return bool(info.get("gl_renderer")) and info.get("wine") == systemcheck.wine_version()

    def run(self, ctx: Context) -> None:
        gpus = systemcheck.list_gpus()
        nvidia = any(g.vendor == "NVIDIA" for g in gpus)
        hybrid = nvidia and any(g.vendor != "NVIDIA" for g in gpus)
        reg = r"HKCU\Software\Wine\X11 Driver"
        # T3: Mit NVIDIA unter XWayland liefert nur GLX einen Kontext auf der NVIDIA-Karte.
        if nvidia:
            ctx.run(["wine", "reg", "add", reg, "/v", "UseEGL", "/t", "REG_SZ", "/d", "N", "/f"])
        # Zwift soll die Auflösung des Desktops nicht umstellen (weder per XRandR noch per XVidMode).
        for value in WINE_DISPLAY_KEYS:
            ctx.run(["wine", "reg", "add", reg, "/v", value, "/t", "REG_SZ", "/d", "N", "/f"])
        ctx.progress(self.id, 40, _("Grafiktest übersetzen"))
        work = paths.CACHE / "gltest"
        work.mkdir(parents=True, exist_ok=True)
        shutil.copy(GLTEST_SRC, work / "GLTest.cs")
        ctx.run(["wine", CSC, "/nologo", "/target:exe", "/platform:x64", "/out:GLTest.exe",
                 "/r:System.Windows.Forms.dll", "GLTest.cs"], cwd=work)
        ctx.progress(self.id, 70, _("Grafiktest ausführen"))
        info = {"offload": hybrid}
        env = dict(ctx.wine_env, **graphics_env(info))
        r = subprocess.run(["wine", "GLTest.exe"], cwd=work, env=env, capture_output=True, text=True, timeout=120)
        ctx.wineserver_kill()
        result = parse_gltest(r.stdout)
        ctx.log(r.stdout.strip())
        if not result.get("gl_renderer"):
            raise SetupError(_("Wine bekommt keinen OpenGL-Kontext; Zwift würde nicht starten."))
        if nvidia and "NVIDIA" not in result.get("gl_vendor", ""):
            ctx.log(_("Warnung: NVIDIA vorhanden, aber OpenGL läuft nicht darauf"))
        state.update("graphics", **info, **result, wine=systemcheck.wine_version())


STEPS: list[Step] = [Installer(), Prefix(), Components(), Launcher(), Game(), Graphics()]


def run_setup(ctx: Context, on_step: Callable[[str, str, str], None]) -> bool:
    """Alle Schritte der Reihe nach; on_step(id, status, text) mit status running/done/skipped/error."""
    # Weitergeführte Einrichtung: DPI der vorhandenen Umgebung an den Bildschirm anpassen
    display.ensure_dpi(paths.PREFIX, ctx.run)
    for step in STEPS:
        if ctx.cancel.is_set():
            return False
        try:
            if step.done(ctx):
                on_step(step.id, "skipped", "schon erledigt")
                continue
            on_step(step.id, "running", "")
            step.run(ctx)
            on_step(step.id, "done", "")
        except SetupError as e:
            on_step(step.id, "error", str(e))
            return False
        except Exception as e:  # unerwartet: trotzdem verständlich melden, Details ins Protokoll
            ctx.log(f"{type(e).__name__}: {e}")
            on_step(step.id, "error", f"Unerwarteter Fehler: {e}")
            return False
    return True
