import re
import sys
from pathlib import Path

from tretlager.core import prepare

ROOT = Path(__file__).resolve().parent.parent

SIM = """NOTE: This is only a simulation!
Inst libasound2-plugins (1.2.12-2.1 Debian:testing [amd64])
Inst wine-devel (11.20~forky-1 winehq:testing [amd64])
Inst winehq-devel (11.20~forky-1 winehq:testing [amd64])
Remv oldwine [1.0]
Conf wine-devel (11.20~forky-1 winehq:testing [amd64])
"""


def test_parse_simulation():
    pkgs = prepare.parse_simulation(SIM)
    assert [(p.name, p.version, p.origin) for p in pkgs] == [
        ("libasound2-plugins", "1.2.12-2.1", "Debian:testing"),
        ("wine-devel", "11.20~forky-1", "winehq:testing"),
        ("winehq-devel", "11.20~forky-1", "winehq:testing")]
    assert prepare.parse_removals(SIM) == ["oldwine"]


def test_parse_simulation_upgrade_line():
    pkgs = prepare.parse_simulation("Inst libfoo [1.0] (1.1 Debian:testing [amd64])\n")
    assert pkgs[0].name == "libfoo" and pkgs[0].version == "1.1"


def test_parse_sizes_first_version_only():
    show = "Package: a\nSize: 100\n\nPackage: a\nSize: 999\n\nPackage: b\nSize: 5\n"
    assert prepare.parse_sizes(show) == {"a": 100, "b": 5}


def test_plan_properties():
    plan = prepare.Plan(True, [prepare.Package("x", "1", "o", 10), prepare.Package("y", "2", "o", 5)])
    assert plan.download_bytes == 15 and not plan.nothing_to_do
    assert prepare.Plan(False).nothing_to_do
    assert not prepare.Plan(False, error="broken").nothing_to_do


def test_sources_text_amd64_only():
    text = prepare.sources_text("/k.key")
    assert "Architectures: amd64\n" in text and "Signed-By: /k.key" in text and "Suites: forky" in text


def test_bundled_key_file_exists():
    assert prepare.KEY_PATH.read_text().startswith("-----BEGIN PGP PUBLIC KEY BLOCK-----")


def test_helper_constants_match_core():
    helper = (ROOT / "helper/setup-system").read_text()
    for name in ("WINEHQ_FPR", "WINEHQ_URI", "WINEHQ_SUITE", "PACKAGES"):
        m = re.search(rf"^{name} = (.+)$", helper, re.M)
        assert m and eval(m.group(1)) == getattr(prepare, name), name  # noqa: S307


def test_helper_refuses_other_commands():
    import subprocess
    r = subprocess.run([sys.executable, "-I", str(ROOT / "helper/setup-system"), "rm", "-rf"],
                       capture_output=True, text=True)
    assert r.returncode == 1 and '"error"' in r.stdout


def test_run_helper_relays_events():
    events = []
    script = ("import json;print(json.dumps({'event':'step','text':'A'}));print('not json');"
              "print(json.dumps({'event':'done','text':'ok'}))")
    rc = prepare.run_helper(events.append, cmd=[sys.executable, "-c", script])
    assert rc == 0
    assert [e["event"] for e in events] == ["step", "log", "done"]


def test_run_helper_pkexec_denied():
    events = []
    rc = prepare.run_helper(events.append, cmd=[sys.executable, "-c", "import sys; sys.exit(126)"])
    assert rc == 126 and events[-1]["event"] == "error"


def test_winehq_source_detection(tmp_path):
    assert not prepare.winehq_source_present(tmp_path)
    (tmp_path / "other.sources").write_text(f"URIs: {prepare.WINEHQ_URI}\n")
    assert prepare.winehq_source_present(tmp_path)


def test_helper_fingerprint_of_bundled_key():
    import importlib.machinery
    import importlib.util
    loader = importlib.machinery.SourceFileLoader("setup_system", str(ROOT / "helper/setup-system"))
    spec = importlib.util.spec_from_loader("setup_system", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    assert mod.fingerprint(str(prepare.KEY_PATH)) == prepare.WINEHQ_FPR
