#!/usr/bin/env python3
"""
Generador de simulación de conversaciones — VERSIÓN REALISTA.
Produce HTML con mockups de teléfono que imitan Instagram DM, WhatsApp y WhatsApp Grupo.

Modos:
  historia  (default) — Jornada completa: IG → WhatsApp → Reserva → Team → Clima → Post
  diario             — Escenarios aleatorios del pool (rotación diaria)

Uso:
    python3 scripts/generar_simulacion_realista.py
    python3 scripts/generar_simulacion_realista.py --modo diario --date 2026-06-15
    python3 scripts/generar_simulacion_realista.py --modo historia --output /ruta/salida.html
"""

import argparse
import sys
from datetime import date, datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from simulaciones.chats.escenarios import (
    ESCENARIOS,
    JORNADA_COMPLETA,
    obtener_escenarios_del_dia,
    obtener_jornada_completa,
)


# ─── Utilidades ───

MESES_ES = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio",
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
DIAS_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

def fecha_es(fecha_obj):
    d = DIAS_ES[fecha_obj.weekday()].capitalize()
    return f"{d}, {fecha_obj.day} de {MESES_ES[fecha_obj.month]} de {fecha_obj.year}"

def avatar_circle(nombre, color, size=32):
    inicial = nombre[0].upper()
    return f"""<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
      <circle cx="{size/2}" cy="{size/2}" r="{size/2 - 1}" fill="{color}" stroke="rgba(255,255,255,0.15)" stroke-width="1"/>
      <text x="{size/2}" y="{size/2}" text-anchor="middle" dominant-baseline="central"
            fill="white" font-size="{size*0.42}" font-weight="600" font-family="system-ui">{inicial}</text>
    </svg>"""


# ─── Render de mensajes ───

def render_mensajes_whatsapp(mensajes, participantes, inicia, duracion_min, agente, is_group):
    """WhatsApp bubbles: incoming (left, white/gray) / outgoing (right, green)."""
    offset = duracion_min / max(len(mensajes) - 1, 1)
    lines = []
    hh, mm = map(int, inicia.split(":"))
    base_min = hh * 60 + mm

    for i, m in enumerate(mensajes):
        t = int(base_min + i * offset)
        hora = f"{t // 60:02d}:{t % 60:02d}"
        es_saliente = m["de"] == agente
        cls = "outgoing" if es_saliente else "incoming"
        color = participantes.get(m["de"], {}).get("color", "#666")
        check = ""
        if es_saliente:
            if i == len(mensajes) - 1:
                check = '<span class="wsp-check blue">✓✓</span>'
            else:
                check = '<span class="wsp-check gray">✓✓</span>'

        if is_group and not es_saliente:
            lines.append(f"""            <div class="msg-row {cls}">
              <div class="bubble {cls}">
                <div class="sender-name" style="color:{color}">{m["de"]}</div>
                <div class="msg-text">{m["texto"]}</div>
                <div class="msg-meta">{hora} {check}</div>
              </div>
            </div>""")
        else:
            lines.append(f"""            <div class="msg-row {cls}">
              <div class="bubble {cls}">
                <div class="msg-text">{m["texto"]}</div>
                <div class="msg-meta">{hora} {check}</div>
              </div>
            </div>""")
    return "\n".join(lines)


def render_mensajes_instagram(mensajes, participantes, inicia, duracion_min, agente):
    """Instagram DM bubbles: sent (gradient right) / received (dark left)."""
    offset = duracion_min / max(len(mensajes) - 1, 1)
    lines = []
    hh, mm = map(int, inicia.split(":"))
    base_min = hh * 60 + mm

    for i, m in enumerate(mensajes):
        t = int(base_min + i * offset)
        hora = f"{t // 60:02d}:{t % 60:02d}"
        es_saliente = m["de"] == agente
        cls = "sent" if es_saliente else "received"
        visto = ""
        if es_saliente and i == len(mensajes) - 1:
            visto = '<span class="ig-seen">Visto</span>'

        lines.append(f"""            <div class="msg-row {cls}">
              <div class="bubble {cls}">
                <div class="msg-text">{m["texto"]}</div>
                <div class="msg-meta">{hora} {visto}</div>
              </div>
            </div>""")
    return "\n".join(lines)


