"""Gateway de OpenClaw — recibe instrucciones del servidor híbrido y ejecuta contra APIs reales."""
from __future__ import annotations
import json, os, re, sys, uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# Cargar .env manualmente para que los conectores tengan los tokens
ENV_FILE = Path(__file__).resolve().parent / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ[k.strip()] = v.strip()  # override, not setdefault

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from crm.connectors import (
    TelegramConnector, KommoConnector, CalendarConnector,
    SheetsConnector, GmailConnector, WhatsAppConnector,
    DocsConnector, AndroidCuaConnector
)

HOST = "127.0.0.1"
PORT = 8082
LOG = []


def send_telegram(payload: dict) -> dict:
    chat_id = payload.get("chat_id", "")
    text = payload.get("text", "")
    r = TelegramConnector().send_message(text)
    return {"ok": r.ok, "data": r.data if r.ok else r.error}


def send_whatsapp(payload: dict) -> dict:
    to = payload.get("to", "5492645480313")
    text = payload.get("text", "")
    r = WhatsAppConnector().send_message(to, text)
    return {"ok": r.ok, "data": r.data if r.ok else r.error}


def create_kommo_lead(payload: dict) -> dict:
    name = payload.get("name", "Lead")
    contacts = payload.get("contacts", [])
    pipeline_id = payload.get("pipeline_id", 13768223)
    contact_data = {"contacts": [{"name": c.get("name", name), "custom_fields_values": [
        {"field_id": None, "values": [{"value": c.get("phone", "")}]}
    ] if c.get("phone") else []} for c in contacts]}
    r = KommoConnector().create_lead(name, {**contact_data, "pipeline_id": pipeline_id})
    return {"ok": r.ok, "data": r.data if r.ok else r.error}


def _fix_date(dt: str) -> str:
    """Convierte DD/MM/YYYY a YYYY-MM-DD en un datetime ISO."""
    m = re.match(r"(\d{2})[/.-](\d{2})[/.-](\d{4})", dt)
    if m:
        return dt.replace(m.group(0), f"{m.group(3)}-{m.group(2)}-{m.group(1)}")
    return dt

def create_calendar_event(payload: dict) -> dict:
    summary = payload.get("summary", "Evento")
    start = _fix_date(payload.get("start", ""))
    end = _fix_date(payload.get("end", ""))
    desc = payload.get("description", "")
    r = CalendarConnector().create_event(summary, start, end, desc)
    return {"ok": r.ok, "data": r.data if r.ok else r.error}


def append_sheets(payload: dict) -> dict:
    sheet_id = payload.get("spreadsheet_id", "1JwcJs_MfcSfvMrrOIznobsIXBcHHAUGbPC2jLIMRjYU")
    values = payload.get("values", [])
    r = SheetsConnector().append_row(sheet_id, values)
    return {"ok": r.ok, "data": r.data if r.ok else r.error}


def send_gmail(payload: dict) -> dict:
    to = payload.get("to", "")
    subject = payload.get("subject", "")
    body = payload.get("body", "")
    r = GmailConnector().send_message(to, subject, body)
    return {"ok": r.ok, "data": r.data if r.ok else r.error}


def send_gmail_html(payload: dict) -> dict:
    """Envía email con cuerpo HTML."""
    import base64, email.mime.text
    to = payload.get("to", "")
    subject = payload.get("subject", "")
    html = payload.get("html", "")
    try:
        svc = GmailConnector()._svc()
        if not svc:
            return {"ok": False, "data": {}} # dry_run
        msg = email.mime.text.MIMEText(html, "html")
        msg["To"] = to
        msg["Subject"] = subject
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        resp = svc.users().messages().send(userId="me", body={"raw": raw}).execute()
        return {"ok": True, "data": {"message_id": resp["id"], "thread_id": resp.get("threadId", "")}}
    except Exception as e:
        return {"ok": False, "data": {}, "error": str(e)}


ACTION_MAP = {
    "telegram.send_message": send_telegram,
    "whatsapp.send_message": send_whatsapp,
    "kommo.create_lead": create_kommo_lead,
    "calendar.create_event": create_calendar_event,
    "sheets.append_row": append_sheets,
    "gmail.send_message": send_gmail,
    "gmail.send_html": send_gmail_html,
}


def _cua_dump_ui(p):
    r = AndroidCuaConnector().dump_ui()
    return {"ok": r.ok, "data": r.data, "error": r.error}

