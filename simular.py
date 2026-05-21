from __future__ import annotations
import json, sys, time, uuid, os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crm.connectors import (
    CalendarConnector, TelegramConnector, KommoConnector,
    WhatsAppConnector, ConnectorResult
)
import parser as parser_mod
from parser import parsear, IA_ENDPOINT, IA_MODEL

DRY = True

BASE = Path(__file__).resolve().parent / "crm_state"
BASE.mkdir(parents=True, exist_ok=True)

LOG = []
PARSER_RESULTS = []

def log(step: str, result: ConnectorResult):
    status = "✅" if result.ok else "❌"
    info = result.data if not result.error else result.error
    LOG.append(f"  {status} {step}: {json.dumps(info, ensure_ascii=False)[:120]}")
    print(LOG[-1])

def notify_team(text: str):
    if DRY:
        log("📢 Notificación", ConnectorResult(ok=True, data={"text": text[:80], "dry": True}))
    else:
        r = TelegramConnector().send_message(text)
        log("📢 Telegram", r)
        if WhatsAppConnector().token:
            r2 = WhatsAppConnector().send_message("5492645480313", text)
            log("📢 WhatsApp", r2)

def dict_a_texto_natural(data: Dict[str, Any], style: int = 0) -> str:
    """Genera texto variado simulando distintos estilos de mensaje."""
    name = data.get("name", "Huésped")
    pax = data.get("pax", 2)
    check_in = data.get("check_in", "")
    check_out = data.get("check_out", "")
    amount = data.get("amount", "")
    source = data.get("source", "Directo")
    phone = data.get("phone", "")

    templates = [
        f"Nueva reserva\nNombre: {name}\nPax: {pax}\nCheck-in: {check_in}\nCheck-out: {check_out}\nMonto: ${amount}\nOrigen: {source}\nTel: {phone}",
        f"Hola! Quiero reservar para {name}, somos {pax} personas. Del {check_in} al {check_out}. Presupuesto ${amount}. 📱{phone}",
        f"{source} - Reserva confirmada\nHuésped: {name}\n{check_in} → {check_out}\n{pax} adultos\nTotal: ${amount}",
        f"📋 Datos de la reserva:\n- Nombre: {name}\n- Personas: {pax}\n- Entrada: {check_in}\n- Salida: {check_out}\n- Abonado: ${amount}",
    ]
    return templates[style % len(templates)]

_style_counter = 0

def probar_parser(nombre_escenario: str, ground_truth: Dict[str, Any]) -> Dict[str, Any]:
    """Convierte a texto natural (variado), parsea con IA+fallback, reporta diferencias."""
    global _style_counter

    style = _style_counter % 4
    _style_counter += 1
    texto = dict_a_texto_natural(ground_truth, style=style)
    print(f"\n  📝 Texto de prueba (estilo {style}): {texto[:100]}...")
    resultado = parsear(texto)

    parsed = resultado.data
    method = resultado.method if resultado.ok else f"fallback_{resultado.error}"

    # Comparar campos clave
    campos = ["name", "pax", "check_in", "check_out", "amount", "phone", "source"]
    aciertos = 0
    total = 0
    diffs = []
    for c in campos:
        gt_val = ground_truth.get(c)
        p_val = parsed.get(c) if parsed else None
        # Normalizar para comparación
        if gt_val is not None and str(gt_val).strip():
            total += 1
            gt_str = str(gt_val).strip().lower()
            p_str = str(p_val).strip().lower() if p_val else ""
            # Check-in/out pueden diferir en formato
            if c in ("check_in", "check_out"):
                if gt_str.replace("-", "/") in p_str.replace("-", "/") or p_str.replace("-", "/") in gt_str.replace("-", "/"):
                    aciertos += 1
                else:
                    diffs.append(f"{c}: esperado={gt_val} vs parseado={p_val}")
            elif c == "amount":
                if gt_str.replace(",", "") in p_str.replace(",", "") or p_str.replace(",", "") in gt_str.replace(",", ""):
                    aciertos += 1
                else:
                    diffs.append(f"{c}: esperado={gt_val} vs parseado={p_val}")
            else:
                if gt_str == p_str:
                    aciertos += 1
                elif c == "source" and (gt_str in p_str or p_str in gt_str):
                    aciertos += 1
                else:
                    diffs.append(f"{c}: esperado={gt_val} vs parseado={p_val}")

    accuracy = round(aciertos / total, 2) if total > 0 else 0

    registro = {
        "escenario": nombre_escenario,
        "method": method,
        "confidence": resultado.confidence,
        "accuracy": accuracy,
        "aciertos": aciertos,
        "total_campos": total,
        "diferencias": diffs,
        "texto_original": texto,
        "ground_truth": ground_truth,
        "parsed": parsed,
        "ok": resultado.ok,
    }
    PARSER_RESULTS.append(registro)

    # Print
    icono = "✅" if accuracy >= 0.8 else "⚠️" if accuracy >= 0.5 else "❌"
    print(f"\n  {icono} [{nombre_escenario}] parser={method} confianza={resultado.confidence:.2f} accuracy={accuracy:.2f} ({aciertos}/{total})")
    if diffs:
        for d in diffs:
            print(f"     ⚠️  {d}")

    # Si el parseo tuvo alta confianza, usar datos parseados. Si no, usar ground truth.
    if resultado.ok and resultado.confidence >= 0.5:
        # Merge: usar parsed pero rellenar huecos con ground truth
        merged = {**ground_truth}
        for k in parsed:
            if parsed[k] and str(parsed[k]).strip():
                merged[k] = parsed[k]
        merged["_parser_method"] = method
        merged["_parser_confidence"] = resultado.confidence
        return merged
    else:
        ground_truth["_parser_method"] = "ground_truth"
        ground_truth["_parser_confidence"] = 0
        return ground_truth

