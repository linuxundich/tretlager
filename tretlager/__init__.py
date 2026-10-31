"""Tretlager – Zwift unter Linux einrichten, starten und mit Sensoren verbinden."""

__version__ = "0.9.0"  # muss zur obersten Version im CHANGELOG passen (tests/test_version.py)

APP_ID = "de.linuxundich.Tretlager"
BRIDGE_BUS_NAME = "de.linuxundich.Tretlager.Bridge"
BRIDGE_OBJECT_PATH = "/de/linuxundich/Tretlager/Bridge"
BRIDGE_UNIT = "tretlager-bridge.service"


def build_id(info: str = "/.flatpak-info") -> str:
    """Kurzkennung des Flatpak-Baus (die ersten 7 Zeichen von app-commit wie bei `flatpak info`).

    Die Versionsnummer ändert sich nur mit einem Release; zwei Bauten derselben Version unterscheidet
    erst diese Kennung. Außerhalb des Flatpaks leer.
    """
    try:
        with open(info, encoding="utf-8") as f:
            for line in f:
                if line.startswith("app-commit="):
                    return line.split("=", 1)[1].strip()[:7]
    except OSError:
        pass
    return ""
