"""
bot.py — Motor del bot de mensajería multicanal

Conecta un canal con el router de intents y los handlers.
Soporta modos de operación (leads/team/guests).

Uso:
    from mensajeria.bot import create_bot, run_bot

    bot = create_bot(channel="telegram", token="...", chat_id=...)
    run_bot(bot, once=True)  # procesa updates pendientes y sale
    run_bot(bot)             # loop infinito
"""

from __future__ import annotations
import asyncio
import signal
import sys
from typing import List, Optional

from mensajeria.core.message import IncomingMessage, OutgoingMessage
from mensajeria.core.router import IntentRouter
from mensajeria.core.state import ConversationState
from mensajeria.channels.base import BaseChannel
from mensajeria.channels.telegram import TelegramChannel
from mensajeria.handlers.info import WelcomeHandler
from mensajeria.handlers.faq import FaqHandler
from mensajeria.handlers.pricing import PricingHandler, AvailabilityHandler, ReserveHandler
from mensajeria.handlers.photos import PhotoHandler
from mensajeria.handlers.voice import ListenHandler, TTS_AVAILABLE
from mensajeria.handlers.fallback import FallbackHandler
from mensajeria.modes.registry import resolve_mode, description as mode_desc, MODE_INFO


MODE_LABELS = {k: v["label"] for k, v in MODE_INFO.items()}


