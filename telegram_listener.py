from __future__ import annotations
import json, os, re, sys, time
from datetime import datetime
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crm.connectors import TelegramConnector, ConnectorResult
from equipo import EQUIPO, HUESPEDES_REGISTRADOS

BASE = Path(__file__).resolve().parent / "crm_state"
OFFSET_FILE = BASE / ".tg_offset"


def cargar_env(path: Path):
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


def quien_es(nombre: str) -> str:
    nombre = nombre.strip().lower()
    for key, m in EQUIPO.items():
        for alias in m["alias"]:
            if alias.lower() in nombre or nombre in alias.lower():
                return key
    return "desconocido"


def parsear_mensaje(texto: str) -> Optional[dict]:
    """Intenta extraer datos de reserva de un mensaje."""

    data = {"raw": texto}

    # Detectar quién envía (TODO: usar remitente real)
    # Nombre del huésped (primera línea o después de "Huésped:")
    for p in ["huésped", "huesped", "nombre", "cliente", "guest"]:
        m = re.search(rf"{p}[\s:]*([A-ZÁÉÍÓÚÜÑa-záéíóúüñ]+(?:\s+[A-ZÁÉÍÓÚÜÑa-záéíóúüñ]+)+)", texto, re.IGNORECASE)
        if m:
            data["name"] = m.group(1).strip()
            break
    if "name" not in data:
        lines = [l.strip() for l in texto.split("\n") if l.strip()]
        if lines:
            data["name"] = lines[0]

    # Pax
    m = re.search(r"(\d+)\s*(pax|personas|adultos|huéspedes)", texto, re.IGNORECASE)
    if m:
        data["pax"] = int(m.group(1))

    # Fechas
    fecha_pat = r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}"
    fechas = re.findall(fecha_pat, texto)
    if len(fechas) >= 2:
        data["check_in"] = fechas[0]
        data["check_out"] = fechas[1]
    elif len(fechas) == 1:
        data["check_in"] = fechas[0]
        m = re.search(r"(hasta|al)\s*" + fecha_pat, texto)
        if m:
            data["check_out"] = re.search(fecha_pat, m.group())[0]

    # Monto
    m = re.search(r"\$[\s]*([\d.,]+)", texto)
    if m:
        data["amount"] = m.group(1)

    # Teléfono
    m = re.search(r"(\+?\d{7,15})", texto)
    if m:
        data["phone"] = m.group(1)

    # Origen
    for src in ["booking", "airbnb", "whatsapp", "instagram", "directo", "web"]:
        if src in texto.lower():
            data["source"] = src.capitalize()
            break

    return data if data.get("name") else None


def procesar_mensaje(texto: str, remitente: str = ""):
    """Procesa un mensaje entrante como posible reserva."""
    from workflow_reserva import ejecutar_reserva

    print(f"\n📩 Mensaje de {remitente}: {texto[:80]}...")
    data = parsear_mensaje(texto)

    if not data:
        msg = (
            "🤖 No entendí el formato. Enviá la reserva así:\n\n"
            "Huésped: Nombre Apellido\n"
            "Pax: 4\n"
            "Check-in: 15/07/2026\n"
            "Check-out: 18/07/2026\n"
            "Monto: $350000\n"
            "Tel: +54 9 264 555-0101"
        )
        TelegramConnector().send_message(msg)
        return

    # Confirmar antes de ejecutar
    preview = (
        f"📋 ¿Confirmás esta reserva?\n\n"
        f"🧑 {data.get('name', '?')}\n"
        f"👥 {data.get('pax', '?')} pax\n"
        f"📅 {data.get('check_in', '?')} → {data.get('check_out', '?')}\n"
        f"💰 ${data.get('amount', '?')}\n"
        f"📱 {data.get('phone', '?')}\n"
        f"🌐 {data.get('source', '?')}\n\n"
        f"Respondé 'si' para ejecutar."
    )
    TelegramConnector().send_message(preview)


def polling_loop(interval: int = 30):
    """Escucha mensajes nuevos en el bot de Telegram."""
    tg = TelegramConnector()
    if not tg.token:
        print("❌ No hay token de Telegram configurado")
        return

    offset = 0
    if OFFSET_FILE.exists():
        offset = int(OFFSET_FILE.read_text().strip())

    print(f"🤖 Escuchando mensajes en Telegram (offset={offset}, cada {interval}s)...")
    print("  Enviá una reserva al bot para procesarla")
    print()

    while True:
        try:
            import urllib.request, urllib.parse

            url = f"https://api.telegram.org/bot{tg.token}/getUpdates"
            params = {"offset": offset + 1, "timeout": interval}
            req = urllib.request.Request(url + "?" + urllib.parse.urlencode(params))
            with urllib.request.urlopen(req, timeout=interval + 5) as resp:
                data = json.loads(resp.read())

            for update in data.get("result", []):
                offset = update["update_id"]
                msg = update.get("message", {})
                text = msg.get("text", "")
                sender = msg.get("from", {}).get("first_name", "")
                chat_id = msg.get("chat", {}).get("id", 0)

                if not text:
                    continue

                # Respuesta afirmativa a una confirmación
                if text.strip().lower() in ("si", "sí", "yes", "ok", "dale", "confirmo"):
                    TelegramConnector().send_message("✅ Ejecutando workflow...")
                    continue

                procesar_mensaje(text, sender)

            OFFSET_FILE.write_text(str(offset))

        except KeyboardInterrupt:
            print("\n👋 Listener detenido")
            break
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(interval)


if __name__ == "__main__":
    cargar_env(Path(__file__).resolve().parent / ".env")

    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Modo único: lee mensajes nuevos y sale
        print("🔍 Revisando mensajes nuevos...")
        import urllib.request, urllib.parse
        tg = TelegramConnector()
        offset = 0
        if OFFSET_FILE.exists():
            offset = int(OFFSET_FILE.read_text().strip())
        url = f"https://api.telegram.org/bot{tg.token}/getUpdates"
        params = {"offset": offset + 1}
        req = urllib.request.Request(url + "?" + urllib.parse.urlencode(params))
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        for update in data.get("result", []):
            offset = update["update_id"]
            msg = update.get("message", {})
            text = msg.get("text", "")
            sender = msg.get("from", {}).get("first_name", "")
            if text:
                procesar_mensaje(text, sender)
        OFFSET_FILE.write_text(str(offset))
    else:
        polling_loop()
