"""
Estado de conversación persistente (turns, leads, offsets, user modes).

Cada chat_id tiene un modo ("leads", "team", "guests") que se persiste
en users.json y determina qué handlers están activos para ese usuario.
"""

from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class ConversationState:
	"""Guarda turns, leads, offsets y modos de usuario en mensajeria/state/."""

	def __init__(self, data_dir: Optional[Union[str, Path]] = None):
		if data_dir is None:
			data_dir = Path(__file__).resolve().parent.parent / "state"
		self.data_dir = Path(data_dir)
		self.data_dir.mkdir(parents=True, exist_ok=True)

	# --- turns ---
	def record_turn(self, speaker: str, text: str, extra: Optional[dict] = None) -> None:
		path = self.data_dir / "turns.json"
		state = self._load(path, {"turns": []})
		entry = {
			"ts": datetime.now(timezone.utc).isoformat(),
			"speaker": speaker,
			"text": text,
		}
		if extra:
			entry.update(extra)
		state["turns"].append(entry)
		self._save(path, state)

	def recent_turns(self, n: int = 5) -> List[dict]:
		path = self.data_dir / "turns.json"
		state = self._load(path, {"turns": []})
		return state["turns"][-n:]

	# --- leads ---
	def record_lead(self, source: str, payload: dict) -> None:
		path = self.data_dir / "leads.json"
		leads = self._load(path, {"items": []})
		leads["items"].append({
			"ts": datetime.now(timezone.utc).isoformat(),
			"source": source,
			"payload": payload,
		})
		self._save(path, leads)

	# --- offset ---
	def load_offset(self, channel: str, default: int = 0) -> int:
		path = self.data_dir / f"{channel}_offset.txt"
		try:
			return int(path.read_text(encoding="utf-8").strip())
		except Exception:
			return default

	def save_offset(self, channel: str, offset: int) -> None:
		path = self.data_dir / f"{channel}_offset.txt"
		path.write_text(f"{int(offset)}\n", encoding="utf-8")

	# --- user mode (chat_id -> modo) ---
	def get_user_mode(self, chat_id: int, default: str = "leads") -> str:
		"""Obtiene el modo persistido para un chat_id."""
		users = self._load(self.data_dir / "users.json", {})
		chat_key = str(chat_id)
		if chat_key in users:
			return users[chat_key].get("mode", default)
		return default

	def set_user_mode(self, chat_id: int, mode: str) -> None:
		"""Persiste el modo para un chat_id."""
		path = self.data_dir / "users.json"
		users = self._load(path, {})
		chat_key = str(chat_id)
		if chat_key not in users:
			users[chat_key] = {}
		users[chat_key]["mode"] = mode
		users[chat_key]["updated_at"] = datetime.now(timezone.utc).isoformat()
		self._save(path, users)

	def register_user(self, chat_id: int, username: str = "", mode: str = "leads") -> None:
		"""Registra un usuario si no existe."""
		path = self.data_dir / "users.json"
		users = self._load(path, {})
		chat_key = str(chat_id)
		if chat_key not in users:
			users[chat_key] = {
				"chat_id": chat_id,
				"username": username,
				"mode": mode,
				"first_seen": datetime.now(timezone.utc).isoformat(),
				"updated_at": datetime.now(timezone.utc).isoformat(),
			}
			self._save(path, users)

	def all_users(self) -> dict:
		"""Devuelve todos los usuarios registrados."""
		return self._load(self.data_dir / "users.json", {})

	# --- helpers ---
	def _load(self, path: Path, default: Any) -> Any:
		if not path.exists():
			return default
		try:
			return json.loads(path.read_text(encoding="utf-8"))
		except Exception:
			return default

	def _save(self, path: Path, data: Any) -> None:
		path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
