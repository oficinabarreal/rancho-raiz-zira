"""
Modos de operación de Zira.

Cada modo define qué handlers se activan, qué datos ve y desde qué
canales puede ser contactado.

Arquitectura:
  Modo = contexto de interacción.
  El router usa el modo activo para filtrar handlers.
  Los datos se cargan según el modo (particionados).
  El canal + identidad del usuario determinan el modo.
"""

from __future__ import annotations
from typing import Dict, Set, Optional

# ─── Definición de modos ──────────────────────────────────────────────

MODE_INFO: Dict[str, dict] = {
    "leads": {
        "label": "🎯 Prospectos",
        "description": "Precios, disponibilidad, fotos y reservas para potenciales huéspedes",
        "handlers": {"welcome", "faq", "prices", "availability", "reserve", "photo", "listen", "fallback", "mode"},
        "channels": {"telegram"},
    },
    "team": {
        "label": "👥 Equipo",
        "description": "Tareas, horarios y operaciones internas del equipo de trabajo",
        "handlers": {"welcome", "tasks", "schedule", "fallback", "mode"},
        "channels": {"telegram"},
    },
    "guests": {
        "label": "🏡 Huéspedes",
        "description": "Acompañamiento: check-in, servicios, asistencia durante la estadía",
        "handlers": {"welcome", "assist", "reserve", "faq", "photo", "fallback", "mode"},
        "channels": {"telegram", "whatsapp"},
    },
}

DEFAULT_MODE = "leads"

# ─── Canal → Modo (por defecto) ──────────────────────────────────────
# Para canales que sirven a múltiples modos, se necesita identidad del usuario
# para resolver el modo. Por ahora mapeo simple.

CHANNEL_MODE: Dict[str, str] = {
    "telegram": DEFAULT_MODE,    # se refina con identidad después
    "console": DEFAULT_MODE,
    "instagram": "leads",
    "whatsapp": "leads",
}

# ─── Forzar modo por chat_id (telegram) ──────────────────────────────
# Útil para fijar el modo del equipo o huéspedes conocidos.
# Se completa a medida que se identifican usuarios.

CHAT_ID_MODE: Dict[int, str] = {
    # Ej: 8272684219: "team"
    # Se completa cuando se identifican chats del equipo
}


def resolve_mode(channel: str, chat_id: Optional[int] = None, user_mode: Optional[str] = None) -> str:
    """Determina el modo activo para un usuario/canal.

    Orden de precedencia:
      1. user_mode (forzado por estado de conversación)
      2. CHAT_ID_MODE (identidad conocida)
      3. CHANNEL_MODE (default por canal)
      4. DEFAULT_MODE
    """
    if user_mode and user_mode in MODE_INFO:
        return user_mode

    if chat_id and chat_id in CHAT_ID_MODE:
        return CHAT_ID_MODE[chat_id]

    mode = CHANNEL_MODE.get(channel, DEFAULT_MODE)
    if mode in MODE_INFO:
        return mode

    return DEFAULT_MODE


def handlers_for_mode(mode: str) -> Set[str]:
    """Devuelve los intents (nombres de handler) que aplican a un modo."""
    info = MODE_INFO.get(mode)
    if info:
        return info["handlers"]
    return MODE_INFO[DEFAULT_MODE]["handlers"]


def set_chat_mode(chat_id: int, mode: str) -> None:
    """Fija el modo para un chat_id específico."""
    if mode in MODE_INFO:
        CHAT_ID_MODE[chat_id] = mode


def description(mode: str) -> str:
    info = MODE_INFO.get(mode)
    if info:
        return f"{info['label']}: {info['description']}"
    return f"Modo desconocido: {mode}"
