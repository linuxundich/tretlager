from tretlager.core import gnomealive, state


def test_parse_value():
    assert gnomealive.parse_value("uint32 5000") == 5000
    assert gnomealive.parse_value("0") == 0
    assert gnomealive.parse_value("") is None
    assert gnomealive.parse_value(None) is None


def test_disable_and_restore(monkeypatch, tmp_path):
    store = {}
    monkeypatch.setattr(state, "load", lambda: dict(store))
    monkeypatch.setattr(state, "save", lambda d: (store.clear(), store.update(d)))
    monkeypatch.setattr(state, "update", lambda sec, **v: store.setdefault(sec, {}).update(v))
    monkeypatch.setattr(gnomealive, "available", lambda: True)
    calls = []
    current = ["uint32 5000"]

    def fake(*args):
        calls.append(args)
        if args[0] == "get":
            return current[0]
        current[0] = args[-1]
        return ""
    monkeypatch.setattr(gnomealive, "_gsettings", fake)
    assert gnomealive.disable()
    assert current[0] == "0" and store["gnome_alive"]["value"] == 5000
    assert gnomealive.disable()  # second call (cut short run) keeps the real value
    assert store["gnome_alive"]["value"] == 5000
    gnomealive.restore()
    assert current[0] == "5000" and "gnome_alive" not in store
    gnomealive.restore()  # nothing remembered: does nothing
    assert current[0] == "5000"


def test_unavailable_outside_gnome(monkeypatch):
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "KDE")
    assert not gnomealive.available() and not gnomealive.disable()


def test_x11_maximize_without_display(monkeypatch):
    from tretlager.core import x11window
    monkeypatch.delenv("DISPLAY", raising=False)
    assert x11window.maximize("zwiftapp.exe") is False
