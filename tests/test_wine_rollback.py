"""Vorige Wine-Version aufbewahren (eine) und Fortschritt beim Zwift-Update (docs/updates.md)."""

import io

import pytest

from tretlager.core import launch, paths, state, wine


@pytest.fixture
def fake_wine(tmp_path, monkeypatch):
    """Mitgeliefertes Wine unter tmp/app/wine; Version per Datei umschaltbar."""
    bundled = tmp_path / "app" / "wine"
    (bundled / "bin").mkdir(parents=True)
    (bundled / "bin" / "wine").write_text("#!/bin/sh\ncat \"$(dirname \"$0\")/v\"\n")
    (bundled / "bin" / "wine").chmod(0o755)
    monkeypatch.setattr(wine, "BUNDLED", bundled)
    monkeypatch.setattr(wine, "KEPT", tmp_path / "data" / "wine-bewaehrt")
    monkeypatch.setattr(paths, "STATE", tmp_path / "state")

    def set_version(v):
        (bundled / "bin" / "v").write_text(v + "\n")
        wine.bundled_version.cache_clear()
    set_version("wine-11.20")
    yield set_version
    wine.bundled_version.cache_clear()


def test_first_good_ride_keeps_a_copy(fake_wine):
    assert wine.record_ride(60) == ""  # zu kurz
    assert wine.record_ride(600) == "wine-11.20"
    assert wine.kept_version() == "wine-11.20" and (wine.KEPT / "bin" / "wine").exists()
    assert wine.record_ride(600) == ""  # schon aufbewahrt


def test_new_wine_replaces_copy_only_after_two_rides(fake_wine):
    wine.record_ride(600)
    fake_wine("wine-11.21")  # Tretlager-Update
    assert wine.record_ride(600) == "" and wine.kept_version() == "wine-11.20"
    assert wine.record_ride(600) == "wine-11.21" and wine.kept_version() == "wine-11.21"


def test_use_kept_switches_path_and_resets_after_next_update(fake_wine):
    wine.record_ride(600)
    fake_wine("wine-11.21")
    wine.set_use_kept(True)
    assert wine.use_kept() and str(wine.bin_dir()).endswith("wine-bewaehrt/bin")
    assert wine.env_path("/usr/bin").startswith(str(wine.KEPT / "bin"))
    assert wine.record_ride(600) == ""  # Fahrten mit der alten Version zählen nicht fürs neue Wine
    assert not wine.check_after_update()  # gleiches mitgeliefertes Wine: Wahl bleibt
    fake_wine("wine-11.22")
    assert wine.check_after_update() and not wine.use_kept()
    assert str(wine.bin_dir()) == str(wine.BUNDLED / "bin")


def test_use_kept_ignored_without_copy(fake_wine):
    state.update("wine", use_kept=True)
    assert not wine.use_kept()


MANIFEST = """<Zwift version="1.0.2" folder="Zwift_1.0.2_ab">
<files>
<file><path>ZwiftApp.exe</path><length>100</length></file>
<file><path>data\\\\worlds.wad</path><length>300</length></file>
<file><path>same.dll</path><length>50</length></file>
</files></Zwift>"""


def test_update_progress_from_manifest(tmp_path):
    z = tmp_path / "Zwift"
    (z / "data").mkdir(parents=True)
    (z / "ZwiftApp.exe").write_bytes(b"x" * 90)  # alte, andere Größe
    (z / "same.dll").write_bytes(b"x" * 50)  # unverändert

    def opener(req, timeout=0):
        url = req.full_url
        body = MANIFEST if url.endswith("manifest.xml") else '<Zwift sversion="1.2" manifest="Zwift_1.0.2_ab_manifest.xml"/>'
        return io.BytesIO(body.encode())
    p = launch.UpdateProgress(opener, z)
    assert p.total == 400 and p.percent() == 0
    (z / "ZwiftApp.exe").write_bytes(b"x" * 100)
    assert p.percent() == 25
    (z / "data" / "worlds.wad").write_bytes(b"x" * 300)
    assert p.percent() == 99  # 100 % erst, wenn die Versionsdatei wechselt


def test_update_progress_unknown_without_manifest(tmp_path):
    def offline(*_a, **_kw):
        raise OSError("offline")
    assert launch.UpdateProgress(offline, tmp_path).percent() == -1


def test_first_install_progress_from_manifest(tmp_path, monkeypatch):
    """Erstinstallation: Fortschritt aus dem Manifest statt geschätzter 4,9 GB."""
    from tretlager.core import manifest, setup
    z = tmp_path / "Zwift"
    z.mkdir()
    monkeypatch.setattr(paths, "ZWIFT_DIR", z)
    monkeypatch.setattr(setup.subprocess, "Popen", lambda *a, **kw: None)
    monkeypatch.setattr(setup.Context, "wineserver_kill", lambda self: None)
    missing = [(z / "a.wad", 100), (z / "ZwiftApp.exe", 300)]
    monkeypatch.setattr(manifest, "UpdateProgress",
                        lambda: type("P", (), {"missing": missing, "total": 400,
                                               "loaded": lambda self: manifest.loaded_bytes(missing)})())
    steps = iter([lambda: (z / "a.wad").write_bytes(b"x" * 100),
                  lambda: (z / "ZwiftApp.exe").write_bytes(b"x" * 300),
                  lambda: ((z / "Zwift_ver_cur_filename.txt").write_text("v.xml"),
                           (z / "v.xml").write_text('<Zwift sversion="1.2"/>'))])
    clock = [0.0]

    def fake_sleep(s):
        clock[0] += s
        next(steps, lambda: None)()
    monkeypatch.setattr(setup.time, "sleep", fake_sleep)
    monkeypatch.setattr(setup.time, "monotonic", lambda: clock[0])
    seen = []
    ctx = setup.Context(progress=lambda step, pct, text: seen.append((round(pct), text)))
    setup.Game().run(ctx)
    assert seen[0][0] == 25 and seen[1][0] == 99  # 100 % erst mit der Versionsdatei
    assert all("etwa" not in text for _pct, text in seen)  # keine Schätzung, das Manifest kennt die Größe


def test_update_progress_counts_launcher_staging(tmp_path):
    """Der Launcher lädt nach Temp\\Zwift\\Downloads und verschiebt erst am Ende (tinytin, 30.10.)."""
    prefix = tmp_path / "prefix"
    z = prefix / "drive_c" / "Program Files (x86)" / "Zwift"
    staging = prefix / "drive_c" / "users" / "testt" / "AppData" / "Local" / "Temp" / "Zwift" / "Downloads"
    z.mkdir(parents=True)
    staging.mkdir(parents=True)
    (staging / "rest-vom-letzten-mal").write_bytes(b"x" * 50)  # zählt nicht

    def opener(req, timeout=0):
        body = MANIFEST if req.full_url.endswith("manifest.xml") else '<Zwift manifest="Zwift_1.0.2_ab_manifest.xml"/>'
        return io.BytesIO(body.encode())
    p = launch.UpdateProgress(opener, z, prefix)
    assert p.total == 450 and p.percent() == 0
    (staging / "chunk").write_bytes(b"x" * 225)  # halb geladen, noch im Zwischenordner
    assert p.percent() == 50
    (staging / "chunk").unlink()  # verschoben: jetzt fertig im Zwift-Ordner
    (z / "ZwiftApp.exe").write_bytes(b"x" * 100)
    (z / "same.dll").write_bytes(b"x" * 50)
    assert round(p.percent()) == 33
