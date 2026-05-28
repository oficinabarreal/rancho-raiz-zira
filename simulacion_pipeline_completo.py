#!/usr/bin/env python3
"""
Simulación completa del pipeline CRM + ARTE.

Flujo:
  1. Genera banner contextual (MCP HTML→imagen)
  2. Genera GIF animado (stop-motion con chroma)
  3. Envía a Telegram para aprobación
  4. Simula aprobación
  5. Envía email con el contenido final
  6. Envía "Posteo exitoso" a Telegram
"""
from __future__ import annotations

import asyncio
import base64
import json
import os
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "hybrid"))

# ── Assets ──────────────────────────────────────────────────────
FOTOS_DIR = HERE / "simulators" / "integracion_publicidad" / "fotos"
AUDIO_DIR = HERE / "simulators" / "integracion_publicidad" / "audio"
OUTPUT_DIR = HERE / "simulaciones_output"
OUTPUT_DIR.mkdir(exist_ok=True)

TEMP_DIR = Path(tempfile.gettempdir()) / "pipeline_sim"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Cargar .env para credenciales
def _cargar_env(path: Path):
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

_cargar_env(HERE / ".env")
_cargar_env(HERE / "hybrid" / ".env")

TELEGRAM_TOKEN = os.environ.get("CRM_TG_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("CRM_TG_CHAT_ID", "")


def log(msg):
    print(f"  {msg}")


def section(title):
    print(f"\n{'='*65}")
    print(f"  {title}")
    print(f"{'='*65}")


# ── 1. Generar banner con MCP ──────────────────────────────────

def html_banner(tema: str, titulo: str, subtitulo: str, cta: str) -> str:
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{
  width:1080px;height:1080px;
  background:linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%);
  display:flex;flex-direction:column;
  align-items:center;justify-content:center;
  font-family:'Arial Black',Arial,sans-serif;
  color:white;text-align:center;
  position:relative;overflow:hidden;
}}
body::before{{
  content:'';
  position:absolute;top:-50%;left:-50%;
  width:200%;height:200%;
  background:radial-gradient(circle at 30% 50%,rgba(197,160,89,0.15) 0%,transparent 60%);
  animation:pulse 4s ease-in-out infinite;
}}
@keyframes pulse{{0%,100%{{opacity:0.5}}50%{{opacity:1}}}}
.tag{{
  font-size:28px;color:#C5A059;font-weight:bold;
  letter-spacing:6px;text-transform:uppercase;
  margin-bottom:20px;z-index:1;
  text-shadow:0 2px 20px rgba(0,0,0,0.3);
}}
.title{{
  font-size:82px;font-weight:900;
  line-height:1.1;margin-bottom:12px;z-index:1;
  text-shadow:0 4px 40px rgba(0,0,0,0.5);
}}
.sub{{
  font-size:28px;color:rgba(255,255,255,0.8);
  margin-bottom:35px;z-index:1;
}}
.cta{{
  display:inline-block;padding:18px 50px;
  background:#C5A059;color:#1a1a1a;
  border-radius:50px;font-size:24px;font-weight:bold;z-index:1;
  box-shadow:0 8px 30px rgba(197,160,89,0.3);
}}
.line{{width:80px;height:3px;background:#C5A059;margin:15px 0 25px;z-index:1;}}
.date{{font-size:16px;color:rgba(255,255,255,0.4);margin-top:40px;z-index:1;}}
</style></head><body>
<div class="tag">{tema}</div>
<div class="line"></div>
<div class="title">{titulo}</div>
<div class="sub">{subtitulo}</div>
<div class="cta">{cta}</div>
<div class="date">{datetime.now().strftime('%B %Y')}</div>
</body></html>"""


async def generar_banner(tema: str) -> dict:
    from mcp_client import html_a_imagen
    html = html_banner(
        tema=tema.upper(),
        titulo="Rancho Raíz",
        subtitulo="Barreal · San Juan · Argentina",
        cta="Reservá tu experiencia →",
    )
    out = str(OUTPUT_DIR / f"banner_{tema}_{datetime.now().strftime('%H%M%S')}.png")
    log("Generando banner con MCP (Chromium)...")
    result = await html_a_imagen(html=html, output_path=out)
    log(f"  Banner: {result['path']} ({result['size']} bytes)")
    return result


# ── 2. Generar GIF animado (stop-motion) ───────────────────────

def html_gif_frame(frame_num: int, total_frames: int, tema: str) -> str:
    progress = frame_num / max(total_frames - 1, 1)
    bounce = int(abs(progress * 2 - 1) * 30)
    opacity = 0.3 + 0.7 * (1 - abs(progress * 2 - 1))
    colors = ["#1a1a2e", "#16213e", "#0f3460", "#1a1a2e"]
    bg = colors[frame_num % len(colors)]
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{
  width:1080px;height:1080px;
  background:{bg};
  display:flex;flex-direction:column;
  align-items:center;justify-content:center;
  font-family:Arial,sans-serif;color:white;text-align:center;
}}
.inner{{
  transform:translateY({bounce}px);
  opacity:{opacity:.3f};
  transition:all 0.1s;
}}
.icon{{font-size:120px;margin-bottom:20px;}}
.tag{{font-size:24px;color:#C5A059;font-weight:bold;letter-spacing:4px;text-transform:uppercase;margin-bottom:10px;}}
.title{{font-size:64px;font-weight:900;margin-bottom:8px;}}
.frame{{font-size:14px;color:rgba(255,255,255,0.3);margin-top:30px;}}
</style></head><body>
<div class="inner">
<div class="icon">✨</div>
<div class="tag">{tema}</div>
<div class="title">Rancho Raíz</div>
</div>
<div class="frame">frame {frame_num+1}/{total_frames}</div>
</body></html>"""


async def generar_gif(tema: str, total_frames: int = 8) -> str:
    from mcp_client import html_a_imagen_bytes
    log(f"Generando GIF stop-motion ({total_frames} frames)...")
    frames = []
    for i in range(total_frames):
        html = html_gif_frame(i, total_frames, tema)
        png = await html_a_imagen_bytes(html=html)
        path = TEMP_DIR / f"frame_{i:03d}.png"
        path.write_bytes(png)
        frames.append(str(path))
        log(f"  Frame {i+1}/{total_frames}")

    gif_out = str(OUTPUT_DIR / f"anim_{tema}_{datetime.now().strftime('%H%M%S')}.gif")
    log("Componiendo GIF con FFmpeg palettegen/paletteuse...")
    palette = TEMP_DIR / "palette.png"
    subprocess.run([
        "ffmpeg", "-y",
        "-framerate", "2",
        "-i", str(TEMP_DIR / "frame_%03d.png"),
        "-vf", "palettegen=stats_mode=diff",
        str(palette),
    ], capture_output=True)
    subprocess.run([
        "ffmpeg", "-y",
        "-framerate", "2",
        "-i", str(TEMP_DIR / "frame_%03d.png"),
        "-i", str(palette),
        "-lavfi", "paletteuse=dither=bayer:bayer_scale=5",
        gif_out,
    ], capture_output=True)
    size = Path(gif_out).stat().st_size
    log(f"  GIF: {gif_out} ({size} bytes)")
    for f in frames:
        Path(f).unlink(missing_ok=True)
    if palette.exists():
        palette.unlink()
    return gif_out


# ── 3. Enviar a Telegram ───────────────────────────────────────

def telegram_send_message(text: str) -> bool:
    if not TELEGRAM_TOKEN:
        log("  ⚠️  TELEGRAM_TOKEN no configurado")
        return False
    import urllib.request
    data = json.dumps({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": [[
                {"text": "✅ Aprobar", "callback_data": "aprobar"},
                {"text": "❌ Rechazar", "callback_data": "rechazar"},
            ]]
        }
    }).encode()
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        resp = json.loads(r.read())
    return resp.get("ok", False)


