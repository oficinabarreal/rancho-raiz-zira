#!/usr/bin/env python3
"""
recordatorio_pagos.py — Revisa facturas próximas y notifica al equipo.

Se ejecuta diariamente (10am ART) vía cron. Busca:
1. Facturas próximas a vencer en el sistema local
2. Nuevos emails de Starlink (errores de pago, suspensiones)
3. Nuevos emails de Naturgy (facturas disponibles, vencimientos)

Envía un resumen por email al equipo.
"""

import sys, json, base64, re, os
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date, datetime, timedelta
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

PROJECT_DIR = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_DIR / "crm_state"
TOKEN_FILE = STATE_DIR / ".google_token.json"
BANNER = "https://raw.githubusercontent.com/oficinabarreal/rancho-raiz-zira/main/assets/banner-recordatorio.svg"
DASHBOARD = "https://oficinabarreal.github.io/rancho-raiz-zira/"

RECIPIENTS = [
    "Diego <oficinabarreal@gmail.com>",
]

# Fechas de vencimiento estimadas por servicio
VENCIMIENTOS = {
    "starlink": {"dia": 10, "nombre": "Starlink Internet"},
    "luz": {"dia": 15, "nombre": "Luz EPE"},
}


def get_gmail():
    creds = Credentials.from_authorized_user_info(json.loads(TOKEN_FILE.read_text()))
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build("gmail", "v1", credentials=creds)


def search_gmail(gmail, query):
    msgs = []
    results = gmail.users().messages().list(userId="me", q=query, maxResults=5).execute()
    for m in results.get("messages", []):
        msg = gmail.users().messages().get(userId="me", id=m["id"], format="metadata",
            metadataHeaders=["From", "Subject", "Date"]).execute()
        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        msgs.append({
            "date": headers.get("Date", "?")[:25],
            "from": headers.get("From", "?"),
            "subject": headers.get("Subject", "?"),
        })
    return msgs


def build_html(starlink_msgs, naturgy_msgs, prox_facturas):
    parts = []

    # Banner
    parts.append(f'<img src="{BANNER}" alt="Recordatorio" style="max-width:100%;border-radius:12px;">')

    # Intro
    hoy = date.today().strftime("%d/%m/%Y")
    parts.append(f"""
    <h1 style="color:#78350f;font-size:20px;margin:16px 0 6px;">🔔 Buenos días</h1>
    <p style="color:#78716c;font-size:13px;margin:0 0 14px;line-height:1.5;">
    Revista de pagos del {hoy}. Les cuento cómo viene el panorama:
    </p>
    """)

    # Starlink
    if starlink_msgs:
        parts.append(f"""
        <div style="background:white;border-radius:10px;padding:14px;margin-bottom:10px;border:1px solid #fca5a5;">
        <h2 style="color:#b91c1c;font-size:14px;margin:0 0 6px;">🚨 Starlink — Requiere atención</h2>
        <p style="color:#78716c;font-size:12px;margin:0;line-height:1.5;">
        Se detectaron {len(starlink_msgs)} comunicaciones recientes sobre el servicio:
        </p>
        <ul style="color:#a8a29e;font-size:12px;margin:6px 0 0;padding-left:16px;">
        """)
        for s in starlink_msgs[:3]:
            parts.append(f"<li><strong>{s['subject'][:60]}</strong> — {s['date'][:16]}</li>")
        parts.append("</ul></div>")
    else:
        parts.append(f"""
        <div style="background:white;border-radius:10px;padding:14px;margin-bottom:10px;border:1px solid #bbf7d0;">
        <h2 style="color:#047857;font-size:14px;margin:0 0 4px;">🛰️ Starlink — Sin novedades</h2>
        <p style="color:#78716c;font-size:12px;margin:0;">Todo en orden con el servicio de internet.</p>
        </div>
        """)

    # Naturgy / Luz
    if naturgy_msgs:
        parts.append(f"""
        <div style="background:white;border-radius:10px;padding:14px;margin-bottom:10px;border:1px solid #fde68a;">
        <h2 style="color:#b45309;font-size:14px;margin:0 0 6px;">💡 Naturgy — Factura disponible</h2>
        <ul style="color:#78716c;font-size:12px;margin:0;padding-left:16px;line-height:1.6;">
        """)
        for n in naturgy_msgs[:3]:
            parts.append(f"<li>{n['subject'][:70]} ({n['date'][:16]})</li>")
        parts.append("</ul></div>")
    else:
        parts.append(f"""
        <div style="background:white;border-radius:10px;padding:14px;margin-bottom:10px;border:1px solid #fde68a;">
        <h2 style="color:#b45309;font-size:14px;margin:0 0 4px;">💡 Luz — Sin novedades</h2>
        <p style="color:#78716c;font-size:12px;margin:0;">No se detectaron nuevas facturas de luz.</p>
        </div>
        """)

    # Próximas facturas
    if prox_facturas:
        parts.append(f"""
        <div style="background:white;border-radius:10px;padding:14px;margin-bottom:14px;border:1px solid #e2e8f0;">
        <h2 style="color:#78350f;font-size:14px;margin:0 0 6px;">📅 Próximos vencimientos</h2>
        <ul style="color:#78716c;font-size:12px;margin:0;padding-left:16px;line-height:1.6;">
        """)
        for f in prox_facturas:
            parts.append(f"<li><strong>{f['nombre']}</strong> — vence en {f['dias']} día(s)</li>")
        parts.append("</ul></div>")

    # Recordatorio
    parts.append(f"""
    <div style="background:rgba(245,158,11,0.05);border-radius:10px;padding:12px;margin-bottom:14px;border:1px solid rgba(245,158,11,0.12);">
    <p style="color:#78716c;font-size:12px;margin:0;text-align:center;line-height:1.5;">
    💡 Si tenés una boleta escaneada, creá un documento en Drive con "factura" en el título y Zira la registra sola.
    <br><a href="{DASHBOARD}" style="color:#d97706;">Ver dashboard →</a>
    </p>
    </div>

    <hr style="border:none;border-top:1px solid #fde68a;margin:16px 0;">

    <p style="color:#a8a29e;font-size:10px;text-align:center;margin:0;">
    <strong style="color:#b45309;">Zira</strong> · Gestión autónoma · Rancho Raíz<br>
    {DASHBOARD}
    </p>
    """)

    return "\n".join(parts)