def reportar_parser_stats():
    """Reporte final del parser."""
    print(f"\n{'='*60}")
    print("📊 REPORTE PARSER IA vs REGEX vs RAW")
    print(f"{'='*60}")
    print(f"Endpoint: {IA_ENDPOINT or 'no configurado'}")
    print(f"Modelo principal: {IA_MODEL or 'ninguno'}")
    print(f"Rate limits: {parser_mod.IA_LAST_RATE_LIMIT or 'ninguno'}")
    print(f"IA disponible: {'✅ SI' if parser_mod.IA_ENDPOINT and parser_mod.IA_MODEL else '❌ NO'}")
    print()

    total = len(PARSER_RESULTS)
    ia_ok = sum(1 for r in PARSER_RESULTS if r["method"].startswith("ia/") and r["ok"])
    regex_ok = sum(1 for r in PARSER_RESULTS if r["method"] == "regex" and r["ok"])
    raw_fallback = sum(1 for r in PARSER_RESULTS if r.get("error") == "RAW_FALLBACK")
    high_accuracy = sum(1 for r in PARSER_RESULTS if r["accuracy"] >= 0.8)
    med_accuracy = sum(1 for r in PARSER_RESULTS if 0.5 <= r["accuracy"] < 0.8)
    low_accuracy = sum(1 for r in PARSER_RESULTS if r["accuracy"] < 0.5)

    print(f"Escenarios probados: {total}")
    print(f"  Parser IA exitoso: {ia_ok}")
    print(f"  Fallback regex: {regex_ok}")
    print(f"  Raw fallback: {raw_fallback}")
    print(f"\nPrecisión general:")
    print(f"  Alta (≥80%):  {high_accuracy}")
    print(f"  Media (50-79%): {med_accuracy}")
    print(f"  Baja (<50%):  {low_accuracy}")
    print()

    for r in PARSER_RESULTS:
        icono = "✅" if r["accuracy"] >= 0.8 else "⚠️" if r["accuracy"] >= 0.5 else "❌"
        print(f"  {icono} {r['escenario']}: method={r['method']} conf={r['confidence']:.2f} acc={r['accuracy']:.2f} ({r['aciertos']}/{r['total_campos']})")

    # Guardar reporte
    report_path = BASE / "parser_report.json"
    report_path.write_text(json.dumps(PARSER_RESULTS, indent=2, ensure_ascii=False))
    print(f"\nReporte guardado en {report_path}")


# ── ESCENARIOS ──

