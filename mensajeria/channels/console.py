"""Canal consola — para desarrollo/testing sin Telegram."""

from __future__ import annotations
from typing import List

from mensajeria.core.message import IncomingMessage, OutgoingMessage
from mensajeria.channels.base import BaseChannel


class ConsoleChannel(BaseChannel):
    """Lee de stdin, escribe a stdout. Ideal para pruebas."""

    def __init__(self):
        self._buffer: List[IncomingMessage] = []

    def name(self) -> str:
        return "console"

    async def poll_once(self) -> List[IncomingMessage]:
        # Si hay buffer pendiente, devolverlo
        if self._buffer:
            msgs = self._buffer[:]
            self._buffer.clear()
            return msgs
        return []

    def inject(self, text: str) -> None:
        """Inyecta un mensaje como si llegara del canal."""
        self._buffer.append(IncomingMessage(
            text=text,
            chat_id=0,
            channel="console",
        ))

    async def send(self, msg: OutgoingMessage) -> bool:
        print(f"\n[Zira] {msg.text}")
        if msg.photo_path:
            print(f"       [foto: {msg.photo_path}]")
        if msg.audio_path:
            print(f"       [audio: {msg.audio_path}]")
        return True
