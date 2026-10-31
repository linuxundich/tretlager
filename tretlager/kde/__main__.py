import sys

try:
    from .app import main
except ImportError as exc:
    # Passt PySide nicht zur Qt der Laufzeit (Flatpak: KDE-Laufzeit schon auf neuer Qt-Patchversion,
    # PySide-BaseApp noch nicht), öffnet sich kein Fenster. Ohne Hinweis sähe man gar nichts.
    from ..core import applog, power
    from ..i18n import _

    applog.warning("Start abgebrochen: %s", exc)
    print(f"tretlager: {exc}", file=sys.stderr)
    power.notify(_("Tretlager cannot start"),
                 _("The program libraries do not match the installed KDE runtime. Please "
                   "update Tretlager (flatpak update). Details are in the log."))
    sys.exit(1)

sys.exit(main())
