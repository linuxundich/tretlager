"""Tretlager for Plasma: setup assistant and main window (PySide6 + Kirigami)."""

from __future__ import annotations

import os
import sys
import threading
import time
from pathlib import Path

from PySide6.QtCore import Property, QObject, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine

from .. import APP_ID, __version__, build_id
from . import desktopstyle, zwiftwindow
from .i18n import LocalizedContext
from ..core import applog, bridgectl, btcompat, display, helpdoc, instance, launch, login, power, prepare, setup, state, systemcheck, wine
from ..i18n import LANGUAGE, _, ngettext

# Embedded sign-in (as in the official launcher): needs QtWebEngine. Without the module,
# only the route through the user's own browser remains.
try:
    from PySide6.QtWebEngineQuick import QtWebEngineQuick
except ImportError:  # python3-pyside6.qtwebenginequick not installed
    QtWebEngineQuick = None

QML_DIR = Path(__file__).parent / "qml"
# Revision of the warnings (WarningDialog.qml); increase it when their content changes
DISCLAIMER_VERSION = 1
POLL_VISIBLE_MS = 1500  # live sensor values while the window is visible
POLL_HIDDEN_MS = 15000
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ICON_FILE = DATA_DIR / "icons" / "de.linuxundich.Tretlager.svg"


