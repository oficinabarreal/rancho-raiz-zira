#!/usr/bin/env python3
"""
Generador de simulación de conversaciones diarias.
Produce un HTML con chats estilo Instagram y WhatsApp.

Modos:
  historia  (default) — Una jornada completa: IG → WhatsApp → Reserva → Team → Clima → Post
  diario             — Escenarios aleatorios del pool (rotación diaria)

Uso:
    python3 scripts/generar_simulacion_chats.py
    python3 scripts/generar_simulacion_chats.py --modo diario --date 2026-06-15
    python3 scripts/generar_simulacion_chats.py --modo historia --output /ruta/salida.html
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

def platoform_label(p):
    return {
        "instagram": ("Instagram DM", "#e1306c"),
        "whatsapp": ("WhatsApp", "#25d366"),
        "whatsapp_grupo": ("WhatsApp Grupo", "#25d366"),
    }.get(p, (p.capitalize(), "#666"))


# ─── Render de mensajes ───

def render_mensajes_instagram(mensajes, participantes, inicia, duracion_min, agente):
    lines = []
    offset = duracion_min / max(len(mensajes) - 1, 1)
    for i, m in enumerate(mensajes):
        es_agente = m["de"] == agente
        cls = "sent" if es_agente else "received"
        color = participantes[m["de"]]["color"]
        inicial = participantes[m["de"]]["inicial"]
        hh, mm = map(int, inicia.split(":"))
        t = int(hh * 60 + mm + i * offset)
        hora = f"{t // 60:02d}:{t % 60:02d}"
        lines.append(f"""          <div class="msg-row {cls}">
            <div class="avatar" style="background:{color}">{inicial}</div>
            <div class="bubble-wrapper">
              <div class="bubble {cls}">{m["texto"]}</div>
              <div class="time">{hora}</div>
            </div>
          </div>""")
    return "\n".join(lines)


def render_mensajes_whatsapp(mensajes, participantes, inicia, duracion_min, agente, is_group=False):
    lines = []
    offset = duracion_min / max(len(mensajes) - 1, 1)
    for i, m in enumerate(mensajes):
        es_out = m["de"] == agente
        cls = "outgoing" if es_out else "incoming"
        color = participantes.get(m["de"], {}).get("color", "#666")
        hh, mm = map(int, inicia.split(":"))
        t = int(hh * 60 + mm + i * offset)
        hora = f"{t // 60:02d}:{t % 60:02d}"
        check = '<span class="chk">✓✓</span>' if es_out else ''
        check_l = '<span class="chk leido">✓✓</span>' if (es_out and i == len(mensajes) - 1) else ''

        if is_group and not es_out:
            lines.append(f"""          <div class="msg-row {cls}">
            <div class="bubble-wrapper">
              <div class="sname" style="color:{color}">{m["de"]}</div>
              <div class="bubble {cls}">{m["texto"]}<span class="meta">{hora} {check}{check_l}</span></div>
            </div>
          </div>""")
        else:
            lines.append(f"""          <div class="msg-row {cls}">
            <div class="bubble-wrapper">
              <div class="bubble {cls}">{m["texto"]}<span class="meta">{hora} {check}{check_l}</span></div>
            </div>
          </div>""")
    return "\n".join(lines)


def render_card(esc, esc_idx=0, total=0):
    """Renderiza una conversación como card."""
    pn, pc = platoform_label(esc["plataforma"])
    is_ig = esc["plataforma"] == "instagram"
    is_gr = esc["plataforma"] == "whatsapp_grupo"
    agente = esc.get("agente", "")

    if is_ig:
        msgs = render_mensajes_instagram(esc["mensajes"], esc["participantes"], esc["inicia"], esc["duracion_min"], agente)
    else:
        msgs = render_mensajes_whatsapp(esc["mensajes"], esc["participantes"], esc["inicia"], esc["duracion_min"], agente, is_gr)

    pp = ", ".join(esc["participantes"].keys())

    fecha_label = "Hoy"
    if esc.get("fecha"):
        f = datetime.strptime(esc["fecha"], "%Y-%m-%d")
        fecha_label = f"{f.day} de {MESES_ES[f.month]}"

    return f"""
    <div class="card platform-{esc['plataforma']}">
      <div class="card-header" style="border-bottom-color:{pc}">
        <div class="platform-badge" style="background:{pc}">{pn}</div>
        <div class="card-title">{esc["titulo"]}</div>
        <div class="card-participants">{pp}</div>
      </div>
      <div class="chat-area">
        <div class="date-divider">{fecha_label}</div>
{msgs}
      </div>
    </div>"""


def render_context_card(contexto, icono="🌤️"):
    """Renderiza una tarjeta de contexto externo (clima, factores, etc)."""
    return f"""
    <div class="context-card">
      <div class="context-icon">{icono}</div>
      <div class="context-text">{contexto}</div>
    </div>"""


# ─── CSS ───

CSS = """
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: #0a0a0f;
      color: #e4e4e7;
      min-height: 100vh;
      -webkit-font-smoothing: antialiased;
    }
    .container {
      max-width: 780px;
      margin: 0 auto;
      padding: 20px 16px 40px;
    }

    /* Header */
    .page-header {
      text-align: center;
      padding: 20px 0 24px;
      border-bottom: 1px solid rgba(255,255,255,0.06);
      margin-bottom: 24px;
    }
    .page-header h1 {
      font-size: 22px;
      font-weight: 700;
      background: linear-gradient(135deg, #e1306c, #f77737, #fca130);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    .page-header .subtitle {
      font-size: 13px;
      color: #71717a;
      margin-top: 4px;
    }
    .page-header .fecha {
      font-size: 11px;
      color: #52525b;
      margin-top: 2px;
    }
    .page-header .modo-badge {
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
      margin-bottom: 28px;
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
    .tl-arrow {
      color: #3f3f46;
      font-size: 14px;
    }
    .tl-stage .tl-icon { font-size: 14px; }

    @media (max-width: 600px) {
      .timeline { gap: 4px; }
      .tl-stage { font-size: 9px; padding: 3px 8px; }
      .tl-arrow { display: none; }
    }

    /* ─── Context card ─── */
    .context-card {
      background: linear-gradient(135deg, rgba(251,191,36,0.08), rgba(251,191,36,0.02));
      border: 1px solid rgba(251,191,36,0.15);
      border-radius: 14px;
      padding: 14px 18px;
      margin: 0 0 20px;
      display: flex;
      align-items: flex-start;
      gap: 12px;
      font-size: 13px;
      line-height: 1.5;
      color: #d4d4d8;
    }
    .context-icon { font-size: 22px; flex-shrink: 0; margin-top: 1px; }
    .context-text { flex: 1; }

    /* ─── Cards ─── */
    .card {
      background: #111115;
      border-radius: 18px;
      overflow: hidden;
      margin-bottom: 20px;
      border: 1px solid rgba(255,255,255,0.06);
      box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    }
    .card-header {
      padding: 14px 16px;
      border-bottom: 3px solid;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .platform-badge {
      display: inline-block;
      font-size: 10px;
      font-weight: 600;
      color: #fff;
      padding: 2px 10px;
      border-radius: 10px;
      width: fit-content;
      letter-spacing: 0.3px;
    }
    .card-title { font-size: 14px; font-weight: 600; color: #f4f4f5; }
    .card-participants { font-size: 11px; color: #71717a; }

    /* Chat Area */
    .chat-area {
      padding: 8px 12px 16px;
      display: flex;
      flex-direction: column;
    }
    .date-divider {
      text-align: center;
      font-size: 11px;
      color: #71717a;
      margin: 8px 0 12px;
      position: relative;
    }
    .date-divider::before, .date-divider::after {
      content: '';
      position: absolute;
      top: 50%;
      width: 35%;
      height: 1px;
      background: rgba(255,255,255,0.06);
    }
    .date-divider::before { left: 0; }
    .date-divider::after { right: 0; }

    /* Messages */
    .msg-row {
      display: flex;
      align-items: flex-end;
      margin-bottom: 4px;
      gap: 8px;
    }
    .bubble-wrapper { max-width: 82%; display: flex; flex-direction: column; }
    .avatar {
      width: 28px; height: 28px; border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      font-size: 11px; font-weight: 700; color: #fff;
      flex-shrink: 0; margin-bottom: 14px;
    }
    .bubble {
      padding: 8px 14px;
      font-size: 13.5px; line-height: 1.45;
      white-space: pre-wrap; word-wrap: break-word;
    }
    .time { font-size: 10px; color: #52525b; margin: 2px 8px 6px; }
    .meta {
      font-size: 10px; color: rgba(255,255,255,0.3);
      display: inline-flex; align-items: center; gap: 2px;
      float: right; margin-left: 8px; padding-top: 2px;
    }
    .chk { font-size: 11px; color: rgba(255,255,255,0.25); }
    .chk.leido { color: #53bdeb; }
    .sname { font-size: 11px; font-weight: 600; margin-bottom: 2px; margin-left: 2px; }

    /* Instagram */
    .platform-instagram .chat-area { background: #0a0a0f; }
    .platform-instagram .msg-row.received { flex-direction: row; }
    .platform-instagram .msg-row.sent { flex-direction: row-reverse; }
    .platform-instagram .msg-row.sent .avatar { display: none; }
    .platform-instagram .bubble.received {
      background: #1c1c1e; color: #f4f4f5; border-radius: 16px 16px 16px 4px;
    }
    .platform-instagram .bubble.sent {
      background: linear-gradient(135deg, #e0115f, #f77737);
      color: #fff; border-radius: 16px 16px 4px 16px;
    }
    .platform-instagram .msg-row.sent .time { text-align: right; }
    .platform-instagram .msg-row.received .time { text-align: left; }

    /* WhatsApp */
    .platform-whatsapp .chat-area,
    .platform-whatsapp_grupo .chat-area { background: #0b141a; }
    .platform-whatsapp .msg-row.incoming,
    .platform-whatsapp_grupo .msg-row.incoming { justify-content: flex-start; }
    .platform-whatsapp .msg-row.outgoing,
    .platform-whatsapp_grupo .msg-row.outgoing { justify-content: flex-end; }
    .platform-whatsapp .bubble.incoming,
    .platform-whatsapp_grupo .bubble.incoming {
      background: #202c33; color: #e9edef; border-radius: 8px 8px 8px 0;
    }
    .platform-whatsapp .bubble.outgoing,
    .platform-whatsapp_grupo .bubble.outgoing {
      background: #005c4b; color: #e9edef; border-radius: 8px 8px 0 8px;
    }
    .platform-whatsapp .msg-row.incoming .bubble-wrapper { align-items: flex-start; }
    .platform-whatsapp .msg-row.outgoing .bubble-wrapper { align-items: flex-end; }

    /* Footer */
    .footer-info {
      text-align: center; font-size: 10px; color: #3f3f46;
      margin-top: 32px; padding: 16px;
      border-top: 1px solid rgba(255,255,255,0.04);
    }

    /* Animación */
    @keyframes fadeUp {
      from { opacity: 0; transform: translateY(14px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .card, .context-card { animation: fadeUp 0.4s ease-out both; }
    .card:nth-child(2) { animation-delay: 0.08s; }
    .card:nth-child(3) { animation-delay: 0.16s; }
    .card:nth-child(4) { animation-delay: 0.24s; }
    .card:nth-child(5) { animation-delay: 0.32s; }
    .card:nth-child(6) { animation-delay: 0.4s; }
    .card:nth-child(7) { animation-delay: 0.48s; }

    /* Responsive */
    @media (max-width: 640px) {
      .container { padding: 12px 10px 30px; }
      .card { border-radius: 14px; }
      .bubble { font-size: 13px; padding: 7px 12px; }
      .page-header h1 { font-size: 18px; }
      .bubble-wrapper { max-width: 88%; }
    }
    @media (min-width: 900px) {
      .container { max-width: 820px; }
      .bubble { font-size: 14px; padding: 9px 16px; }
    }
"""


# ─── Generadores de HTML ───

def generar_html_historia(jornada, fecha_obj):
    """Modo historia: timeline + contexto + capítulos conectados."""
    fecha_str = fecha_obj.isoformat()
    fecha_display = fecha_es(fecha_obj)
    total = len(jornada)

    # Timeline
    timeline_items = []
    for i, cap in enumerate(jornada):
        cls = "active" if i == 0 else "done"  # first chapter = current, rest = pending/done
        # Actually, mark chapters up to first as active
        # Let's say all are "done" visually since they show a complete story
        timeline_items.append(
            f'<div class="tl-stage done"><span class="tl-icon">{cap["icono"]}</span>{cap["etapa"]}</div>'
        )
        if i < total - 1:
            timeline_items.append('<span class="tl-arrow">→</span>')

    timeline_html = "\n          ".join(timeline_items)

    # Cards
    cards_html = ""
    for i, cap in enumerate(jornada):
        # Context card before chapters that have external context
        if i == 4:  # Before bienvenida/clima
            cards_html += render_context_card(
                "🌧️ El pronóstico del Servicio Meteorológico indica lluvias para el fin de semana de llegada en Barreal. "
                "Sira ajusta automáticamente el mensaje de bienvenida para incluir recomendaciones de abrigo y actividades bajo techo.",
                "🌤️"
            )
        if i == 5:  # Before seguimiento
            cards_html += render_context_card(
                "☀️ El frente de lluvia pasó. Ahora el clima mejora. Sira hace seguimiento proactivo "
                "y recomienda actividades al aire libre según el pronóstico actualizado.",
                "🌤️"
            )

        cards_html += render_card(cap, i, total)

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Jornada Rancho Raíz · {fecha_str}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>{CSS}</style>
</head>
<body>
  <div class="container">
    <header class="page-header">
      <h1>🏔️ Rancho Raíz · Jornada Completa</h1>
      <div class="subtitle">De Instagram a la estadía — el viaje completo de un huésped</div>
      <div class="fecha">{fecha_display}</div>
      <div class="modo-badge">✨ 7 capítulos · 1 historia</div>
    </header>

    <div class="timeline">
      {timeline_html}
    </div>

    <div class="conversations">
      {cards_html}
    </div>

    <footer class="footer-info">
      <div>🤖 Simulación generada por Zira · Rancho Raíz CRM</div>
      <div>{fecha_str} · {total} capítulos · Clima integrado · Seguimiento proactivo</div>
    </footer>
  </div>
</body>
</html>"""


def generar_html_diario(escenarios, fecha_obj):
    """Modo diario: escenarios individuales."""
    fecha_str = fecha_obj.isoformat()
    fecha_display = fecha_es(fecha_obj)
    cards_html = "\n".join(render_card(e, i, len(escenarios)) for i, e in enumerate(escenarios))

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Simulación Rancho Raíz · {fecha_str}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>{CSS}</style>
</head>
<body>
  <div class="container">
    <header class="page-header">
      <h1>🏔️ Rancho Raíz · Conversaciones</h1>
      <div class="subtitle">Simulación del día</div>
      <div class="fecha">{fecha_display}</div>
      <div class="modo-badge">📱 {len(escenarios)} conversaciones</div>
    </header>

    <div class="conversations">
      {cards_html}
    </div>

    <footer class="footer-info">
      <div>🤖 Generado automáticamente por Zira · Rancho Raíz CRM</div>
      <div>{fecha_str}</div>
    </footer>
  </div>
</body>
</html>"""


# ─── CLI ───

def main():
    parser = argparse.ArgumentParser(description="Generar simulación de conversaciones")
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
