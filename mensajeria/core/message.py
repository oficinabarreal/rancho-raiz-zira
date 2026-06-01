"""Mensaje normalizado entre canales y handlers."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class IncomingMessage:
    """Mensaje entrante normalizado, sin importar el canal de origen."""
    text: str = ""
    chat_id: int = 0
    user_id: int = 0
    username: str = ""
    channel: str = "unknown"       # "telegram", "console", etc.
    raw: dict = field(default_factory=dict)  # payload original del canal
    is_command: bool = False        # /start, /menu, etc.
    has_photo: bool = False
    photo_file_id: str = ""         # file_id para Telegram
    photo_caption: str = ""
    callback_data: str = ""         # para inline keyboards
    mode: str = ""                  # modo activo: "leads", "team", "guests"
    mode_suggested: str = ""        # modo sugerido por router (si había cambio)


@dataclass
class OutgoingMessage:
    """Respuesta a enviar por un canal."""
    text: str = ""
    chat_id: int = 0
    reply_markup: Optional[dict] = None
    photo_path: Optional[str] = None
    photo_caption: str = ""
    audio_path: Optional[str] = None
    audio_caption: str = ""


@dataclass
class IntentResult:
    """Resultado del clasificador de intents."""
    intent: str = "fallback"
    confidence: float = 0.0
    data: dict = field(default_factory=dict)
