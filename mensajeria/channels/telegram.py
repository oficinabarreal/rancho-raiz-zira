"""Canal Telegram — hereda de Zira bot pero con la nueva arquitectura."""

from __future__ import annotations
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from mensajeria.core.message import IncomingMessage, OutgoingMessage
from mensajeria.channels.base import BaseChannel


class TelegramChannel(BaseChannel):
    """Canal Telegram usando Bot API (polling long-poll)."""

    def __init__(self, token: str, default_chat_id: int, state=None):
        self.token = token
        self.default_chat_id = default_chat_id
        self.state = state
        self._offset: Optional[int] = None
        self._media_dir = Path(__file__).resolve().parent.parent / "media"
        self._media_dir.mkdir(parents=True, exist_ok=True)

    def name(self) -> str:
        return "telegram"

    # --- API calls ---

    def _api(self, method: str, data: dict) -> dict:
        url = f"https://api.telegram.org/bot{self.token}/{method}"
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        if not payload.get("ok"):
            raise RuntimeError(f"Telegram API {method} failed: {payload}")
        return payload

    def _multipart(self, method: str, fields: dict, file_field: str, file_path: Path,
                   file_mime: str) -> dict:
        boundary = f"----ziramultipart{int(time.time())}"
        parts = []
        for key, value in fields.items():
            parts.append(f"--{boundary}\r\n".encode())
            parts.append(f'Content-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(f'Content-Disposition: form-data; name="{file_field}"; filename="{file_path.name}"\r\n'.encode())
        parts.append(f"Content-Type: {file_mime}\r\n\r\n".encode())
        parts.append(file_path.read_bytes())
        parts.append(f"\r\n--{boundary}--\r\n".encode())
        url = f"https://api.telegram.org/bot{self.token}/{method}"
        req = urllib.request.Request(
            url, data=b"".join(parts),
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        if not payload.get("ok"):
            raise RuntimeError(f"Telegram {method} failed: {payload}")
        return payload

    # --- receive ---

    async def poll_once(self) -> List[IncomingMessage]:
        if self._offset is None:
            if self.state:
                self._offset = self.state.load_offset("telegram")
            else:
                self._offset = 0

        params = {
            "limit": 25,
            "timeout": 20,
            "allowed_updates": json.dumps(["message", "callback_query"]),
        }
        if self._offset:
            params["offset"] = self._offset
        query = urllib.parse.urlencode(params)
        url = f"https://api.telegram.org/bot{self.token}/getUpdates?{query}"
        with urllib.request.urlopen(url, timeout=40) as resp:
            payload = json.loads(resp.read().decode("utf-8"))

        if not payload.get("ok"):
            return []
        updates = payload.get("result", [])
        if not isinstance(updates, list):
            return []

        messages = []
        for update in updates:
            if not isinstance(update, dict):
                continue
            update_id = int(update.get("update_id", 0))
            self._offset = max(self._offset or 0, update_id + 1)
            if self.state:
                self.state.save_offset("telegram", self._offset)

            msg = self._parse_update(update)
            if msg:
                messages.append(msg)
        return messages

    def _parse_update(self, update: dict) -> Optional[IncomingMessage]:
        """Convierte un update de Telegram en IncomingMessage."""
        # Callback query
        cq = update.get("callback_query")
        if isinstance(cq, dict):
            data = cq.get("data", "")
            msg_data = cq.get("message", {})
            chat = msg_data.get("chat", {})
            chat_id = chat.get("id", 0)
            if not isinstance(data, str) or not isinstance(chat_id, int):
                return None
            return IncomingMessage(
                text="",
                chat_id=chat_id,
                channel="telegram",
                callback_data=data,
                raw=cq,
            )

        # Regular message
        msg_data = update.get("message")
        if not isinstance(msg_data, dict):
            return None
        chat = msg_data.get("chat", {})
        chat_id = chat.get("id", 0)
        if not isinstance(chat_id, int):
            return None

        text = msg_data.get("text", "")
        if not isinstance(text, str):
            text = ""

        # Photos
        photos = msg_data.get("photo")
        has_photo = isinstance(photos, list) and len(photos) > 0
        photo_file_id = ""
        photo_caption = ""
        if has_photo:
            last_photo = photos[-1]
            if isinstance(last_photo, dict) and isinstance(last_photo.get("file_id"), str):
                photo_file_id = last_photo["file_id"]
                photo_caption = msg_data.get("caption") if isinstance(msg_data.get("caption"), str) else ""

        return IncomingMessage(
            text=text,
            chat_id=chat_id,
            user_id=msg_data.get("from", {}).get("id", 0),
            username=msg_data.get("from", {}).get("username", ""),
            channel="telegram",
            is_command=text.strip().startswith("/"),
            has_photo=has_photo,
            photo_file_id=photo_file_id,
            photo_caption=photo_caption,
            raw=msg_data,
        )

    # --- send ---

    async def send(self, msg: OutgoingMessage) -> bool:
        chat_id = msg.chat_id or self.default_chat_id
        try:
            if msg.audio_path:
                audio = Path(msg.audio_path)
                if audio.exists():
                    self._multipart("sendAudio", {
                        "chat_id": chat_id,
                        "caption": msg.audio_caption,
                    }, "audio", audio, "audio/mpeg")
                    return True
            if msg.photo_path:
                photo = Path(msg.photo_path)
                if photo.exists():
                    kb = json.dumps(msg.reply_markup, ensure_ascii=False) if msg.reply_markup else None
                    fields = {"chat_id": chat_id, "caption": msg.photo_caption}
                    if kb:
                        fields["reply_markup"] = kb
                    self._multipart("sendPhoto", fields, "photo", photo, "image/jpeg")
                    return True
            # Plain text
            payload: Dict[str, Any] = {"chat_id": chat_id, "text": msg.text}
            if msg.reply_markup:
                payload["reply_markup"] = msg.reply_markup
            self._api("sendMessage", payload)
            return True
        except Exception as e:
            print(f"[TelegramChannel] Error sending: {e}")
            return False

    def download_file(self, file_id: str) -> Optional[Path]:
        """Descarga un archivo de Telegram (foto, etc.) a media/."""
        try:
            meta = self._api("getFile", {"file_id": file_id})
            result = meta.get("result", {})
            if not isinstance(result, dict):
                return None
            file_path = result.get("file_path")
            if not isinstance(file_path, str):
                return None
            ext = Path(file_path).suffix or ".bin"
            target = self._media_dir / f"{int(time.time())}_{file_id[:8]}{ext}"
            url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"
            with urllib.request.urlopen(url, timeout=60) as resp:
                target.write_bytes(resp.read())
            return target
        except Exception as e:
            print(f"[TelegramChannel] Download error: {e}")
            return None

    def edit_reply_markup(self, chat_id: int, message_id: int, reply_markup: Optional[dict]) -> None:
        """Actualiza el teclado inline de un mensaje existente."""
        payload = {"chat_id": chat_id, "message_id": message_id}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        self._api("editMessageReplyMarkup", payload)
