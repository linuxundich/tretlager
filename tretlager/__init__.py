"""Tretlager – set up Zwift on Linux, start it and connect it to sensors."""

__version__ = "0.11.3"  # must match the topmost version in the CHANGELOG (tests/test_version.py)

APP_ID = "de.linuxundich.Tretlager"
BRIDGE_BUS_NAME = "de.linuxundich.Tretlager.Bridge"
BRIDGE_OBJECT_PATH = "/de/linuxundich/Tretlager/Bridge"
BRIDGE_UNIT = "tretlager-bridge.service"


def build_id(info: str = "/.flatpak-info") -> str:
    """Short ID of the Flatpak build (the first 7 characters of app-commit, as in `flatpak info`).

    The version number only changes with a release; only this ID tells two builds of the same
    version apart. Empty outside the Flatpak.
    """
    try:
        with open(info, encoding="utf-8") as f:
            for line in f:
                if line.startswith("app-commit="):
                    return line.split("=", 1)[1].strip()[:7]
    except OSError:
        pass
    return ""
