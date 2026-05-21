from __future__ import annotations
import json, os, sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crm.connectors import (
    GmailConnector, CalendarConnector, SheetsConnector,
    TelegramConnector, InstagramConnector, DriveConnector,
    ConnectorResult
)

BASE = Path(__file__).resolve().parent / "crm_state"
SHEET_RESERVAS = "1JwcJs_MfcSfvMrrOIznobsIXBcHHAUGbPC2jLIMRjYU"


def cargar_env(path: Path):
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


def seccion(titulo: str, contenido: str) -> str:
    return f"\n📌 {titulo}\n{'-'*40}\n{contenido}\n"


def generar_informe() -> str:
    partes = []
    ahora = datetime.now().strftime("%d/%m/%Y %H:%M")

    # ── Hoy en el calendario ──
    cal = CalendarConnector()
    r = cal.list_upcoming(20)
    hoy_eventos = []
    hoy = datetime.now().strftime("%Y-%m-%d")
    if r.ok:
        for e in r.data.get("events", []):
            if hoy in e.get("start", ""):
                hoy_eventos.append(f"  {e['summary']} ({e['start'][:16]})")

    if hoy_eventos:
        partes.append(seccion("HOY EN LA POSADA", "\n".join(hoy_eventos)))
    else:
        partes.append(seccion("HOY EN LA POSADA", "  Sin eventos programados."))

    # ── Próximas reservas (7 días) ──
    sheets = SheetsConnector()
    r = sheets.read(SHEET_RESERVAS)
    prox = []
    if r.ok:
        rows = r.data.get("values", [])
        headers = rows[0] if rows else []
        for row in rows[2:]:
            if len(row) >= 4:
                prox.append(f"  {row[1] if len(row)>1 else '?'} — {row[3] if len(row)>3 else '?'}")
    if prox:
        partes.append(seccion("PRÓXIMAS RESERVAS", "\n".join(prox[:5])))
    else:
        partes.append(seccion("PRÓXIMAS RESERVAS", "  Sin datos."))

    # ── Instagram ──
    ig = InstagramConnector()
    r = ig.get_media(5)
    ig_info = []
    if r.ok:
        data = r.data
        if isinstance(data, dict) and "data" in data:
            items = data["data"]
        elif isinstance(data, list):
            items = data
        else:
            items = []
        for m in items:
            caption = (m.get("caption", "") or "")[:60]
            ts = m.get("timestamp", "")[:10]
            ig_info.append(f"  {ts} | {m.get('media_type', '?')} | {caption}")
    partes.append(seccion(
        "INSTAGRAM - Últimas publicaciones",
        "\n".join(ig_info) if ig_info else "  Token IG configurado pero sin datos recientes."
    ))

    # ── Inventario ──
    inv_path = BASE / "inventario.json"
    if inv_path.exists():
        inv = json.loads(inv_path.read_text())
        items = inv if isinstance(inv, list) else []
        inv_info = [f"  {i.get('name', '?')}: {i.get('quantity', 0)}" for i in items[:10]]
        total = len(items)
        if inv_info:
            inv_info.append(f"  Total items: {total}")
    else:
        inv_info = ["  Sin inventario cargado aún."]
    partes.append(seccion("INVENTARIO", "\n".join(inv_info)))

    # ── Estado del CRM ──
    crm_files = {
        "Reservas": "reservas.json",
        "Incidentes": "incidentes.json",
        "Pagos": "pagos.json",
        "Tickets": "tickets.json",
        "Huéspedes": "huespedes.json",
    }
    crm_info = []
    for label, fname in crm_files.items():
        p = BASE / fname
        if p.exists():
            data = json.loads(p.read_text())
            count = len(data) if isinstance(data, list) else len(data.get("registrados", []))
            crm_info.append(f"  {label}: {count} registros")
    partes.append(seccion("ESTADO DEL CRM", "\n".join(crm_info)))

    # ── Estado IA Parser ──
    from parser import IA_LAST_RATE_LIMIT, IA_FALLBACK_MODELS, IA_MODEL, IA_ENDPOINT
    ia_info = []
    if not IA_ENDPOINT:
        ia_info.append("  ⚠️ IA no configurada — solo regex")
    else:
        ia_info.append(f"  ✅ IA endpoint activo (modelo: {IA_MODEL})")
        if IA_LAST_RATE_LIMIT:
            ia_info.append(f"  ⏳ Rate limit en: {IA_LAST_RATE_LIMIT}")
            disponibles = [m for m in IA_FALLBACK_MODELS if m != IA_LAST_RATE_LIMIT]
            ia_info.append(f"  🔄 Rotación disponible: {', '.join(disponibles)}")
        else:
            ia_info.append(f"  ✅ Sin rate limits activos")
    partes.append(seccion("ESTADO IA PARSER", "\n".join(ia_info)))

    # ── Resumen IA ──
    resumen = []
    resumen.append(f"  📅 Eventos hoy: {len(hoy_eventos)}")
    resumen.append(f"  🧑 Próximas reservas: {len(prox)}")
    resumen.append(f"  📸 Posts IG: {len(ig_info)}")
    resumen.append(f"  📦 Items inventario: {total if inv_path.exists() else 'pendiente'}")
    resumen.append(f"\n  Generado: {ahora}")
    if hoy_eventos:
        resumen.append(f"\n  🎯 Atención: {hoy_eventos[0]}")

    partes.append(seccion("RESUMEN EJECUTIVO PARA LEO", "\n".join(resumen)))

    return f"📋 INFORME DIARIO RANCHO RAÍZ — {ahora}\n{'='*50}" + "".join(partes)


def enviar_informe():
    informe = generar_informe()

    # 1. Telegram al grupo
    tg = TelegramConnector()
    r = tg.send_message(informe[:4000])
    print(f"📱 Telegram: {'✅' if r.ok else '❌'}")

    # 2. Email a Leo
    gmail = GmailConnector()
    r = gmail.send_message(
        "ltelloraiz@gmail.com",
        f"📋 Informe Diario Rancho Raíz - {datetime.now().strftime('%d/%m/%Y')}",
        informe
    )
    print(f"📧 Email Leo: {'✅' if r.ok else '❌'}")

    # 3. Email a oficinabarreal (copia)
    r = gmail.send_message(
        "oficinabarreal@gmail.com",
        f"📋 Copia Informe Diario - {datetime.now().strftime('%d/%m/%Y')}",
        informe
    )
    print(f"📧 Email copia: {'✅' if r.ok else '❌'}")

    # 4. Guardar local
    log_path = BASE / f"informes"
    log_path.mkdir(exist_ok=True)
    (log_path / f"{datetime.now().strftime('%Y%m%d_%H%M')}.txt").write_text(informe)
    print(f"💾 Guardado en {log_path}/")

    return informe


if __name__ == "__main__":
    cargar_env(Path(__file__).resolve().parent / ".env")
    print("📋 Generando informe diario...\n")
    informe = generar_informe()
    print(informe[:1000])
    print(f"\n... ({len(informe)} caracteres total)")

    if "--send" in sys.argv:
        print("\n→ Enviando...")
        enviar_informe()