class Backend(QObject):
    """Bridge between QML and core. Long tasks run in threads, results arrive via signals."""

    checksChanged = Signal()
    busyChanged = Signal()
    remoteCommand = Signal(str)  # from a second invocation: "show" or "start"
    _checksDone = Signal(list)

    def __init__(self, auto_start: bool = False) -> None:
        super().__init__()
        self._auto_start = auto_start
        self._checks: list[dict] = []
        self._busy = False
        self._checksDone.connect(self._set_checks)  # thread → main thread (queued)
        self._init_prepare()
        self._init_setup()
        self._init_login()
        self._init_sensors()
        self._init_launch()

    @Property(list, notify=checksChanged)
    def checks(self) -> list:
        return self._checks

    @Property(str, notify=checksChanged)
    def overall(self) -> str:
        if not self._checks:
            return ""
        return systemcheck.overall([systemcheck.Check(**c) for c in self._checks])

    @Property(bool, notify=busyChanged)
    def busy(self) -> bool:
        return self._busy

    @Slot()
    def runChecks(self) -> None:
        if self._busy:
            return
        self._busy = True
        self.busyChanged.emit()
        threading.Thread(target=lambda: self._checksDone.emit([c.to_dict() for c in systemcheck.run_all()]),
                         daemon=True).start()

    def _set_checks(self, checks: list) -> None:
        self._checks = checks
        self._busy = False
        self.checksChanged.emit()
        self.busyChanged.emit()

    # --- Step "Prepare system" ---

    planChanged = Signal()
    prepareChanged = Signal()
    _planDone = Signal(dict)
    _prepareEvent = Signal(dict)

    def _init_prepare(self) -> None:
        self._plan: dict = {}
        self._plan_busy = False
        self._prep = {"running": False, "percent": 0.0, "step": "", "log": "", "result": "", "error": ""}
        self._planDone.connect(self._set_plan)
        self._prepareEvent.connect(self._on_prepare_event)

    @Property("QVariantMap", notify=planChanged)
    def plan(self) -> dict:
        return self._plan

    @Property(bool, notify=planChanged)
    def planBusy(self) -> bool:
        return self._plan_busy

    @Property("QVariantMap", notify=prepareChanged)
    def prepare(self) -> dict:
        return self._prep

    @Slot()
    def loadPlan(self) -> None:
        if self._plan_busy:
            return
        self._plan_busy = True
        self.planChanged.emit()

        def work():
            try:
                # Test switch: pretend the WineHQ source is missing (to test the flow on set-up systems).
                force = os.environ.get("TRETLAGER_TEST_FORCE_SOURCE") == "1"
                result = prepare.plan(force_temp_source=force).to_dict()
            except Exception as e:  # planning must never take down the UI
                result = {"error": str(e), "packages": [], "removals": [], "nothing_to_do": False}
            self._planDone.emit(result)
        threading.Thread(target=work, daemon=True).start()

    def _set_plan(self, plan: dict) -> None:
        self._plan = plan
        self._plan_busy = False
        self.planChanged.emit()

    @Slot()
    def runPrepare(self) -> None:
        if self._prep["running"]:
            return
        self._prep = {"running": True, "percent": 0.0, "step": _("Requesting permission…"), "log": "",
                      "result": "", "error": ""}
        self.prepareChanged.emit()

        def work():
            rc = prepare.run_helper(self._prepareEvent.emit)
            self._prepareEvent.emit({"event": "exit", "code": rc})
        threading.Thread(target=work, daemon=True).start()

    def _on_prepare_event(self, ev: dict) -> None:
        p = dict(self._prep)
        kind = ev.get("event")
        if kind == "step":
            p["step"] = _(ev.get("text", ""))
        elif kind == "progress":
            p["percent"] = float(ev.get("percent", p["percent"]))
            p["step"] = _(ev["text"]) if ev.get("text") else p["step"]
        elif kind == "log":
            p["log"] = (p["log"] + ev.get("text", "") + "\n")[-20000:]
        elif kind == "done":
            p.update(result="done", percent=100.0, step=_("Done: {wine}").format(wine=ev.get("wine", "")).strip())
        elif kind == "error":
            p.update(result="error", error=_(ev.get("text") or "Unknown error"))
        elif kind == "exit":
            p["running"] = False
            if ev.get("code") and not p["result"]:
                p.update(result="error", error=p["error"] or _("Helper exited with code {code}").format(code=ev["code"]))
        self._prep = p
        self.prepareChanged.emit()


    # --- Step "Set up Zwift" ---

    setupChanged = Signal()
    _setupEvent = Signal(dict)

    def _init_setup(self) -> None:
        self._setup = self._fresh_setup()
        self._setup_ctx: setup.Context | None = None
        self._setupEvent.connect(self._on_setup_event)

    @staticmethod
    def _fresh_setup() -> dict:
        return {"running": False, "result": "", "error": "", "current": "", "percent": 0.0, "text": "",
                "log": "", "steps": [{"id": s.id, "title": s.title, "status": "pending", "detail": ""}
                                     for s in setup.STEPS]}

    @Property("QVariantMap", notify=setupChanged)
    def zwiftSetup(self) -> dict:
        return self._setup

    @Slot()
    def runSetup(self) -> None:
        if self._setup["running"]:
            return
        self._setup = dict(self._fresh_setup(), running=True)
        self.setupChanged.emit()
        ctx = setup.Context(
            progress=lambda step, pct, text: self._setupEvent.emit({"k": "progress", "step": step, "pct": pct, "text": text}),
            log=lambda text: self._setupEvent.emit({"k": "log", "text": text}))
        self._setup_ctx = ctx

        def work():
            ok = setup.run_setup(ctx, lambda i, st, t: self._setupEvent.emit({"k": "step", "id": i, "status": st, "text": t}))
            self._setupEvent.emit({"k": "end", "ok": ok})
        threading.Thread(target=work, daemon=True).start()

    @Slot()
    def cancelSetup(self) -> None:
        if self._setup_ctx:
            self._setup_ctx.cancel.set()

    def _on_setup_event(self, ev: dict) -> None:
        s = dict(self._setup)
        kind = ev["k"]
        if kind == "progress":
            s.update(current=ev["step"], percent=float(ev["pct"]), text=ev["text"])
        elif kind == "log":
            s["log"] = (s["log"] + ev["text"] + "\n")[-30000:]
        elif kind == "step":
            steps = [dict(x) for x in s["steps"]]
            for x in steps:
                if x["id"] == ev["id"]:
                    x["status"], x["detail"] = ev["status"], ev["text"]
            s["steps"] = steps
            if ev["status"] == "running":
                s.update(current=ev["id"], percent=0.0, text="")
            elif ev["status"] == "error":
                s.update(result="error", error=ev["text"])
        elif kind == "end":
            s["running"] = False
            if ev["ok"]:
                s.update(result="done", current="", text="")
        self._setup = s
        self.setupChanged.emit()


    # --- Step "Sign-in" ---

    loginChanged = Signal()
    _loginEvent = Signal(dict)

    def _init_login(self) -> None:
        self._login = {"state": "none", "access_left": 0, "refresh_left": 0, "consent": login.consent_given(),
                       "busy": False, "waiting": False, "error": ""}
        self._login_state_value = ""
        self._loginEvent.connect(self._on_login_event)
        app = QGuiApplication.instance()
        app.clipboard().dataChanged.connect(self.checkClipboard)
        # Check when switching back to the window; under Wayland the clipboard is only readable with focus.
        app.focusWindowChanged.connect(lambda _window: self.checkClipboard())

    @Property("QVariantMap", notify=loginChanged)
    def loginInfo(self) -> dict:
        return self._login

    def _login_update(self, **kw) -> None:
        self._login = dict(self._login, **kw)
        self.loginChanged.emit()

    def _on_login_event(self, ev: dict) -> None:
        self._login_update(**ev)

    @Slot()
    def loadLogin(self) -> None:
        self._login_update(busy=True, error="")

        def work():
            try:
                token = login.valid_token()  # renews if needed
                st = login.status(token)
                self._loginEvent.emit(dict(st, busy=False))
            except login.LoginError as e:
                self._loginEvent.emit({"busy": False, "error": str(e)})
        threading.Thread(target=work, daemon=True).start()

    @Slot()
    def giveConsent(self) -> None:
        login.give_consent()
        self._login_update(consent=True)

    @staticmethod
    def _ui_language() -> str:
        """Language of the Zwift sign-in page: the same as Tretlager's UI."""
        return LANGUAGE

    def on_quit(self) -> None:
        """Clean up on quit: if Zwift is no longer running, stop the bridge (unless on autostart).
        Otherwise it would keep running if the window closed before the post-ride cleanup."""
        zwift = self._launch.get("zwiftRunning", False)
        applog.info("Window closed, Zwift running: %s", zwift)
        if zwift:
            return
        try:
            if bridgectl.is_running() and not bridgectl.autostart():
                bridgectl.set_running(False)
                applog.info("Sensor bridge stopped on quit")
        except bridgectl.BridgeError as e:
            applog.warning("Bridge on quit: %s", e)

    @Slot()
    def quitNow(self) -> None:
        """Quit even during a ride, after confirmation."""
        applog.info("Quitting during the ride confirmed")
        QGuiApplication.quit()

    @Property(bool, constant=True)
    def flatpak(self) -> bool:
        """In the Flatpak Tretlager ships its own Wine; the *Prepare* step is skipped."""
        return bridgectl.IN_FLATPAK

    @Property(bool, constant=True)
    def embeddedLogin(self) -> bool:
        return QtWebEngineQuick is not None

    @Slot(result=str)
    def startEmbeddedLogin(self) -> str:
        """Sign-in page for the embedded window; the redirect comes back via submitRedirect."""
        self._login_state_value = login.new_state()
        self._login_update(waiting=False, error="")
        return login.auth_url(self._login_state_value, self._ui_language())

    @Slot()
    def startBrowserLogin(self) -> None:
        self._login_state_value = login.new_state()
        self._login_update(waiting=True, error="")
        QDesktopServices.openUrl(QUrl(login.auth_url(self._login_state_value, self._ui_language())))

    @Slot()
    def checkClipboard(self) -> None:
        if not self._login.get("waiting") or self._login.get("busy"):
            return
        text = QGuiApplication.clipboard().text().strip()
        if text.startswith("https://launcher.zwift.com/launcher") and "code=" in text:
            self.submitRedirect(text)

    @Slot(str)
    def submitRedirect(self, url: str) -> None:
        try:
            code = login.parse_redirect(url, self._login_state_value or None)
        except login.LoginError as e:
            self._login_update(error=str(e))
            return
        self._login_update(busy=True, error="")

        def work():
            try:
                token = login.exchange_code(code)
                login.Keyring().save(token)
                self._loginEvent.emit(dict(login.status(token), busy=False, waiting=False))
            except login.LoginError as e:
                self._loginEvent.emit({"busy": False, "error": str(e)})
        threading.Thread(target=work, daemon=True).start()

    @Slot()
    def logout(self) -> None:
        """Sign out of Zwift (end the session on the server) and delete the token from the keyring."""
        def work():
            err = ""
            try:
                kr = login.Keyring()
                tok = kr.load()
                if tok and tok.get("refresh_token"):
                    try:
                        login.logout_remote(tok)
                    except login.LoginError as e:
                        err = str(e)
                kr.delete()
            except login.LoginError as e:
                err = str(e)
            self._loginEvent.emit({"state": "none", "access_left": 0, "refresh_left": 0, "error": err})
        threading.Thread(target=work, daemon=True).start()


    # --- Sensors (bridge) ---

    sensorsChanged = Signal()
    _sensorsEvent = Signal(dict)

    def _init_sensors(self) -> None:
        self._sensors = {"installed": True, "running": False, "autostart": False, "network": False,
                         "devices": [], "scanning": False,
                         "found": [], "scanned": False, "error": "",
                         "adapters": [], "adapter": "", "adapterHci": "", "adapterMissing": False}
        self._chip = btcompat.adapter_chip()
        self._sensorsEvent.connect(self._on_sensors_event)
        self._poll = QTimer(self)
        self._poll.setInterval(POLL_VISIBLE_MS)
        self._poll.timeout.connect(self.refreshSensors)
        self._poll_busy = False
        self._adapters_at = 0.0

    @Property("QVariantMap", notify=sensorsChanged)
    def sensors(self) -> dict:
        return self._sensors

    def _on_sensors_event(self, ev: dict) -> None:
        self._sensors = dict(self._sensors, **ev)
        self.sensorsChanged.emit()

    def _bg(self, fn) -> None:
        def work():
            try:
                fn()
            except (bridgectl.BridgeError, OSError, ValueError) as e:
                self._sensorsEvent.emit({"error": str(e), "scanning": False})
        threading.Thread(target=work, daemon=True).start()

    @Slot(bool)
    def setWindowHidden(self, hidden: bool) -> None:
        """When minimized (e.g. during a ride) nobody sees the live values: poll less often.
        Each poll starts two gdbus processes; every 1.5 s that cost a good 1 % CPU when idle."""
        self._poll.setInterval(POLL_HIDDEN_MS if hidden else POLL_VISIBLE_MS)

    @Slot(bool)
    def setSensorPolling(self, on: bool) -> None:
        if on:
            self.refreshSensors()
            self._poll.start()
        else:
            self._poll.stop()

    @Slot()
    def refreshSensors(self) -> None:
        if self._poll_busy:
            return
        self._poll_busy = True

        def work():
            try:
                st = bridgectl.status()
                ev = {}
                # Refresh the adapter list less often (one busctl call per adapter).
                if time.monotonic() - self._adapters_at > 10:
                    self._adapters_at = time.monotonic()
                    ev["adapters"] = btcompat.list_adapters()
                chip = btcompat.adapter_chip((st or {}).get("adapter_hci") or "hci0")
                self._chip = chip
                self._sensorsEvent.emit(dict(ev, **{
                    "installed": bridgectl.unit_installed(), "running": st is not None,
                    "autostart": bridgectl.autostart(),
                    "adapter": (st or {}).get("adapter", ""), "adapterHci": (st or {}).get("adapter_hci", ""),
                    "adapterMissing": (st or {}).get("adapter_missing", False),
                    "devices": btcompat.annotate((st or {}).get("devices", []), chip),
                    "network": not (st or {}).get("local_only", True)}))
            finally:
                self._poll_busy = False
        self._bg(work)

    @Slot(bool)
    def setBridgeRunning(self, on: bool) -> None:
        self._bg(lambda: (bridgectl.set_running(on), self.refreshSensors()))

    @Slot(bool)
    def setBridgeNetwork(self, on: bool) -> None:
        """Also offer the bridge to Zwift on other devices on the network (instead of only 127.0.0.1)."""
        self._bg(lambda: (bridgectl.set_local_only(not on), self.refreshSensors()))

    @Slot(str)
    def setBridgeAdapter(self, address: str) -> None:
        """Choose the adapter; the bridge reconnects the devices through it."""
        self._adapters_at = 0.0
        self._bg(lambda: (bridgectl.set_adapter(address), self.refreshSensors()))

    @Slot(bool)
    def setBridgeAutostart(self, on: bool) -> None:
        self._bg(lambda: (bridgectl.set_autostart(on), self.refreshSensors()))

    @Slot()
    def scanDevices(self) -> None:
        self._on_sensors_event({"scanning": True, "found": [], "error": ""})

        def work():
            found = btcompat.annotate(bridgectl.scan(10), self._chip)
            self._sensorsEvent.emit({"scanning": False, "found": found, "scanned": True})
        self._bg(work)

    @Slot(str, str, str)
    def addDevice(self, address: str, name: str, role: str) -> None:
        self._bg(lambda: (bridgectl.add_device(address, name, role), self.refreshSensors()))
        self._on_sensors_event({"found": [dict(d, configured=d["configured"] or d["address"] == address)
                                          for d in self._sensors["found"]]})

    @Slot(str, bool)
    def setDeviceEnabled(self, address: str, enabled: bool) -> None:
        """Pause (False) or resume a sensor: while paused, the bridge does not look for it."""
        self._bg(lambda: (bridgectl.set_device_enabled(address, enabled), self.refreshSensors()))

    @Slot(str)
    def removeDevice(self, address: str) -> None:
        self._bg(lambda: (bridgectl.remove_device(address), self.refreshSensors()))

    # --- Main window: start Zwift ---

    launchChanged = Signal()
    _launchEvent = Signal(dict)

    def _init_launch(self) -> None:
        self._launch = {"busy": False, "zwiftRunning": False, "text": "", "percent": -1, "error": "", "needLogin": False,
                        "wine": {"bundled": "", "kept": "", "useKept": False, "active": ""},
                        "log": "", "version": "", "remote": "", "renderer": "", "login": "",
                        "onBattery": power.on_ac() is False, "powerChanged": False, "gpuErrors": ""}
        self._launchEvent.connect(self._on_launch_event)
        self._ac_at_start: bool | None = None
        # Watch the power source: notice on battery, note changes during start and ride.
        self._power_timer = QTimer(self)
        self._power_timer.setInterval(2000)
        self._power_timer.timeout.connect(self._check_power)
        self._power_timer.start()

    def _check_power(self) -> None:
        ac = power.on_ac()
        ev = {}
        if (ac is False) != self._launch["onBattery"]:
            ev["onBattery"] = ac is False
        active = self._launch["busy"] or self._launch["zwiftRunning"]
        if active and self._ac_at_start is not None and ac is not None and ac != self._ac_at_start \
                and not self._launch["powerChanged"]:
            ev["powerChanged"] = True
            self._on_launch_event({"logline": _("Power source changed: AC") if ac else _("Power source changed: battery")})
            threading.Thread(target=power.notify, daemon=True, args=(
                _("Power source changed"),
                _("Switching between AC and battery can upset the NVIDIA driver. If Zwift "
                  "hangs, close it with Alt+F4 and restart it with the power adapter connected."))).start()
        if ev:
            self._on_launch_event(ev)

    @Property("QVariantMap", notify=launchChanged)
    def launchInfo(self) -> dict:
        return self._launch

    @Property(bool, constant=True)
    def autoStart(self) -> bool:
        """Called as `tretlager --start`: start Zwift right away, then quit Tretlager."""
        return self._auto_start and self.setupComplete and self.disclaimerAccepted

    @Property(str, constant=True)
    def version(self) -> str:
        return __version__

    @Property(str, constant=True)
    def build(self) -> str:
        """Short ID of the installed Flatpak build (as in `flatpak info`), else empty."""
        return build_id()

    @Property(str, constant=True)
    def licenseText(self) -> str:
        """Full GPL text for the About page: Debian system copy, else LICENSE from the source tree."""
        for path in (Path("/usr/share/common-licenses/GPL-3"), Path(__file__).resolve().parents[2] / "LICENSE"):
            if path.is_file():
                return path.read_text()
        return _("GNU General Public License, version 3 or later: https://www.gnu.org/licenses/gpl-3.0.html")

    @Property(list, constant=True)
    def helpSections(self) -> list:
        """Help (help.md, or help.<lang>.md) as sections with entries and column (see core/helpdoc.py)."""
        localized = DATA_DIR / f"help.{LANGUAGE}.md"
        source = localized if LANGUAGE != "en" and localized.exists() else DATA_DIR / "help.md"
        return helpdoc.layout(helpdoc.parse(source.read_text()))

    @Slot()
    def prewarmBridge(self) -> None:
        """Start the bridge on opening already, so trainer and strap are connected when you get on."""
        def work():
            if not self._launch.get("zwiftRunning") and bridgectl.restart_if_outdated(__version__):
                self._launchEvent.emit({"logline": _("Sensor bridge restarted after an update")})
            if bridgectl.unit_installed() and not bridgectl.is_running():
                bridgectl.set_running(True)
            self.refreshSensors()
        self._bg(work)

    @Property(bool, constant=True)
    def setupComplete(self) -> bool:
        return state.load().get("setup", {}).get("complete") is True

    @Slot()
    def markSetupComplete(self) -> None:
        state.update("setup", complete=True)

    disclaimerChanged = Signal()

    @Property(bool, notify=disclaimerChanged)
    def disclaimerAccepted(self) -> bool:
        """Warnings confirmed on first start? Ask again when their text changes."""
        return state.load().get("disclaimer", {}).get("accepted") == DISCLAIMER_VERSION

    @Slot()
    def acceptDisclaimer(self) -> None:
        state.update("disclaimer", accepted=DISCLAIMER_VERSION)
        applog.info("Warnings confirmed (revision %s)", DISCLAIMER_VERSION)
        self.disclaimerChanged.emit()

    def _on_launch_event(self, ev: dict) -> None:
        if "logline" in ev:
            ev = dict(ev, log=(self._launch["log"] + ev.pop("logline") + "\n")[-20000:])
        self._launch = dict(self._launch, **ev)
        self.launchChanged.emit()

    @Slot()
    def refreshOverview(self) -> None:
        def work():
            st = state.load()
            info = {"version": setup.game_version(), "remote": st.get("game", {}).get("remote", ""),
                    "renderer": st.get("graphics", {}).get("gl_renderer", ""),
                    "wine": {"bundled": wine.bundled_version(), "kept": wine.kept_version(),
                             "useKept": wine.use_kept(), "active": systemcheck.wine_version()}}
            try:  # update check in the background, so the main window shows it before the start
                info["remote"] = launch.remote_version()
                state.update("game", remote=info["remote"], checked=int(time.time()))
            except OSError:
                pass
            try:
                tok = login.Keyring().load()
                ls = login.status(tok)
                info["login"] = {"valid": _("valid"), "refreshable": _("renewed at start"),
                                 "expired": _("expired – please sign in again"),
                                 "none": _("not signed in")}[ls["state"]]
                if ls["state"] in ("valid", "refreshable"):
                    days = ls["refresh_left"] // 86400
                    info["login"] += ngettext(", renewal for {n} more day", ", renewal for {n} more days", days).format(n=days)
            except login.LoginError as e:
                info["login"] = str(e)
            self._launchEvent.emit(info)
        threading.Thread(target=work, daemon=True).start()

    @Slot(bool)
    def setUseKeptWine(self, on: bool) -> None:
        """Start Zwift with the kept, previous Wine version (way back after an update)."""
        wine.set_use_kept(on)
        applog.info("Previous Wine version %s", "on" if on else "off")
        self.refreshOverview()

    @Slot()
    def startZwift(self) -> None:
        if self._launch["busy"] or self._launch["zwiftRunning"]:
            return
        self._ac_at_start = power.on_ac()
        started_at = time.time()
        self._on_launch_event({"busy": True, "error": "", "needLogin": False, "text": _("Preparing the start"),
                               "powerChanged": False, "gpuErrors": ""})
        launcher = launch.Launcher(progress=lambda t, p=-1: self._launchEvent.emit({"text": t, "percent": float(p)}),
                                   log=lambda t: self._launchEvent.emit({"logline": t}))

        def work():
            try:
                launcher.run()
            except launch.NeedLogin:
                self._launchEvent.emit({"busy": False, "needLogin": True, "text": ""})
                return
            except (launch.LaunchError, bridgectl.BridgeError, login.LoginError, setup.SetupError) as e:
                self._launchEvent.emit({"busy": False, "error": str(e), "text": ""})
                self._after_exit_quietly(launcher)
                self._report_gpu_errors(started_at)
                return
            except Exception as e:  # report the type only: exceptions may contain command lines
                applog.warning("Start failed: %s", type(e).__name__)
                self._launchEvent.emit({"busy": False, "error": _("Unexpected error ({name})").format(name=type(e).__name__), "text": ""})
                self._after_exit_quietly(launcher)
                return
            self._launchEvent.emit({"busy": False, "zwiftRunning": True, "text": _("Zwift is running"), "percent": -1})
            applog.info("Zwift running (%s)", systemcheck.wine_version())
            ride_start = time.monotonic()
            # An error while checking must not end the monitoring: otherwise the UI would stay
            # at "Zwift is running" forever, and nobody would clean up.
            misses = 0
            while misses < 2:  # not seen twice = ended (short gap on an in-game restart)
                time.sleep(5)
                try:
                    misses = 0 if launcher.running() else misses + 1
                except OSError:
                    pass
            applog.info("Zwift ended, cleaning up")
            self._after_exit_quietly(launcher)
            try:  # if the bundled Wine has proven itself, it becomes the kept version
                kept = wine.record_ride(time.monotonic() - ride_start)
                if kept:
                    applog.info("Wine %s kept as the proven version", kept)
                    self._launchEvent.emit({"logline": _("{version} kept as the proven Wine version").format(version=kept)})
            except OSError as e:
                applog.warning("Keeping Wine: %s", e)
            self._launchEvent.emit({"zwiftRunning": False, "text": _("Zwift closed")})
            self._report_gpu_errors(started_at)
            self.refreshOverview()
        threading.Thread(target=work, daemon=True).start()


    @staticmethod
    def _after_exit_quietly(launcher) -> None:
        try:
            launcher.after_exit()
        except Exception as e:  # cleanup is optional; errors go to the log only
            applog.warning("Cleanup after Zwift: %s", type(e).__name__)

    def _report_gpu_errors(self, since: float) -> None:
        """After the ride: did the NVIDIA driver report errors? (runs in the worker thread)"""
        codes = power.nvidia_xids(since)
        if codes:
            text = power.describe_xids(codes)
            self._launchEvent.emit({"gpuErrors": text, "logline": _("NVIDIA driver reported {errors}").format(errors=text)})

    # --- Single instance ---

    def listen_for_instances(self) -> None:
        """Do not open further invocations as a second window; hand them over to this one."""
        def on_command(cmd: str) -> None:
            applog.info("Second invocation: %s", cmd)
            self.remoteCommand.emit(cmd)
        self._instance_socket = instance.listen(on_command)


