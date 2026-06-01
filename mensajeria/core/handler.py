"""Base handler — todos los handlers heredan de acá."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List

from mensajeria.core.message import IncomingMessage, OutgoingMessage


class BaseHandler(ABC):
    """Un handler procesa un mensaje y produce respuestas.

    Cada handler se registra en el router con uno o más intents.
    Puede declarar en qué modos está activo via `modes`.
    """

    # Set de modos en los que este handler está activo.
    # Si está vacío, aplica a todos los modos.
    modes: set = set()

    @abstractmethod
    def intent(self) -> str:
        """Nombre del intent que este handler maneja."""
        ...

    @abstractmethod
    async def handle(self, msg: IncomingMessage) -> List[OutgoingMessage]:
        """Procesa el mensaje y devuelve una o más respuestas."""
        ...

    def confidence(self, msg: IncomingMessage) -> float:
        """Confianza opcional (0-1) para priorizar handlers. 1 = máxima."""
        return 0.5