def escenario_1_nueva_reserva():
    """Booking → IA parse → Kommo → Calendar → Notificar"""
    print(f"\n{'='*60}")
    print("ESCENARIO 1: Nueva reserva desde Booking (con IA parser)")
    print(f"{'='*60}")

    guest_gt = {
        "name": "María García",
        "pax": 4,
        "check_in": "2026-06-15",
        "check_out": "2026-06-18",
        "source": "Booking",
        "amount": "345000",
        "phone": "5491155550101"
    }

    guest = probar_parser("Booking - María García", guest_gt)

    r = KommoConnector().create_lead(
        f"Reserva {guest['name']}",
        {
            "contacts": [{
                "name": guest["name"],
                "custom_fields_values": [
                    {"field_id": None, "values": [{"value": guest.get("phone", "")}]}
                ]
            }],
            "pipeline_id": 13768223
        }
    )
    log(f"Kommo lead: {guest['name']}", r)
    lead_id = r.data.get("lead_id", "?")

    cal = CalendarConnector()
    if not DRY:
        r = cal.create_event(
            f"🟢 IN: {guest['name']} ({guest['pax']}pax)",
            f"{guest['check_in']}T14:00:00",
            f"{guest['check_in']}T15:00:00",
            f"Reserva Booking\nHuéspedes: {guest['pax']}\nLead: {lead_id}\nParser: {guest.get('_parser_method','?')}"
        )
        log("Calendar check-in", r)
        r = cal.create_event(
            f"🔴 OUT: {guest['name']}",
            f"{guest['check_out']}T10:00:00",
            f"{guest['check_out']}T11:00:00",
            f"Check-out {guest['name']}"
        )
        log("Calendar check-out", r)
    else:
        log("Calendar check-in/out", ConnectorResult(ok=True, data={"dry": True}))

    method_icon = "🤖" if guest.get("_parser_method", "").startswith("ia") else "📐" if guest.get("_parser_method") == "regex" else "📄"
    parser_info = f"[{method_icon} {guest.get('_parser_method','?')} conf:{guest.get('_parser_confidence',0):.2f}]"
    notify_team(
        f"🆕 NUEVA RESERVA\n{guest['name']} - {guest['pax']} pax\n"
        f"Check-in: {guest['check_in']}\nCheck-out: {guest['check_out']}\n"
        f"Origen: {guest.get('source','?')} | Lead #{lead_id}\n{parser_info}"
    )

def escenario_2_checkin():
    """Check-in con IA"""
    print(f"\n{'='*60}")
    print("ESCENARIO 2: Check-in (con IA parser)")
    print(f"{'='*60}")

    guest_gt = {"name": "María García", "check_in": "2026-06-15"}
    guest = probar_parser("Check-in - María García", guest_gt)

    if not DRY:
        r = CalendarConnector().create_event(
            f"✅ CHECK-IN REALIZADO: {guest['name']}",
            f"{guest['check_in']}T18:00:00",
            f"{guest['check_in']}T19:00:00",
            f"Huésped instalado. Casa lista.\nParser: {guest.get('_parser_method','?')}"
        )
        log("✅ Confirmación check-in", r)
    else:
        log("✅ Confirmación check-in", ConnectorResult(ok=True, data={"dry": True}))

    method_icon = "🤖" if guest.get("_parser_method", "").startswith("ia") else "📐"
    notify_team(
        f"✅ CHECK-IN COMPLETADO\n{guest['name']} ya está instalado.\n"
        f"Casa preparada y llave entregada.\n[{method_icon} {guest.get('_parser_method','?')}]"
    )

def escenario_3_problema():
    """Reporte de problema con IA"""
    print(f"\n{'='*60}")
    print("ESCENARIO 3: Reporte de problema (con IA parser)")
    print(f"{'='*60}")

    incidente_gt = {
        "guest": "María García",
        "tipo": "heladera",
        "desc": "No enfría bien. Hace ruido.",
        "severidad": "media"
    }
    # Para incidentes el parser extrae datos del texto del reporte
    texto_reporte = f"Problema con la heladera en la cabaña de {incidente_gt['guest']}. {incidente_gt['desc']} Severidad: {incidente_gt['severidad']}."
    resultado = parsear(texto_reporte)
    if resultado.ok and resultado.data.get("name"):
        parsed_name = resultado.data["name"]
        method = resultado.method
        conf = resultado.confidence
    else:
        parsed_name = incidente_gt["guest"]
        method = "regex"
        conf = 0
    print(f"  {'✅' if conf >= 0.5 else '⚠️'} [Incidente] parser={method} conf={conf:.2f} nombre={parsed_name}")

    report = BASE / "incidentes.json"
    incidents = json.loads(report.read_text()) if report.exists() else []
    incidents.append({
        "id": str(uuid.uuid4())[:8],
        "fecha": datetime.now().isoformat(),
        **incidente_gt,
        "_parser_method": method,
        "_parser_confidence": conf,
    })
    report.write_text(json.dumps(incidents, indent=2, ensure_ascii=False))
    log("📋 Incidencia guardada", ConnectorResult(ok=True, data={"file": str(report)}))

    notify_team(
        f"⚠️ INCIDENCIA\nHuésped: {incidente_gt['guest']}\n"
        f"Problema: {incidente_gt['tipo']}\n{incidente_gt['desc']}\n"
        f"Severidad: {incidente_gt['severidad']}\n"
        f"[{'🤖 IA' if method.startswith('ia') else '📐 regex'} {method} conf:{conf:.2f}]"
    )

