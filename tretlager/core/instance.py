"""Nur eine Tretlager-Instanz: Weitere Aufrufe geben ihren Befehl an die laufende weiter.

Abstrakter Unix-Socket je Benutzer; er verschwindet mit dem Prozess, es bleibt keine Datei liegen.
"""

from __future__ import annotations

import os
import socket
import struct
import threading
from typing import Callable

COMMANDS = ("show", "start")


def socket_name(uid: int | None = None) -> str:
    # TRETLAGER_INSTANCE nur für Tests: eine zweite Instanz neben der laufenden starten
    suffix = os.environ.get("TRETLAGER_INSTANCE", "")
    return f"\0tretlager-{os.getuid() if uid is None else uid}" + (f"-{suffix}" if suffix else "")


def forward(command: str, name: str | None = None) -> bool:
    """Läuft Tretlager schon, den Befehl dorthin schicken und True liefern."""
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        s.connect(name or socket_name())
        s.sendall(command.encode())
        return True
    except OSError:
        return False
    finally:
        s.close()


def peer_uid(conn: socket.socket) -> int:
    """Benutzer-ID der Gegenseite (SO_PEERCRED); -1, wenn nicht ermittelbar."""
    try:
        _pid, uid, _gid = struct.unpack("3i", conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED,
                                                              struct.calcsize("3i")))
        return uid
    except OSError:
        return -1


def listen(on_command: Callable[[str], None], name: str | None = None) -> socket.socket:
    """Auf Befehle weiterer Aufrufe warten (eigener Thread); Rückgabe hält den Socket am Leben."""
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(name or socket_name())
    srv.listen(4)

    def loop():
        while True:
            try:
                conn, _ = srv.accept()
            except OSError:
                return
            with conn:
                # Abstrakte Sockets haben keine Dateirechte: Jeder Benutzer im selben Netz-Namensraum
                # könnte sich verbinden. Nur Befehle vom eigenen Benutzer annehmen.
                if peer_uid(conn) != os.getuid():
                    continue
                cmd = conn.recv(64).decode(errors="ignore").strip()
            if cmd in COMMANDS:
                on_command(cmd)
    threading.Thread(target=loop, daemon=True).start()
    return srv
