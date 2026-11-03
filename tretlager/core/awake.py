"""Keep the screen on during a ride ("caffeine").

While pedalling nobody touches mouse or keyboard, and Zwift under Wine does not ask the desktop to
stay awake: Plasma and GNOME dim the screen, switch it off and lock the session. While Zwift runs,
Tretlager therefore asks the Inhibit portal (org.freedesktop.portal.Inhibit; inside and outside
the Flatpak, on Plasma and GNOME) to suppress idle and suspend. The inhibition lasts as long as
the D-Bus connection: if Tretlager crashes, it ends by itself.

Checked on tinytin (2026-11-03, Plasma 6.7): the KDE portal turns the call into PowerDevil
AddInhibition(InterruptSession | ChangeScreenSettings). GNOME's portal uses the session manager's
idle and suspend inhibitors.

The switch is in the main window (state.json "awake.enabled", on by default). gdbus is no use here
(it ends the connection right away), and QtDBus cannot send the uint32 flags from Python; so
dbus-fast runs on its own event loop in a thread.
"""

from __future__ import annotations

import asyncio
import threading

from . import applog, state

PORTAL = "org.freedesktop.portal.Desktop"
PORTAL_PATH = "/org/freedesktop/portal/desktop"
SUSPEND = 4
IDLE = 8


def enabled() -> bool:
    return state.load().get("awake", {}).get("enabled", True) is not False


def set_enabled(on: bool) -> None:
    state.update("awake", enabled=bool(on))


class KeepAwake:
    """Holds an inhibition while `want(True)` is in effect; calls return immediately."""

    def __init__(self, connect=None) -> None:
        self._connect = connect  # for tests: coroutine function returning a message bus
        self._loop: asyncio.AbstractEventLoop | None = None
        self._bus = None
        self._handle = ""
        self.wanted = False

    @property
    def active(self) -> bool:
        return self._bus is not None

    def want(self, on: bool, reason: str = "") -> None:
        if on == self.wanted:
            return
        self.wanted = on
        if self._loop is None:
            self._loop = asyncio.new_event_loop()
            threading.Thread(target=self._loop.run_forever, name="keep-awake", daemon=True).start()
        asyncio.run_coroutine_threadsafe(self._apply(on, reason), self._loop)

    async def _apply(self, on: bool, reason: str) -> None:
        from dbus_fast import Message, MessageType, Variant

        if on and self._bus is None:
            try:
                if self._connect:
                    bus = await self._connect()
                else:
                    from dbus_fast.aio import MessageBus
                    bus = await MessageBus().connect()
            except Exception as e:
                applog.warning("Keep screen on: no session bus (%s)", type(e).__name__)
                return
            reply = await bus.call(Message(destination=PORTAL, path=PORTAL_PATH,
                                           interface="org.freedesktop.portal.Inhibit", member="Inhibit",
                                           signature="sua{sv}", body=["", IDLE | SUSPEND,
                                                                      {"reason": Variant("s", reason)}]))
            if reply.message_type == MessageType.ERROR:
                applog.warning("Keep screen on: portal refused (%s)", reply.error_name)
                bus.disconnect()
                return
            self._bus, self._handle = bus, reply.body[0]
            applog.info("Keep screen on: active")
        elif not on and self._bus is not None:
            bus, self._bus = self._bus, None
            try:
                await bus.call(Message(destination=PORTAL, path=self._handle,
                                       interface="org.freedesktop.portal.Request", member="Close"))
            except Exception:
                pass  # disconnecting ends the inhibition as well
            bus.disconnect()
            applog.info("Keep screen on: released")
