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
    power.notify(_("Tretlager startet nicht"),
                 _("Die Programmbibliotheken passen nicht zur installierten KDE-Laufzeit. "
                   "Bitte Tretlager aktualisieren (flatpak update). Details im Protokoll."))
    sys.exit(1)

sys.exit(main())
