import io
import json
import subprocess

import pytest

from tretlager.core import bridgectl, launch


def fake_run(stdout="", returncode=0, seen=None):
    def run(cmd, **_kw):
        if seen is not None:
            seen.append(cmd)
        return subprocess.CompletedProcess(cmd, returncode, stdout, "Fehler" if returncode else "")
    return run


def test_status_parses_busctl_json():
    payload = {"running": True, "devices": [{"name": "KICKR"}]}
    out = json.dumps({"type": "s", "data": [json.dumps(payload)]})
    assert bridgectl.status(run=fake_run(out)) == payload


def test_status_none_when_bridge_down():
    assert bridgectl.status(run=fake_run(returncode=1)) is None


def test_busctl_arguments_and_bool_formatting():
    seen = []
    bridgectl.set_device_enabled("AA:BB", False, run=fake_run(json.dumps({"type": "b", "data": [True]}), seen=seen))
    cmd = seen[0]
    assert cmd[:3] == ["busctl", "--user", "--json=short"]
    assert cmd[-4:] == ["SetDeviceEnabled", "sb", "AA:BB", "false"]


def test_scan_uses_long_timeout():
    seen = []
    bridgectl.scan(10, run=fake_run(json.dumps({"type": "s", "data": ["[]"]}), seen=seen))
    assert "--timeout=70" in seen[0]


def test_systemctl_errors_raise():
    with pytest.raises(bridgectl.BridgeError):
        bridgectl.set_running(True, run=fake_run(returncode=1))


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_remote_version():
    xml = b'<Zwift version="1.0.168000" sversion="1.125.0 (168000)" manifest="x"/>'
    assert launch.remote_version(lambda req, timeout=0: FakeResponse(xml)) == "1.125.0 (168000)"


def test_wine_tasks_parsing(monkeypatch):
    out = ("Abbildname                     PID Sitzungsname     Sitz.-Nr. Speichernutzung\n"
           "========================= ======== ================ =========== ============\n"
           "ZwiftLauncher.exe              344 Console                    1    440.116 K\n"
           "ZwiftApp.exe                   700 Console                    1  3.000.000 K\n")
    monkeypatch.setattr(launch.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 0, out, ""))
    assert launch.wine_tasks({}) == {"ZwiftLauncher.exe": 344, "ZwiftApp.exe": 700}


def test_kwin_script_targets_zwift_window():
    assert "zwiftapp.exe" in launch.KWIN_SCRIPT and "setMaximize(true, true)" in launch.KWIN_SCRIPT


def test_bundled_runfromprocess_source():
    assert "PROC_THREAD_ATTRIBUTE_PARENT_PROCESS" in launch.RFP_SRC.read_text()


def test_runfromprocess_expands_file_argument():
    src = launch.RFP_SRC.read_text()
    assert "ExpandFileArg" in src and '"=@"' in src


def test_start_never_puts_token_on_command_line():
    import inspect
    code = inspect.getsource(launch.Launcher.start)
    assert "--token=@" in code and "json.dumps(token)" in code
    call = code[code.index('"--token=@"'):]
    assert "stdout=subprocess.DEVNULL" in call[:400]  # Zwift erbt sonst die Pipe


def test_logout_remote_posts_refresh_token():
    from tretlager.core import login
    seen = []

    def opener(req, timeout=0):
        seen.append((req.full_url, req.data.decode()))
        return FakeResponse(b"")
    login.logout_remote({"refresh_token": "r1"}, opener)
    assert seen[0][0].endswith("/logout") and "refresh_token=r1" in seen[0][1]


def test_help_text_and_icon_are_bundled():
    from pathlib import Path
    data = Path(launch.__file__).resolve().parent.parent / "data"
    assert "## Sensoren in Zwift koppeln" in (data / "hilfe.md").read_text()
    assert (data / "icons" / "de.linuxundich.Tretlager.svg").read_text().startswith("<svg")


def test_desktop_files_offer_direct_start():
    from pathlib import Path
    root = Path(launch.__file__).resolve().parents[2] / "data"
    main = (root / "de.linuxundich.Tretlager.desktop.in").read_text()
    zwift = (root / "de.linuxundich.Tretlager.Zwift.desktop.in").read_text()
    assert "Actions=start;" in main and "--start" in main
    assert "--start" in zwift and "Icon=de.linuxundich.Tretlager" in zwift