def _cua_screenshot(p):
    r = AndroidCuaConnector().screenshot()
    return {"ok": r.ok, "data": r.data, "error": r.error}

def _cua_tap(p):
    r = AndroidCuaConnector().tap(p.get("x", 0), p.get("y", 0))
    return {"ok": r.ok, "data": r.data, "error": r.error}

def _cua_tap_text(p):
    r = AndroidCuaConnector().tap_text(p.get("text", ""), p.get("exact", True))
    return {"ok": r.ok, "data": r.data, "error": r.error}

def _cua_type_text(p):
    r = AndroidCuaConnector().type_text(p.get("text", ""))
    return {"ok": r.ok, "data": r.data, "error": r.error}

def _cua_press_key(p):
    r = AndroidCuaConnector().press_key(p.get("key", ""))
    return {"ok": r.ok, "data": r.data, "error": r.error}

def _cua_swipe(p):
    r = AndroidCuaConnector().swipe(p.get("x1", 0), p.get("y1", 0), p.get("x2", 0), p.get("y2", 0), p.get("duration_ms", 300))
    return {"ok": r.ok, "data": r.data, "error": r.error}

def _cua_open_app(p):
    r = AndroidCuaConnector().open_app(p.get("package", ""))
    return {"ok": r.ok, "data": r.data, "error": r.error}

def _cua_home(p):
    r = AndroidCuaConnector().go_home()
    return {"ok": r.ok, "data": r.data, "error": r.error}

def _cua_back(p):
    r = AndroidCuaConnector().go_back()
    return {"ok": r.ok, "data": r.data, "error": r.error}

def _cua_scroll_down(p):
    r = AndroidCuaConnector().scroll_down()
    return {"ok": r.ok, "data": r.data, "error": r.error}

def _cua_scroll_up(p):
    r = AndroidCuaConnector().scroll_up()
    return {"ok": r.ok, "data": r.data, "error": r.error}

def _cua_find(p):
    r = AndroidCuaConnector().find(p.get("text", ""), p.get("resource_id", ""), p.get("class_name", ""))
    return {"ok": r.ok, "data": r.data, "error": r.error}

def _cua_state(p):
    r = AndroidCuaConnector().get_screen_state()
    return {"ok": r.ok, "data": r.data, "error": r.error}

ACTION_MAP.update({
    "android.cua.dump_ui": _cua_dump_ui,
    "android.cua.screenshot": _cua_screenshot,
    "android.cua.tap": _cua_tap,
    "android.cua.tap_text": _cua_tap_text,
    "android.cua.type_text": _cua_type_text,
    "android.cua.press_key": _cua_press_key,
    "android.cua.swipe": _cua_swipe,
    "android.cua.open_app": _cua_open_app,
    "android.cua.home": _cua_home,
    "android.cua.back": _cua_back,
    "android.cua.scroll_down": _cua_scroll_down,
    "android.cua.scroll_up": _cua_scroll_up,
    "android.cua.find": _cua_find,
    "android.cua.state": _cua_state,
})


class GatewayHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        data = json.loads(body) if body else {}

        if self.path == "/execute":
            action = data.get("action", "")
            payload = data.get("payload", {})
            print(f"\n  ⚡ Gateway ejecuta: {action}")
            print(f"     Payload: {json.dumps(payload, ensure_ascii=False)[:100]}")

            handler = ACTION_MAP.get(action)
            if handler:
                result = handler(payload)
                # Convertir ConnectorResult a dict si es necesario
                if hasattr(result, 'ok'):
                    result = {"ok": result.ok, "data": result.data, "error": result.error}
                status = "✅" if result.get("ok") else "❌"
                print(f"     {status} Resultado: {json.dumps(result, ensure_ascii=False)[:120]}")
                LOG.append({"action": action, "result": result})
            else:
                result = {"ok": False, "error": f"Unknown action: {action}"}
                print(f"     ❌ {result['error']}")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode("utf-8"))

        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "actions": list(ACTION_MAP.keys())}).encode("utf-8"))

        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        if self.path == "/logs":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(LOG[-20:], indent=2, ensure_ascii=False).encode("utf-8"))
        elif self.path == "/health":
            self.do_POST()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), GatewayHandler)
    print(f"🚀 OpenClaw Gateway corriendo en {HOST}:{PORT}")
    print(f"   Acciones disponibles: {', '.join(ACTION_MAP.keys())}")
    print(f"   Esperando instrucciones del servidor híbrido...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Gateway detenido")
        server.server_close()