def main() -> int:
    start = "--start" in sys.argv[1:]
    if instance.forward("start" if start else "show"):
        return 0
    restyle = desktopstyle.wanted(in_flatpak=bridgectl.IN_FLATPAK)
    if restyle:
        # Outside Plasma the portal reports the desktop's icon theme (GNOME: Adwaita), which the KDE
        # runtime lacks: status, step and button icons would stay empty, controls in Fusion style.
        # The Plasma platform theme brings Breeze (style, icons, colors) in full.
        # Force it, not just default it: Flatpak passes a host QT_QPA_PLATFORMTHEME through
        # (e.g. qt5ct from ~/.bash_profile), which is missing in the sandbox.
        os.environ["QT_QPA_PLATFORMTHEME"] = "kde"
    if QtWebEngineQuick is not None:
        if bridgectl.IN_FLATPAK:
            # WebEngine comes from the BaseApp (/app), but Qt only looks for the helper process in the
            # runtime's paths (/usr) and aborts without it at the first WebEngineView (SIGABRT)
            os.environ.setdefault("QTWEBENGINEPROCESS_PATH", "/app/bin/QtWebEngineProcess")
            os.environ.setdefault("QTWEBENGINE_DICTIONARIES_PATH", "/app/qtwebengine_dictionaries")
        QtWebEngineQuick.initialize()  # must run before the QGuiApplication
    app = QGuiApplication(sys.argv)
    app.setApplicationName("Tretlager")
    app.setOrganizationDomain("linuxundich.de")
    app.setDesktopFileName(APP_ID)
    app.setWindowIcon(QIcon.fromTheme(APP_ID, QIcon(str(ICON_FILE))))
    if restyle:
        desktopstyle.DesktopStyle(app).start()  # light/dark and font from the desktop
    engine = QQmlApplicationEngine()
    localized = LocalizedContext()  # i18n functions for Kirigami Addons
    engine.rootContext().setContextObject(localized)
    backend = Backend(auto_start=start)
    backend.listen_for_instances()
    zwiftwindow.register(app)
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    # Scaling for Wine (LogPixels) in case KWin's XWayland setting is unreadable (Flatpak):
    # the window's is fractional under Wayland (e.g. 1.6), the screen's is rounded up.
    for window in engine.rootObjects():
        display.set_scale(window.devicePixelRatio())
        window.screenChanged.connect(lambda _s, w=window: display.set_scale(w.devicePixelRatio()))
    if not engine.rootObjects():
        return 1
    applog.info("Start %s%s%s", __version__, f" (Flatpak, Build {build_id()})" if bridgectl.IN_FLATPAK else "", " --start" if start else "")
    app.aboutToQuit.connect(backend.on_quit)
    code = app.exec()
    applog.info("Exited (code %s)", code)
    return code
