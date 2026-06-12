#!/usr/bin/env python3
"""
Envía el link de la demo de simulación de chats al equipo,
para que vean la demo interactiva antes de leer el informe.
"""

import base64
import sys
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

TOKEN_FILE = PROJECT_DIR / "crm_state" / ".google_token.json"
SIMULACION_URL = "https://oficinabarreal.github.io/rancho-raiz-zira/simulaciones/chats/index.html"

RECIPIENTS = [
    "Leo Tello <ltelloraiz@gmail.com>",
    "Ramonleandrotello@gmail.com",
    "Ayelen Juricevic <ayelenjuricevic@gmail.com>",
]
BCC = ["Diego <oficinabarreal@gmail.com>"]

SUBJECT = "👁️ Primero mirá la demo — después leé el informe"


def build_html():
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#0a0a0f;font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#e4e4e7;">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;margin:0 auto;">

  <tr>
    <td style="padding:40px 20px 10px;text-align:center;">
      <div style="font-size:52px;margin-bottom:12px;">🏔️</div>
      <h1 style="color:#f4f4f5;font-size:20px;font-weight:700;margin:0 0 6px;">Antes de leer el informe...</h1>
      <p style="color:#71717a;font-size:13px;margin:0 0 20px;line-height:1.5;">
        Te compartimos la <strong style="color:#d4d4d8;">demo interactiva</strong> para que veas<br>
        cómo Zira conversa con huéspedes en cada etapa,<br>
        desde Instagram hasta el seguimiento post-estadía.
      </p>
    </td>
  </tr>

  <!-- BOTÓN GRANDE -->
  <tr>
    <td style="padding:0 20px;">
      <a href="{SIMULACION_URL}" target="_blank"
         style="display:block;background:linear-gradient(135deg,#e0115f,#f77737,#fca130);
                border-radius:18px;padding:28px 20px;text-align:center;
                text-decoration:none;box-shadow:0 8px 32px rgba(225,48,108,0.3);">
        <div style="font-size:36px;margin-bottom:10px;">🎬</div>
        <div style="color:#fff;font-size:22px;font-weight:800;letter-spacing:-0.3px;">
          Ver Demo Interactiva
        </div>
        <div style="color:rgba(255,255,255,0.75);font-size:12px;margin-top:6px;">
          Simulación completa · Instagram · WhatsApp · Clima · Seguimiento
        </div>
      </a>
    </td>
  </tr>

  <tr>
    <td style="padding:24px 20px 0;text-align:center;">
      <p style="color:#71717a;font-size:12px;line-height:1.6;margin:0 0 4px;">
        Después de ver la demo, leé el informe que te mandamos antes:<br>
        <strong style="color:#d4d4d8;">"Zira: Evolución y Propuesta para el Equipo"</strong>
      </p>
      <p style="color:#52525b;font-size:11px;margin:12px 0 0;">
        La demo muestra el viaje completo de Lucía — una huésped que descubre<br>
        Rancho Raíz en Instagram, reserva, recibe alerta del clima,<br>
        tiene seguimiento durante su estadía y deja reseña.
      </p>
    </td>
  </tr>

  <tr>
    <td style="padding:20px;text-align:center;">
      <div style="font-size:10px;color:#3f3f46;">
        <div>🏔️ Zira · Rancho Raíz CRM · Barreal, San Juan</div>
      </div>
    </td>
  </tr>

</table>
</body>
</html>"""


def get_service():
    from googleapiclient.discovery import build
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), ["https://mail.google.com/"])
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())
        else:
            print("❌ Token inválido")
            sys.exit(1)
    return build("gmail", "v1", credentials=creds)


def main():
    print("🔐 Conectando...")
    svc = get_service()
    print("✅ Conectado")

    bcc_str = ", ".join(BCC)
    html = build_html()

    for r in RECIPIENTS:
        print(f"  📧 Enviando a {r}...")
        msg = MIMEMultipart("mixed")
        msg["To"] = r
        msg["Subject"] = SUBJECT
        msg["Bcc"] = bcc_str
        alt = MIMEMultipart("alternative")
        alt.attach(MIMEText(f"Abrí la demo acá: {SIMULACION_URL}", "plain", "utf-8"))
        alt.attach(MIMEText(html, "html", "utf-8"))
        msg.attach(alt)
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        result = svc.users().messages().send(userId="me", body={"raw": raw}).execute()
        print(f"     ✅ Enviado (id: {result.get('id', '?')})")

    print(f"\n✅ Listo. {len(RECIPIENTS)} emails con link a la demo.")


if __name__ == "__main__":
    main()
