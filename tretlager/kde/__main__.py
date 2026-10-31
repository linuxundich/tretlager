import sys

try:
    from .app import main
except ImportError as exc:
    # If PySide does not match the runtime's Qt (Flatpak: KDE runtime already on a newer Qt patch
    # release, PySide BaseApp not yet), no window opens. Without a notice you would see nothing.
    from ..core import applog, power
    from ..i18n import _

    applog.warning("Start aborted: %s", exc)
    print(f"tretlager: {exc}", file=sys.stderr)
    power.notify(_("Tretlager cannot start"),
                 _("The program libraries do not match the installed KDE runtime. Please "
                   "update Tretlager (flatpak update). Details are in the log."))
    sys.exit(1)

sys.exit(main())
