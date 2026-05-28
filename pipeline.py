#!/usr/bin/env python3
"""
Pipeline CRM + ARTE — modo cache primero, aprobación manual.

Modos:
  --mode cache     usa solo assets pre-generados (default)
  --mode full      genera banner/GIF durante el pipeline
  --force          regenera aunque exista cache
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

FOTOS_DIR = HERE / "simulators" / "integracion_publicidad" / "fotos"
AUDIO_DIR = HERE / "simulators" / "integracion_publicidad" / "audio"
OUTPUT_DIR = HERE / "simulaciones_output"
OUTPUT_DIR.mkdir(exist_ok=True)
REEL_DIR = Path.home() / "ranchoraiz_reels"
TEMP_DIR = Path(tempfile.gettempdir()) / "pipeline"
TEMP_DIR.mkdir(parents=True, exist_ok=True)


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


# ── Helpers Telegram ────────────────────────────────────────────

def tg_call(method: str, payload: dict) -> dict | None:
    if not TELEGRAM_TOKEN:
        log("  ⚠️  TELEGRAM_TOKEN no configurado")
        return None
    import urllib.request
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{method}"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data,
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  ⚠️  Telegram error: {e}")
        return None


def tg_send_media(media_list: list[dict], text: str = "") -> bool:
    """Send media group (up to 10 items)."""
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "media": media_list,
    }
    if text:
        payload["text"] = text
    resp = tg_call("sendMediaGroup", payload)
    return resp is not None and resp.get("ok", False)


def tg_send_message(text: str, buttons: list | None = None) -> bool:
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }
    if buttons:
        payload["reply_markup"] = {"inline_keyboard": buttons}
    resp = tg_call("sendMessage", payload)
    return resp is not None and resp.get("ok", False)


def _tg_multipart(method: str, path: str, field: str, mime: str, caption: str = "",
                  reply_markup: dict | None = None) -> bool:
    if not TELEGRAM_TOKEN:
        return False
    p = Path(path)
    if not p.exists():
        return False
    import urllib.request
    boundary = f"----boundary{uuid.uuid4().hex}"
    body = bytearray()
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(b'Content-Disposition: form-data; name="chat_id"\r\n\r\n')
    body.extend(TELEGRAM_CHAT_ID.encode())
    body.extend(b"\r\n")
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(f'Content-Disposition: form-data; name="{field}"; filename="{p.name}"\r\n'.encode())
    body.extend(f"Content-Type: {mime}\r\n\r\n".encode())
    body.extend(p.read_bytes())
    body.extend(b"\r\n")
    if caption:
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(b'Content-Disposition: form-data; name="caption"\r\n\r\n')
        body.extend(caption.encode())
        body.extend(b"\r\n")
    if reply_markup:
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(b'Content-Disposition: form-data; name="reply_markup"\r\n\r\n')
        body.extend(json.dumps(reply_markup).encode())
        body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{method}"
    req = urllib.request.Request(url, data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        with urllib.request.urlopen(req) as r:
            resp = json.loads(r.read())
        return resp.get("ok", False)
    except Exception as e:
        log(f"  ⚠️  Error {method}: {e}")
        return False


def tg_send_photo(path: str, caption: str = "", reply_markup: dict | None = None) -> bool:
    return _tg_multipart("sendPhoto", path, "photo", "image/png", caption, reply_markup)


def tg_send_animation(path: str, caption: str = "", reply_markup: dict | None = None) -> bool:
    return _tg_multipart("sendAnimation", path, "animation", "image/gif", caption, reply_markup)


def tg_send_video(path: str, caption: str = "", reply_markup: dict | None = None) -> bool:
    return _tg_multipart("sendVideo", path, "video", "video/mp4", caption, reply_markup)


# ── 1. Cache helpers ────────────────────────────────────────────

def buscar_cache(tema: str) -> dict:
    banners = sorted(OUTPUT_DIR.glob(f"banner_{tema}_*.png"),
                     key=os.path.getmtime, reverse=True)
    gifs = sorted(OUTPUT_DIR.glob(f"anim_{tema}_*.gif"),
                  key=os.path.getmtime, reverse=True)
    reels_proj = list(OUTPUT_DIR.glob(f"reel_{tema}_*.mp4"))
    reels_dir = list(REEL_DIR.glob("*.mp4")) if REEL_DIR.exists() else []
    reels = sorted(reels_proj + reels_dir, key=os.path.getmtime, reverse=True)
    result = {}
    if banners:
        b = banners[0]
        result["banner"] = {"path": str(b), "size": b.stat().st_size, "mtime": os.path.getmtime(b)}
    if gifs:
        result["gif"] = {"path": str(gifs[0]), "size": gifs[0].stat().st_size, "mtime": os.path.getmtime(gifs[0])}
    if reels:
        r = reels[0]
        result["reel"] = {"path": str(r), "size": r.stat().st_size, "mtime": os.path.getmtime(r)}
    return result


# ── 2. Generación bajo demanda ──────────────────────────────────

def html_banner(tema, titulo, subtitulo, cta):
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1080px;background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:'Arial Black',Arial,sans-serif;color:white;text-align:center;position:relative;overflow:hidden;}}
body::before{{content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;background:radial-gradient(circle at 30% 50%,rgba(197,160,89,0.15) 0%,transparent 60%);animation:pulse 4s ease-in-out infinite;}}
@keyframes pulse{{0%,100%{{opacity:0.5}}50%{{opacity:1}}}}
.tag{{font-size:28px;color:#C5A059;font-weight:bold;letter-spacing:6px;text-transform:uppercase;margin-bottom:20px;z-index:1;}}
.title{{font-size:82px;font-weight:900;line-height:1.1;margin-bottom:12px;z-index:1;}}
.sub{{font-size:28px;color:rgba(255,255,255,0.8);margin-bottom:35px;z-index:1;}}
.cta{{display:inline-block;padding:18px 50px;background:#C5A059;color:#1a1a1a;border-radius:50px;font-size:24px;font-weight:bold;z-index:1;}}
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


def html_gif_frame(i, total, tema):
    colors = ["#1a1a2e", "#16213e", "#0f3460", "#1a1a2e"]
    bg = colors[i % len(colors)]
    p = i / max(total - 1, 1)
    bounce = int(abs(p * 2 - 1) * 30)
    opacity = 0.3 + 0.7 * (1 - abs(p * 2 - 1))
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1080px;background:{bg};display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:Arial,sans-serif;color:white;text-align:center;}}
.inner{{transform:translateY({bounce}px);opacity:{opacity:.3f};}}
.icon{{font-size:120px;margin-bottom:20px;}}
.tag{{font-size:24px;color:#C5A059;font-weight:bold;letter-spacing:4px;text-transform:uppercase;margin-bottom:10px;}}
.title{{font-size:64px;font-weight:900;margin-bottom:8px;}}
</style></head><body>
<div class="inner"><div class="icon">✨</div><div class="tag">{tema}</div><div class="title">Rancho Raíz</div></div>
</body></html>"""


