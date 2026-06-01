"""Router de intents — clasifica texto y mapea a handlers, consciente de modos."""

from __future__ import annotations
from typing import Dict, List, Optional, Type, Set

from mensajeria.core.message import IncomingMessage, IntentResult
from mensajeria.core.handler import BaseHandler


class IntentRouter:
    """Clasifica mensajes y los enruta al handler adecuado.

    Soporta modo-activo: si el mensaje trae un ``mode``, el router solo
    considera handlers que sirvan ese modo. Así un usuario en modo "team"
    no recibe precios de leads, etc.

    Handlers sin ``modes`` (set vacío) se consideran multi-modo y aplican
    siempre.
    """

    def __init__(self):
        self._handlers: Dict[str, BaseHandler] = {}
        self._fallback: Optional[BaseHandler] = None

    def register(self, handler: BaseHandler) -> None:
        intent = handler.intent()
        if intent == "fallback":
            self._fallback = handler
        else:
            self._handlers[intent] = handler

    # ── Filtro por modo ─────────────────────────────────────────────

    def active_handlers(self, mode: str = "") -> Dict[str, BaseHandler]:
        """Devuelve handlers que sirven al modo indicado.

        Si mode está vacío, devuelve todos (comportamiento legacy).
        Handlers sin ``modes`` (set vacío = multi-modo) siempre incluidos.
        """
        if not mode:
            return dict(self._handlers)
        result = {}
        for intent, handler in self._handlers.items():
            h_modes = getattr(handler, "modes", set())
            if not h_modes or mode in h_modes:
                result[intent] = handler
        return result

    def is_valid_for_mode(self, intent: str, mode: str) -> bool:
        """¿El intent es válido en este modo?"""
        if not mode:
            return True
        handler = self._handlers.get(intent)
        if handler is None:
            return False
        h_modes = getattr(handler, "modes", set())
        return not h_modes or mode in h_modes

    # ── Clasificación ───────────────────────────────────────────────

    def classify(self, msg: IncomingMessage) -> IntentResult:
        """Clasifica el texto del mensaje en un intent, considerando el modo activo."""
        intent_result = self._classify_raw(msg)

        # Si hay modo activo, verificar que el intent sea válido
        if msg.mode and not self.is_valid_for_mode(intent_result.intent, msg.mode):
            # Intent no disponible en este modo → sugerir modo o fallback
            intent_result = IntentResult(
                intent="fallback",
                confidence=0.0,
                data={"mode_mismatch": True, "suggested_intent": intent_result.intent},
            )

        return intent_result

    def _classify_raw(self, msg: IncomingMessage) -> IntentResult:
        """Clasificación pura (sin filtro de modo)."""
        if msg.is_command:
            cmd = msg.text.strip().lower()
            base = cmd.split()[0] if cmd else ""
            if base in ("/start", "/menu", "/hola"):
                return IntentResult(intent="welcome", confidence=1.0)
            if base in ("/modo", "/mode", "/modos"):
                return IntentResult(intent="mode", confidence=1.0)
            if base in ("/precios", "/precio"):
                return IntentResult(intent="prices", confidence=1.0)
            if base in ("/disponibilidad", "/disponible", "/fechas"):
                return IntentResult(intent="availability", confidence=1.0)
            if base in ("/reservar", "/reserva", "/book"):
                return IntentResult(intent="reserve", confidence=1.0)

        if msg.callback_data:
            cd = msg.callback_data
            if cd.startswith("zira:faq:"):
                return IntentResult(intent="faq", confidence=1.0, data={"key": cd.split(":", 2)[2]})
            if cd == "zira:prices":
                return IntentResult(intent="prices", confidence=1.0)
            if cd == "zira:availability":
                return IntentResult(intent="availability", confidence=1.0)
            if cd == "zira:reserve":
                return IntentResult(intent="reserve", confidence=1.0)
            if cd == "zira:photo":
                return IntentResult(intent="photo", confidence=1.0)
            if cd == "zira:listen":
                return IntentResult(intent="listen", confidence=1.0)

        if msg.has_photo:
            return IntentResult(intent="photo", confidence=1.0)

        # Fallback: clasificación por reglas
        intent, conf = self._classify_text(msg.text)
        return IntentResult(intent=intent, confidence=conf)

    def _classify_text(self, text: str) -> tuple:
        """Clasificación por reglas (herencia de Zira)."""
        t = text.lower().strip()
        if any(token in t for token in ["precio", "precios", "tarifa", "costo", "valor", "cuanto", "cuánto"]):
            return "prices", 0.8
        if any(token in t for token in ["disponible", "disponibilidad", "fecha", "fechas", "cuando", "cuándo", "hay lugar"]):
            return "availability", 0.8
        if any(token in t for token in ["reserv", "seña", "reserva", "book", "alquilar", "quiero ir"]):
            return "reserve", 0.8
        if any(token in t for token in ["foto", "imagen", "post", "publicar", "feed", "subir"]):
            return "photo", 0.8
        if any(token in t for token in ["ubicacion", "ubicación", "donde queda", "dónde queda", "mapa", "llegar", "direccion", "dirección"]):
            return "faq", 0.7
        if any(token in t for token in ["incluye", "comodidades", "servicios", "amenities", "que tiene", "qué tiene", "tiene wifi"]):
            return "faq", 0.7
        if any(token in t for token in ["info", "posada", "hospedaje", "alojamiento", "quiénes son", "quienes son", "que es", "qué es"]):
            return "faq", 0.7
        return "fallback", 0.0

    # ── Resolución ─────────────────────────────────────────────────

    def resolve(self, intent: str, mode: str = "") -> Optional[BaseHandler]:
        """Resuelve un intent a su handler, respetando el modo si se especifica.

        Si el modo está activo y el handler no lo sirve, devuelve fallback
        en lugar de un handler inválido.
        """
        handler = self._handlers.get(intent)
        if handler is None:
            return self._fallback

        # Verificar modo
        if mode:
            h_modes = getattr(handler, "modes", set())
            if h_modes and mode not in h_modes:
                return self._fallback

        return handler

    def list_intents(self, mode: str = "") -> List[str]:
        """Lista intents disponibles, opcionalmente filtrados por modo."""
        if mode:
            return sorted(self.active_handlers(mode).keys())
        return sorted(self._handlers.keys())
