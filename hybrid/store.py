from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


BASE = Path(__file__).resolve().parent / "crm_state"
BASE.mkdir(parents=True, exist_ok=True)


def _path(name: str) -> Path:
    return BASE / name


def read(name: str, default: Any = None) -> Any:
    p = _path(name)
    if not p.exists():
        return default if default is not None else ([] if name.endswith("s.json") else {})
    return json.loads(p.read_text())


def write(name: str, data: Any):
    _path(name).write_text(json.dumps(data, indent=2, ensure_ascii=False))


def append(name: str, item: Any):
    items = read(name, [])
    items.append(item)
    write(name, items)


def update(name: str, key: str, value: Any):
    data = read(name, {})
    data[key] = value
    write(name, data)
