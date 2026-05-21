from __future__ import annotations
import json, os, sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crm.connectors import (
    GmailConnector, CalendarConnector, KommoConnector,
    TelegramConnector, SheetsConnector, ConnectorResult
)

BASE = Path(__file__).resolve().parent / "crm_state"
BASE.mkdir(parents=True, exist_ok=True)
SHEET_ID = "1JwcJs_MfcSfvMrrOIznobsIXBcHHAUGbPC2jLIMRjYU"
KOMMO_PIPELINE = 13768223


def cargar_env(path: Path):
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


def buscar_reservas_en_mails() -> List[Dict[str, Any]]:
    """Busca mails no leídos con posibles reservas."""
    gmail = GmailConnector()
    r = gmail.list_messages(max_results=20, query="is:unread reserva OR booking OR huésped OR posada OR rancho")
    if not r.ok or not r.data.get("messages"):
        r = gmail.list_messages(max_results=20, query="is:unread")
        if not r.ok:
            print("  ❌ No se pudo leer Gmail:", r.error)
            return []
    return r.data.get("messages", [])


def parsear_reserva(texto: str) -> Optional[Dict[str, Any]]:
    """Extrae datos de reserva del texto usando parser híbrido IA+regex."""
    from parser import parsear
    resultado = parsear(texto)
    if resultado.ok and resultado.data.get("name"):
        return resultado.data
    return None


def mostrar_reserva(data: Dict[str, Any], idx: int):
    name = data.get("name") or "?"
    print(f"\n  [{idx}] {name}")
    print(f"      Pax: {data.get('pax', '?')}")
    print(f"      Check-in: {data.get('check_in', '?')}")
    print(f"      Check-out: {data.get('check_out', '?')}")
    print(f"      Monto: ${data.get('amount', '?')}")
    print(f"      Origen: {data.get('source', '?')}")
    print(f"      Mail: {data.get('from', '?')}")
    print(f"      Tel: {data.get('phone', '?')}")


def ejecutar_reserva(data: Dict[str, Any]) -> Dict[str, str]:
    """Ejecuta el flujo completo para una reserva."""
    resultados = {}

    name = data["name"]
    check_in = data.get("check_in", "")
    check_out = data.get("check_out", "")
    pax = data.get("pax", 2)
    amount = data.get("amount", "")
    source = data.get("source", "Mail")
    phone = data.get("phone", "")

    # 1. Kommo lead
    lead_payload = {"pipeline_id": KOMMO_PIPELINE}
    contact = {"name": name}
    if phone:
        contact["custom_fields_values"] = [
            {"field_id": None, "values": [{"value": phone}]}
        ]
    lead_payload["contacts"] = [contact]

    r = KommoConnector().create_lead(f"Reserva {name}", lead_payload)
    if r.ok:
        lead_id = r.data.get("lead_id", "?")
        resultados["kommo"] = f"Lead #{lead_id}"
        print(f"  ✅ Kommo: lead #{lead_id}")
    else:
        resultados["kommo"] = f"❌ {r.error}"
        print(f"  ❌ Kommo: {r.error[:80]}")

    # 2. Calendar events
    cal = CalendarConnector()
    desc = f"Reserva {name}\nPax: {pax}\nOrigen: {source}\nMonto: ${amount}"
    if check_in:
        try:
            r = cal.create_event(
                f"🟢 IN: {name} ({pax}pax)",
                f"{check_in}T14:00:00",
                f"{check_in}T15:00:00",
                desc
            )
            resultados["calendar_in"] = "OK" if r.ok else "❌"
            print(f"  ✅ Calendar check-in: {name}")
        except Exception:
            resultados["calendar_in"] = "❌"
    if check_out:
        try:
            r = cal.create_event(
                f"🔴 OUT: {name}",
                f"{check_out}T10:00:00",
                f"{check_out}T11:00:00",
                f"Check-out {name}"
            )
            resultados["calendar_out"] = "OK" if r.ok else "❌"
            print(f"  ✅ Calendar check-out: {name}")
        except Exception:
            resultados["calendar_out"] = "❌"

    # 3. Sheets
    sheet_id = data.get("spreadsheet_id", SHEET_ID)
    r = SheetsConnector().append_row(sheet_id, [
        "", name, str(pax), str(check_in), str(check_out),
        str(amount), source
    ])
    if r.ok:
        resultados["sheets"] = "OK"
        print(f"  ✅ Sheets: fila agregada")
    else:
        resultados["sheets"] = f"❌ {r.error}"
        print(f"  ❌ Sheets: {r.error[:80]}")

    # 4. Telegram
    msg = (
        f"🆕 RESERVA NUEVA\n{name} - {pax} pax\n"
        f"Check-in: {check_in}\nCheck-out: {check_out}\n"
        f"💰 ${amount}\n📱 {phone}\n📧 Origen: {source}"
    )
    r = TelegramConnector().send_message(msg)
    if r.ok:
        resultados["telegram"] = "OK"
        print(f"  ✅ Telegram: notificación enviada")
    else:
        resultados["telegram"] = f"❌ {r.error}"
        print(f"  ❌ Telegram: {r.error[:80]}")

    # 5. Guardar en log local
    historial = BASE / "reservas_procesadas.json"
    hist = json.loads(historial.read_text()) if historial.exists() else []
    hist.append({
        "fecha": datetime.now().isoformat(),
        "data": data,
        "resultados": resultados
    })
    historial.write_text(json.dumps(hist, indent=2, ensure_ascii=False))

    return resultados


def main():
    cargar_env(Path(__file__).resolve().parent / ".env")

    print("=" * 60)
    print("WORKFLOW: Gmail → Kommo → Calendar → Sheets → Telegram")
    print("=" * 60)

    # 1. Leer mails
    print("\n📧 Buscando reservas en Gmail...")
    mensajes = buscar_reservas_en_mails()
    reservas = []
    if mensajes:
        print(f"  {len(mensajes)} mails encontrados.")
        for m in mensajes[:5]:
            snippet = m.get("snippet", "") + " " + m.get("subject", "")
            data = parsear_reserva(snippet)
            if data:
                data["from"] = m.get("from", "")
                reservas.append(data)

    if not reservas:
        print("  No se encontraron reservas en los mails.")
        print("\n📋 Usando modo demo con datos de prueba...\n")
        reservas = [
            {"name": "Demo García", "pax": 3, "check_in": "2026-07-15",
             "check_out": "2026-07-18", "amount": "350000",
             "source": "Booking", "phone": "5491155550101",
             "from": "booking@reservas.com"},
            {"name": "Demo Pérez", "pax": 2, "check_in": "2026-08-01",
             "check_out": "2026-08-05", "amount": "420000",
             "source": "Airbnb", "phone": "5491155550202",
             "from": "airbnb@reservas.com"},
        ]

    # 2. Mostrar y confirmar
    print(f"\n📋 {len(reservas)} reservas detectadas:")
    for i, r in enumerate(reservas):
        mostrar_reserva(r, i + 1)

    print("\n" + "=" * 60)
    print("EJECUTANDO flujo completo...")
    print("=" * 60)

    for i, res in enumerate(reservas):
        print(f"\n--- Reserva {i+1}: {res['name']} ---")
        ejecutar_reserva(res)

    print(f"\n" + "=" * 60)
    print("✅ WORKFLOW COMPLETADO")
    print("=" * 60)
    print(f"Historial: {BASE / 'reservas_procesadas.json'}")


if __name__ == "__main__":
    DRY = "--dry" in sys.argv
    main()
