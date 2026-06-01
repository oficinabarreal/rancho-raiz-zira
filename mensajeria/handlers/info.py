"""Handler: menú de bienvenida / comandos básicos."""

from __future__ import annotations
from typing import List

from mensajeria.core.handler import BaseHandler
from mensajeria.core.message import IncomingMessage, OutgoingMessage

MENU_LAYOUT = {
    "inline_keyboard": [
        [
            {"text": "📋 Info posada", "callback_data": "zira:faq:about"},
            {"text": "📍 Ubicación", "callback_data": "zira:faq:location"},
        ],
        [
            {"text": "🛏️ Qué incluye", "callback_data": "zira:faq:amenities"},
            {"text": "💰 Precios", "callback_data": "zira:prices"},
        ],
        [
            {"text": "📅 Disponibilidad", "callback_data": "zira:availability"},
            {"text": "✅ Reservar", "callback_data": "zira:reserve"},
            {"text": "📷 Subir foto", "callback_data": "zira:photo"},
        ],
        [
            {"text": "🔊 Escuchar", "callback_data": "zira:listen"},
        ],
    ]
}


def welcome_text() -> str:
    return (
        "🏡 Hola, soy Zira.\n\n"
        "Puedo ayudarte con la posada en Barreal, Calingasta, San Juan, "
        "al pie de la Cordillera de los Andes.\n\n"
        "Usá los botones o escribime tu consulta."
    )


class WelcomeHandler(BaseHandler):
    """Menú de bienvenida — aplica a todos los modos."""

    def intent(self) -> str:
        return "welcome"

    async def handle(self, msg: IncomingMessage) -> List[OutgoingMessage]:
        return [OutgoingMessage(
            text=welcome_text(),
            chat_id=msg.chat_id,
            reply_markup=MENU_LAYOUT,
        )]