def escenario_4_checkout():
    """Check-out con IA"""
    print(f"\n{'='*60}")
    print("ESCENARIO 4: Check-out (con IA parser)")
    print(f"{'='*60}")

    guest_gt = {"name": "María García", "check_out": "2026-06-18"}
    payment_gt = 345000
    guest = probar_parser("Check-out - María García", guest_gt)

    pagos = BASE / "pagos.json"
    payments = json.loads(pagos.read_text()) if pagos.exists() else []
    payments.append({
        "id": str(uuid.uuid4())[:8],
        "guest": guest["name"],
        "fecha": guest["check_out"],
        "monto": payment_gt,
        "metodo": "efectivo/transferencia",
        "recibido_por": "Diego",
        "_parser_method": guest.get("_parser_method", "?"),
    })
    pagos.write_text(json.dumps(payments, indent=2, ensure_ascii=False))
    log("💰 Pago registrado", ConnectorResult(ok=True, data={"monto": payment_gt}))

    if not DRY:
        r = CalendarConnector().create_event(
            f"🧹 LIMPIEZA: {guest['name']}",
            f"{guest['check_out']}T11:00:00",
            f"{guest['check_out']}T14:00:00",
            f"Limpieza post-checkout. Chiqui asignada.\nParser: {guest.get('_parser_method','?')}"
        )
        log("🧹 Evento limpieza", r)
    else:
        log("🧹 Evento limpieza", ConnectorResult(ok=True, data={"dry": True}))

    method_icon = "🤖" if guest.get("_parser_method", "").startswith("ia") else "📐"
    notify_team(
        f"🔴 CHECK-OUT: {guest['name']}\n"
        f"Pagó: ${payment_gt:,}\n"
        f"🧹 Limpieza asignada.\n[{method_icon} {guest.get('_parser_method','?')}]"
    )

def escenario_5_resumen_diario():
    """Resumen diario con IA"""
    print(f"\n{'='*60}")
    print("ESCENARIO 5: Resumen diario (con IA parser)")
    print(f"{'='*60}")

    hoy_texto = f"Hoy {datetime.now().strftime('%Y-%m-%d')} tengo check-in de María García (4 pax), check-out de Juan Pérez y limpieza a las 11."
    resultado = parsear(hoy_texto)
    print(f"  Resultado del parser en texto libre: method={resultado.method} conf={resultado.confidence:.2f} ok={resultado.ok}")
    if resultado.ok:
        print(f"  Datos extraídos: {resultado.data}")

    noti = f"📋 HOY {datetime.now().strftime('%Y-%m-%d')}\n"
    if not DRY:
        r = CalendarConnector().list_upcoming(20)
        events = r.data.get("events", [])
        hoy = datetime.now().strftime("%Y-%m-%d")
        hoy_events = [e for e in events if hoy in e.get("start", "")]
        noti += f"Eventos hoy: {len(hoy_events)}\n"
        for e in hoy_events:
            noti += f"  {e['start'][:16]} {e['summary']}\n"
    else:
        noti += (
            f"  Check-in: María García (4pax) 15:00\n"
            f"  Check-out: Juan Pérez 10:00\n"
            f"  Limpieza: 11:00-14:00\n"
        )

    parser_line = f"[🤖 parser: {resultado.method} conf:{resultado.confidence:.2f}]" if resultado.ok else "[📐 fallback regex]"
    noti += parser_line
    notify_team(noti)