def telegram_send_photo(path: str, caption: str = "") -> bool:
    if not TELEGRAM_TOKEN:
        log("  ⚠️  TELEGRAM_TOKEN no configurado")
        return False
    import mimetypes
    import urllib.request
    p = Path(path)
    if not p.exists():
        log(f"  ✗ Archivo no encontrado: {path}")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    boundary = f"----boundary{uuid.uuid4().hex}"
    mime = mimetypes.guess_type(p.name)[0] or "image/png"
    body = bytearray()
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(f'Content-Disposition: form-data; name="chat_id"\r\n\r\n'.encode())
    body.extend(TELEGRAM_CHAT_ID.encode())
    body.extend(b"\r\n")
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(f'Content-Disposition: form-data; name="photo"; filename="{p.name}"\r\n'.encode())
    body.extend(f"Content-Type: {mime}\r\n\r\n".encode())
    body.extend(p.read_bytes())
    body.extend(b"\r\n")
    if caption:
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="caption"\r\n\r\n'.encode())
        body.extend(caption.encode())
        body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())
    req = urllib.request.Request(url, data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req) as r:
        resp = json.loads(r.read())
    return resp.get("ok", False)


def telegram_send_document(path: str, caption: str = "") -> bool:
    if not TELEGRAM_TOKEN:
        log("  ⚠️  TELEGRAM_TOKEN no configurado")
        return False
    import mimetypes
    import urllib.request
    p = Path(path)
    if not p.exists():
        log(f"  ✗ Archivo no encontrado: {path}")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
    boundary = f"----boundary{uuid.uuid4().hex}"
    mime = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
    body = bytearray()
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(f'Content-Disposition: form-data; name="chat_id"\r\n\r\n'.encode())
    body.extend(TELEGRAM_CHAT_ID.encode())
    body.extend(b"\r\n")
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(f'Content-Disposition: form-data; name="document"; filename="{p.name}"\r\n'.encode())
    body.extend(f"Content-Type: {mime}\r\n\r\n".encode())
    body.extend(p.read_bytes())
    body.extend(b"\r\n")
    if caption:
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="caption"\r\n\r\n'.encode())
        body.extend(caption.encode())
        body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())
    req = urllib.request.Request(url, data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req) as r:
        resp = json.loads(r.read())
    return resp.get("ok", False)


