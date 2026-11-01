"""Short log of start, ride and exit of the interface (for troubleshooting; no token or similar).

Lives at $XDG_STATE_HOME/tretlager/tretlager.log (inside the sandbox in the Flatpak) and is rotated
at 200 kB (one older file is kept); in debug mode at 2 MB, with the launch steps as well.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from . import paths

_log = logging.getLogger("tretlager.app")
_handler: RotatingFileHandler | None = None
if not _log.handlers:
    try:
        paths.STATE.mkdir(parents=True, exist_ok=True)
        _handler = RotatingFileHandler(paths.STATE / "tretlager.log", maxBytes=200_000, backupCount=1,
                                       encoding="utf-8")
        _handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S"))
        _log.addHandler(_handler)
    except OSError:
        _log.addHandler(logging.NullHandler())
    _log.setLevel(logging.INFO)
    _log.propagate = False

debug = _log.debug
info = _log.info
warning = _log.warning


def set_debug(on: bool) -> None:
    _log.setLevel(logging.DEBUG if on else logging.INFO)
    if _handler is not None:
        _handler.maxBytes = 2_000_000 if on else 200_000