# ─── Render de teléfono ───

def render_phone(esc, idx=0):
    """Renderiza una conversación dentro de un mockup de teléfono."""
    pn = esc["plataforma"]
    is_ig = pn == "instagram"
    is_gr = pn == "whatsapp_grupo"
    agente = esc.get("agente", "")

    if is_ig:
        msgs = render_mensajes_instagram(esc["mensajes"], esc["participantes"], esc["inicia"], esc["duracion_min"], agente)
    else:
        msgs = render_mensajes_whatsapp(esc["mensajes"], esc["participantes"], esc["inicia"], esc["duracion_min"], agente, is_gr)

    # Header
    if is_ig:
        # Instagram header: profile pic, username, icons
        primer_participante = [n for n in esc["participantes"] if n != agente]
        if not primer_participante:
            primer_participante = list(esc["participantes"].keys())
        contacto = primer_participante[0]
        info = esc["participantes"][contacto]
        color_contacto = info.get("color", "#5856d6")

        header = f"""<div class="phone-header ig-header">
            <div class="ig-back"><svg width="22" height="22" viewBox="0 0 24 24" fill="none"><path d="M15 18L9 12L15 6" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>
            <div class="ig-avatar">{avatar_circle(contacto, color_contacto, 30)}</div>
            <div class="ig-contact">
              <div class="ig-name">{contacto}</div>
              <div class="ig-status">Activo hace 2m</div>
            </div>
            <div class="ig-actions">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M12 16C14.2091 16 16 14.2091 16 12C16 9.79086 14.2091 8 12 8C9.79086 8 8 9.79086 8 12C8 14.2091 9.79086 16 12 16Z" stroke="white" stroke-width="1.5"/><path d="M21 12H21.01" stroke="white" stroke-width="2" stroke-linecap="round"/><path d="M3 12H3.01" stroke="white" stroke-width="2" stroke-linecap="round"/></svg>
            </div>
          </div>"""
    else:
        # WhatsApp header
        if is_gr:
            nombre_grupo = esc.get("titulo", "Grupo Rancho Raíz").replace("👥 ", "")
            header = f"""<div class="phone-header wsp-header">
            <div class="wsp-back"><svg width="22" height="22" viewBox="0 0 24 24" fill="none"><path d="M15 18L9 12L15 6" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>
            <div class="wsp-avatar-group">
              <svg width="36" height="36" viewBox="0 0 36 36"><circle cx="18" cy="18" r="17" fill="#2a3942"/><text x="18" y="18" text-anchor="middle" dominant-baseline="central" fill="#8696a0" font-size="14" font-weight="600" font-family="system-ui">G</text></svg>
            </div>
            <div class="wsp-contact">
              <div class="wsp-name">{nombre_grupo}</div>
              <div class="wsp-status">{len(esc["participantes"])} participantes</div>
            </div>
            <div class="wsp-actions">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M15 10L20 15L15 20" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M4 4V11C4 12.0609 4.42143 13.0783 5.17157 13.8284C5.92172 14.5786 6.93913 15 8 15H20" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </div>
          </div>"""
        else:
            primer_participante = [n for n in esc["participantes"] if n != agente]
            if not primer_participante:
                primer_participante = list(esc["participantes"].keys())
            contacto = primer_participante[0]
            info = esc["participantes"][contacto]
            color_contacto = info.get("color", "#5e5ce6")

            header = f"""<div class="phone-header wsp-header">
            <div class="wsp-back"><svg width="22" height="22" viewBox="0 0 24 24" fill="none"><path d="M15 18L9 12L15 6" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>
            <div class="wsp-avatar">{avatar_circle(contacto, color_contacto, 36)}</div>
            <div class="wsp-contact">
              <div class="wsp-name">{contacto}</div>
              <div class="wsp-status">en línea</div>
            </div>
            <div class="wsp-actions">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M15 10L20 15L15 20" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M4 4V11C4 12.0609 4.42143 13.0783 5.17157 13.8284C5.92172 14.5786 6.93913 15 8 15H20" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><rect x="2" y="2" width="20" height="16" rx="2" stroke="white" stroke-width="1.5"/><path d="M2 7H22" stroke="white" stroke-width="1.5"/></svg>
            </div>
          </div>"""

    # Date divider
    fecha_label = "Hoy"
    if esc.get("fecha"):
        f = datetime.strptime(esc["fecha"], "%Y-%m-%d")
        fecha_label = f"{f.day} de {MESES_ES[f.month]}"

    # Contexto si tiene (soporta .contexto y .descripcion)
    contexto = esc.get("contexto") or esc.get("descripcion", "")
    contexto_html = ""
    if contexto:
        icono = esc.get("icono", "💬")
        contexto_html = f"""<div class="phone-context">
          <span class="ctx-icon">{icono}</span>
          <span class="ctx-text">{contexto}</span>
        </div>"""

    # Chat area
    chat_bg_class = "ig-bg" if is_ig else "wsp-bg"

    return f"""<div class="phone-wrapper" style="animation-delay:{idx * 0.08}s">
      {contexto_html}
      <div class="phone {is_ig and 'phone-ig' or 'phone-wsp'}">
        <div class="phone-notch"></div>
        {header}
        <div class="chat-area {chat_bg_class}">
          <div class="date-divider">{fecha_label}</div>
          {msgs}
        </div>
        <div class="phone-input {is_ig and 'ig-input' or 'wsp-input'}">
          {is_ig and '''<div class="ig-input-inner">
            <div class="ig-placeholder">Mensaje...</div>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M22 2L11 13" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </div>''' or '''<div class="wsp-input-inner">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="2" fill="#8696a0"/><circle cx="5" cy="12" r="2" fill="#8696a0"/><circle cx="19" cy="12" r="2" fill="#8696a0"/></svg>
            <div class="wsp-placeholder">Mensaje</div>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM12 20C7.59 20 4 16.41 4 12C4 7.59 7.59 4 12 4C16.41 4 20 7.59 20 12C20 16.41 16.41 20 12 20Z" fill="#8696a0"/><path d="M12 7V12L15 15" stroke="#8696a0" stroke-width="1.5" stroke-linecap="round"/></svg>
            <div class="wsp-mic">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="#8696a0"><path d="M12 14C13.66 14 15 12.66 15 11V5C15 3.34 13.66 2 12 2C10.34 2 9 3.34 9 5V11C9 12.66 10.34 14 12 14Z"/><path d="M17 11C17 13.76 14.76 16 12 16C9.24 16 7 13.76 7 11H5C5 14.53 7.61 17.43 11 17.92V21H13V17.92C16.39 17.43 19 14.53 19 11H17Z"/></svg>
            </div>
          </div>'''}
        </div>
      </div>
      <div class="phone-label">{esc["titulo"]}</div>
    </div>"""


