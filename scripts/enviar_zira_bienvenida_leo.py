#!/usr/bin/env python3
"""
Envía a Leo el link de la página de bienvenida de Zira para huéspedes.
Es su primer día interactuando con info para huéspedes.
Corto, directo, con el link grande al inicio.
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
GUEST_URL = "https://oficinabarreal.github.io/rancho-raiz-zira/simulaciones/chats/zira-huespedes.html"

RECIPIENTS = [
    "Leo Tello <ltelloraiz@gmail.com>",
    "Ramonleandrotello@gmail.com",
]
BCC = ["Diego <oficinabarreal@gmail.com>"]

SUBJECT = "🏔️ Zira hoy: página de bienvenida para huéspedes"


def build_html():
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#0a0a0f;font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#e4e4e7;">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;margin:0 auto;">

  <tr>
    <td style="padding:40px 20px 10px;text-align:center;">
      <div style="font-size:52px;margin-bottom:12px;">🏔️</div>
      <h1 style="color:#f4f4f5;font-size:20px;font-weight:700;margin:0 0 6px;">
        Hoy es el primer día de Zira
      </h1>
      <p style="color:#71717a;font-size:13px;margin:0 0 20px;line-height:1.5;">
        Recibiendo huéspedes con información útil,<br>
        tal como la pediste.
      </p>
    </td>
  </tr>

  <!-- BOTÓN GRANDE -->
  <tr>
    <td style="padding:0 20px;">
      <a href="{GUEST_URL}" target="_blank"
         style="display:block;background:linear-gradient(135deg,#e0115f,#f77737,#fca130);
                border-radius:18px;padding:28px 20px;text-align:center;
                text-decoration:none;box-shadow:0 8px 32px rgba(225,48,108,0.3);">
        <div style="font-size:36px;margin-bottom:10px;">🌐</div>
        <div style="color:#fff;font-size:22px;font-weight:800;letter-spacing:-0.3px;">
          Ver Página de Bienvenida
        </div>
        <div style="color:rgba(255,255,255,0.75);font-size:12px;margin-top:6px;">
          Zira · Rancho Raíz · Barreal
        </div>
      </a>
    </td>
  </tr>

  <tr>
    <td style="padding:24px 20px 0;text-align:left;">
      <p style="color:#d4d4d8;font-size:13px;line-height:1.7;margin:0 0 10px;">
        <strong>¿Qué es esto?</strong> Una página web que Zira les muestra a los huéspedes
        cuando confirman su reserva. Tiene:
      </p>
      <ul style="color:#a8a29e;font-size:12.5px;line-height:1.8;padding-left:20px;margin:0 0 14px;">
        <li>Datos de la casa (dirección exacta, amenities, horarios)</li>
        <li>Actividades de Barreal (dunas, cabalgatas, astroturismo, etc.)</li>
        <li>Mapa con cómo llegar</li>
        <li>Formulario para que los huéspedes nos cuenten alergias y preferencias</li>
        <li>Botón de WhatsApp directo a Diego</li>
      </ul>
      <p style="color:#d4d4d8;font-size:13px;line-height:1.7;margin:0 0 10px;">
        <strong>✅ Tus pedidos ya están:</strong> incluí el mensaje de Zira sobre
        cuidado de la energía y el medio ambiente — que apaguen luces y calefacción
        al salir, cierren puertas, cuiden el agua.
      </p>
      <p style="color:#a8a29e;font-size:12.5px;line-height:1.7;margin:0 0 10px;">
        Por ahora Zira funciona <strong>como página web</strong> y no como bot de WhatsApp
        (el bot automatizado todavía no es tan eficiente como queremos). La web nos deja
        tener algo sólido desde ahora mientras seguimos mejorando el bot.
      </p>
      <p style="color:#d4d4d8;font-size:13px;line-height:1.7;margin:0 0 4px;">
        <strong>Leonardo:</strong> revisala cuando tengas un momento y decime si te cierra
        esta idea de Zira como asistente de huéspedes vía web. Es corta, mirala y
        cualquier cosa me decís. Queremos arrancar con esto cuanto antes.
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
        alt.attach(MIMEText(f"Abrí la página de bienvenida de Zira acá:\n{GUEST_URL}", "plain", "utf-8"))
        alt.attach(MIMEText(html, "html", "utf-8"))
        msg.attach(alt)
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        result = svc.users().messages().send(userId="me", body={"raw": raw}).execute()
        print(f"     ✅ Enviado (id: {result.get('id', '?')})")

    print(f"\n✅ Listo. {len(RECIPIENTS)} emails enviados a Leo.")


if __name__ == "__main__":
    main()
