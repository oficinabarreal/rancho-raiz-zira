"""Handler: respuesta de voz (TTS) — usa edge-tts como Zira."""

from __future__ import annotations
from typing import List

from mensajeria.core.handler import BaseHandler
from mensajeria.core.message import IncomingMessage, OutgoingMessage
from mensajeria.handlers.info import MENU_LAYOUT


TTS_AVAILABLE = False
try:
    import edge_tts  # noqa: F401
    TTS_AVAILABLE = True
except ImportError:
    pass


class ListenHandler(BaseHandler):
    """TTS — aplica a todos los modos."""

    def intent(self) -> str:
        return "listen"

    async def handle(self, msg: IncomingMessage) -> List[OutgoingMessage]:
        text = msg.text or "Hola, soy Zira. Preguntame lo que quieras sobre la posada."
        if not TTS_AVAILABLE:
            return [OutgoingMessage(
                text=f"🔊 Audio no disponible ahora (falta edge-tts).\n\n{text}",
                chat_id=msg.chat_id,
                reply_markup=MENU_LAYOUT,
            )]
        # El TTS se genera en el bot loop después del dispatch
        return [OutgoingMessage(
            text=text,
            chat_id=msg.chat_id,
            reply_markup=MENU_LAYOUT,
        )]
