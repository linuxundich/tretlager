"""Remember the monitor of the Zwift window (KWin reports it over D-Bus, see core/launch.py).

While Zwift runs, a KWin script calls `SetOutput(name)` whenever the window changes monitors.
The next launch moves the window there before maximising it.
"""

from __future__ import annotations

from PySide6.QtCore import ClassInfo, QObject, Slot
from PySide6.QtDBus import QDBusConnection

from ..core import applog, launch, state


@ClassInfo({"D-Bus Interface": launch.WINDOW_INTERFACE})
class ZwiftWindow(QObject):
    @Slot(str)
    def SetOutput(self, name: str) -> None:  # noqa: N802 (D-Bus method name)
        if not name or state.load().get("window", {}).get("output") == name:
            return
        state.update("window", output=name)
        applog.info("Zwift window on monitor %s", name)


def register(parent: QObject) -> ZwiftWindow | None:
    """Offer the object on the session bus; None if that fails (the window then stays where KWin puts it)."""
    bus = QDBusConnection.sessionBus()
    obj = ZwiftWindow(parent)
    if not bus.registerService(launch.WINDOW_BUS_NAME) or not bus.registerObject(
            launch.WINDOW_OBJECT_PATH, obj, QDBusConnection.RegisterOption.ExportAllSlots):
        applog.warning("D-Bus: could not offer %s", launch.WINDOW_OBJECT_PATH)
        return None
    return obj
