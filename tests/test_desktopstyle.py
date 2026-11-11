import pytest

pytest.importorskip("PySide6.QtDBus")
from tretlager.kde import desktopstyle  # noqa: E402

COLORS = """[ColorEffects:Disabled]
Color=56,56,56

[Colors:Window]
BackgroundNormal=32,35,38
ForegroundNormal=252,252,252

[Colors:Header][Inactive]
BackgroundNormal=1,2,3

[General]
Name=Breeze Dark
"""


def test_wanted_only_in_flatpak_outside_plasma():
    assert desktopstyle.wanted({"XDG_CURRENT_DESKTOP": "GNOME"}, in_flatpak=True)
    assert not desktopstyle.wanted({"XDG_CURRENT_DESKTOP": "KDE"}, in_flatpak=True)
    assert desktopstyle.wanted({"XDG_CURRENT_DESKTOP": "ubuntu:GNOME"}, in_flatpak=False)
    assert not desktopstyle.wanted({"XDG_CURRENT_DESKTOP": "KDE"}, in_flatpak=False)


def test_scheme_name():
    assert desktopstyle.scheme_name(1) == "BreezeDark"
    assert desktopstyle.scheme_name(0) == "BreezeLight"
    assert desktopstyle.scheme_name(2) == "BreezeLight"
    assert desktopstyle.scheme_name(None) == "BreezeLight"


def test_parse_font():
    assert desktopstyle.parse_font("Adwaita Sans 12") == ("Adwaita Sans", 12.0)
    assert desktopstyle.parse_font("Cantarell Bold 10.5") == ("Cantarell", 10.5)
    assert desktopstyle.parse_font("Adwaita Sans") is None
    assert desktopstyle.parse_font("") is None


def test_read_colors(tmp_path):
    f = tmp_path / "BreezeDark.colors"
    f.write_text(COLORS)
    colors = desktopstyle.read_colors(f)
    assert colors == {"Window": {"BackgroundNormal": (32, 35, 38), "ForegroundNormal": (252, 252, 252)}}
