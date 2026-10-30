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
