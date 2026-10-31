"""State file of the setup: ~/.local/state/tretlager/state.json.

Each step checks on the real system whether it is done. Only extra information is kept here:
installer check result, graphics path, versions, timestamps.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from . import paths


def _file() -> Path:
    return paths.STATE / "state.json"


def load() -> dict:
    try:
        return json.loads(_file().read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save(data: dict) -> None:
    f = _file()
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(f)


def update(section: str, **values) -> dict:
    data = load()
    data.setdefault(section, {}).update(values, updated=int(time.time()))
    save(data)
    return data
