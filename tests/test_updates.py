"""Updating without snapshots: reconcile the setup before every start (docs/updates.md)."""

import json

import pytest

from tretlager.core import launch, paths, setup, state, systemcheck


@pytest.fixture
def prefix(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "PREFIX", tmp_path / "prefix")
    monkeypatch.setattr(paths, "ZWIFT_DIR", tmp_path / "prefix" / "drive_c" / "Program Files (x86)" / "Zwift")
    monkeypatch.setattr(paths, "STATE", tmp_path / "state")
    (tmp_path / "prefix" / "drive_c").mkdir(parents=True)
    (tmp_path / "prefix" / "system.reg").write_text("WINE REGISTRY Version 2\n")
    return tmp_path / "prefix"


def test_prefix_needs_update_after_new_wine(prefix, monkeypatch):
    monkeypatch.setattr(systemcheck, "wine_version", lambda *_a: "wine-11.20")
    state.update("graphics", wine="wine-11.20")  # environment from 0.8.x: only the graphics test knows the version
    assert setup.Prefix().done(setup.Context())
    monkeypatch.setattr(systemcheck, "wine_version", lambda *_a: "wine-11.21")
    assert not setup.Prefix().done(setup.Context())
    assert not setup.Graphics().done(setup.Context())  # graphics test runs again with the new Wine


def test_prefix_update_suppresses_install_dialogs(prefix, monkeypatch):
    monkeypatch.setattr(systemcheck, "wine_version", lambda *_a: "wine-11.21")
    seen = []

    class Ctx(setup.Context):
        def run(self, cmd, env=None, cwd=None, timeout=3600):
            seen.append((cmd, (env or {}).get("WINEDLLOVERRIDES")))
            return 0

        def wineserver_wait(self):
            pass
    monkeypatch.setattr(setup.display, "ensure_dpi", lambda *_a: None)
    setup.Prefix().run(Ctx())
    # without the variable wineboot waits for a Mono/Gecko dialog (tinytin, 2026-10-30)
    assert seen == [(["wine", "wineboot", "-u"], "mscoree,mshtml=")]
    assert json.loads((paths.STATE / "state.json").read_text())["prefix"]["wine"] == "wine-11.21"


def test_components_from_winetricks_log(prefix):
    (prefix / "winetricks.log").write_text("arial\ncorefonts\ndotnet48\nd3dcompiler_47\nwebview2\n")
    assert setup.Components().done(setup.Context())
    (prefix / "winetricks.log").write_text("corefonts\ndotnet48\n")
    assert not setup.Components().done(setup.Context())


def test_installer_not_needed_once_launcher_exists(prefix):
    paths.ZWIFT_DIR.mkdir(parents=True)
    (paths.ZWIFT_DIR / "ZwiftLauncher.exe").write_bytes(b"MZ")
    assert setup.Installer().done(setup.Context())


def test_reconcile_reports_failed_step(monkeypatch, tmp_path):
    monkeypatch.setattr(paths, "DATA", tmp_path)
    (tmp_path / "snapshots" / "prefix-old").mkdir(parents=True)

    def failing(ctx, on_step):
        on_step("prefix", "running", "")
        on_step("prefix", "error", "Wine could not create the environment.")
        return False
    monkeypatch.setattr(setup, "run_setup", failing)
    texts = []
    launcher = launch.Launcher(progress=texts.append, log=lambda _t: None)
    with pytest.raises(launch.LaunchError, match="Wine could not"):
        launcher.reconcile()
    assert any("Wine environment" in t for t in texts)
    assert not (tmp_path / "snapshots").exists()  # leftover cleaned up
