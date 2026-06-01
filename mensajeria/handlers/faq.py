"""Handler: FAQ (info posada, ubicación, amenities, etc.)"""

from __future__ import annotations
from typing import List

from mensajeria.core.handler import BaseHandler
from mensajeria.core.message import IncomingMessage, OutgoingMessage
from mensajeria.handlers.info import MENU_LAYOUT


def about_text() -> str:
    return (
        "🏡 Sobre la posada\n\n"
        "Estamos en Barreal, Calingasta, San Juan, al pie de la Cordillera de los Andes.\n\n"
        "La casa es para descansar, mirar la montaña y trabajar con tranquilidad.\n"
        "Puedo pasar más fotos, precios y disponibilidad cuando quieras."
    )


def location_text() -> str:
    return (
        "📍 Ubicación\n\n"
        "La posada está en Barreal, Calingasta, San Juan.\n"
        "Es una zona de cordillera, con paisaje abierto y mucho cielo limpio.\n\n"
        "Si querés, también te paso cómo llegar y un mapa de referencia."
    )


def amenities_text() -> str:
    return (
        "🛏️ Qué incluye\n\n"
        "• living-comedor\n"
        "• cocina equipada\n"
        "• baño completo\n"
        "• habitación principal\n"
        "• WiFi\n"
        "• pileta\n"
        "• galería\n"
        "• parrillero\n\n"
        "Capacidad: 1 a 5 personas."
    )


FAQ_TEXTS = {
    "about": about_text,
    "location": location_text,
    "amenities": amenities_text,
}


class FaqHandler(BaseHandler):
    """FAQ — leads y guests."""
    modes = {"leads", "guests"}

    def intent(self) -> str:
        return "faq"

    async def handle(self, msg: IncomingMessage) -> List[OutgoingMessage]:
        key = msg.callback_data.split("zira:faq:", 1)[1] if msg.callback_data else ""
        # Si no viene por callback, intentar clasificar por texto
        if not key:
            key = self._classify_faq(msg.text)
        text_fn = FAQ_TEXTS.get(key, about_text)
        return [OutgoingMessage(
            text=text_fn(),
            chat_id=msg.chat_id,
            reply_markup=MENU_LAYOUT,
        )]

    def _classify_faq(self, text: str) -> str:
        t = text.lower().strip()
        if any(token in t for token in ["ubicacion", "ubicación", "donde", "dónde", "mapa", "llegar"]):
            return "location"
        if any(token in t for token in ["incluye", "servicios", "comodidades", "wifi", "pileta"]):
            return "amenities"
        return "about"
