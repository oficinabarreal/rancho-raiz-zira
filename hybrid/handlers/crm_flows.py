from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional
from config import settings
from models import GatewayResponse, Instruction, Reserva, Incidente, Pago, InformeDiario
import parser as parser_mod
from parser import parsear, configurar_ia
import store
import uuid


def init_parser():
    if settings.ia_available:
        configurar_ia(settings.ia_endpoint, settings.ia_api_key, settings.ia_model)


def nueva_reserva(event_data: Dict[str, Any]) -> GatewayResponse:
    raw_text = event_data.get("raw_text", "")
    source = event_data.get("source", event_data.get("from", ""))
    from_addr = event_data.get("from", "")

    result = parsear(raw_text)
    parsed = result.data if result.ok else {}

    reserva = Reserva(
        name=parsed.get("name", ""),
        pax=parsed.get("pax", 1),
        check_in=parsed.get("check_in", ""),
        check_out=parsed.get("check_out", ""),
        amount=parsed.get("amount", ""),
        phone=parsed.get("phone", ""),
        email=parsed.get("email", from_addr),
        source=parsed.get("source", source),
        nights=parsed.get("nights", 0),
        notes=f"Parser: {result.method} (conf: {result.confidence:.2f})" if result.ok else "No parseado automáticamente"
    )

    if not reserva.name:
        return GatewayResponse(
            event_id=event_data.get("event_id", ""),
            status="error",
            message="No se pudo extraer nombre de la reserva. Revisión manual requerida.",
            parser_info={"method": result.method, "confidence": result.confidence, "error": result.error}
        )

    # Guardar
    reserva_dict = reserva.model_dump() if hasattr(reserva, "model_dump") else reserva.dict()
    reserva_dict["fecha_recepcion"] = datetime.now().isoformat()
    reserva_dict["id"] = str(uuid.uuid4())[:8]
    store.append("reservas.json", reserva_dict)

    instructions = _build_reserva_instructions(reserva_dict)

    return GatewayResponse(
        event_id=event_data.get("event_id", ""),
        status="ok",
        message=f"Reserva procesada: {reserva.name}",
        instructions=instructions,
        state_updates={"reserva": reserva_dict},
        parser_info={"method": result.method, "confidence": result.confidence}
    )


def _to_iso(date_str: str) -> str:
    """Convierte DD/MM/YYYY a YYYY-MM-DD."""
    for sep in ["/", "-", "."]:
        if sep in date_str:
            parts = date_str.split(sep)
            if len(parts) == 3 and len(parts[2]) == 4:
                return f"{parts[2]}-{parts[1]}-{parts[0]}"
    return date_str

def _build_reserva_instructions(reserva: Dict[str, Any]) -> List[Instruction]:
    ins: List[Instruction] = []
    name = reserva.get("name", "?")
    pax = reserva.get("pax", 1)
    check_in = _to_iso(reserva.get("check_in", ""))
    check_out = _to_iso(reserva.get("check_out", ""))
    amount = reserva.get("amount", "")
    phone = reserva.get("phone", "")
    source = reserva.get("source", "?")

    notif = (
        f"🆕 NUEVA RESERVA\n{name} - {pax} pax\n"
        f"Check-in: {check_in}\nCheck-out: {check_out}\n"
        f"💰 ${amount}\n📱 {phone}\n📧 Origen: {source}"
    )

    ins.append(Instruction(action="telegram.send_message", payload={
        "chat_id": settings.tg_chat_id, "text": notif
    }))

    ins.append(Instruction(action="kommo.create_lead", payload={
        "name": f"Reserva {name}",
        "contacts": [{"name": name, "phone": phone}],
        "pipeline_id": settings.kommo_pipeline_id,
        "custom_fields": {"origen": source, "pax": pax, "monto": amount}
    }))

    if check_in:
        ins.append(Instruction(action="calendar.create_event", payload={
            "summary": f"🟢 IN: {name} ({pax}pax)",
            "start": f"{check_in}T14:00:00",
            "end": f"{check_in}T15:00:00",
            "description": f"Check-in {name}\nPax: {pax}\nOrigen: {source}\nMonto: ${amount}"
        }))

    if check_out:
        ins.append(Instruction(action="calendar.create_event", payload={
            "summary": f"🔴 OUT: {name}",
            "start": f"{check_out}T10:00:00",
            "end": f"{check_out}T11:00:00",
            "description": f"Check-out {name}"
        }))

    ins.append(Instruction(action="sheets.append_row", payload={
        "spreadsheet_id": settings.sheet_reservas,
        "values": ["", name, str(pax), str(check_in), str(check_out), str(amount), source]
    }))

    return ins


