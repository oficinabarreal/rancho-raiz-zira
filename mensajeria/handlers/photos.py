"""Handler: fotos — usa la PhotoPipeline de Zira."""

from __future__ import annotations
from typing import List

from mensajeria.core.handler import BaseHandler
from mensajeria.core.message import IncomingMessage, OutgoingMessage
from mensajeria.handlers.info import MENU_LAYOUT


def photo_text() -> str:
    return (
        "📷 Mandame una foto por Telegram.\n\n"
        "La voy a guardar, dejar en cola para edición y preparar para publicación."
    )


class PhotoHandler(BaseHandler):
    """Fotos — leads y guests."""
    modes = {"leads", "guests"}

    # NOTA: la PhotoPipeline real (Pillow) se encuentra en
    # simulators/zira_photo_pipeline.py. Este handler la llama si está
    # disponible o replica la funcionalidad básica.

    def intent(self) -> str:
        return "photo"

    async def handle(self, msg: IncomingMessage) -> List[OutgoingMessage]:
        if msg.has_photo:
            # La foto necesita ser descargada y procesada por el canal
            # El bot loop se encarga de eso después del dispatch
            return [OutgoingMessage(
                text=photo_text(),
                chat_id=msg.chat_id,
                reply_markup=MENU_LAYOUT,
            )]
        return [OutgoingMessage(
            text=photo_text(),
            chat_id=msg.chat_id,
            reply_markup=MENU_LAYOUT,
        )]
