"""Keep the screen on during the ride: inhibit through the portal, release afterwards."""

import time

import pytest

pytest.importorskip("dbus_fast")
from dbus_fast import MessageType  # noqa: E402

from tretlager.core import awake  # noqa: E402


class FakeBus:
    def __init__(self, calls):
        self.calls = calls
        self.connected = True

    async def call(self, msg):
        self.calls.append((msg.interface, msg.member, msg.body))
        class Reply:
            message_type = MessageType.METHOD_RETURN
            body = ["/org/freedesktop/portal/desktop/request/1_1/t"]
        return Reply()

    def disconnect(self):
        self.connected = False


def wait_for(cond):
    for _ in range(100):
        if cond():
            return True
        time.sleep(0.01)
    return False


def test_inhibit_and_release():
    calls, buses = [], []

    async def connect():
        buses.append(FakeBus(calls))
        return buses[-1]
    keep = awake.KeepAwake(connect)
    keep.want(True, "Zwift ride")
    keep.want(True, "Zwift ride")  # repeated: no second inhibition
    assert wait_for(lambda: keep.active)
    assert calls == [("org.freedesktop.portal.Inhibit", "Inhibit", ["", awake.IDLE | awake.SUSPEND, calls[0][2][2]])]
    assert calls[0][2][2]["reason"].value == "Zwift ride"
    keep.want(False)
    assert wait_for(lambda: not buses[0].connected)
    assert calls[-1][:2] == ("org.freedesktop.portal.Request", "Close") and not keep.active


def test_enabled_by_default(tmp_path, monkeypatch):
    monkeypatch.setattr(awake.state, "_file", lambda: tmp_path / "state.json")
    assert awake.enabled()
    awake.set_enabled(False)
    assert not awake.enabled()
