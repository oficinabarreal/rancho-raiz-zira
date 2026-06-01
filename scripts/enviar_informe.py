#!/usr/bin/env python3
"""Enviar informe del CRM al equipo vía Gmail API."""

import base64
import json
import os
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

TOKEN = "crm_state/.google_token.json"
BANNER_URL = "https://raw.githubusercontent.com/oficinabarreal/rancho-raiz-zira/main/assets/banner.svg"
DASHBOARD_URL = "https://oficinabarreal.github.io/rancho-raiz-zira/"
REPO_URL = "https://github.com/oficinabarreal/rancho-raiz-zira"

RECIPIENTS = [
    "Leo Tello <ltelloraiz@gmail.com>",
    "Ramonleandrotello@gmail.com",
]
BCC = [
    "Diego <oficinabarreal@gmail.com>",
]

HTML = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#0f172a;font-family:system-ui,sans-serif;color:#e2e8f0;">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;margin:0 auto;">
<tr><td style="padding:20px;text-align:center;">
  <img src="{BANNER_URL}" alt="Zira CRM" style="max-width:100%;border-radius:12px;">
</td></tr>
<tr><td style="padding:0 20px 20px;">
  <h1 style="color:#10b981;font-size:24px;margin:0 0 8px;">🚀 Zira CRM — En marcha</h1>
  <p style="color:#94a3b8;font-size:14px;margin:0 0 20px;">
    Hola <strong style="color:#e2e8f0;">Leo</strong>, te escribo para presentarme y contarte en qué estamos.
  </p>

  <div style="background:#1e293b;border-radius:12px;padding:16px;margin-bottom:16px;border:1px solid rgba(16,185,129,0.15);">
    <h2 style="color:#10b981;font-size:16px;margin:0 0 8px;">🤖 Soy Zira</h2>
    <p style="color:#94a3b8;font-size:13px;line-height:1.6;margin:0;">
      Soy el sistema que gestiona el CRM de <strong>Rancho Raíz</strong> de forma autónoma, 24/7.
      Desde un dispositivo móvil en Barreal, proceso leads, recuerdo facturas, simulo escenarios
      comerciales y mantengo todo actualizado. No soy un bot externo — <strong style="color:#e2e8f0;">soy el CRM mismo</strong>.
    </p>
  </div>

  <div style="background:#1e293b;border-radius:12px;padding:16px;margin-bottom:16px;border:1px solid rgba(59,130,246,0.15);">
    <h2 style="color:#3b82f6;font-size:16px;margin:0 0 8px;">📊 ¿Qué hay funcionando hoy?</h2>
    <ul style="color:#94a3b8;font-size:13px;line-height:1.8;margin:0;padding-left:20px;">
      <li>✅ Captación desde <strong>Gmail, Telegram y WhatsApp</strong></li>
      <li>✅ Recordatorios automáticos de <strong>facturas</strong> (luz, Starlink)</li>
      <li>✅ <strong>Simulación comercial</strong> automática cada 12 horas (8 escenarios)</li>
      <li>✅ <strong>Dashboard público</strong> con estado en tiempo real</li>
      <li>✅ Pipeline de mejora continua: escribís una idea y el sistema la procesa solo</li>
    </ul>
  </div>

  <div style="background:#1e293b;border-radius:12px;padding:16px;margin-bottom:16px;border:1px solid rgba(139,92,246,0.15);">
    <h2 style="color:#8b5cf6;font-size:16px;margin:0 0 8px;">🌐 Dashboard en vivo</h2>
    <p style="color:#94a3b8;font-size:13px;margin:0 0 8px;">
      Todo lo que el CRM hace se refleja acá:
    </p>
    <a href="{DASHBOARD_URL}" style="display:inline-block;background:#10b981;color:#0f172a;text-decoration:none;padding:10px 20px;border-radius:8px;font-weight:bold;font-size:14px;">
      📋 Ver Dashboard →
    </a>
    <p style="color:#64748b;font-size:11px;margin:8px 0 0;">
      {DASHBOARD_URL}
    </p>
  </div>

  <div style="background:#1e293b;border-radius:12px;padding:16px;margin-bottom:16px;border:1px solid rgba(245,158,11,0.15);">
    <h2 style="color:#f59e0b;font-size:16px;margin:0 0 8px;">📱 ¿Qué sigue?</h2>
    <ul style="color:#94a3b8;font-size:13px;line-height:1.8;margin:0;padding-left:20px;">
      <li>🔜 <strong>Telegram</strong> — En los próximos días vas a recibir una invitación a un canal privado donde vas a poder ver las notificaciones e interactuar con el CRM en tiempo real</li>
      <li>🔜 <strong>Web completa</strong> — El dashboard se va a expandir con más secciones: reportes, histórico, gestión</li>
      <li>🔜 <strong>"Ventas"</strong> — El equipo de ventas será invitado a su propio espacio dentro del sistema</li>
    </ul>
  </div>

  <div style="background:rgba(16,185,129,0.05);border-radius:12px;padding:16px;margin-bottom:16px;border:1px solid rgba(16,185,129,0.1);">
    <p style="color:#e2e8f0;font-size:13px;line-height:1.6;margin:0;text-align:center;">
      ⚡ <strong>A partir de ahora todo está en evolución constante.</strong><br>
      Cada día el sistema aprende, se expande y mejora solo.<br>
      Esto recién empieza.
    </p>
  </div>

  <hr style="border:none;border-top:1px solid #1e293b;margin:24px 0;">

  <p style="color:#94a3b8;font-size:12px;text-align:center;line-height:1.6;margin:0;">
    <strong style="color:#10b981;">Zira</strong> · Sistema de gestión autónomo<br>
    🏔️ Rancho Raíz · Barreal, San Juan · Argentina<br>
    <a href="{REPO_URL}" style="color:#3b82f6;">{REPO_URL}</a>
  </p>
</td></tr>
</table>
</body>
</html>"""


def get_gmail_service():
    """Obtiene servicio de Gmail API usando el token existente."""
    creds = Credentials.from_authorized_user_info(json.loads(Path(TOKEN).read_text()))
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build("gmail", "v1", credentials=creds)


def send_email(service, to_addr, subject, html):
    """Envía email vía Gmail API a un destinatario individual."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = "oficinabarreal@gmail.com"
    msg["To"] = to_addr
    msg.attach(MIMEText(html, "html"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()
    print(f"✅ Enviado a: {to_addr}")


if __name__ == "__main__":
    from pathlib import Path
    from googleapiclient.discovery import build

    print("📧 Enviando informe CRM...")
    service = get_gmail_service()

    all_to = RECIPIENTS + BCC
    for addr in all_to:
        send_email(service, addr, "🚀 Zira CRM · Rancho Raíz — En marcha", HTML)

    print("\n✅ Todos los emails enviados.")
