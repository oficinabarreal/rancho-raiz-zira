#!/usr/bin/env python3
"""
Envía el informe de evolución de Zira al equipo (Leo, Ayelén, Diego)
vía Gmail API usando el HTML del informe como cuerpo del email.
"""

import base64
import json
import os
import sys
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

TOKEN_FILE = PROJECT_DIR / "crm_state" / ".google_token.json"
REPORT_FILE = PROJECT_DIR / "simulaciones" / "chats" / "informe-evolucion-zira.html"
SIMULACION_URL = "https://oficinabarreal.github.io/rancho-raiz-zira/simulaciones/chats/index.html"

RECIPIENTS = [
    "Leo Tello <ltelloraiz@gmail.com>",
    "Ramonleandrotello@gmail.com",
    "Ayelen Juricevic <ayelenjuricevic@gmail.com>",
]
BCC = ["Diego <oficinabarreal@gmail.com>"]

SUBJECT = "🏔️ Zira · Evolución y propuesta para el equipo"


def build_html_email():
    """Construye un HTML apto para email con estilos inline."""
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#0a0a0f;font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#e4e4e7;">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:640px;margin:0 auto;">

  <!-- HERO -->
  <tr>
    <td style="background:linear-gradient(135deg,#e0115f,#f77737,#fca130);border-radius:0 0 28px 28px;padding:36px 20px 40px;text-align:center;">
      <div style="font-size:44px;margin-bottom:10px;">🏔️</div>
      <h1 style="color:#fff;font-size:22px;font-weight:800;margin:0 0 6px;">Zira: Evolución y Propuesta</h1>
      <p style="color:rgba(255,255,255,0.85);font-size:13px;margin:0 0 12px;line-height:1.5;">
        Cómo Zira se integra al equipo, aprende de cada situación,<br>
        y asegura que ningún huésped se quede sin respuesta.
      </p>
      <span style="display:inline-block;background:rgba(255,255,255,0.2);border-radius:20px;padding:4px 14px;color:#fff;font-size:10px;font-weight:600;letter-spacing:0.3px;">🤖 Auto-evolución · Junio 2026</span>
    </td>
  </tr>

  <tr><td style="padding:24px 16px 0;">

    <!-- 1. AUTO-EVOLUCIÓN -->
    <h2 style="font-size:17px;font-weight:700;color:#f4f4f5;margin:0 0 12px;display:flex;align-items:center;gap:8px;">
      <span style="display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:50%;background:linear-gradient(135deg,#e0115f,#f77737);color:#fff;font-size:11px;font-weight:700;margin-right:8px;">1</span>
      Lo que Zira aprendió hoy
    </h2>
    <div style="background:#111115;border-radius:16px;padding:18px 20px;border:1px solid rgba(255,255,255,0.06);margin-bottom:20px;">
      <p style="font-size:13.5px;line-height:1.65;color:#d4d4d8;margin:0 0 14px;">
        Hoy, mientras simulábamos el viaje completo de un huésped —desde que da like a una foto en Instagram hasta que deja su reseña post-estadía— <strong style="color:#f4f4f5;">Zira observó algo importante:</strong>
      </p>
      <div style="background:linear-gradient(135deg,rgba(251,191,36,0.08),rgba(251,191,36,0.02));border:1px solid rgba(251,191,36,0.15);border-radius:12px;padding:14px 16px;margin-bottom:12px;">
        <div style="font-size:20px;margin-bottom:4px;">🌧️</div>
        <p style="font-size:12.5px;color:#d4d4d8;margin:0;line-height:1.5;"><strong style="color:#f4f4f5;">El clima afecta la experiencia.</strong> Si llegan huéspedes y está por llover, Zira puede <strong style="color:#f4f4f5;">avisar antes</strong> con recomendaciones de abrigo, actividades bajo techo, y tranquilizar al huésped. No espera a que pregunten.</p>
      </div>
      <div style="background:linear-gradient(135deg,rgba(251,191,36,0.08),rgba(251,191,36,0.02));border:1px solid rgba(251,191,36,0.15);border-radius:12px;padding:14px 16px;">
        <div style="font-size:20px;margin-bottom:4px;">🔥</div>
        <p style="font-size:12.5px;color:#d4d4d8;margin:0;line-height:1.5;"><strong style="color:#f4f4f5;">Imprevistos pasan.</strong> Una estufa rota, un camino cortado, una reserva que llega de improvisto. Zira puede <strong style="color:#f4f4f5;">coordinar al equipo al instante</strong>.</p>
      </div>
    </div>

    <!-- 2. CAPACIDADES -->
    <h2 style="font-size:17px;font-weight:700;color:#f4f4f5;margin:0 0 12px;">
      <span style="display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:50%;background:linear-gradient(135deg,#e0115f,#f77737);color:#fff;font-size:11px;font-weight:700;margin-right:8px;">2</span>
      Lo que Zira ya puede hacer
    </h2>
    <table width="100%" cellpadding="6" cellspacing="0" style="margin-bottom:20px;">
      <tr>
        <td width="50%" style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.05);border-radius:10px;padding:12px;text-align:center;">
          <div style="font-size:24px;margin-bottom:4px;">🌐</div>
          <div style="font-size:12px;font-weight:600;color:#f4f4f5;">Multi-idioma 24/7</div>
          <div style="font-size:10px;color:#71717a;margin-top:2px;line-height:1.4;">Responde en el idioma del lead. Nunca descansa.</div>
        </td>
        <td width="5"></td>
        <td width="50%" style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.05);border-radius:10px;padding:12px;text-align:center;">
          <div style="font-size:24px;margin-bottom:4px;">📸</div>
          <div style="font-size:12px;font-weight:600;color:#f4f4f5;">Instagram DM</div>
          <div style="font-size:10px;color:#71717a;margin-top:2px;line-height:1.4;">Captura leads desde likes y DMs, deriva a WhatsApp.</div>
        </td>
      </tr>
      <tr><td colspan="3" height="6"></td></tr>
      <tr>
        <td width="50%" style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.05);border-radius:10px;padding:12px;text-align:center;">
          <div style="font-size:24px;margin-bottom:4px;">💬</div>
          <div style="font-size:12px;font-weight:600;color:#f4f4f5;">WhatsApp Completo</div>
          <div style="font-size:10px;color:#71717a;margin-top:2px;line-height:1.4;">Desde consulta hasta seguimiento post-estadía.</div>
        </td>
        <td width="5"></td>
        <td width="50%" style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.05);border-radius:10px;padding:12px;text-align:center;">
          <div style="font-size:24px;margin-bottom:4px;">🤝</div>
          <div style="font-size:12px;font-weight:600;color:#f4f4f5;">Derivación al Equipo</div>
          <div style="font-size:10px;color:#71717a;margin-top:2px;line-height:1.4;">Deriva a Ayelén o Leo con todo el contexto cuando se necesita un humano.</div>
        </td>
      </tr>
      <tr><td colspan="3" height="6"></td></tr>
      <tr>
        <td width="50%" style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.05);border-radius:10px;padding:12px;text-align:center;">
          <div style="font-size:24px;margin-bottom:4px;">🧹</div>
          <div style="font-size:12px;font-weight:600;color:#f4f4f5;">Coordinación Interna</div>
          <div style="font-size:10px;color:#71717a;margin-top:2px;line-height:1.4;">Avisa al equipo: Chiqui prepara, Diego recibe, Leo confirma.</div>
        </td>
        <td width="5"></td>
        <td width="50%" style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.05);border-radius:10px;padding:12px;text-align:center;">
          <div style="font-size:24px;margin-bottom:4px;">🌤️</div>
          <div style="font-size:12px;font-weight:600;color:#f4f4f5;">Alertas Inteligentes</div>
          <div style="font-size:10px;color:#71717a;margin-top:2px;line-height:1.4;">Clima, caminos, eventos. Zira se anticipa sola.</div>
        </td>
      </tr>
    </table>

    <!-- 3. VALOR 24/7 -->
    <h2 style="font-size:17px;font-weight:700;color:#f4f4f5;margin:0 0 12px;">
      <span style="display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:50%;background:linear-gradient(135deg,#e0115f,#f77737);color:#fff;font-size:11px;font-weight:700;margin-right:8px;">3</span>
      El valor de estar siempre
    </h2>
    <div style="background:#111115;border-radius:16px;padding:18px 20px;border:1px solid rgba(255,255,255,0.06);margin-bottom:20px;">
      <p style="font-size:13.5px;line-height:1.65;color:#d4d4d8;margin:0 0 10px;"><strong style="color:#f4f4f5;">Zira no duerme.</strong> Cuando llega un mensaje a Instagram o WhatsApp a las 2am, Zira responde al instante en el idioma del lead, da la info que necesita, y si el lead quiere reservar, le toma los datos y deriva a Ayelén.</p>
      <p style="font-size:13.5px;line-height:1.65;color:#d4d4d8;margin:0;"><strong style="color:#f4f4f5;">En cualquier idioma.</strong> Si llega un turista de Brasil, Francia o Estados Unidos, Zira les responde en su idioma. No necesitan saber español para sentirse bienvenidos.</p>
    </div>

    <!-- 4. ESCALABILIDAD -->
    <h2 style="font-size:17px;font-weight:700;color:#f4f4f5;margin:0 0 12px;">
      <span style="display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:50%;background:linear-gradient(135deg,#e0115f,#f77737);color:#fff;font-size:11px;font-weight:700;margin-right:8px;">4</span>
      Escalabilidad: Booking y más
    </h2>
    <div style="background:#111115;border-radius:16px;padding:18px 20px;border:1px solid rgba(255,255,255,0.06);margin-bottom:20px;">
      <p style="font-size:12.5px;color:#d4d4d8;margin:0 0 8px;line-height:1.5;">Hoy Zira maneja <strong style="color:#f4f4f5;">Instagram + WhatsApp</strong>. Cuando el rancho escale, Zira puede integrarse con <strong style="color:#f4f4f5;">Booking.com, Airbnb</strong>, recibir notificaciones de nuevas reservas, coordinar al equipo automáticamente, y dar la bienvenida sin que nadie toque un botón. También puede solicitar <strong style="color:#f4f4f5;">reseñas post-estadía</strong> y encuestar a los huéspedes.</p>
    </div>

    <!-- 5. LA PROPUESTA -->
    <h2 style="font-size:17px;font-weight:700;color:#f4f4f5;margin:0 0 12px;">
      <span style="display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:50%;background:linear-gradient(135deg,#e0115f,#f77737);color:#fff;font-size:11px;font-weight:700;margin-right:8px;">5</span>
      La pregunta para el equipo
    </h2>
    <div style="background:linear-gradient(135deg,rgba(251,191,36,0.08),rgba(251,191,36,0.02));border:1px solid rgba(251,191,36,0.15);border-radius:16px;padding:18px 20px;margin-bottom:20px;">
      <div style="font-size:22px;margin-bottom:8px;">🤔</div>
      <ol style="padding-left:18px;margin:0;">
        <li style="font-size:12.5px;color:#d4d4d8;margin-bottom:8px;line-height:1.5;"><strong style="color:#f4f4f5;">¿Queremos que Zira atienda en el Instagram y WhatsApp reales?</strong> Hasta ahora son simulaciones. El próximo paso es que Zira interactúe con huéspedes de verdad.</li>
        <li style="font-size:12.5px;color:#d4d4d8;margin-bottom:8px;line-height:1.5;"><strong style="color:#f4f4f5;">¿Estamos listos para invertir en la infraestructura?</strong> Zira necesita un lugar donde vivir 24/7. Esto implica un costo mensual de servidor en la nube.</li>
        <li style="font-size:12.5px;color:#d4d4d8;margin-bottom:0;line-height:1.5;"><strong style="color:#f4f4f5;">¿Preferimos ir de golpe o de a poco?</strong> Podemos conectar Zira a las cuentas reales desde el día uno, o hacer un período de prueba gradual.</li>
      </ol>
    </div>

    <!-- DOS CAMINOS -->
    <div style="background:#111115;border-radius:16px;padding:18px 20px;border:1px solid rgba(255,255,255,0.06);margin-bottom:20px;">
      <p style="font-size:13px;font-weight:600;color:#f4f4f5;margin:0 0 10px;">Dos caminos posibles:</p>
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td width="28" valign="top" style="padding:2px 0;">
            <div style="width:26px;height:26px;border-radius:50%;background:linear-gradient(135deg,#fca130,#f77737);display:flex;align-items:center;justify-content:center;color:#fff;font-size:11px;font-weight:700;">A</div>
          </td>
          <td style="padding:0 0 10px 10px;">
            <div style="font-size:13px;font-weight:600;color:#f4f4f5;">Producción completa</div>
            <div style="font-size:11.5px;color:#71717a;line-height:1.5;">Zira se conecta al Instagram y WhatsApp real. Empieza a atender leads desde el día 1. <strong style="color:#a1a1aa;">Recomendado si hay confianza y ganas de ver resultados rápido.</strong></div>
          </td>
        </tr>
        <tr>
          <td width="28" valign="top" style="padding:2px 0;">
            <div style="width:26px;height:26px;border-radius:50%;background:linear-gradient(135deg,#5ac8fa,#34c759);display:flex;align-items:center;justify-content:center;color:#fff;font-size:11px;font-weight:700;">B</div>
          </td>
          <td style="padding:0 0 0 10px;">
            <div style="font-size:13px;font-weight:600;color:#f4f4f5;">Implementación gradual</div>
            <div style="font-size:11.5px;color:#71717a;line-height:1.5;">Zira arranca en modo "asesora": solo responde consultas simples y deriva todo lo importante al equipo. Con el tiempo se le dan más permisos. <strong style="color:#a1a1aa;">Recomendado si quieren ir con cuidado y ajustar sobre la marcha.</strong></div>
          </td>
        </tr>
      </table>
    </div>

    <!-- CIERRE -->
    <div style="background:linear-gradient(135deg,#e0115f,#f77737);border-radius:18px;padding:24px 20px;text-align:center;margin-bottom:16px;">
      <h3 style="color:#fff;font-size:18px;font-weight:800;margin:0 0 8px;">🏔️ ¿Damos el siguiente paso?</h3>
      <p style="color:rgba(255,255,255,0.85);font-size:13px;line-height:1.6;margin:0;">
        Zira ya demostró que puede entender el negocio, anticiparse a los imprevistos,<br>
        y coordinar al equipo.<br>
        <strong>Ahora la pregunta es si el equipo quiere que Zira<br>
        empiece a trabajar con huéspedes reales.</strong><br><br>
        No hay apuro. Podemos seguir simulando o dar el salto mañana.<br>
        <strong>Lo decidimos juntos.</strong> 🤝
      </p>
    </div>

    <!-- LINK A DEMO -->
    <div style="background:#111115;border-radius:12px;padding:14px 18px;border:1px solid rgba(255,255,255,0.04);text-align:center;">
      <p style="font-size:11px;color:#71717a;margin:0;">
        👁️ Podés ver la <a href="{SIMULACION_URL}" style="color:#f77737;text-decoration:none;border-bottom:1px solid rgba(247,119,55,0.3);">demo interactiva de la simulación</a>
        para entender mejor cómo funciona Zira con el equipo.
      </p>
    </div>

  </td></tr>

  <!-- FOOTER -->
  <tr>
    <td style="padding:24px 16px;text-align:center;">
      <div style="font-size:10px;color:#3f3f46;">
        <div>🏔️ Generado por Zira · Rancho Raíz CRM</div>
        <div style="margin-top:2px;">Auto-evolución · Escenarios: estufa, clima, reservas imprevistas</div>
      </div>
    </td>
  </tr>

