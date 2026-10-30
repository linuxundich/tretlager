from tretlager.core import display


def _prefix(tmp_path, dpi=None):
    reg = "WINE REGISTRY Version 2\n\n[Control Panel\\\\Desktop] 1700000000\n#time=1\n\"FontSmoothing\"=\"2\"\n"
    if dpi is not None:
        reg += f'"LogPixels"=dword:{dpi:08x}\n'
    reg += "\n[Software\\\\Wine] 1\n\"Version\"=\"win10\"\n"
    (tmp_path / "user.reg").write_text(reg)
    return tmp_path


def test_wine_dpi_from_scale(tmp_path):
    display.set_scale(1.6)
    try:
        assert display.wine_dpi({"XDG_CONFIG_HOME": str(tmp_path)}) == 154
    finally:
        display.set_scale(0)


def test_wine_dpi_fallbacks(tmp_path):
    display.set_scale(0)
    assert display.wine_dpi({"XDG_CONFIG_HOME": str(tmp_path)}) == 96
    (tmp_path / "kwinrc").write_text("[Xwayland]\nScale=1.6\n")
    display.set_scale(2)  # Bildschirm aufgerundet; kwinrc hat Vorrang
    try:
        assert display.wine_dpi({"XDG_CONFIG_HOME": str(tmp_path)}) == 154
    finally:
        display.set_scale(0)
    assert display.wine_dpi({"XDG_CONFIG_HOME": str(tmp_path), "TRETLAGER_DPI": "120"}) == 120


def test_current_dpi(tmp_path):
    assert display.current_dpi(_prefix(tmp_path, 96)) == 96
    assert display.current_dpi(_prefix(tmp_path)) is None


def test_ensure_dpi_only_when_different(tmp_path):
    calls = []
    prefix = _prefix(tmp_path, 154)
    assert display.ensure_dpi(prefix, calls.append, 154) is None and not calls
    assert display.ensure_dpi(prefix, calls.append, 192) == 192
    assert calls[0][:3] == ["wine", "reg", "add"] and "192" in calls[0]


def test_ensure_dpi_without_prefix(tmp_path):
    calls = []
    assert display.ensure_dpi(tmp_path / "fehlt", calls.append, 154) is None and not calls
