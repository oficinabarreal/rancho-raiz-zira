#!/usr/bin/env python3
"""
OpenClaw — Daemon de automatizacion en segundo plano.
Opciones:
  --cron          Ejecuta tareas programadas y sale
  --webhook PORT  Escucha webhooks en el puerto dado
  --once          Ejecuta una sola ronda de tareas
  --listen        Escucha webhooks permanentemente
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent


def cargar_env(path: Path):
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


cargar_env(HERE / ".env")

PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", str(HERE.parent)))
TG_TOKEN = os.environ.get("CRM_TG_TOKEN", "")
TG_CHAT_ID = os.environ.get("CRM_TG_CHAT_ID", "")
IA_ENDPOINT = os.environ.get("CRM_IA_ENDPOINT", "")
IA_API_KEY = os.environ.get("CRM_IA_API_KEY", "")
IA_MODEL = os.environ.get("CRM_IA_MODEL", "opencode/big-pickle")


def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def tg_notify(text: str):
    if not TG_TOKEN:
        return
    import urllib.request
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    data = json.dumps({"chat_id": TG_CHAT_ID, "text": text}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass


def ia_query(prompt: str, system: str = "") -> str:
    """Consulta el modelo opencode/big-pickle via ia_client (CLI + fallback Zen API)."""
    from ia_client import query
    return query(prompt, system, use_cli=True)


def tareas_cron():
    """Ejecuta las tareas programadas."""
    log("OpenClaw: ejecutando tareas cron...")
    pipeline = PROJECT_ROOT / "pipeline.py"
    resultados = []

    # Tarea 1: Verificar estado del proyecto
    log("  * Verificando pipeline...")
    if pipeline.exists():
        resultados.append(f"Pipeline: presente ({pipeline.stat().st_size} bytes)")
    else:
        resultados.append("Pipeline: NO ENCONTRADO")

    # Tarea 2: Consultar IA para resumen
    prompt = "Resumi el estado actual del proyecto basado en los archivos disponibles."
    respuesta = ia_query(prompt, "Sos un asistente de monitoreo de proyectos.")
    resultados.append(f"IA: {respuesta[:100]}...")

    # Notificar
    resumen = "\n".join(resultados)
    log(f"  Resultados:\n{resumen}")
    tg_notify(f"OpenClaw Cron ({datetime.now().strftime('%d/%m %H:%M')}):\n{resumen}")


def webhook_handler(path: str, headers: dict, body: bytes) -> dict:
    """Procesa webhooks entrantes."""
    log(f"Webhook recibido: {path}")
    try:
        data = json.loads(body) if body else {}
    except json.JSONDecodeError:
        data = {"raw": body.decode(errors="replace")}

    prompt = (
        f"Webhook recibido en {path}\n"
        f"Headers: {json.dumps(dict(headers), indent=2)}\n"
        f"Body: {json.dumps(data, indent=2)}\n\n"
        "Determina si esto requiere accion y cual."
    )
    respuesta = ia_query(prompt, "Sos un automatizador de webhooks. Respondé solo JSON.")
    tg_notify(f"Webhook {path} procesado:\n{respuesta[:200]}")
    return {"status": "ok", "response": respuesta}


def webhook_server(port: int = 8083):
    """Servidor webhook simple."""
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length else b""
            result = webhook_handler(self.path, dict(self.headers), body)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        def log_message(self, fmt, *args):
            log(f"HTTP: {args}")

    server = HTTPServer(("0.0.0.0", port), Handler)
    log(f"OpenClaw escuchando webhooks en puerto {port}...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("Webhook server detenido.")


if __name__ == "__main__":
    if "--once" in sys.argv:
        tareas_cron()
    elif "--cron" in sys.argv:
        tareas_cron()
    elif "--webhook" in sys.argv:
        idx = sys.argv.index("--webhook")
        port = int(sys.argv[idx + 1]) if idx + 1 < len(sys.argv) else 8083
        webhook_server(port)
    elif "--listen" in sys.argv:
        webhook_server(8083)
    else:
        log("OpenClaw disponible.")
        log("  --cron         Ejecutar tareas programadas")
        log("  --webhook PORT Escuchar webhooks en puerto")
        log("  --once         Una sola ronda de tareas")
        log("  --listen       Escuchar webhooks permanentemente")