async def generar_banner(tema: str) -> dict:
    from mcp_client import html_a_imagen
    html = html_banner(tema.upper(), "Rancho Raíz", "Barreal · San Juan · Argentina", "Reservá tu experiencia →")
    out = str(OUTPUT_DIR / f"banner_{tema}_{datetime.now().strftime('%H%M%S')}.png")
    log("Generando banner...")
    t0 = time.time()
    result = await html_a_imagen(html=html, output_path=out)
    dt = time.time() - t0
    log(f"  Banner listo ({result['size']} bytes, {dt:.1f}s)")
    return result


async def generar_gif(tema: str, total_frames: int = 4) -> str:
    from mcp_client import html_a_imagen_bytes
    log(f"Generando GIF ({total_frames} frames)...")
    frames = []
    for i in range(total_frames):
        html = html_gif_frame(i, total_frames, tema)
        png = await html_a_imagen_bytes(html=html)
        path = TEMP_DIR / f"frame_{i:03d}.png"
        path.write_bytes(png)
        frames.append(str(path))
    palette = TEMP_DIR / "palette.png"
    subprocess.run(["ffmpeg", "-y", "-framerate", "2",
        "-i", str(TEMP_DIR / "frame_%03d.png"),
        "-vf", "palettegen=stats_mode=diff",
        str(palette)], capture_output=True)
    gif_out = str(OUTPUT_DIR / f"anim_{tema}_{datetime.now().strftime('%H%M%S')}.gif")
    subprocess.run(["ffmpeg", "-y", "-framerate", "2",
        "-i", str(TEMP_DIR / "frame_%03d.png"),
        "-i", str(palette),
        "-lavfi", "paletteuse=dither=bayer:bayer_scale=5",
        gif_out], capture_output=True)
    size = Path(gif_out).stat().st_size
    log(f"  GIF listo ({size} bytes)")
    for f in frames:
        Path(f).unlink(missing_ok=True)
    palette.unlink(missing_ok=True)
    return gif_out