class Bot:
	"""Orquesta canal + router + handlers, consciente de modos."""

	def __init__(self, channel: BaseChannel, state: Optional[ConversationState] = None):
		self.channel = channel
		self.state = state or ConversationState()
		self.router = IntentRouter()
		self._running = False

		# Registrar handlers por defecto
		self._register_defaults()

	def _register_defaults(self) -> None:
		for h in [
			WelcomeHandler(),
			FaqHandler(),
			PricingHandler(),
			AvailabilityHandler(),
			ReserveHandler(),
			PhotoHandler(),
			ListenHandler(),
			FallbackHandler(),
		]:
			self.router.register(h)

	# ── Resolución de modo ───────────────────────────────────────────

	def _resolve_user_mode(self, msg: IncomingMessage) -> str:
		"""Determina el modo activo para un mensaje entrante.

		Orden: estado persistente > chat_id conocido > canal > default.
		"""
		# 1. Modo persistido en state (si el usuario ya fue identificado)
		if msg.chat_id:
			persisted = self.state.get_user_mode(msg.chat_id)
			if persisted:
				return persisted

		# 2. Resolver por canal + registry
		mode = resolve_mode(channel=msg.channel, chat_id=msg.chat_id)
		return mode

	# ── Comando /modo ──────────────────────────────────────────────

	async def _handle_mode_command(self, msg: IncomingMessage) -> List[OutgoingMessage]:
		"""Procesa /modo — muestra o cambia el modo activo."""
		from mensajeria.modes.registry import MODE_INFO, set_chat_mode

		parts = msg.text.strip().lower().split()
		current = self.state.get_user_mode(msg.chat_id) or "leads"
		current_label = MODE_INFO.get(current, {}).get("label", current)

		# Sin argumentos → mostrar modo actual y opciones
		if len(parts) < 2:
			available = []
			for m, info in MODE_INFO.items():
				m_label = info["label"]
				marker = " ◀ ACTIVO" if m == current else ""
				available.append(f"  {m_label} (`/modo {m}`){marker}")
			text = (
				f"📌 *Modo actual:* {current_label}\n\n"
				f"*Modos disponibles:*\n" + "\n".join(available) + "\n\n"
				f"Usá `/modo <nombre>` para cambiar."
			)
		else:
			# Cambiar modo
			target = parts[1]
			if target in MODE_INFO:
				self.state.set_user_mode(msg.chat_id, target)
				set_chat_mode(msg.chat_id, target)
				new_label = MODE_INFO[target]["label"]
				text = f"✅ Modo cambiado a {new_label}.\n\n{MODE_INFO[target]['description']}"
				msg.mode_suggested = target
			else:
				valid = ", ".join(MODE_INFO.keys())
				text = f"❌ Modo '{target}' no válido. Usá: {valid}"

		return [OutgoingMessage(text=text, chat_id=msg.chat_id)]

	# ── Procesamiento ────────────────────────────────────────────────

	async def process_message(self, msg: IncomingMessage) -> List[OutgoingMessage]:
		"""Procesa un mensaje entrante: resuelve modo, clasifica, enruta, ejecuta handler."""

		# Registrar usuario si es nuevo
		if msg.chat_id:
			self.state.register_user(chat_id=msg.chat_id, username=msg.username)

		# Resolver y asignar modo
		msg.mode = self._resolve_user_mode(msg)

		# Registrar turno
		label = "Cliente"
		if msg.channel == "telegram" and msg.callback_data:
			label = "Cliente(callback)"
		self.state.record_turn(label, msg.text or msg.callback_data, extra={"mode": msg.mode} if msg.mode else None)

		# ── Interceptar comando /modo (antes de classify para evitar mode_mismatch) ──
		if msg.is_command:
			parts = msg.text.strip().lower().split()
			base = parts[0] if parts else ""
			if base in ("/modo", "/mode", "/modos"):
				return await self._handle_mode_command(msg)

		# Clasificar intent (router ya considera el modo)
		intent_result = self.router.classify(msg)

		# Resolver handler respetando el modo
		handler = self.router.resolve(intent_result.intent, mode=msg.mode)
		if handler is None:
			handler = self.router.resolve("fallback", mode=msg.mode)

		# Ejecutar handler
		if handler:
			responses = await handler.handle(msg)
		else:
			responses = [OutgoingMessage(
				text="No entendí tu consulta. Usá los botones del menú.",
				chat_id=msg.chat_id,
			)]

		# Si hubo mode_mismatch, agregar aclaración
		if intent_result.data.get("mode_mismatch"):
			suggested = intent_result.data.get("suggested_intent", "")
			responses.insert(0, OutgoingMessage(
				text=f"📌 Estás en modo {MODE_LABELS.get(msg.mode, msg.mode)}. "
				     f"Esa consulta no aplica acá. Te redirijo al menú general.",
				chat_id=msg.chat_id,
			))

		# Registrar respuesta
		for resp in responses:
			self.state.record_turn("Zira", resp.text)

		# Registrar lead si es relevante (solo en modo leads)
		if msg.mode == "leads" and intent_result.intent not in ("welcome", "fallback"):
			self.state.record_lead(intent_result.intent, {
				"chat_id": msg.chat_id,
				"text": msg.text,
				"intent": intent_result.intent,
				"mode": msg.mode,
			})

		return responses

	async def tick(self) -> int:
		"""Un ciclo de polling: recibe mensajes y responde."""
		messages = await self.channel.poll_once()
		for msg in messages:
			responses = await self.process_message(msg)
			for resp in responses:
				await self.channel.send(resp)
		return len(messages)

	async def run_forever(self) -> None:
		"""Loop infinito de polling."""
		self._running = True
		print(f"[Bot] Iniciando loop en canal '{self.channel.name()}'...")
		while self._running:
			try:
				count = await self.tick()
				if count:
					print(f"[Bot] Procesados {count} mensajes")
			except KeyboardInterrupt:
				break
			except Exception as e:
				print(f"[Bot] Error en tick: {e}")
			await asyncio.sleep(1)
		print("[Bot] Detenido.")

	def stop(self) -> None:
		self._running = False


def create_telegram_bot(token: str, chat_id: int) -> Bot:
	"""Crea un bot conectado a Telegram."""
	state = ConversationState()
	channel = TelegramChannel(token, chat_id, state=state)
	return Bot(channel, state=state)


def run_bot(bot: Bot, once: bool = False, timeout: int = 30) -> None:
	"""Ejecuta el bot en modo once o infinito.

	Args:
		bot: Instancia de Bot
		once: Si True, procesa updates pendientes y sale
		timeout: Timeout en segundos para modo once
	"""

	async def _run_once():
		count = await bot.tick()
		print(f"[Bot] Procesados {count} mensajes (modo once)")

	async def _run_forever():
		await bot.run_forever()

	loop = asyncio.new_event_loop()
	asyncio.set_event_loop(loop)

	if once:
		loop.run_until_complete(asyncio.wait_for(_run_once(), timeout=timeout))
	else:
		for sig in (signal.SIGINT, signal.SIGTERM):
			try:
				loop.add_signal_handler(sig, bot.stop)
			except NotImplementedError:
				pass
		try:
			loop.run_until_complete(_run_forever())
		except KeyboardInterrupt:
			pass
		finally:
			bot.stop()
			loop.close()
