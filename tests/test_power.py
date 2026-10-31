import subprocess

from tretlager.core import power


def _supply(root, name, kind, online=None):
    d = root / name
    d.mkdir()
    (d / "type").write_text(kind + "\n")
    if online is not None:
        (d / "online").write_text(online + "\n")


def test_on_ac(tmp_path):
    _supply(tmp_path, "AC0", "Mains", "1")
    _supply(tmp_path, "BAT0", "Battery")
    assert power.on_ac(tmp_path) is True
    (tmp_path / "AC0" / "online").write_text("0\n")
    assert power.on_ac(tmp_path) is False


def test_on_ac_without_mains(tmp_path):
    _supply(tmp_path, "BAT0", "Battery")
    assert power.on_ac(tmp_path) is None


def test_nvidia_xids_parses_journal():
    out = ("NVRM: GPU at PCI:0000:01:00: GPU-22e7\n"
           "NVRM: Xid (PCI:0000:01:00): 69, pid=364001, name=main, Class Error: channel 0x00000004\n"
           "NVRM: Xid (PCI:0000:01:00): 69, pid=364001, name=main, Class Error: channel 0x00000005\n"
           "NVRM: Xid (PCI:0000:01:00): 13, pid=1, name=x\n")

    def run(cmd, **kw):
        assert "--since" in cmd
        return subprocess.CompletedProcess(cmd, 0, stdout=out)
    codes = power.nvidia_xids(1000, run=run)
    assert codes == [69, 69, 13]
    assert power.describe_xids(codes) == "Xid 13, Xid 69 (2×)"


def test_nvidia_xids_without_journal():
    def run(cmd, **kw):
        raise OSError("no journalctl")
    assert power.nvidia_xids(0, run=run) == []


def test_notify_calls_gdbus(monkeypatch):
    monkeypatch.setattr(power.shutil, "which", lambda name: "/usr/bin/gdbus")
    calls = []
    power.notify("Titel", "Text", run=lambda cmd, **kw: calls.append(cmd))
    assert calls and calls[0][0] == "gdbus" and "Titel" in calls[0]
