"""Handler: respuesta por defecto cuando no hay match."""

from __future__ import annotations
from typing import List

from mensajeria.core.handler import BaseHandler
from mensajeria.core.message import IncomingMessage, OutgoingMessage
from mensajeria.handlers.info import MENU_LAYOUT


class FallbackHandler(BaseHandler):
    """Fallback — aplica a todos los modos."""

    def intent(self) -> str:
        return "fallback"

    async def handle(self, msg: IncomingMessage) -> List[OutgoingMessage]:
        return [OutgoingMessage(
            text="Decime si querés precios, disponibilidad, reservar o subir una foto.",
            chat_id=msg.chat_id,
            reply_markup=MENU_LAYOUT,
        )]
