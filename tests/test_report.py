import zipfile

from tretlager.core import debug, launch, report


def test_scrub_masks_secrets():
    jwt = "eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.c2lnbmF0dXJlMTIzNDU2"
    text = (f'Authorization: Bearer abc123 x={jwt} {{"access_token": "secret1", "refresh_token": "r"}} '
            "ZwiftApp.exe --token=@Z:\\run\\t.json password=hunter2 mail me@example.com")
    out = report.scrub(text)
    for secret in (jwt, "abc123", "secret1", '"r"', "hunter2", "me@example.com", "@Z:"):
        assert secret not in out
    assert "ZwiftApp.exe --token=[removed]" in out and "[e-mail]" in out


def test_scrub_keeps_ordinary_log_lines():
    for line in ("[19:46:22] resize: 2870 x 1749 Wahoo KICKR FE2E._wahoo-fitness-tnp._tcp.local. port 36866",
                 "org.freedesktop.secrets=talk"):
        assert report.scrub(line) == line


def test_collect_files_finds_logs(tmp_path):
    state = tmp_path / "state"
    state.mkdir()
    (state / "tretlager.log").write_text("start\n")
    (state / "zwift-wine.log").write_text("err\n")
    logs = tmp_path / "prefix/drive_c/users/me/AppData/Local/Zwift/Logs"
    logs.mkdir(parents=True)
    (logs / "Log.txt").write_text("[1] Log Time\n")
    (logs / "Log (old 1).txt").write_text("[1] old\n")
    files = report.collect_files(tmp_path / "prefix", state, tmp_path / "missing.json")
    assert set(files) == {"tretlager/tretlager.log", "tretlager/zwift-wine.log", "zwift/Log.txt", "zwift/Log (old 1).txt"}


def test_build_writes_scrubbed_zip(tmp_path):
    log = tmp_path / "Log.txt"
    log.write_text("token eyJaaaaaaaaaa.bbbbbbbbbbbb.cccccccccccc end\n")
    dest = tmp_path / "r.zip"
    names = report.build(dest, files={"zwift/Log.txt": log}, summary="Version: 1\n")
    assert names == ["report.txt", "zwift/Log.txt"]
    with zipfile.ZipFile(dest) as z:
        assert z.read("zwift/Log.txt").decode() == "token [token] end\n"
        assert z.read("report.txt").decode() == "Version: 1\n"


def test_large_logs_keep_head_and_tail(tmp_path, monkeypatch):
    monkeypatch.setattr(report, "MAX_BYTES", 100)
    monkeypatch.setattr(report, "HEAD_BYTES", 20)
    f = tmp_path / "big.log"
    f.write_text("H" * 20 + "x" * 500 + "T" * 80)
    text = report._read(f)
    assert text.startswith("H" * 20) and text.endswith("T" * 80) and "left out" in text


def test_default_name():
    assert report.default_name(0).startswith("tretlager-report-1970-01-01-")


def test_debug_mode_logs_wine_exceptions(monkeypatch):
    monkeypatch.delenv("TRETLAGER_WINE_DEBUG", raising=False)
    monkeypatch.setenv(debug.ENV, "1")
    assert launch.wine_log_env({})["WINEDEBUG"] == debug.WINE_CHANNELS