def escenario_6_flujo_completo_con_revision():
    """Flujo completo booking → revisión → aprobación con IA"""
    print(f"\n{'='*60}")
    print("ESCENARIO 6: Flujo completo con revisión (con IA parser)")
    print(f"{'='*60}")

    ticket_gt = {
        "id": str(uuid.uuid4())[:8],
        "guest": "Pedro Rodríguez",
        "pax": 3,
        "check_in": "2026-07-01",
        "check_out": "2026-07-05",
        "source": "WhatsApp directo",
        "amount": "420000",
        "estado": "pendiente_revision",
        "creado_por": "Ayelen",
        "revisado_por": None
    }

    parsed = probar_parser("Ticket - Pedro Rodríguez", ticket_gt)

    tickets = BASE / "tickets.json"
    existing = json.loads(tickets.read_text()) if tickets.exists() else []
    existing.append({
        **ticket_gt,
        "_parser_method": parsed.get("_parser_method", "?"),
        "_parser_confidence": parsed.get("_parser_confidence", 0),
    })
    tickets.write_text(json.dumps(existing, indent=2, ensure_ascii=False))
    log("🎫 Ticket pendiente de revisión", ConnectorResult(ok=True, data={"id": ticket_gt["id"], "guest": ticket_gt["guest"]}))

    method_icon = "🤖" if parsed.get("_parser_method", "").startswith("ia") else "📐"
    amt = ticket_gt.get("amount", "0")
    try:
        amt_fmt = f"${int(amt):,}"
    except (ValueError, TypeError):
        amt_fmt = f"${amt}"
    notify_team(
        f"🎫 NUEVO TICKET #{ticket_gt['id']} (pendiente)\n"
        f"{ticket_gt['guest']} - {ticket_gt['pax']} pax\n"
        f"{ticket_gt['check_in']} → {ticket_gt['check_out']}\n"
        f"💰 {amt_fmt}\n"
        f"Creado por: {ticket_gt['creado_por']}\n"
        f"👉 Leo: necesitás aprobar esta reserva.\n"
        f"[{method_icon} {parsed.get('_parser_method','?')} conf:{parsed.get('_parser_confidence',0):.2f}]"
    )

    # Simular aprobación
    ticket_gt["estado"] = "aprobado"
    ticket_gt["revisado_por"] = "Leo"
    existing[-1] = ticket_gt
    tickets.write_text(json.dumps(existing, indent=2, ensure_ascii=False))
    log("✅ Ticket aprobado por Leo", ConnectorResult(ok=True, data=ticket_gt))

    if not DRY:
        r = KommoConnector().create_lead(
            f"Reserva {ticket_gt['guest']}",
            {"contacts": [{"name": ticket_gt["guest"]}], "pipeline_id": 13768223}
        )
        log("Kommo lead creado tras aprobación", r)

        r = CalendarConnector().create_event(
            f"🟢 IN: {ticket_gt['guest']} ({ticket_gt['pax']}pax)",
            f"{ticket_gt['check_in']}T14:00:00",
            f"{ticket_gt['check_in']}T15:00:00",
            f"Aprobado por {ticket_gt['revisado_por']}\nParser: {parsed.get('_parser_method','?')}"
        )
        log("Calendar check-in", r)
    else:
        log("Kommo + Calendar post-aprobación", ConnectorResult(ok=True, data={"dry": True}))

    notify_team(
        f"✅ TICKET #{ticket_gt['id']} APROBADO por {ticket_gt['revisado_por']}\n"
        f"{ticket_gt['guest']} - acciones ejecutadas.\n"
        f"Diego: prepará la casa para el {ticket_gt['check_in']}.\n"
        f"[{method_icon} parser activo]"
    )


if __name__ == "__main__":
    DRY = "--real" not in sys.argv

    print(f"Modo: {'🔧 SIMULACIÓN (dry_run)' if DRY else '🚀 PRODUCCIÓN'}")
    print(f"Endpoint IA: {IA_ENDPOINT or 'no configurado'}")
    print(f"Modelo IA: {IA_MODEL or 'ninguno'}")
    print()

    escenario_1_nueva_reserva()
    escenario_2_checkin()
    escenario_3_problema()
    escenario_4_checkout()
    escenario_5_resumen_diario()
    escenario_6_flujo_completo_con_revision()

    print(f"\n{'='*60}")
    print("RESUMEN")
    print(f"{'='*60}")
    for line in LOG:
        print(line)

    # Reporte del parser
    reportar_parser_stats()

    print(f"\nArchivos generados en {BASE}/:")
    for f in ["tickets.json", "incidentes.json", "pagos.json", "parser_report.json"]:
        p = BASE / f
        if p.exists():
            print(f"  {f}: {p.stat().st_size} bytes")