# ─── CSS ───

CSS = """/* ─── Reset ─── */
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  background: #0a0a0f;
  color: #e4e4e7;
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
}

/* ─── Layout ─── */
.page {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px 16px 40px;
}

/* Header */
.page-header {
  text-align: center;
  padding: 20px 0 24px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  margin-bottom: 28px;
}
.page-header h1 {
  font-size: 22px;
  font-weight: 700;
  background: linear-gradient(135deg, #e1306c, #f77737, #25d366);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.page-header .sub {
  font-size: 13px;
  color: #71717a;
  margin-top: 4px;
}
.page-header .fecha { font-size: 11px; color: #52525b; margin-top: 2px; }
.page-header .badge {
  display: inline-block;
  font-size: 9px;
  background: rgba(255,255,255,0.06);
  color: #71717a;
  padding: 2px 10px;
  border-radius: 10px;
  margin-top: 6px;
}

/* ─── Timeline (modo historia) ─── */
.timeline {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: center;
  margin-bottom: 32px;
  padding: 8px 0;
}
.tl-stage {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 500;
  background: rgba(255,255,255,0.04);
  color: #52525b;
  border: 1px solid rgba(255,255,255,0.04);
  transition: all 0.3s;
}
.tl-stage.active {
  background: linear-gradient(135deg, #e1306c, #f77737);
  color: #fff;
  border-color: transparent;
  box-shadow: 0 2px 12px rgba(225,48,108,0.3);
}
.tl-stage.done {
  background: rgba(0, 92, 75, 0.2);
  color: #34d399;
  border-color: rgba(0, 92, 75, 0.3);
}
.tl-arrow { color: #3f3f46; font-size: 14px; }
.tl-icon { font-size: 14px; }

@media (max-width: 600px) {
  .timeline { gap: 4px; }
  .tl-stage { font-size: 9px; padding: 3px 8px; }
  .tl-arrow { display: none; }
}

/* ─── Grid de teléfonos ─── */
.phones-grid {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 36px;
}

/* ─── Teléfono ─── */
.phone-wrapper {
  width: 100%;
  max-width: 400px;
  animation: fadeUp 0.5s ease-out both;
}
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.phone-context {
  background: linear-gradient(135deg, rgba(251,191,36,0.08), rgba(251,191,36,0.02));
  border: 1px solid rgba(251,191,36,0.15);
  border-radius: 12px;
  padding: 10px 14px;
  margin-bottom: 8px;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 12px;
  line-height: 1.5;
  color: #a1a1aa;
}
.ctx-icon { font-size: 16px; flex-shrink: 0; }
.ctx-text { flex: 1; }

.phone {
  position: relative;
  width: 100%;
  border-radius: 28px;
  overflow: hidden;
  box-shadow:
    0 0 0 1px rgba(255,255,255,0.08),
    0 8px 40px rgba(0,0,0,0.5),
    0 2px 10px rgba(0,0,0,0.3);
  background: #000;
}
.phone-notch {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 130px;
  height: 24px;
  background: #000;
  border-radius: 0 0 16px 16px;
  z-index: 10;
}
.phone-notch::before {
  content: '';
  position: absolute;
  top: 6px;
  left: 50%;
  transform: translateX(-50%);
  width: 8px;
  height: 8px;
  background: #1a1a2e;
  border-radius: 50%;
  border: 1px solid #2a2a3e;
}
.phone-notch::after {
  content: '';
  position: absolute;
  top: 8px;
  right: 28px;
  width: 12px;
  height: 4px;
  background: #1a1a2e;
  border-radius: 2px;
}

/* ─── Phone Header: Instagram ─── */
.ig-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 32px 12px 8px;
  background: #000;
  color: #fff;
}
.ig-back { margin-right: 2px; }
.ig-avatar { flex-shrink: 0; }
.ig-contact { flex: 1; min-width: 0; }
.ig-name { font-size: 14px; font-weight: 600; }
.ig-status { font-size: 11px; color: #8e8e93; }
.ig-actions { display: flex; gap: 12px; }

/* ─── Phone Header: WhatsApp ─── */
.wsp-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 32px 12px 8px;
  background: #202c33;
  color: #fff;
}
.wsp-back { margin-right: 2px; }
.wsp-avatar, .wsp-avatar-group { flex-shrink: 0; }
.wsp-contact { flex: 1; min-width: 0; }
.wsp-name { font-size: 15px; font-weight: 500; }
.wsp-status { font-size: 11px; color: #8696a0; }
.wsp-actions { display: flex; gap: 14px; }

/* ─── Chat Areas ─── */
.chat-area {
  padding: 8px 12px 12px;
  display: flex;
  flex-direction: column;
  min-height: 200px;
}
.ig-bg { background: #000; }
.wsp-bg { background: #0b141a; }

.date-divider {
  text-align: center;
  font-size: 11px;
  color: #71717a;
  margin: 4px 0 10px;
  position: relative;
}

/* ─── Messages ─── */
.msg-row {
  display: flex;
  margin-bottom: 3px;
}
.msg-row.sent { justify-content: flex-end; }
.msg-row.received { justify-content: flex-start; }
.msg-row.incoming { justify-content: flex-start; }
.msg-row.outgoing { justify-content: flex-end; }

.bubble {
  max-width: 82%;
  padding: 7px 12px;
  font-size: 13.5px;
  line-height: 1.45;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* ─── Instagram Bubbles ─── */
.ig-bg .bubble.sent {
  background: linear-gradient(135deg, #e0115f, #f77737);
  color: #fff;
  border-radius: 16px 16px 4px 16px;
}
.ig-bg .bubble.received {
  background: #1c1c1e;
  color: #f4f4f5;
  border-radius: 16px 16px 16px 4px;
}

/* ─── WhatsApp Bubbles ─── */
.wsp-bg .bubble.incoming {
  background: #202c33;
  color: #e9edef;
  border-radius: 8px 8px 8px 0;
}
.wsp-bg .bubble.outgoing {
  background: #005c4b;
  color: #e9edef;
  border-radius: 8px 8px 0 8px;
}

.sender-name {
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 2px;
}

.msg-text { word-wrap: break-word; }

.msg-meta {
  font-size: 10px;
  color: rgba(255,255,255,0.35);
  display: flex;
  align-items: center;
  gap: 3px;
  justify-content: flex-end;
  margin-top: 2px;
}
.outgoing .msg-meta { color: rgba(255,255,255,0.4); }

/* WhatsApp checks */
.wsp-check { font-size: 12px; margin-left: 2px; }
.wsp-check.gray { color: rgba(255,255,255,0.3); }
.wsp-check.blue { color: #53bdeb; }

/* Instagram visto */
.ig-seen { font-size: 10px; color: rgba(255,255,255,0.35); }

/* ─── Phone Input ─── */
.phone-input {
  padding: 8px 12px 16px;
  border-top: 1px solid rgba(255,255,255,0.06);
}
.ig-input { background: #000; }
.wsp-input { background: #202c33; }

.ig-input-inner {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #1c1c1e;
  border-radius: 20px;
  padding: 6px 12px;
}
.ig-placeholder {
  flex: 1;
  font-size: 14px;
  color: #8e8e93;
}

.wsp-input-inner {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #2a3942;
  border-radius: 24px;
  padding: 6px 12px;
}
.wsp-placeholder {
  flex: 1;
  font-size: 14px;
  color: #8696a0;
}
.wsp-mic {
  width: 32px;
  height: 32px;
  background: #00a884;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.wsp-mic svg { fill: #fff; width: 18px; height: 18px; }

/* ─── Phone Label ─── */
.phone-label {
  text-align: center;
  font-size: 12px;
  color: #52525b;
  margin-top: 8px;
  padding: 4px 0;
}

/* ─── Footer ─── */
.footer {
  text-align: center;
  font-size: 10px;
  color: #3f3f46;
  margin-top: 40px;
  padding: 16px;
  border-top: 1px solid rgba(255,255,255,0.04);
}

/* ─── Responsive ─── */
@media (min-width: 768px) {
  .phones-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
    gap: 32px;
    align-items: start;
  }
  .phone-wrapper { max-width: 100%; }
}
@media (max-width: 400px) {
  .phone { border-radius: 20px; }
  .bubble { font-size: 13px; padding: 6px 10px; }
}
"""


