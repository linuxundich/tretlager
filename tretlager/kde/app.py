"""Tretlager für Plasma: Einrichtungsassistent und Hauptfenster (PySide6 + Kirigami)."""

from __future__ import annotations

import sys
import threading
from pathlib import Path

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine

from .. import APP_ID
from ..core import systemcheck

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
