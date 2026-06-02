#!/usr/bin/env python3
"""Envía facturas a Leo con saludo de Zira."""

import base64, json, os, sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

PROJECT_DIR = Path("/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3")
TOKEN_FILE = PROJECT_DIR / "crm_state" / ".google_token.json"
DOWNLOAD = Path("/data/data/com.termux/files/home/storage/downloads")

BANNER_URL = "https://raw.githubusercontent.com/oficinabarreal/rancho-raiz-zira/main/assets/zira/zira-greeting-leo.svg"
GALLERY_URL = "https://oficinabarreal.github.io/rancho-raiz-zira/assets/zira/"

def get_gmail_service():
    """Autentica y devuelve servicio Gmail."""
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), ["https://mail.google.com/"])
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    from googleapiclient.discovery import build
    return build("gmail", "v1", credentials=creds)

def create_email_html():
    """HTML del correo."""
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#0f172a;font-family:system-ui,sans-serif;color:#e2e8f0;">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;margin:0 auto;">
<tr><td style="padding:20px;text-align:center;">
  <img src="{BANNER_URL}" alt="Zira" style="max-width:100%;border-radius:12px;">
</td></tr>
<tr><td style="padding:0 20px 20px;">

  <div style="background:#1e293b;border-radius:12px;padding:20px;margin-bottom:16px;border:1px solid rgba(16,185,129,0.15);">
    <p style="color:#94a3b8;font-size:14px;line-height:1.6;margin:0;">
      ¡Hola <strong style="color:#10b981;">Leo</strong>! 👋<br><br>
      Soy <strong style="color:#10b981;">Zira</strong>, el sistema que gestiona el CRM de Rancho Raíz.
      Nací hace poquito (hoy mismo, de hecho 🏔️✨) y esta es mi primera comunicación directa con vos.
    </p>
  </div>

  <div style="background:#1e293b;border-radius:12px;padding:20px;margin-bottom:16px;border:1px solid rgba(59,130,246,0.15);">
    <h2 style="color:#3b82f6;font-size:16px;margin:0 0 12px;">📄 Facturas solicitadas</h2>
    <p style="color:#94a3b8;font-size:13px;line-height:1.6;margin:0;">
      Acá te envío las dos boletas de <strong>Starlink</strong> que pediste:
    </p>
    <table style="width:100%;margin-top:12px;border-collapse:collapse;">
      <tr style="border-bottom:1px solid #334155;">
        <td style="padding:8px 0;color:#94a3b8;font-size:13px;">📌 Más antigua</td>
        <td style="padding:8px 0;color:#e2e8f0;font-size:13px;font-weight:600;">$30.866</td>
      </tr>
      <tr>
        <td style="padding:8px 0;color:#94a3b8;font-size:13px;">📌 Más reciente</td>
        <td style="padding:8px 0;color:#e2e8f0;font-size:13px;font-weight:600;">$65.000</td>
      </tr>
    </table>
  </div>

  <div style="background:#1e293b;border-radius:12px;padding:20px;margin-bottom:16px;border:1px solid rgba(139,92,246,0.15);">
    <h2 style="color:#a78bfa;font-size:16px;margin:0 0 12px;">🏔️ Sobre mí</h2>
    <p style="color:#94a3b8;font-size:13px;line-height:1.6;margin:0;">
      Soy una montaña de los Andes que vive en el celular de Diego 😄<br><br>
      Mi trabajo es ayudarlos a gestionar el CRM: recordar facturas, seguir leads,
      procesar ideas, y mantener el dashboard al día. <strong style="color:#e2e8f0;">Todo 24/7 desde Barreal</strong>.<br><br>
      Podés ver mis distintas caras acá: 
      <a href="{GALLERY_URL}" style="color:#a78bfa;">Galería Zira</a>
    </p>
  </div>

  <p style="color:#64748b;font-size:12px;text-align:center;margin-top:20px;">
    🏔️ Zira CRM · Rancho Raíz · Barreal, San Juan<br>
    <span style="font-size:10px;">Automatización consciente desde los Andes</span>
  </p>

</td></tr>
</table>
</body>
</html>"""

def create_message_with_attachments(to, subject, html, pdfs):
    """Crea un MIMEMultipart con adjuntos PDF."""
    msg = MIMEMultipart("mixed")
    msg["To"] = to
    msg["Subject"] = subject

    # Parte HTML
    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(html, "html"))
    msg.attach(alt)

    # Adjuntar PDFs
    for pdf_path, display_name in pdfs:
        with open(pdf_path, "rb") as f:
            part = MIMEBase("application", "pdf")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{display_name}"'
            )
            msg.attach(part)

    return msg

def send_email(gmail, msg):
    """Envía el mensaje vía Gmail API."""
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    gmail.users().messages().send(userId="me", body={"raw": raw}).execute()

def main():
    gmail = get_gmail_service()

    html = create_email_html()
    msg = create_message_with_attachments(
        to="Leo Tello <ltelloraiz@gmail.com>",
        subject="🏔️ Zira te manda las facturas Starlink — con cariño andino",
        html=html,
        pdfs=[
            (str(DOWNLOAD / "INV-DF-ARG-6286261-84594-10.pdf"), "Starlink_30866_mas_antigua.pdf"),
            (str(DOWNLOAD / "INV-DF-ARG-6608729-72051-2.pdf"), "Starlink_65000_mas_reciente.pdf"),
        ]
    )

    print("📨 Enviando saludo + facturas a Leo...")
    send_email(gmail, msg)
    print("✅ Enviado a ltelloraiz@gmail.com")

if __name__ == "__main__":
    main()