# ─── Generadores de HTML ───

def generar_html_historia(jornada, fecha_obj):
    fecha_str = fecha_obj.isoformat()
    fecha_display = fecha_es(fecha_obj)
    total = len(jornada)

    # Timeline
    timeline_items = []
    for i, cap in enumerate(jornada):
        timeline_items.append(
            f'<div class="tl-stage done"><span class="tl-icon">{cap["icono"]}</span>{cap["etapa"]}</div>'
        )
        if i < total - 1:
            timeline_items.append('<span class="tl-arrow">→</span>')
    timeline_html = "\n          ".join(timeline_items)

    # Phone mockups
    phones_html = "\n".join(render_phone(cap, i) for i, cap in enumerate(jornada))

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Jornada Rancho Raíz · {fecha_str}</title>
  <style>{CSS}</style>
</head>
<body>
  <div class="page">
    <header class="page-header">
      <h1>🏔️ Rancho Raíz · Jornada Completa</h1>
      <div class="sub">De Instagram a la estadía — el viaje completo de un huésped</div>
      <div class="fecha">{fecha_display}</div>
      <div class="badge">✨ {total} capítulos · 1 historia</div>
    </header>

    <div class="timeline">
      {timeline_html}
    </div>

    <div class="phones-grid">
      {phones_html}
    </div>

    <footer class="footer">
      <div>🤖 Simulación generada por Zira · Rancho Raíz CRM</div>
      <div>{fecha_str} · {total} capítulos</div>
    </footer>
  </div>
