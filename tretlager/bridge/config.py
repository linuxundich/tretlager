"""Gespeicherte Geräte der Bridge: ~/.config/tretlager/bridge.json."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

BASE_PORT = 36866


def config_path() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "tretlager" / "bridge.json"


@dataclass
class DeviceConfig:
    address: str  # BLE-Adresse, z. B. CE:E7:78:71:FE:2E
    name: str  # Name des BLE-Geräts
    role: str  # trainer, power, cadence, heartrate, other
    port: int  # DIRCON-Port dieses Geräts
    enabled: bool = True


@dataclass
class BridgeConfig:
    devices: list[DeviceConfig] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path | None = None) -> "BridgeConfig":
        path = path or config_path()
        try:
            raw = json.loads(path.read_text())
        except FileNotFoundError:
            return cls()
        return cls(devices=[DeviceConfig(**d) for d in raw.get("devices", [])])

    def save(self, path: Path | None = None) -> None:
        path = path or config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"devices": [asdict(d) for d in self.devices]}, indent=2) + "\n")
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
