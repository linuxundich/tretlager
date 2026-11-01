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


def gdbus_run(responses, seen=None):
    """Answers depending on the method: NameHasOwner, GetStatus etc."""
    def run(cmd, **_kw):
        if seen is not None:
            seen.append(cmd)
        method = cmd[cmd.index("--method") + 1].rsplit(".", 1)[-1]
        out, rc = responses.get(method, ("", 1))
        return subprocess.CompletedProcess(cmd, rc, out, "" if rc == 0 else "Fehler")
    return run


def test_status_parses_gdbus_string():
    payload = {"running": True, "devices": [{"name": "KICKR „Fe2E“ \'x\'", "on": True}]}
    text = json.dumps(payload, ensure_ascii=False)
    gv = "(" + repr(text) + ",)"  # the GVariant text of a string matches a Python literal
    run = gdbus_run({"NameHasOwner": ("(true,)", 0), "GetStatus": (gv, 0)})
    assert bridgectl.status(run=run) == payload


def test_status_none_when_bridge_down():
    assert bridgectl.status(run=gdbus_run({"NameHasOwner": ("(false,)", 0)})) is None


def test_gdbus_arguments_and_formatting():
    seen = []
    bridgectl.set_device_enabled("AA:BB", False, run=gdbus_run({"SetDeviceEnabled": ("(true,)", 0)}, seen))
    cmd = seen[0]
    assert cmd[:3] == ["gdbus", "call", "--session"]
    assert cmd[-3:] == ["de.linuxundich.Tretlager.Bridge.SetDeviceEnabled", "'AA:BB'", "false"]


def test_scan_uses_long_timeout_and_uint():
    seen = []
    bridgectl.scan(10, run=gdbus_run({"Scan": ("('[]',)", 0)}, seen))
    assert "--timeout=70" in seen[0] and seen[0][-1] == "uint32 10"


def test_set_running_activates_over_dbus():
    seen = []
    run = gdbus_run({"NameHasOwner": ("(false,)", 0), "StartServiceByName": ("(uint32 1,)", 0)}, seen)
    bridgectl.set_running(True, run=run, popen=lambda *a, **k: pytest.fail("no process expected"))
    assert any("org.freedesktop.DBus.StartServiceByName" in c for c in seen)


def test_set_running_falls_back_to_process(monkeypatch):
    monkeypatch.setattr(bridgectl, "IN_FLATPAK", False)
    started = []
    run = gdbus_run({"NameHasOwner": ("(false,)", 0)})
    bridgectl.set_running(True, run=run, popen=lambda cmd, **k: started.append((cmd, k)))
    assert started and started[0][0][-2:] == ["-m", "tretlager.bridge"] and started[0][1]["start_new_session"]


def test_set_running_off_calls_quit():
    seen = []
    bridgectl.set_running(False, run=gdbus_run({"NameHasOwner": ("(true,)", 0), "Quit": ("(true,)", 0)}, seen))
    assert any("de.linuxundich.Tretlager.Bridge.Quit" in c for c in seen)


def test_autostart_remembered(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    import importlib
    from tretlager.core import paths, state
    importlib.reload(paths); importlib.reload(state)
    monkeypatch.setattr(bridgectl, "state", state)
    monkeypatch.setattr(bridgectl, "IN_FLATPAK", False)
    bridgectl.set_autostart(True)
    assert bridgectl.autostart() is True


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_remote_version():
    xml = b'<Zwift version="1.0.168000" sversion="1.125.0 (168000)" manifest="x"/>'
    assert launch.remote_version(lambda req, timeout=0: FakeResponse(xml)) == "1.125.0 (168000)"


def test_wine_tasks_parsing(monkeypatch):
    out = ("Image Name                     PID Session Name        Session#    Mem Usage\n"
           "========================= ======== ================ =========== ============\n"
           "ZwiftLauncher.exe              344 Console                    1    440,116 K\n"
           "ZwiftApp.exe                   700 Console                    1  3,000,000 K\n")
    monkeypatch.setattr(launch.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 0, out, ""))
    assert launch.wine_tasks({}) == {"ZwiftLauncher.exe": 344, "ZwiftApp.exe": 700}


