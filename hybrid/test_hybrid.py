"""Simula el Gateway enviando eventos al servidor híbrido."""
import requests, json, sys, time, uuid
from datetime import datetime

BASE = "http://127.0.0.1:8081"
RESULTS = []


def test(label: str, endpoint: str, payload: dict) -> dict:
    try:
        r = requests.post(f"{BASE}{endpoint}", json=payload, timeout=15)
        data = r.json()
        ok = r.status_code == 200 and data.get("status") == "ok"
        parser_info = data.get("parser_info", {})
        instructions = data.get("instructions", [])
        RESULTS.append({
            "label": label,
            "ok": ok,
            "status_code": r.status_code,
            "status": data.get("status"),
            "message": data.get("message", ""),
            "parser_method": parser_info.get("method", "N/A"),
            "parser_confidence": parser_info.get("confidence", 0),
            "instructions": len(instructions),
            "instruction_actions": [i["action"] for i in instructions],
        })
        icon = "✅" if ok else "❌"
        print(f"\n  {icon} {label}")
        print(f"     Status: {data.get('status')} | {data.get('message', '')[:60]}")
        if parser_info:
            print(f"     Parser: {parser_info.get('method','?')} conf:{parser_info.get('confidence',0):.2f}")
        if instructions:
            print(f"     Instrucciones ({len(instructions)}): {', '.join(i['action'] for i in instructions)[:80]}")
        return data
    except Exception as e:
        RESULTS.append({"label": label, "ok": False, "error": str(e)})
        print(f"\n  ❌ {label}: {e}")
        return {}


print("=" * 65)
print("🧪 TEST FLUJO COMPLETO — CRM HÍBRIDO vs GATEWAY")
print("=" * 65)

# ── 1. Health check ──
print("\n📌 1. HEALTH CHECK")
r = requests.get(f"{BASE}/health", timeout=5)
print(f"   Status: {r.json()['status']}")
print(f"   IA Parser: {r.json()['ia_parser']}")
print(f"   IA Model: {r.json()['ia_model']}")

# ── 2. Nueva reserva (estilo Booking) ──
print("\n📌 2. NUEVA RESERVA — Booking")
test("Booking - María García", "/webhook/reserva", {
    "event_id": str(uuid.uuid4())[:8],
    "type": "nueva_reserva",
    "source": "gmail",
    "data": {
        "raw_text": "Nueva reserva\nNombre: María García\nPax: 4\nCheck-in: 15/06/2026\nCheck-out: 18/06/2026\nMonto: $345000\nOrigen: Booking\nTel: 5491155550101"
    }
})

# ── 3. Nueva reserva (estilo WhatsApp) ──
print("\n📌 3. NUEVA RESERVA — WhatsApp")
test("WhatsApp - Pedro Rodríguez", "/webhook/reserva", {
    "event_id": str(uuid.uuid4())[:8],
    "type": "nueva_reserva",
    "source": "whatsapp",
    "data": {
        "raw_text": "Hola! Quiero reservar para Pedro Rodríguez, somos 3 personas. Del 01/07/2026 al 05/07/2026. Presupuesto $420000. Mi celu es +54 9 264 548-0313. Directo."
    }
})

# ── 4. Nueva reserva (estilo Telegram / lenguaje natural) ──
print("\n📌 4. NUEVA RESERVA — Telegram (lenguaje natural)")
test("Telegram - Tomás Scala", "/webhook/reserva", {
    "event_id": str(uuid.uuid4())[:8],
    "type": "nueva_reserva",
    "source": "telegram",
    "data": {
        "raw_text": "Buenas! Tengo una reserva para Tomás Scala, 4 personas, del 15/07 al 18/07, $450.000, Booking."
    }
})

# ── 5. Incidente ──
print("\n📌 5. INCIDENTE")
test("Heladera - María García", "/webhook/incidente", {
    "event_id": str(uuid.uuid4())[:8],
    "type": "incidente",
    "source": "telegram",
    "data": {
        "guest": "María García",
        "tipo": "heladera",
        "desc": "No enfría bien. Hace ruido.",
        "severidad": "media",
        "reportado_por": "Diego"
    }
})

# ── 6. Pago ──
print("\n📌 6. PAGO")
test("Pago - Pedro Rodríguez", "/webhook/pago", {
    "event_id": str(uuid.uuid4())[:8],
    "type": "pago",
    "source": "manual",
    "data": {
        "guest": "Pedro Rodríguez",
        "monto": 420000,
        "metodo": "transferencia",
        "fecha": "2026-07-05",
        "recibido_por": "Diego"
    }
})

# ── 7. Informe diario ──
print("\n📌 7. INFORME DIARIO")
test("Informe completo", "/webhook/informe", {
    "event_id": str(uuid.uuid4())[:8],
    "type": "informe_diario",
    "source": "cron",
    "data": {}
})

# ── 8. Ver estado ──
print("\n📌 8. ESTADO FINAL")
for col in ["reservas", "incidentes", "pagos"]:
    r = requests.get(f"{BASE}/state/{col}", timeout=5)
    data = r.json()
    print(f"   {col}: {data['count']} registros")

# ── Reporte ──
print(f"\n{'='*65}")
print("📊 REPORTE DE LA SIMULACIÓN")
print(f"{'='*65}")
print(f"\n{'Escenario':<35} {'Status':<8} {'Parser':<22} {'Conf':<6} {'Inst':<5}")
print("-" * 76)
for r in RESULTS:
    icon = "✅" if r.get("ok") else "❌"
    parser = r.get("parser_method", "N/A")
    conf = r.get("parser_confidence", 0)
    inst = r.get("instructions", 0)
    msg = r.get("message", "")[:40]
    print(f"{r['label']:<35} {icon:<8} {parser:<22} {conf:<6.2f} {inst:<5}")

aciertos = sum(1 for r in RESULTS if r.get("ok"))
print(f"\nTotal: {len(RESULTS)} escenarios | ✅ {aciertos} exitosos | ❌ {len(RESULTS)-aciertos} fallos")