</body>
</html>"""


def generar_html_diario(escenarios, fecha_obj):
    fecha_str = fecha_obj.isoformat()
    fecha_display = fecha_es(fecha_obj)

    # Ordenar por hora
    escenarios.sort(key=lambda e: e["inicia"])

    # Separar por plataforma para agrupar visualmente
    phones_html = "\n".join(render_phone(e, i) for i, e in enumerate(escenarios))

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Simulación Rancho Raíz · {fecha_str}</title>
  <style>{CSS}</style>
</head>
<body>
  <div class="page">
    <header class="page-header">
      <h1>🏔️ Rancho Raíz · Conversaciones del Día</h1>
      <div class="sub">Simulación de atención a huéspedes</div>
      <div class="fecha">{fecha_display}</div>
      <div class="badge">📱 {len(escenarios)} conversaciones</div>
    </header>

    <div class="phones-grid">
      {phones_html}
    </div>

    <footer class="footer">
      <div>🤖 Generado automáticamente por Zira · Rancho Raíz CRM</div>
      <div>{fecha_str}</div>
    </footer>
  </div>
</body>
</html>"""


# ─── CLI ───

def main():
    parser = argparse.ArgumentParser(description="Generar simulación de conversaciones (realista)")
    parser.add_argument("--date", default=None, help="Fecha YYYY-MM-DD (default: hoy)")
    parser.add_argument("--output", default=None, help="Ruta del HTML de salida")
    parser.add_argument("--modo", default="historia", choices=["historia", "diario"],
                        help="historia: jornada completa conectada (default) | diario: escenarios rotativos")
    parser.add_argument("--cantidad", type=int, default=6, help="Solo modo diario: escenarios a mostrar")
    args = parser.parse_args()

    fecha_obj = date.today() if args.date is None else datetime.strptime(args.date, "%Y-%m-%d").date()

    if args.modo == "historia":
        jornada = obtener_jornada_completa()
        if not jornada:
            print("❌ No hay jornada disponible")
            sys.exit(1)
        print(f"🏔️ Generando JORNADA COMPLETA para {fecha_obj}")
        print(f"   {len(jornada)} capítulos:")
        for c in jornada:
            fe = f" [{c['fecha']}]" if c.get("fecha") else ""
            print(f"     Cap {c['capitulo']}: {c['etapa']:14s} {c['plataforma']:16s} {c['inicia']}{fe}  {c['titulo']}")
        html = generar_html_historia(jornada, fecha_obj)
    else:
        escenarios = obtener_escenarios_del_dia(fecha_obj, cantidad=args.cantidad)
        if not escenarios:
            print("❌ No hay escenarios disponibles")
            sys.exit(1)
        print(f"📱 Generando simulación DIARIA para {fecha_obj}")
        print(f"   {len(escenarios)} escenarios:")
        for e in escenarios:
            print(f"     {e['plataforma']:16s} {e['id']:30s} {e['inicia']}  {e['titulo']}")
        html = generar_html_diario(escenarios, fecha_obj)

    output_path = args.output
    if output_path is None:
        output_path = str(PROJECT_DIR / "simulaciones" / "chats" / "index.html")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(html, encoding="utf-8")

    print(f"\n✅ HTML generado: {output_path} ({len(html):,} bytes)")
    print(f"   Abrí con: python3 -m http.server y navegá a localhost:8000/simulaciones/chats/index.html")


if __name__ == "__main__":
    main()