async def generar_reel(tema: str) -> str:
    from flows.arte.reel_pipeline import generar_reel as gr
    log("Generando reel...")
    t0 = time.time()
    result = await gr(tema=tema, duracion=5, tagline="Rancho Raiz",
                      title="Veni a conocer", subtitle="Barreal, San Juan",
                      cta="Reserva ahora")
    dt = time.time() - t0
    log(f"  Reel listo ({result.get('size', '?')} bytes, {dt:.1f}s)")
    return result.get("path", "")


# ── 4. Email (opcional) ─────────────────────────────────────────

def enviar_email(subject: str, body: str) -> bool:
    try:
        sys.path.insert(0, str(HERE))
        from crm.connectors import GmailConnector
        gmail = GmailConnector()
    except Exception as e:
        log(f"  ⚠️  Gmail no disponible: {e}")
        return False
    try:
        to = "oficinabarreal@gmail.com"
        body_text = f"""{body}

--
Zira · Rancho Raíz CRM · {datetime.now().strftime('%d/%m/%Y %H:%M')}"""
        result = gmail.send_message(to, subject, body_text.strip())
        if result.ok:
            log(f"  ✅ Email enviado a {to}")
        else:
            log(f"  ⚠️  Error email: {result.error}")
        return result.ok
    except Exception as e:
        log(f"  ⚠️  Error enviando email: {e}")
        return False


# ── 4. Pipeline ─────────────────────────────────────────────────

