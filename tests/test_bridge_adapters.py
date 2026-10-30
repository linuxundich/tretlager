import pytest

pytest.importorskip("dbus_fast")

from tretlager.bridge import adapters
from tretlager.bridge.config import BridgeConfig


def test_resolve():
    found = {"hci0": "AA:AA:AA:AA:AA:AA", "hci1": "BB:BB:BB:BB:BB:BB"}
    assert adapters.resolve("", found) == ("", False)
    assert adapters.resolve("bb:bb:bb:bb:bb:bb", found) == ("hci1", False)
    assert adapters.resolve("CC:CC:CC:CC:CC:CC", found) == ("", True)


def test_config_keeps_adapter(tmp_path):
    path = tmp_path / "bridge.json"
    cfg = BridgeConfig(adapter="BB:BB:BB:BB:BB:BB")
    cfg.save(path)
    assert BridgeConfig.load(path).adapter == "BB:BB:BB:BB:BB:BB"
    path.write_text('{"devices": []}')
    assert BridgeConfig.load(path).adapter == ""
