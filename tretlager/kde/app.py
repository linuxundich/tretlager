"""Tretlager für Plasma: Einrichtungsassistent und Hauptfenster (PySide6 + Kirigami)."""

from __future__ import annotations

import os
import sys
import threading
from pathlib import Path

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine

from .. import APP_ID
from ..core import login, prepare, setup, systemcheck

QML_DIR = Path(__file__).parent / "qml"


class Backend(QObject):
    """Brücke zwischen QML und Kern. Lange Arbeiten laufen in Threads, Ergebnisse kommen per Signal."""

    checksChanged = Signal()
    busyChanged = Signal()
    _checksDone = Signal(list)

    def __init__(self) -> None:
        super().__init__()
        self._checks: list[dict] = []
        self._busy = False
        self._checksDone.connect(self._set_checks)  # Thread → Hauptthread (queued)
        self._init_prepare()
        self._init_setup()
        self._init_login()

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
        try:
            login.Keyring().delete()
        except login.LoginError as e:
            self._login_update(error=str(e))
            return
        self._login_update(state="none", access_left=0, refresh_left=0)


def main() -> int:
    app = QGuiApplication(sys.argv)
    app.setApplicationName("Tretlager")
    app.setOrganizationDomain("linuxundich.de")
    app.setDesktopFileName(APP_ID)
    app.setWindowIcon(QIcon.fromTheme("applications-games"))
    engine = QQmlApplicationEngine()
    backend = Backend()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    if not engine.rootObjects():
        return 1
    return app.exec()
