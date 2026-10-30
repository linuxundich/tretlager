"""Kurzes Protokoll von Start, Fahrt und Beenden der Oberfläche (für Fehlersuche, kein Token o. Ä.).

Liegt unter $XDG_STATE_HOME/tretlager/tretlager.log (im Flatpak in der Sandbox) und wird ab
200 kB rotiert (eine ältere Datei bleibt).
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from . import paths

_log = logging.getLogger("tretlager.app")
if not _log.handlers:
    try:
        paths.STATE.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(paths.STATE / "tretlager.log", maxBytes=200_000, backupCount=1,
                                      encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S"))
        _log.addHandler(handler)
    except OSError:
        _log.addHandler(logging.NullHandler())
    _log.setLevel(logging.INFO)
    _log.propagate = False

info = _log.info
warning = _log.warning
