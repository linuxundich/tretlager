"""Only one Tretlager instance: further invocations pass their command to the running one.

Abstract Unix socket per user; it disappears with the process, no file is left behind.
"""

from __future__ import annotations

import os
import socket
import struct
import threading
from typing import Callable

COMMANDS = ("show", "start")


def socket_name(uid: int | None = None) -> str:
    # TRETLAGER_INSTANCE only for tests: start a second instance next to the running one
    suffix = os.environ.get("TRETLAGER_INSTANCE", "")
    return f"\0tretlager-{os.getuid() if uid is None else uid}" + (f"-{suffix}" if suffix else "")


def forward(command: str, name: str | None = None) -> bool:
    """If Tretlager is already running, send the command there and return True."""
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
    """User ID of the peer (SO_PEERCRED); -1 if it cannot be determined."""
    try:
        _pid, uid, _gid = struct.unpack("3i", conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED,
                                                              struct.calcsize("3i")))
        return uid
    except OSError:
        return -1


def listen(on_command: Callable[[str], None], name: str | None = None) -> socket.socket:
    """Wait for commands from further invocations (own thread); the return value keeps the socket alive."""
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
                # Abstract sockets have no file permissions: any user in the same network namespace
                # could connect. Only accept commands from our own user.
                if peer_uid(conn) != os.getuid():
                    continue
                cmd = conn.recv(64).decode(errors="ignore").strip()
            if cmd in COMMANDS:
                on_command(cmd)
    threading.Thread(target=loop, daemon=True).start()
    return srv
