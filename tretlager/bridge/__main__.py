import asyncio
import logging
import os
from logging.handlers import RotatingFileHandler

from ..core import debug, paths
from .service import run

FORMAT = "%(levelname)s %(name)s: %(message)s"


def setup_logging() -> None:
    """stderr (journal outside the Flatpak) plus bridge.log next to tretlager.log: inside the
    Flatpak the journal cannot be read, the error report collects the file."""
    verbose = debug.enabled()
    logging.basicConfig(level=os.environ.get("TRETLAGER_LOG", "INFO"), format=FORMAT)
    if verbose:
        logging.getLogger("tretlager").setLevel(logging.DEBUG)  # not bleak/dbus-fast: far too chatty
    try:
        paths.STATE.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(paths.STATE / "bridge.log", encoding="utf-8", backupCount=1,
                                      maxBytes=2_000_000 if verbose else 500_000)
    except OSError:
        return
    handler.setFormatter(logging.Formatter("%(asctime)s " + FORMAT, "%Y-%m-%d %H:%M:%S"))
    logging.getLogger().addHandler(handler)


def main() -> None:
    setup_logging()
    asyncio.run(run())


if __name__ == "__main__":
    main()
