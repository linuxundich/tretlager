"""Devices saved by the bridge: ~/.config/tretlager/bridge.json."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

BASE_PORT = 36866

log = logging.getLogger(__name__)


def config_path() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "tretlager" / "bridge.json"


@dataclass
class DeviceConfig:
    address: str  # BLE address, e.g. CE:E7:78:71:FE:2E
    name: str  # name of the BLE device
    role: str  # trainer, power, cadence, heartrate, other
    port: int  # DIRCON port of this device
    enabled: bool = True


@dataclass
class BridgeConfig:
    devices: list[DeviceConfig] = field(default_factory=list)
    # True: only for Zwift on this computer (announced on 127.0.0.1, survives network changes).
    # False: also for Zwift on other devices in the network (Apple TV, iPad, second computer).
    local_only: bool = True
    # Address of the Bluetooth adapter (e.g. a USB dongle); empty = BlueZ default adapter.
    adapter: str = ""

    @classmethod
    def load(cls, path: Path | None = None) -> "BridgeConfig":
        path = path or config_path()
        try:
            raw = json.loads(path.read_text())
            fields = set(DeviceConfig.__dataclass_fields__)
            return cls(devices=[DeviceConfig(**{k: v for k, v in d.items() if k in fields})
                                for d in raw.get("devices", [])],
                       local_only=raw.get("local_only", True), adapter=raw.get("adapter", ""))
        except FileNotFoundError:
            return cls()
        except (OSError, ValueError, TypeError, AttributeError) as e:
            # Broken file (interrupted write, manual edit): without this path the bridge would not
            # start at all. Move the file aside so nothing is lost, and start empty.
            backup = path.with_suffix(".broken")
            try:
                path.replace(backup)
            except OSError:
                pass
            log.error("%s unreadable (%s), saved as %s", path, e, backup.name)
            return cls()

    def save(self, path: Path | None = None) -> None:
        path = path or config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"local_only": self.local_only, "adapter": self.adapter,
                                   "devices": [asdict(d) for d in self.devices]}, indent=2) + "\n")
        tmp.replace(path)

    def find(self, address: str) -> DeviceConfig | None:
        address = address.upper()
        return next((d for d in self.devices if d.address == address), None)

    def free_port(self) -> int:
        used = {d.port for d in self.devices}
        port = BASE_PORT
        while port in used:
            port += 1
        return port

    def add(self, address: str, name: str, role: str) -> DeviceConfig:
        existing = self.find(address)
        if existing:
            return existing
        dev = DeviceConfig(address=address.upper(), name=name, role=role, port=self.free_port())
        self.devices.append(dev)
        return dev

    def remove(self, address: str) -> bool:
        dev = self.find(address)
        if dev:
            self.devices.remove(dev)
        return dev is not None
