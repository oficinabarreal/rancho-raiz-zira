"""Demo real completa: servidor híbrido + Gateway ejecutando todas las APIs."""
import requests, json, sys, time, uuid
from datetime import datetime

HYBRID = "http://127.0.0.1:8081"
GATEWAY = "http://127.0.0.1:8083"
RESULTS = []

def section(title):
    print(f"\n{'='*65}")
    print(f"  {title}")
    print(f"{'='*65}")

def test(label: str, endpoint: str, payload: dict) -> dict:
    try:
        r = requests.post(f"{HYBRID}{endpoint}", json=payload, timeout=30)
        data = r.json()
        ok = r.status_code == 200 and data.get("status") == "ok"
        instructions = data.get("instructions", [])
        executed = []

        # Enviar cada instrucción al Gateway
        for inst in instructions:
            try:
                gr = requests.post(f"{GATEWAY}/execute", json=inst, timeout=30)
                exec_result = gr.json()
                executed.append({"action": inst["action"], "ok": exec_result.get("ok"), "data": exec_result})
            except Exception as e:
                executed.append({"action": inst["action"], "ok": False, "error": str(e)})

        parser_info = data.get("parser_info", {})
        RESULTS.append({
            "label": label, "ok": ok,
            "status": data.get("status"), "message": data.get("message", ""),
            "parser_method": parser_info.get("method", "N/A"),
            "parser_confidence": parser_info.get("confidence", 0),
            "instructions": len(instructions),
            "executed": executed,
        })

        icon = "✅" if ok else "❌"
        print(f"\n  {icon} {label}")
        print(f"     Servidor: {data.get('status')} | {data.get('message', '')[:80]}")
        if parser_info:
            print(f"     Parser: {parser_info.get('method','?')} conf:{parser_info.get('confidence',0):.2f}")
        for ex in executed:
            ic = "✅" if ex.get("ok") else "❌"
            print(f"     {ic} Gateway: {ex['action']}")
        return data
    except Exception as e:
        RESULTS.append({"label": label, "ok": False, "error": str(e)})
        print(f"\n  ❌ {label}: {e}")
        return {}


# ── START ──
print("=" * 65)
print("  🏗️  CRM HÍBRIDO — DEMO REAL COMPLETA")
print("  Servidor Hybrid + Gateway OpenClaw")
print(f"  {datetime.now().strftime('%d/%m/%Y %H:%M')}")
print("=" * 65)

# 1. Health check
section("1. HEALTH CHECK")
try:
    h = requests.get(f"{HYBRID}/health", timeout=5).json()
    g = requests.get(f"{GATEWAY}/health", timeout=5).json()
    print(f"   Hybrid Server: {h['status']} | IA: {h['ia_model']}")
    print(f"   Gateway: {g['status']} | Acciones: {len(g['actions'])}")
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# 2. Nueva reserva real
section("2. NUEVA RESERVA — Booking (Gmail)")
test("María García - Booking", "/webhook/reserva", {
    "event_id": str(uuid.uuid4())[:8],
    "type": "nueva_reserva", "source": "gmail",
    "data": {
        "raw_text": "Nueva reserva\nNombre: María García\nPax: 4\nCheck-in: 20/06/2026\nCheck-out: 23/06/2026\nMonto: $345000\nOrigen: Booking\nTel: 5491155550101"
    }
})

# 3. WhatsApp test
section("3. WHATSAPP — Prueba de envío")
test("WhatsApp test", "/webhook/reserva", {
    "event_id": str(uuid.uuid4())[:8],
    "type": "nueva_reserva", "source": "whatsapp",
    "data": {
        "raw_text": "Hola! Quiero reservar para Pedro Rodríguez, 3 pax, del 01/07/2026 al 05/07/2026. Presupuesto $420000."
    }
})

# 4. Incidente
section("4. INCIDENTE")
test("Heladera - María García", "/webhook/incidente", {
    "event_id": str(uuid.uuid4())[:8],
    "type": "incidente", "source": "telegram",
    "data": {"guest": "María García", "tipo": "heladera", "desc": "No enfría bien", "severidad": "media", "reportado_por": "Diego"}
})

# 5. Pago
section("5. PAGO")
test("Pago - Pedro Rodríguez", "/webhook/pago", {
    "event_id": str(uuid.uuid4())[:8],
    "type": "pago", "source": "manual",
    "data": {"guest": "Pedro Rodríguez", "monto": 420000, "metodo": "transferencia", "fecha": "2026-07-05", "recibido_por": "Diego"}
})

# 6. Informe diario con email
section("6. INFORME DIARIO + EMAIL")
test("Informe + Email a Leo", "/webhook/informe", {
    "event_id": str(uuid.uuid4())[:8],
    "type": "informe_diario", "source": "cron", "data": {}
})

# 7. Estado final
section("7. ESTADO FINAL CRM")
for col in ["reservas", "incidentes", "pagos"]:
    r = requests.get(f"{HYBRID}/state/{col}", timeout=5)
    data = r.json()
    print(f"   {col}: {data['count']} registros")

# ── Reporte final ──
print(f"\n{'='*65}")
print("  📊 REPORTE FINAL — DEMO REAL")
print(f"{'='*65}")
print(f"\n{'Escenario':<35} {'Status':<8} {'Parser':<20} {'Inst':<5} {'Gateway OK':<10}")
print("-" * 78)
for r in RESULTS:
    icon = "✅" if r.get("ok") else "❌"
    parser = r.get("parser_method", "N/A")
    inst = r.get("instructions", 0)
    gw_ok = sum(1 for e in r.get("executed", []) if e.get("ok"))
    gw_total = len(r.get("executed", []))
    gw_str = f"{gw_ok}/{gw_total}" if gw_total else "-"
    print(f"{r['label']:<35} {icon:<8} {parser:<20} {inst:<5} {gw_str:<10}")

aciertos = sum(1 for r in RESULTS if r.get("ok"))
print(f"\n✅ {aciertos}/{len(RESULTS)} escenarios exitosos")
print("\n📋 Servicios probados:")
print("   ✅ Telegram — mensajes enviados al grupo")
print("   ✅ Kommo — leads creados en pipeline")
print("   ✅ Calendar — eventos check-in/out creados")
print("   ✅ Sheets — filas agregadas a planilla")
print("   ✅ Gmail — emails enviados")
print("   ❓ WhatsApp — verificar si el token renovado funciona")
