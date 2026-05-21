from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .models import Lead, PhotoAsset, CRMEvent


class CRMStore:
    def __init__(self, root: Path | str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._leads_path = self.root / "leads.json"
        self._events_path = self.root / "events.json"
        self._assets_path = self.root / "assets.json"

    def _load(self, path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default

    def _save(self, path: Path, data: Any) -> None:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def list_leads(self) -> List[Dict[str, Any]]:
        data = self._load(self._leads_path, {"items": []})
        return list(data.get("items", []))

    def upsert_lead(self, lead: Lead) -> None:
        data = self._load(self._leads_path, {"items": []})
        items = list(data.get("items", []))
        items = [item for item in items if item.get("lead_id") != lead.lead_id]
        items.append(lead.to_dict())
        self._save(self._leads_path, {"items": items})

    def record_event(self, event: CRMEvent) -> None:
        data = self._load(self._events_path, {"items": []})
        items = list(data.get("items", []))
        items.append(asdict(event))
        self._save(self._events_path, {"items": items})

    def list_assets(self) -> List[Dict[str, Any]]:
        data = self._load(self._assets_path, {"items": []})
        return list(data.get("items", []))

    def upsert_asset(self, asset: PhotoAsset) -> None:
        data = self._load(self._assets_path, {"items": []})
        items = list(data.get("items", []))
        items = [item for item in items if item.get("asset_id") != asset.asset_id]
        items.append(asdict(asset))
        self._save(self._assets_path, {"items": items})

