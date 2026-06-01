"""Handler: precios, disponibilidad y reservas."""

from __future__ import annotations
from typing import List

from mensajeria.core.handler import BaseHandler
from mensajeria.core.message import IncomingMessage, OutgoingMessage
from mensajeria.handlers.info import MENU_LAYOUT


def prices_text() -> str:
    return (
        "💰 Tarifario 2026\n\n"
        "• 5 personas → $120.000 / noche\n"
        "• 4 personas → $115.000 / noche\n"
        "• 3 personas → $105.000 / noche\n"
        "• 2 personas → $95.000 / noche\n"
        "• 1 persona → $80.000 / noche\n\n"
        "No incluye desayuno.\n"
        "Para reservar, seña de 1 noche."
    )


def availability_text() -> str:
    return (
        "📅 Para consultar disponibilidad, decime:\n\n"
        "• fechas exactas\n"
        "• cantidad de personas\n\n"
        "Con eso te confirmo al toque."
    )


def reserve_text() -> str:
    return (
        "✅ Para reservar:\n\n"
        "1. Elegí fecha y cantidad de personas.\n"
        "2. Coordinamos la seña.\n"
        "3. Confirmamos la reserva.\n\n"
        "Si querés, también te paso el detalle por Telegram."
    )


class PricingHandler(BaseHandler):
    """Solo para prospectos (leads)."""
    modes = {"leads"}

    def intent(self) -> str:
        return "prices"

    async def handle(self, msg: IncomingMessage) -> List[OutgoingMessage]:
        return [OutgoingMessage(
            text=prices_text(),
            chat_id=msg.chat_id,
            reply_markup=MENU_LAYOUT,
        )]


class AvailabilityHandler(BaseHandler):
    """Disponibilidad — leads y guests."""
    modes = {"leads", "guests"}

    def intent(self) -> str:
        return "availability"

    async def handle(self, msg: IncomingMessage) -> List[OutgoingMessage]:
        return [OutgoingMessage(
            text=availability_text(),
            chat_id=msg.chat_id,
            reply_markup=MENU_LAYOUT,
        )]


class ReserveHandler(BaseHandler):
    """Reservas — leads y guests."""
    modes = {"leads", "guests"}

    def intent(self) -> str:
        return "reserve"

    async def handle(self, msg: IncomingMessage) -> List[OutgoingMessage]:
        return [OutgoingMessage(
            text=reserve_text(),
            chat_id=msg.chat_id,
            reply_markup=MENU_LAYOUT,
        )]