</table>
</body>
</html>"""


def get_gmail_service():
    """Obtiene el servicio de Gmail con las credenciales existentes."""
    from googleapiclient.discovery import build
    
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(
            str(TOKEN_FILE),
            ["https://mail.google.com/"]
        )
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())
        else:
            print("❌ Token no disponible o inválido. Corré primero la autenticación OAuth.")
            sys.exit(1)
    
    return build("gmail", "v1", credentials=creds)


def send_email(service, to_addr, html_body, subject, bcc_addr=None):
    """Envía un email HTML vía Gmail API."""
    msg = MIMEMultipart("mixed")
    msg["To"] = to_addr
    msg["Subject"] = subject
    if bcc_addr:
        msg["Bcc"] = bcc_addr

    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(
        "Este mensaje requiere un cliente que soporte HTML.\n\n"
        "Podés ver la versión web en: https://oficinabarreal.github.io/rancho-raiz-zira/simulaciones/chats/index.html",
        "plain", "utf-8"
    ))
    alt.attach(MIMEText(html_body, "html", "utf-8"))
    msg.attach(alt)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    result = service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return result


def main():
    print("🔐 Conectando a Gmail API...")
    service = get_gmail_service()
    print("✅ Conectado")

    html_body = build_html_email()
    bcc_str = ", ".join(BCC)

    for recipient in RECIPIENTS:
        print(f"  📧 Enviando a {recipient}...")
        try:
            result = send_email(service, recipient, html_body, SUBJECT, bcc_addr=bcc_str)
            msg_id = result.get("id", "?")
            print(f"     ✅ Enviado (id: {msg_id})")
        except Exception as e:
            print(f"     ❌ Error: {e}")

    print(f"\n✅ Listo. {len(RECIPIENTS)} emails enviados.")


if __name__ == "__main__":
    main()