def test_kwin_script_targets_zwift_window():
    script = launch.maximize_script(None)
    assert "zwiftapp.exe" in script and "setMaximize(true, true)" in script
    assert "s.name === null" in script  # no remembered monitor: maximise where the window is


def test_kwin_script_moves_before_maximising():
    script = launch.maximize_script('HDMI-A-1"')
    assert 's.name === "HDMI-A-1\\""' in script  # quoted for JavaScript
    move, maximise = script.index("sendClientToScreen"), script.index("setMaximize")
    assert move < maximise and "} else {" in script[move:maximise]


def test_watch_script_reports_output_to_tretlager():
    assert f'callDBus("{launch.WINDOW_BUS_NAME}", "{launch.WINDOW_OBJECT_PATH}"' in launch.WATCH_SCRIPT
    assert "outputChanged" in launch.WATCH_SCRIPT and "windowAdded" in launch.WATCH_SCRIPT


def test_remembered_output_goes_into_the_script(monkeypatch):
    seen = {}
    monkeypatch.setattr(launch.state, "load", lambda: {"window": {"output": "HDMI-A-1"}})
    monkeypatch.setattr(launch, "run_kwin_script", lambda name, src, log, keep=False: seen.setdefault("src", src))
    launch.maximize_window_kde(print)
    assert '"HDMI-A-1"' in seen["src"]


def test_scripts_do_nothing_outside_kde(monkeypatch):
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "GNOME")
    assert launch.run_kwin_script("x", "", print) is False


def test_bundled_runfromprocess_source():
    assert "PROC_THREAD_ATTRIBUTE_PARENT_PROCESS" in launch.RFP_SRC.read_text()


def test_runfromprocess_expands_file_argument():
    src = launch.RFP_SRC.read_text()
    assert "ExpandFileArg" in src and '"=@"' in src


def test_start_never_puts_token_on_command_line():
    import inspect
    code = inspect.getsource(launch.Launcher._start)
    assert "--token=@" in code and "json.dumps(token)" in code
    call = code[code.index('"--token=@"'):][:400]
    # Output goes to the log file, never into a pipe (otherwise Zwift inherits it).
    assert "stdout=wine_log" in call and "PIPE" not in call and "capture_output" not in call


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
    assert "## Sensors" in (data / "help.md").read_text()
    assert (data / "icons" / "de.linuxundich.Tretlager.svg").read_text().startswith("<svg")


def test_desktop_files_offer_direct_start():
    from pathlib import Path
    root = Path(launch.__file__).resolve().parents[2] / "data"
    main = (root / "de.linuxundich.Tretlager.desktop.in").read_text()
    zwift = (root / "de.linuxundich.Tretlager.Zwift.desktop.in").read_text()
    assert "Actions=start;" in main and "--start" in main
    assert "--start" in zwift and "Icon=de.linuxundich.Tretlager" in zwift


def test_kwin_script_dir_visible_from_host(monkeypatch, tmp_path):
    from tretlager.core import launch
    monkeypatch.delenv("FLATPAK_ID", raising=False)
    assert launch._host_visible_tmpdir() is None
    monkeypatch.setenv("FLATPAK_ID", "de.linuxundich.Tretlager")
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    assert launch._host_visible_tmpdir() == str(tmp_path / "app" / "de.linuxundich.Tretlager")


def test_wine_log_env_defaults_to_errors(monkeypatch):
    from tretlager.core import launch
    monkeypatch.delenv("TRETLAGER_WINE_DEBUG", raising=False)
    env = launch.wine_log_env({"WINEDEBUG": "-all", "WINEPREFIX": "/p"})
    assert env == {"WINEDEBUG": "-all,err+all", "WINEPREFIX": "/p"}


def test_wine_log_env_override(monkeypatch):
    from tretlager.core import launch
    monkeypatch.setenv("TRETLAGER_WINE_DEBUG", "-all,err+all,+seh")
    assert launch.wine_log_env({"WINEDEBUG": "-all"})["WINEDEBUG"] == "-all,err+all,+seh"
