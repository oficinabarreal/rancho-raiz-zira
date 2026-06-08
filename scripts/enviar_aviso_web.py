#!/usr/bin/env python3
"""Enviar aviso sitio web a Leo - Automejora CRM."""

import base64, os, sys
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
TOKEN_FILE = PROJECT / "crm_state" / ".google_token.json"

SITE_URL = "https://oficinabarreal.github.io/rancho-raiz-zira/"
DASHBOARD_URL = "https://oficinabarreal.github.io/rancho-raiz-zira/panel/"
BANNER_URL = "https://raw.githubusercontent.com/oficinabarreal/rancho-raiz-zira/main/assets/zira-mountain.svg"
AGENT_URL = "https://github.com/oficinabarreal/rancho-raiz-zira/actions/workflows/zira-agent.yml"

HTML = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#0b1121;font-family:'Segoe UI',system-ui,-apple-system,sans-serif;color:#f1f5f9;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#0b1121;">
<tr><td align="center" style="padding:40px 20px;">
<table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">

<!-- Banner -->
<tr>
<td style="padding-bottom:30px;text-align:center;">
<img src=\"""" + BANNER_URL + """\" alt="Zira" style="width:120px;height:120px;border-radius:50%;border:2px solid rgba(197,160,89,0.3);">
<div style="margin-top:18px;font-size:11px;letter-spacing:4px;color:#C5A059;text-transform:uppercase;">Automejora . CRM</div>
</td>
</tr>

<!-- Card principal -->
<tr>
<td style="background:linear-gradient(135deg,#1e293b,#0f172a);border-radius:16px;padding:36px 32px;border:1px solid rgba(255,255,255,0.06);">

<div style="font-size:28px;font-weight:800;margin-bottom:6px;letter-spacing:-1px;">
&#127956; <span style="background:linear-gradient(135deg,#f1f5f9,#C5A059);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Rancho Raiz</span> ya tiene web
</div>
<div style="font-size:15px;color:#C5A059;margin-bottom:24px;font-weight:500;letter-spacing:1px;">Sitio oficial - Posada de Montana - Barreal</div>

<!-- Link -->
<div style="background:rgba(197,160,89,0.08);border:1px solid rgba(197,160,89,0.15);border-radius:12px;padding:16px 20px;margin-bottom:24px;text-align:center;">
<a href=\"""" + SITE_URL + """\" style="color:#C5A059;font-size:16px;font-weight:600;text-decoration:none;">""" + SITE_URL + """ &rarr;</a>
<div style="color:#64748b;font-size:12px;margin-top:6px;">Online - GitHub Pages - SSL</div>
</div>

<div style="color:#cbd5e1;font-size:14px;line-height:1.7;margin-bottom:20px;">
<b style="color:#f1f5f9;">Que es esto?</b><br>
El sistema CRM (Zira) genero automaticamente el sitio web de la posada como parte del proceso de <b style="color:#C5A059;">automejora continua</b> del sistema. La web esta <b style="color:#f1f5f9;">en construccion</b> - es el esqueleto con la identidad visual de la montana.
</div>

<div style="color:#cbd5e1;font-size:14px;line-height:1.7;margin-bottom:20px;">
<b style="color:#f1f5f9;">Que falta?</b><br>
Las mejores fotos de la posada. Cuando las tengas, se completan los espacios de habitaciones, servicios y galeria. Queda a <b style="color:#C5A059;">tu criterio</b> definir el estilo definitivo - colores, tono, fotos que reflejen la experiencia Rancho Raiz.
</div>

<div style="background:rgba(16,185,129,0.06);border:1px solid rgba(16,185,129,0.12);border-radius:12px;padding:16px 20px;margin-bottom:20px;">
<div style="display:flex;align-items:flex-start;gap:10px;">
<span style="font-size:20px;">&#129302;</span>
<div>
<div style="color:#10b981;font-weight:600;font-size:13px;margin-bottom:4px;">Vigilancia activa</div>
<div style="color:#94a3b8;font-size:13px;line-height:1.5;">
El sistema CRM monitorea permanentemente el sitio. Cada visita, cada interaccion de posibles huespedes queda registrada. La web esta respaldada por un <b style="color:#f1f5f9;">agente autonomo de IA</b> (Zira Agent) que corre todos los dias desde GitHub Actions y genera contenido fresco.
</div>
</div>
</div>
</div>

