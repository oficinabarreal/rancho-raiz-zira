from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── Incoming webhook events from Gateway ────────────────

class GatewayEvent(BaseModel):
    event_id: str = ""
    type: str  # nueva_reserva, checkin, checkout, incidente, pago, telegram_msg, informe_diario
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    source: str = ""  # gmail, telegram, whatsapp, instagram, manual
    data: Dict[str, Any] = {}


# ── Instructions to send back to Gateway ────────────────

class Instruction(BaseModel):
    action: str  # telegram.send_message, kommo.create_lead, calendar.create_event, sheets.append_row, etc.
    payload: Dict[str, Any] = {}


class GatewayResponse(BaseModel):
    event_id: str = ""
    status: str = "ok"  # ok, error, partial
    message: str = ""
    instructions: List[Instruction] = []
    state_updates: Dict[str, Any] = {}
    parser_info: Dict[str, Any] = {}


# ── Business data models ────────────────────────────────

class Reserva(BaseModel):
    name: str = ""
    pax: int = 1
    check_in: str = ""
    check_out: str = ""
    amount: str = ""
    phone: str = ""
    email: str = ""
    source: str = ""
    nights: int = 0
    notes: str = ""


class Incidente(BaseModel):
    guest: str = ""
    tipo: str = ""
    desc: str = ""
    severidad: str = "media"  # baja, media, alta
    reportado_por: str = ""
    fecha: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))


class Pago(BaseModel):
    guest: str = ""
    monto: float = 0.0
    metodo: str = "efectivo"
    fecha: str = ""
    recibido_por: str = ""
    notas: str = ""


class MiembroEquipo(BaseModel):
    nombre: str = ""
    rol: str = ""
    telegram_id: str = ""
    email: str = ""
    telefono: str = ""
    responsabilidades: List[str] = []


class InformeDiario(BaseModel):
    fecha: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    eventos_hoy: List[Dict[str, Any]] = []
    reservas_proximas: List[Dict[str, Any]] = []
    ultimas_publicaciones: List[Dict[str, Any]] = []
    inventario: List[Dict[str, Any]] = []
    estado_crm: Dict[str, int] = {}
    estado_parser: Dict[str, Any] = {}