def send_email(gmail, addr, html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🔔 Revista de pagos · Zira CRM"
    msg["From"] = "oficinabarreal@gmail.com"
    msg["To"] = addr
    msg.attach(MIMEText(html, "html"))
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    gmail.users().messages().send(userId="me", body={"raw": raw}).execute()
    print(f"  ✅ {addr.split('<')[0].strip() or addr}")


def calcular_proximas():
    """Calcula días hasta vencimiento desde el sistema local."""
    prox = []
    today = date.today()
    for svc, info in VENCIMIENTOS.items():
        dia = info["dia"]
        vto = date(today.year, today.month, dia)
        if vto < today:
            # Ya pasó este mes, calcular para el próximo
            if today.month == 12:
                vto = date(today.year + 1, 1, dia)
            else:
                vto = date(today.year, today.month + 1, dia)
        dias = (vto - today).days
        prox.append({"nombre": info["nombre"], "dias": dias})
    return prox


def main():
    print("📋 Revista de pagos — Zira")
    gmail = get_gmail()

    print("  Buscando comunicaciones...")
    starlink = search_gmail(gmail, "from:starlink.com after:2026/05/01")
    naturgy = search_gmail(gmail, "from:avisossj@naturgy.com.ar after:2026/05/01")
    prox = calcular_proximas()

    print(f"  Starlink: {len(starlink)} mensajes")
    print(f"  Naturgy: {len(naturgy)} mensajes")
    print(f"  Próximas: {len(prox)} facturas")

    html = build_html(starlink, naturgy, prox)
    print("\n  Enviando...")
    for addr in RECIPIENTS:
        send_email(gmail, addr, html)

    print(f"\n✅ Revista enviada a {len(RECIPIENTS)} destinatarios")

    # También notificar por Telegram si hay algo urgente
    if starlink_msgs or any(f["dias"] <= 5 for f in prox):
        try:
            tg_token = os.environ.get("CRM_TG_TOKEN")
            tg_chat = os.environ.get("CRM_TG_CHAT_ID")
            if tg_token and tg_chat:
                import urllib.request
                resumen = "🔔 *Revista de pagos Zira*\n\n"
                if starlink_msgs:
                    resumen += f"🚨 Starlink: {len(starlink_msgs)} comunicación(es)\n"
                for f in prox:
                    emoji = "🟢" if f["dias"] > 7 else "🟡" if f["dias"] > 3 else "🔴"
                    resumen += f"{emoji} {f['nombre']}: vence en {f['dias']} días\n"
                msg = resumen.replace(" ", "%20").replace("\n", "%0A")
                urllib.request.urlopen(
                    f"https://api.telegram.org/bot{tg_token}/sendMessage?chat_id={tg_chat}&text={msg}&parse_mode=Markdown"
                )
                print("  ✅ Telegram notificado")
        except Exception as e:
            print(f"  ⚠️ Telegram: {e}")


if __name__ == "__main__":
    main()