<!-- Stats row -->
<tr><td style="padding:20px 0;">
<table width="100%" cellpadding="0" cellspacing="0">
<tr>
<td width="30%" style="text-align:center;padding:12px;background:rgba(30,41,59,0.4);border-radius:10px;border:1px solid rgba(255,255,255,0.04);">
<div style="font-size:22px;font-weight:800;color:#C5A059;">+70</div>
<div style="font-size:10px;color:#64748b;letter-spacing:1px;text-transform:uppercase;">Posts IG</div>
</td>
<td width="5%" style="padding:4px;"></td>
<td width="30%" style="text-align:center;padding:12px;background:rgba(30,41,59,0.4);border-radius:10px;border:1px solid rgba(255,255,255,0.04);">
<div style="font-size:22px;font-weight:800;color:#C5A059;">24/7</div>
<div style="font-size:10px;color:#64748b;letter-spacing:1px;text-transform:uppercase;">Zira Activa</div>
</td>
<td width="5%" style="padding:4px;"></td>
<td width="30%" style="text-align:center;padding:12px;background:rgba(30,41,59,0.4);border-radius:10px;border:1px solid rgba(255,255,255,0.04);">
<div style="font-size:22px;font-weight:800;color:#C5A059;">&#9721;</div>
<div style="font-size:10px;color:#64748b;letter-spacing:1px;text-transform:uppercase;">Cloud Native</div>
</td>
</tr>
</table>
</td></tr>

<!-- Dashboard card -->
<tr>
<td style="background:linear-gradient(135deg,#1e293b,#0f172a);border-radius:16px;padding:24px 28px;border:1px solid rgba(255,255,255,0.06);margin-top:20px;">
<div style="color:#94a3b8;font-size:13px;line-height:1.6;">
&#128202; <b style="color:#f1f5f9;">Dashboard interno</b> disponible en <a href=\"""" + DASHBOARD_URL + """\" style="color:#60a5fa;text-decoration:none;">""" + DASHBOARD_URL + """</a> - metricas de facturas, testeo y actividad del sistema.
</div>
<div style="color:#64748b;font-size:12px;margin-top:12px;">
&#9881; Agente autonomo: <a href=\"""" + AGENT_URL + """\" style="color:#60a5fa;text-decoration:none;">ver ejecuciones</a>
</div>
</td>
</tr>

<!-- Footer -->
<tr>
<td style="padding:30px 0 0;text-align:center;">
<div style="border-top:1px solid rgba(255,255,255,0.05);padding-top:24px;">
<div style="font-size:11px;color:#475569;letter-spacing:1px;margin-bottom:4px;">Generado por Zira - Sistema CRM Rancho Raiz</div>
<div style="font-size:10px;color:#334155;">Barreal, Calingasta - San Juan - Argentina</div>
<div style="font-size:10px;color:#334155;margin-top:8px;">Esta es una comunicacion automatica del sistema de automejora del CRM.</div>
</div>
</td>
</tr>

</table>
</td></tr>
</table>
</body>
</html>
"""

def send():
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), ["https://mail.google.com/"])
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    
    svc = build("gmail", "v1", credentials=creds)
    
    # To Leo
    msg = MIMEMultipart("mixed")
    msg["To"] = "Leo Tello <ltelloraiz@gmail.com>"
    msg["Subject"] = "Rancho Raiz - Sitio web online (Automejora CRM)"
    
    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText("Rancho Raiz ya tiene sitio web. Link: " + SITE_URL + " - En construccion, a tu criterio el estilo.", "plain"))
    alt.attach(MIMEText(HTML, "html"))
    msg.attach(alt)
    
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    result = svc.users().messages().send(userId="me", body={"raw": raw}).execute()
    print("Enviado a Leo:", result["id"])
    
    # BCC to Diego
    msg2 = MIMEMultipart("mixed")
    msg2["To"] = "oficinabarreal@gmail.com"
    msg2["Subject"] = "Copia: " + msg["Subject"]
    
    alt2 = MIMEMultipart("alternative")
    alt2.attach(MIMEText(HTML, "html"))
    msg2.attach(alt2)
    
    raw2 = base64.urlsafe_b64encode(msg2.as_bytes()).decode()
    result2 = svc.users().messages().send(userId="me", body={"raw": raw2}).execute()
    print("Copia a Diego:", result2["id"])

if __name__ == "__main__":
    send()
