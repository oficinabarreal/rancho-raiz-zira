"""Base para canales de mensajería."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List

from mensajeria.core.message import IncomingMessage, OutgoingMessage


class BaseChannel(ABC):
    """Un canal recibe mensajes entrantes y envía respuestas."""

    @abstractmethod
    async def poll_once(self) -> List[IncomingMessage]:
        """Obtiene los mensajes nuevos desde el canal (polling)."""
        ...

    @abstractmethod
    async def send(self, msg: OutgoingMessage) -> bool:
        """Envía una respuesta por el canal."""
        ...

    @abstractmethod
    def name(self) -> str:
        """Nombre único del canal (telegram, console, webhook...)."""
        ...