def procesar_incidente(event_data: Dict[str, Any]) -> GatewayResponse:
    data = event_data.get("data", event_data)
    incidente = Incidente(
        guest=data.get("guest", data.get("name", "")),
        tipo=data.get("tipo", "general"),
        desc=data.get("desc", data.get("descripcion", "")),
        severidad=data.get("severidad", "media"),
        reportado_por=data.get("reportado_por", data.get("reported_by", "Sistema")),
    )
    inc_dict = incidente.model_dump() if hasattr(incidente, "model_dump") else incidente.dict()
    inc_dict["id"] = str(uuid.uuid4())[:8]
    store.append("incidentes.json", inc_dict)

    return GatewayResponse(
        event_id=event_data.get("event_id", ""),
        status="ok",
        message=f"Incidencia registrada: {incidente.tipo} - {incidente.guest}",
        instructions=[Instruction(action="telegram.send_message", payload={
            "chat_id": settings.tg_chat_id,
            "text": f"⚠️ INCIDENCIA\nHuésped: {incidente.guest}\nProblema: {incidente.tipo}\n{incidente.desc}\nSeveridad: {incidente.severidad}"
        })],
        state_updates={"incidente": inc_dict}
    )


def procesar_pago(event_data: Dict[str, Any]) -> GatewayResponse:
    data = event_data.get("data", event_data)
    pago = Pago(
        guest=data.get("guest", ""),
        monto=float(data.get("monto", data.get("amount", 0))),
        metodo=data.get("metodo", "efectivo"),
        fecha=data.get("fecha", datetime.now().strftime("%Y-%m-%d")),
        recibido_por=data.get("recibido_por", "Diego"),
    )
    pago_dict = pago.model_dump() if hasattr(pago, "model_dump") else pago.dict()
    pago_dict["id"] = str(uuid.uuid4())[:8]
    store.append("pagos.json", pago_dict)

    amt = pago.monto
    try:
        amt_fmt = f"${amt:,.0f}"
    except (ValueError, TypeError):
        amt_fmt = f"${amt}"

    return GatewayResponse(
        event_id=event_data.get("event_id", ""),
        status="ok",
        message=f"Pago registrado: {pago.guest} - {amt_fmt}",
        instructions=[Instruction(action="telegram.send_message", payload={
            "chat_id": settings.tg_chat_id,
            "text": f"💰 PAGO REGISTRADO\nHuésped: {pago.guest}\nMonto: {amt_fmt}\nMétodo: {pago.metodo}\nRecibió: {pago.recibido_por}"
        })],
        state_updates={"pago": pago_dict}
    )


def generar_informe(event_data: Dict[str, Any]) -> GatewayResponse:
    ahora = datetime.now().strftime("%d/%m/%Y %H:%M")
    reservas = store.read("reservas.json", [])
    incidentes = store.read("incidentes.json", [])
    pagos = store.read("pagos.json", [])

    prox = [r for r in reservas[-5:] if r.get("check_in")]
    inc_activos = [i for i in incidentes[-3:] if i.get("severidad") in ("alta", "media")]

    informe = f"📋 INFORME DIARIO RANCHO RAÍZ — {ahora}\n{'='*50}\n"
    informe += f"\n📌 RESERVAS ({len(reservas)} totales)\n"
    for r in prox:
        informe += f"  {r.get('name','?')} — {r.get('check_in','?')}\n"
    informe += f"\n📌 INCIDENTES PENDIENTES ({len(inc_activos)})\n"
    for i in inc_activos:
        informe += f"  {i.get('tipo','?')} - {i.get('guest','?')} [{i.get('severidad','?')}]\n"
    informe += f"\n📌 PAGOS ({len(pagos)} registrados)\n"
    for p in pagos[-3:]:
        informe += f"  {p.get('guest','?')}: ${p.get('monto',0)}\n"

    parser_state = "✅ Activo" if parser_mod.IA_ENDPOINT else "❌ No configurado"
    if parser_mod.IA_LAST_RATE_LIMIT:
        parser_state += f" (rate limit en {parser_mod.IA_LAST_RATE_LIMIT})"
    informe += f"\n📌 IA Parser: {parser_state}\n"
    informe += f"\nGenerado: {ahora}"

    store.write("informe_diario.txt", informe)

    return GatewayResponse(
        event_id=event_data.get("event_id", ""),
        status="ok",
        message="Informe diario generado",
        instructions=[
            Instruction(action="telegram.send_message", payload={
                "chat_id": settings.tg_chat_id, "text": informe[:4000]
            }),
            Instruction(action="gmail.send_message", payload={
                "to": settings.report_email,
                "subject": f"📋 Informe Diario Rancho Raíz - {datetime.now().strftime('%d/%m/%Y')}",
                "body": informe
            }),
        ],
        state_updates={"informe_generado": ahora}
    )
