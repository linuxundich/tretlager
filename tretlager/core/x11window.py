"""Maximise a window through the X11 protocol (EWMH), for desktops without a KWin script.

Zwift runs under Wine as an X11 client (XWayland on GNOME), does not fill the screen by itself
and GNOME has no API to maximise another program's window. The window manager accepts the
standard `_NET_WM_STATE` request from any client; that is all `wmctrl` does. Plain ctypes on
libX11, so no extra package is needed.
"""

from __future__ import annotations

import ctypes
import ctypes.util


class _ClientMessage(ctypes.Structure):
    _fields_ = [("type", ctypes.c_int), ("serial", ctypes.c_ulong), ("send_event", ctypes.c_int),
                ("display", ctypes.c_void_p), ("window", ctypes.c_ulong), ("message_type", ctypes.c_ulong),
                ("format", ctypes.c_int), ("data", ctypes.c_long * 5)]


class _ClassHint(ctypes.Structure):
    _fields_ = [("res_name", ctypes.c_void_p), ("res_class", ctypes.c_void_p)]


CLIENT_MESSAGE = 33
SUBSTRUCTURE_NOTIFY_REDIRECT = (1 << 19) | (1 << 20)
XA_WINDOW = 33
_ERROR_HANDLER = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)
_ignore_errors = _ERROR_HANDLER(lambda _d, _e: 0)  # the default handler would end the process


def maximize(wm_class: str) -> bool:
    """Maximise the first normal window whose WM_CLASS (name or class) equals `wm_class`
    (case-insensitive). False if there is no X display, no such window or the call failed."""
    name = ctypes.util.find_library("X11")
    if not name:
        return False
    x = ctypes.CDLL(name)
    x.XOpenDisplay.restype = ctypes.c_void_p
    x.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x.XDefaultRootWindow.restype = ctypes.c_ulong
    x.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
    x.XInternAtom.restype = ctypes.c_ulong
    x.XInternAtom.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
    x.XSetErrorHandler.argtypes = [_ERROR_HANDLER]
    x.XGetClassHint.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(_ClassHint)]
    x.XGetWindowProperty.argtypes = [
        ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_long, ctypes.c_long, ctypes.c_int,
        ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_void_p)]
    x.XSendEvent.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int, ctypes.c_long, ctypes.c_void_p]
    x.XFree.argtypes = [ctypes.c_void_p]
    x.XSetErrorHandler(_ignore_errors)
    dpy = x.XOpenDisplay(None)
    if not dpy:
        return False
    try:
        root = x.XDefaultRootWindow(dpy)
        atom = lambda n: x.XInternAtom(dpy, n, 0)  # noqa: E731
        kind, fmt, count, rest, data = ctypes.c_ulong(), ctypes.c_int(), ctypes.c_ulong(), ctypes.c_ulong(), ctypes.c_void_p()
        if x.XGetWindowProperty(dpy, root, atom(b"_NET_CLIENT_LIST"), 0, 4096, 0, XA_WINDOW,
                                ctypes.byref(kind), ctypes.byref(fmt), ctypes.byref(count),
                                ctypes.byref(rest), ctypes.byref(data)) != 0 or not data.value:
            return False
        windows = list(ctypes.cast(data, ctypes.POINTER(ctypes.c_ulong))[:count.value])
        x.XFree(data)
        wanted = wm_class.lower()
        done = False
        for win in windows:
            hint = _ClassHint()
            if not x.XGetClassHint(dpy, win, ctypes.byref(hint)):
                continue
            names = {(ctypes.string_at(p) if p else b"").decode(errors="replace").lower()
                     for p in (hint.res_name, hint.res_class)}
            if hint.res_name:
                x.XFree(hint.res_name)
            if hint.res_class:
                x.XFree(hint.res_class)
            if wanted not in names:
                continue
            ev = _ClientMessage(type=CLIENT_MESSAGE, send_event=1, window=win, format=32,
                                message_type=atom(b"_NET_WM_STATE"))
            ev.data[:] = [1, atom(b"_NET_WM_STATE_MAXIMIZED_VERT"), atom(b"_NET_WM_STATE_MAXIMIZED_HORZ"), 1, 0]
            buf = (ctypes.c_long * 24)()  # XEvent is a union of 24 longs
            ctypes.memmove(buf, ctypes.byref(ev), ctypes.sizeof(ev))
            x.XSendEvent(dpy, root, 0, SUBSTRUCTURE_NOTIFY_REDIRECT, buf)
            done = True
        x.XFlush.argtypes = [ctypes.c_void_p]
        x.XFlush(dpy)
        x.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
        x.XSync(dpy, 0)
        return done
    finally:
        x.XCloseDisplay.argtypes = [ctypes.c_void_p]
        x.XCloseDisplay(dpy)
