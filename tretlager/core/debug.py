"""Debug mode: more detail in the logs of the interface, the bridge and Wine (for error reports).

Switched on permanently under About Tretlager (state.json), or for one session with `--debug`
(sets TRETLAGER_DEBUG=1, which the bridge inherits when the interface starts it).
"""

from __future__ import annotations

import os

from . import state

ENV = "TRETLAGER_DEBUG"
# Wine channels in debug mode: errors plus every exception Zwift raises (no unwinding traces).
WINE_CHANNELS = "-all,err+all,warn+seh"


def enabled() -> bool:
    return os.environ.get(ENV) == "1" or state.load().get("debug", {}).get("enabled") is True


def set_enabled(on: bool) -> None:
    state.update("debug", enabled=bool(on))
