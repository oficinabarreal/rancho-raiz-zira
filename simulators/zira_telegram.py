#!/usr/bin/env python3
"""Shared Zira Telegram helpers for the demo bot and simulator."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
import sys
from typing import Any, Dict, List

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from crm_simulator import build_zira_dialogue

BASE_DIR = Path(__file__).resolve().parent
STATE_FILE = BASE_DIR / "zira_state.json"
LEADS_FILE = BASE_DIR / "zira_leads.json"
OFFSET_FILE = BASE_DIR / "zira_offset.txt"
MEDIA_DIR = BASE_DIR / "zira_media"

MENU_LAYOUT: List[List[Dict[str, str]]] = [
    [
        {"text": "Info posada", "callback_data": "zira:faq:about"},
        {"text": "Ubicación", "callback_data": "zira:faq:location"},
    ],
    [
        {"text": "Qué incluye", "callback_data": "zira:faq:amenities"},
        {"text": "Precios", "callback_data": "zira:prices"},
    ],
    [
        {"text": "Disponibilidad", "callback_data": "zira:availability"},
        {"text": "Reservar", "callback_data": "zira:reserve"},
        {"text": "Subir foto", "callback_data": "zira:photo"},
    ],
    [
        {"text": "Escuchar", "callback_data": "zira:listen"},
        {"text": "Más preguntas", "callback_data": "zira:faq:about"},
    ],
]


def ensure_dirs() -> None:
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def welcome_text() -> str:
    return (
        "Hola, soy Zira.\n\n"
        "Puedo ayudarte con la posada en Barreal, Calingasta, San Juan, "
        "al pie de la Cordillera de los Andes.\n\n"
        "Usa los botones o escribime tu consulta."
    )


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


def photo_text() -> str:
    return (
        "📷 Mandame una foto por Telegram.\n\n"
        "La voy a guardar, dejar en cola para edición y preparar para publicación."
    )


def audio_hint_text(key: str) -> str:
    if key == "about":
        return "Sobre la posada."
    if key == "location":
        return "Ubicación de la posada."
    if key == "amenities":
        return "Servicios incluidos en la posada."
    if key == "prices":
        return "Tarifario de la posada."
    if key == "availability":
        return "Disponibilidad de fechas."
    if key == "reserve":
        return "Instrucciones para reservar."
    if key == "photo":
        return "Cómo enviar una foto para editar y publicar."
    return "Respuesta de Zira."


def faq_text(key: str) -> str:
    if key == "about":
        return about_text()
    if key == "location":
        return location_text()
    if key == "amenities":
        return amenities_text()
    if key == "prices":
        return prices_text()
    if key == "availability":
        return availability_text()
    if key == "reserve":
        return reserve_text()
    if key == "photo":
        return photo_text()
    return welcome_text()


def classify_text(text: str) -> str:
    t = text.lower().strip()
    if any(token in t for token in ["info", "posada", "hospedaje", "alojamiento", "quiénes son", "quienes son"]):
        return "about"
    if any(token in t for token in ["ubicacion", "ubicación", "donde queda", "dónde queda", "mapa", "llegar", "direccion", "dirección"]):
        return "location"
    if any(token in t for token in ["incluye", "comodidades", "servicios", "amenities", "que tiene", "qué tiene"]):
        return "amenities"
    if any(token in t for token in ["precio", "precios", "tarifa", "costo", "valor"]):
        return "prices"
    if any(token in t for token in ["disponible", "disponibilidad", "fecha", "fechas", "cuando"]):
        return "availability"
    if any(token in t for token in ["reserv", "seña", "reserva", "book"]):
        return "reserve"
    if any(token in t for token in ["foto", "imagen", "post", "publicar", "feed"]):
        return "photo"
    return "fallback"


def build_inline_keyboard() -> Dict[str, Any]:
    return {"inline_keyboard": MENU_LAYOUT}


def record_turn(speaker: str, text: str) -> None:
    ensure_dirs()
    state = load_json(STATE_FILE, {"turns": []})
    state.setdefault("turns", []).append(
        {
            "ts": datetime.utcnow().isoformat() + "Z",
            "speaker": speaker,
            "text": text,
        }
    )
    save_json(STATE_FILE, state)


def load_offset(default: int = 0) -> int:
    try:
        return int(OFFSET_FILE.read_text(encoding="utf-8").strip())
    except Exception:
        return default


def save_offset(offset: int) -> None:
    OFFSET_FILE.write_text(f"{int(offset)}\n", encoding="utf-8")


def record_lead(source: str, payload: Dict[str, Any]) -> None:
    ensure_dirs()
    leads = load_json(LEADS_FILE, {"items": []})
    leads.setdefault("items", []).append(
        {
            "ts": datetime.utcnow().isoformat() + "Z",
            "source": source,
            "payload": payload,
        }
    )
    save_json(LEADS_FILE, leads)


def dialogue_lines() -> List[str]:
    lines: List[str] = []
    for turn in build_zira_dialogue():
        lines.append(f"{turn.speaker}: {turn.text}")
    return lines
