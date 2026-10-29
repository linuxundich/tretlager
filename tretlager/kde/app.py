"""Tretlager für Plasma: Einrichtungsassistent und Hauptfenster (PySide6 + Kirigami)."""

from __future__ import annotations

import os
import sys
import threading
import time
from pathlib import Path

from PySide6.QtCore import Property, QObject, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine

from .. import APP_ID
from ..core import bridgectl, instance, launch, login, prepare, setup, state, systemcheck

QML_DIR = Path(__file__).parent / "qml"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ICON_FILE = DATA_DIR / "icons" / "de.linuxundich.Tretlager.svg"


class Backend(QObject):
    """Brücke zwischen QML und Kern. Lange Arbeiten laufen in Threads, Ergebnisse kommen per Signal."""

    checksChanged = Signal()
    busyChanged = Signal()
    remoteCommand = Signal(str)  # von einem zweiten Aufruf: "show" oder "start"
    _checksDone = Signal(list)

    def __init__(self, auto_start: bool = False) -> None:
        super().__init__()
        self._auto_start = auto_start
        self._checks: list[dict] = []
        self._busy = False
        self._checksDone.connect(self._set_checks)  # Thread → Hauptthread (queued)
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

    # --- Schritt „System vorbereiten“ ---

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
                # Testschalter: so tun, als fehle die WineHQ-Quelle (Ablauf auf fertigen Systemen prüfen).
                force = os.environ.get("TRETLAGER_TEST_FORCE_SOURCE") == "1"
                result = prepare.plan(force_temp_source=force).to_dict()
            except Exception as e:  # Planung darf die Oberfläche nie mitreißen
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
        self._prep = {"running": True, "percent": 0.0, "step": "Berechtigung anfragen …", "log": "",
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
            p["step"] = ev.get("text", "")
        elif kind == "progress":
            p["percent"] = float(ev.get("percent", p["percent"]))
            p["step"] = ev.get("text") or p["step"]
        elif kind == "log":
            p["log"] = (p["log"] + ev.get("text", "") + "\n")[-20000:]
        elif kind == "done":
            p.update(result="done", percent=100.0, step=f"Fertig: {ev.get('wine', '')}".strip())
        elif kind == "error":
            p.update(result="error", error=ev.get("text", "Unbekannter Fehler"))
        elif kind == "exit":
            p["running"] = False
            if ev.get("code") and not p["result"]:
                p.update(result="error", error=p["error"] or f"Helfer beendet mit Code {ev['code']}")
        self._prep = p
        self.prepareChanged.emit()


    # --- Schritt „Zwift einrichten“ ---

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


    # --- Schritt „Anmeldung“ ---

    loginChanged = Signal()
    _loginEvent = Signal(dict)

    def _init_login(self) -> None:
        self._login = {"state": "none", "access_left": 0, "refresh_left": 0, "consent": login.consent_given(),
                       "busy": False, "waiting": False, "error": ""}
        self._login_state_value = ""
        self._loginEvent.connect(self._on_login_event)
        app = QGuiApplication.instance()
        app.clipboard().dataChanged.connect(self.checkClipboard)
        # Beim Zurückwechseln ins Fenster prüfen; unter Wayland ist die Zwischenablage erst mit Fokus lesbar.
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
                token = login.valid_token()  # erneuert bei Bedarf
                st = login.status(token)
                self._loginEvent.emit(dict(st, busy=False))
            except login.LoginError as e:
                self._loginEvent.emit({"busy": False, "error": str(e)})
        threading.Thread(target=work, daemon=True).start()

    @Slot()
    def giveConsent(self) -> None:
        login.give_consent()
        self._login_update(consent=True)

    @Slot()
    def startBrowserLogin(self) -> None:
        self._login_state_value = login.new_state()
        self._login_update(waiting=True, error="")
        QDesktopServices.openUrl(QUrl(login.auth_url(self._login_state_value)))

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
        """Bei Zwift abmelden (Sitzung serverseitig beenden) und das Token aus dem Schlüsselbund löschen."""
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


    # --- Sensoren (Bridge) ---

    sensorsChanged = Signal()
    _sensorsEvent = Signal(dict)

    def _init_sensors(self) -> None:
        self._sensors = {"installed": True, "running": False, "autostart": False, "network": False,
                         "devices": [], "scanning": False,
                         "found": [], "scanned": False, "error": ""}
        self._sensorsEvent.connect(self._on_sensors_event)
        self._poll = QTimer(self)
        self._poll.setInterval(1500)
        self._poll.timeout.connect(self.refreshSensors)
        self._poll_busy = False

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
                self._sensorsEvent.emit({
                    "installed": bridgectl.unit_installed(), "running": st is not None,
                    "autostart": bridgectl.autostart(), "devices": (st or {}).get("devices", []),
                    "network": not (st or {}).get("local_only", True)})
            finally:
                self._poll_busy = False
        self._bg(work)

    @Slot(bool)
    def setBridgeRunning(self, on: bool) -> None:
        self._bg(lambda: (bridgectl.set_running(on), self.refreshSensors()))

    @Slot(bool)
    def setBridgeNetwork(self, on: bool) -> None:
        """Bridge auch für Zwift auf anderen Geräten im Netz anbieten (statt nur 127.0.0.1)."""
        self._bg(lambda: (bridgectl.set_local_only(not on), self.refreshSensors()))

    @Slot(bool)
    def setBridgeAutostart(self, on: bool) -> None:
        self._bg(lambda: (bridgectl.set_autostart(on), self.refreshSensors()))

    @Slot()
    def scanDevices(self) -> None:
        self._on_sensors_event({"scanning": True, "found": [], "error": ""})

        def work():
            found = bridgectl.scan(10)
            self._sensorsEvent.emit({"scanning": False, "found": found, "scanned": True})
        self._bg(work)

    @Slot(str, str, str)
    def addDevice(self, address: str, name: str, role: str) -> None:
        self._bg(lambda: (bridgectl.add_device(address, name, role), self.refreshSensors()))
        self._on_sensors_event({"found": [dict(d, configured=d["configured"] or d["address"] == address)
                                          for d in self._sensors["found"]]})

    @Slot(str)
    def removeDevice(self, address: str) -> None:
        self._bg(lambda: (bridgectl.remove_device(address), self.refreshSensors()))

    # --- Hauptfenster: Zwift starten ---

    launchChanged = Signal()
    _launchEvent = Signal(dict)

    def _init_launch(self) -> None:
        self._launch = {"busy": False, "zwiftRunning": False, "text": "", "error": "", "needLogin": False,
                        "log": "", "version": "", "remote": "", "renderer": "", "login": ""}
        self._launchEvent.connect(self._on_launch_event)

    @Property("QVariantMap", notify=launchChanged)
    def launchInfo(self) -> dict:
        return self._launch

    @Property(bool, constant=True)
    def autoStart(self) -> bool:
        """Mit `tretlager --start` aufgerufen: Zwift gleich starten, danach Tretlager beenden."""
        return self._auto_start and self.setupComplete

    @Property(str, constant=True)
    def helpText(self) -> str:
        return (DATA_DIR / "hilfe.md").read_text()

    @Slot()
    def prewarmBridge(self) -> None:
        """Bridge schon beim Öffnen starten, damit Trainer und Gurt beim Aufsteigen verbunden sind."""
        def work():
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
                    "renderer": st.get("graphics", {}).get("gl_renderer", "")}
            try:  # Update-Prüfung im Hintergrund, damit das Hauptfenster es vor dem Start zeigt
                info["remote"] = launch.remote_version()
                state.update("game", remote=info["remote"], checked=int(time.time()))
            except OSError:
                pass
            try:
                tok = login.Keyring().load()
                ls = login.status(tok)
                info["login"] = {"valid": "gültig", "refreshable": "wird beim Start erneuert",
                                 "expired": "abgelaufen – bitte neu anmelden",
                                 "none": "nicht angemeldet"}[ls["state"]]
                if ls["state"] in ("valid", "refreshable"):
                    info["login"] += f", Erneuerung noch {ls['refresh_left'] // 86400} Tage"
            except login.LoginError as e:
                info["login"] = str(e)
            self._launchEvent.emit(info)
        threading.Thread(target=work, daemon=True).start()

    @Slot()
    def startZwift(self) -> None:
        if self._launch["busy"] or self._launch["zwiftRunning"]:
            return
        self._on_launch_event({"busy": True, "error": "", "needLogin": False, "text": "Start vorbereiten"})
        launcher = launch.Launcher(progress=lambda t: self._launchEvent.emit({"text": t}),
                                   log=lambda t: self._launchEvent.emit({"logline": t}))

        def work():
            try:
                launcher.run()
            except launch.NeedLogin:
                self._launchEvent.emit({"busy": False, "needLogin": True, "text": ""})
                return
            except (launch.LaunchError, bridgectl.BridgeError, login.LoginError, setup.SetupError) as e:
                self._launchEvent.emit({"busy": False, "error": str(e), "text": ""})
                launcher.after_exit()
                return
            except Exception as e:  # nur den Typ melden: Ausnahmen können Befehlszeilen enthalten
                self._launchEvent.emit({"busy": False, "error": f"Unerwarteter Fehler ({type(e).__name__})", "text": ""})
                return
            self._launchEvent.emit({"busy": False, "zwiftRunning": True, "text": "Zwift läuft"})
            while launcher.running():
                time.sleep(5)
            launcher.after_exit()
            self._launchEvent.emit({"zwiftRunning": False, "text": "Zwift beendet"})
            self.refreshOverview()
        threading.Thread(target=work, daemon=True).start()


    # --- Nur eine Instanz ---

    def listen_for_instances(self) -> None:
        """Weitere Aufrufe nicht als zweites Fenster starten, sondern an dieses weitergeben."""
        self._instance_socket = instance.listen(self.remoteCommand.emit)


def main() -> int:
    start = "--start" in sys.argv[1:]
    if instance.forward("start" if start else "show"):
        return 0
    app = QGuiApplication(sys.argv)
    app.setApplicationName("Tretlager")
    app.setOrganizationDomain("linuxundich.de")
    app.setDesktopFileName(APP_ID)
    app.setWindowIcon(QIcon.fromTheme(APP_ID, QIcon(str(ICON_FILE))))
    engine = QQmlApplicationEngine()
    backend = Backend(auto_start=start)
    backend.listen_for_instances()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    if not engine.rootObjects():
        return 1
    return app.exec()