# ── 4. Enviar email via Gmail ──────────────────────────────────

def enviar_email(subject: str, body: str, attachment_path: str = "") -> dict:
    try:
        sys.path.insert(0, str(HERE))
        from crm.connectors import GmailConnector
        gmail = GmailConnector()
    except Exception as e:
        log(f"  ⚠️  No se pudo inicializar Gmail: {e}")
        return {"ok": False, "error": str(e)}

    body_text = f"""{body}

--
Zira 🤖
Rancho Raíz — CRM Autónomo
Simulación de Pipeline Completo
{datetime.now().strftime('%d/%m/%Y %H:%M')}
"""
    to = "oficinabarreal@gmail.com"
    try:
        result = gmail.send_message(to, subject, body_text.strip())
        if result.ok:
            log(f"  ✅ Email enviado a {to}")
        else:
            log(f"  ⚠️  Error email: {result.error}")
        return {"ok": result.ok, "to": to, "data": result.data, "error": result.error}
    except Exception as e:
        log(f"  ⚠️  Error enviando email: {e}")
        return {"ok": False, "error": str(e)}


# ── 5. Pipeline completo ────────────────────────────────────────

async def pipeline_completo():
    tema = "montanas"
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

    section("PIPELINE CRM + ARTE — SIMULACIÓN COMPLETA")
    log(f"Inicio: {fecha}\n")
    log(f"Contexto: Promocion temporada alta - Tucuman/Rancho Raiz")
    log(f"Tema visual: {tema.upper()}")
    log(f"Destinos: Telegram + Email\n")

    results = {}

    # ── Paso 1: Banner ──
    section("1. ARTE — GENERAR BANNER")
    banner_candidates = sorted(OUTPUT_DIR.glob(f"banner_{tema}_*.png"), key=os.path.getmtime, reverse=True)
    if banner_candidates and (time.time() - os.path.getmtime(banner_candidates[0])) < 3600:
        results["banner"] = {"path": str(banner_candidates[0]), "size": banner_candidates[0].stat().st_size, "width": 1080, "height": 1080}
        log(f"  Usando banner existente: {results['banner']['path']}")
    else:
        results["banner"] = await generar_banner(tema)
    log("")

    # ── Paso 2: GIF animado (skip si archivo reciente existe) ──
    section("2. ARTE — GENERAR GIF ANIMADO")
    gif_candidates = sorted(OUTPUT_DIR.glob(f"anim_{tema}_*.gif"), key=os.path.getmtime, reverse=True)
    if gif_candidates and (time.time() - os.path.getmtime(gif_candidates[0])) < 3600:
        results["gif"] = str(gif_candidates[0])
        log(f"  Usando GIF existente: {results['gif']}")
    else:
        results["gif"] = await generar_gif(tema, total_frames=4)
    log("")

    # ── Paso 3: Enviar a Telegram para aprobación ──
    section("3. MENSAJERIA — ENVIAR A TELEGRAM (APROBACIÓN)")
    msg_aprobacion = (
        f"<b>Pipeline CRM + ARTE — Solicitud de Aprobación</b>\n\n"
        f"Tema: {tema.upper()}\n"
        f"Banner generado: {Path(results['banner']['path']).name}\n"
        f"GIF animado: {Path(results['gif']).name}\n\n"
        f"<i>¿Aprobás este contenido para publicar?</i>"
    )

    # Enviar mensaje con botones de aprobación
    ok = telegram_send_message(msg_aprobacion)
    if ok:
        log("  ✅ Mensaje de aprobación enviado a Telegram")
    else:
        log("  ⚠️  No se pudo enviar mensaje a Telegram (verificar token)")

    # Enviar los archivos visuales
    for key, path in [("Banner", results["banner"]["path"]), ("GIF", results["gif"])]:
        if key == "Banner":
            ok = telegram_send_photo(path, f"📸 {key} - {tema.upper()}")
        else:
            ok = telegram_send_document(path, f"🎬 {key} - {tema.upper()}")
        log(f"  {'✅' if ok else '⚠️'} {key} enviado a Telegram")

    log("")

    # ── Paso 4: Simular aprobación ──
    section("4. APROBACION — SIMULADA (auto-approve)")
    log("  Esperando 3 segundos (simulación de revisión)...")
    await asyncio.sleep(3)
    log("  ✅ Contenido APROBADO automáticamente")
    log("")

    # ── Paso 5: Enviar email con resultado ──
    section("5. NOTIFICACION — ENVIAR EMAIL")
    email_subject = f"Contenido aprobado para publicar — Rancho Raíz ({tema})"
    email_body = (
        f"Se ha aprobado nuevo contenido para publicar.\n\n"
        f"Tema: {tema}\n"
        f"Banner: {results['banner']['path']}\n"
        f"  Tamaño: {results['banner']['size']} bytes\n"
        f"  Resolución: {results['banner'].get('width', '?')}x{results['banner'].get('height', '?')}\n"
        f"GIF: {results['gif']}\n"
        f"  Tamaño: {Path(results['gif']).stat().st_size} bytes\n\n"
        f"Aprobado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        f"Pipeline: CAPTACION → CREACION → APROBACION → POSTEO"
    )
    try:
        enviar_email(email_subject, email_body)
    except Exception as e:
        log(f"  ⚠️  Email no enviado (no crítico): {e}")
    log("")

    # ── Paso 6: Posteo exitoso ──
    section("6. MENSAJERIA — POSTEO EXITOSO")
    msg_posteado = (
        f"<b>Posteo realizado exitosamente</b> ✅\n\n"
        f"Tema: {tema.upper()}\n"
        f"Banner: {Path(results['banner']['path']).name}\n"
        f"GIF: {Path(results['gif']).name}\n\n"
        f"<i>Contenido publicado en los canales correspondientes.</i>"
    )
    ok = telegram_send_message(msg_posteado)
    if ok:
        log("  ✅ Mensaje 'Posteo exitoso' enviado a Telegram")
    else:
        log("  ⚠️  No se pudo enviar mensaje a Telegram")

    # ── Resumen final ──
    section("RESUMEN FINAL")
    log(f"Banner:  {results['banner']['path']}")
    log(f"GIF:     {results['gif']}")
    log(f"Estado:  COMPLETADO ✅")
    log(f"Hora:    {datetime.now().strftime('%H:%M:%S')}")
    log(f"")
    log(f"Pipeline ejecutado:")
    log(f"  1. CAPTACION (simulada: tema={tema})")
    log(f"  2. CREACION_CONTENIDO (banner + GIF generados)")
    log(f"  3. ESPERA_APROBACION (enviado a Telegram)")
    log(f"  4. APROBACION (simulada)")
    log(f"  5. POSTEO_ACTIVO (email enviado)")
    log(f"  6. Posteo exitoso notificado en Telegram")
    log(f"")
    log(f"Archivos en: {OUTPUT_DIR}")


if __name__ == "__main__":
    asyncio.run(pipeline_completo())