def tg_poll_decision(timeout: int = 120) -> str:
    import urllib.request
    from urllib.error import HTTPError
    offset = 0
    deadline = time.time() + timeout

    # Limpiar updates viejos antes de empezar
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        params = json.dumps({"offset": -1, "timeout": 1}).encode()
        req = urllib.request.Request(url, data=params, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            updates = json.loads(r.read()).get("result", [])
        if updates:
            offset = max(u["update_id"] for u in updates) + 1
    except Exception:
        pass

    while time.time() < deadline:
        try:
            params = json.dumps({"offset": offset, "timeout": 10}).encode()
            req = urllib.request.Request(url, data=params, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as r:
                updates = json.loads(r.read()).get("result", [])
        except Exception:
            time.sleep(1)
            continue

        for u in updates:
            offset = u["update_id"] + 1
            cq = u.get("callback_query")
            if not cq:
                continue
            data = cq.get("data", "")
            cq_id = cq["id"]
            if data not in ("aprobar", "rechazar"):
                continue
            try:
                answer = json.dumps({
                    "callback_query_id": cq_id,
                    "text": "Procesando..."
                }).encode()
                areq = urllib.request.Request(
                    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery",
                    data=answer, headers={"Content-Type": "application/json"}
                )
                urllib.request.urlopen(areq, timeout=10)
            except HTTPError:
                continue
            return data
        time.sleep(0.5)
    return "rechazar"


async def run_pipeline(modo: str = "cache", force: bool = False,
                       solo_banner: bool = False, solo_gif: bool = False,
                       solo_reel: bool = False, poll: bool = False):
    tema = "montanas"

    section(f"PIPELINE CRM + ARTE — modo={modo}")
    log(f"Inicio: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    log(f"Tema: {tema.upper()}")

    # ── Paso 1: Assets ──
    section("1. OBTENER ASSETS")
    cache = buscar_cache(tema)
    if force:
        cache = {}
    necesita_banner = "banner" not in cache and not solo_gif and not solo_reel
    necesita_gif = "gif" not in cache and not solo_banner and not solo_reel
    necesita_reel = "reel" not in cache and not solo_banner and not solo_gif

    if necesita_banner and modo == "cache":
        log("  ✗ No hay banner en cache. Ejecutá con --mode full o sin --force si ya existe.")
        return
    if necesita_gif and modo == "cache":
        log("  ✗ No hay GIF en cache. Ejecutá con --mode full o sin --force si ya existe.")
        return
    if necesita_reel and modo == "cache":
        log("  ✗ No hay reel en cache. Usá --mode full --force para generar uno nuevo, o copiá un .mp4 a ~/ranchoraiz_reels/")
        return

    if not necesita_banner:
        log(f"  ✅ Banner desde cache: {Path(cache['banner']['path']).name} ({cache['banner']['size']} bytes)")
    if not necesita_gif:
        log(f"  ✅ GIF desde cache: {Path(cache['gif']['path']).name} ({cache['gif']['size']} bytes)")
    if not necesita_reel:
        log(f"  ✅ Reel desde cache: {Path(cache['reel']['path']).name} ({cache['reel']['size']} bytes)")

    if necesita_banner:
        cache["banner"] = await generar_banner(tema)
    if necesita_gif:
        gif_path = await generar_gif(tema, total_frames=4)
        cache["gif"] = {"path": gif_path, "size": Path(gif_path).stat().st_size}
    if necesita_reel:
        reel_path = await generar_reel(tema)
        cache["reel"] = {"path": reel_path, "size": Path(reel_path).stat().st_size if reel_path else 0}

    log("")

    # ── Paso 2: Enviar assets a Telegram ──
    section("2. ENVIAR A TELEGRAM")

    if solo_reel:
        rpath = cache["reel"]["path"]
        ok_reel = tg_send_video(rpath, f"Rancho Raiz: {tema.upper()}")
        log(f"  {'✅' if ok_reel else '⚠️'} Reel ({Path(rpath).name})")
    elif solo_gif:
        gif_path = cache["gif"]["path"]
        ok_gif = tg_send_animation(gif_path, f"Rancho Raiz: {tema.upper()}")
        log(f"  {'✅' if ok_gif else '⚠️'} GIF ({Path(gif_path).name})")
    else:
        ok_banner = tg_send_photo(cache["banner"]["path"], f"Rancho Raiz: {tema.upper()}")
        log(f"  {'✅' if ok_banner else '⚠️'} Banner ({Path(cache['banner']['path']).name})")

        if not solo_banner and "gif" in cache:
            gif_path = cache["gif"]["path"]
            ok_gif = tg_send_animation(gif_path, f"GIF - {tema.upper()}")
            if not ok_gif:
                ok_gif = tg_send_message(f"GIF adjunto: {Path(gif_path).name}")
            log(f"  {'✅' if ok_gif else '⚠️'} GIF ({Path(gif_path).name})")

        if not solo_banner and "reel" in cache:
            rpath = cache["reel"]["path"]
            ok_reel = tg_send_video(rpath, f"Reel - {tema.upper()}")
            log(f"  {'✅' if ok_reel else '⚠️'} Reel ({Path(rpath).name})")

    # Botones de aprobación después de todos los assets
    ok_btns = tg_send_message("Aprobas este contenido?", buttons=[[
        {"text": "Aprobar", "callback_data": "aprobar"},
        {"text": "Rechazar", "callback_data": "rechazar"},
    ]])
    log(f"  {'✅' if ok_btns else '⚠️'} Botones de aprobación enviados")

    # ── Paso 3: Esperar aprobación ──
    section("3. APROBACION")
    if poll:
        log("  Esperando que presiones un botón en Telegram...")
        decision = tg_poll_decision(timeout=120)
    else:
        log("  Escribí 'aprobar' (a) o 'rechazar' (r) y Enter:")
        decision = ""
        while decision.lower() not in ("aprobar", "a", "rechazar", "r", "s", "n"):
            try:
                decision = input("  → ")
            except (EOFError, KeyboardInterrupt):
                decision = "rechazar"
    aprobado = decision.lower() in ("aprobar", "a", "s")
    log(f"  {'✅ Aprobado' if aprobado else '❌ Rechazado'}")
    log("")

    if not aprobado:
        tg_send_message(f"Sin publicacion — {tema.upper()}")
        section("PIPELINE CANCELADO")
        log("  Contenido rechazado. Pipeline detenido.")
        return

    # ── Paso 4: Posteo exitoso ──
    section("4. POSTEO EXITOSO")
    detalles = f"Tema: {tema.upper()}"
    if not solo_gif and not solo_reel and "banner" in cache:
        detalles += f"\nBanner: {Path(cache['banner']['path']).name}"
    if not solo_banner and not solo_reel and "gif" in cache:
        detalles += f"\nGIF: {Path(cache['gif']['path']).name}"
    if not solo_banner and not solo_gif and "reel" in cache:
        detalles += f"\nReel: {Path(cache['reel']['path']).name}"
    ok_post = tg_send_message(
        f"Publicacion exitosa\n\n{detalles}"
    )
    log(f"  {'✅' if ok_post else '⚠️'} Mensaje de posteo exitoso enviado")
    log("")

    # ── Paso 5: Email notificación ──
    section("5. NOTIFICACION EMAIL")
    email_ok = enviar_email(
        f"Contenido aprobado — Rancho Raíz ({tema})",
        f"Contenido aprobado para publicar.\n\n"
        f"Tema: {tema}\n"
        f"Banner: {cache.get('banner', {}).get('path', '-')}\n"
        f"GIF: {cache.get('gif', {}).get('path', '-')}\n"
        f"Reel: {cache.get('reel', {}).get('path', '-')}\n"
        f"Aprobado: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        f"Pipeline: CAPTACION → CREACION → APROBACION → POSTEO"
    )

    # ── Resumen ──
    section("RESUMEN")
    log(f"Modo: {modo}")
    log(f"Assets: {'cache' if modo == 'cache' else 'generados'}")
    if solo_reel:
        log(f"Reel:   {cache['reel']['path']}")
    elif solo_banner:
        log(f"Banner: {cache['banner']['path']}")
        log(f"GIF:    (omitido --solo-banner)")
        if "reel" in cache:
            log(f"Reel:   {cache['reel']['path']}")
    elif solo_gif:
        log(f"Banner: (omitido --solo-gif)")
        log(f"GIF:    {cache['gif']['path']}")
        if "reel" in cache:
            log(f"Reel:   {cache['reel']['path']}")
    else:
        log(f"Banner: {cache['banner']['path']}")
        if "gif" in cache:
            log(f"GIF:    {cache['gif']['path']}")
        if "reel" in cache:
            log(f"Reel:   {cache['reel']['path']}")
    log(f"Email:  {'✅ enviado' if email_ok else '⚠️ opcional no enviado'}")
    log(f"Estado: COMPLETADO ✅")
    log(f"Hora:   {datetime.now().strftime('%H:%M:%S')}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Pipeline CRM + ARTE")
    parser.add_argument("--mode", choices=["cache", "full"], default="cache")
    parser.add_argument("--force", action="store_true", help="Regenerar aunque exista cache")
    parser.add_argument("--solo-banner", action="store_true", help="Solo banner, sin GIF ni reel")
    parser.add_argument("--solo-gif", action="store_true", help="Solo GIF, sin banner ni reel")
    parser.add_argument("--solo-reel", action="store_true", help="Solo reel, sin banner ni GIF")
    parser.add_argument("--poll", action="store_true", help="Esperar decisión por botón de Telegram")
    args = parser.parse_args()
    asyncio.run(run_pipeline(modo=args.mode, force=args.force,
                solo_banner=args.solo_banner, solo_gif=args.solo_gif,
                solo_reel=args.solo_reel, poll=args.poll))
