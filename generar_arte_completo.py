#!/usr/bin/env python3
"""
Laboratorio ARTE — Generacion completa: banner + GIF + reel con audio
Sigue el estandar documentado en ARTE_OPENCODE.md.
Metodologia: probar combinaciones, documentar resultados.
"""
import asyncio
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

OUTPUT_DIR = HERE / "simulaciones_output"
TEMP_DIR = Path(tempfile.gettempdir()) / "laboratorio_arte"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

TEMA = "barreal"  # tema nuevo, diferente a "montanas"

# ── Timeline ──
timeline = {}

def log(msg):
    print(f"  {msg}")

def section(title):
    print(f"\n{'='*65}")
    print(f"  {title}")
    print(f"{'='*65}")

# ── Helpers Telegram ──
def _cargar_env():
    env_path = HERE / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

_cargar_env()
TELEGRAM_TOKEN = os.environ.get("CRM_TG_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("CRM_TG_CHAT_ID", "8272684219")

def tg_send_photo(path: str, caption: str) -> bool:
    p = Path(path)
    if not p.exists():
        return False
    boundary = f"----boundary{uuid.uuid4().hex}"
    body = bytearray()
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(b'Content-Disposition: form-data; name="chat_id"\r\n\r\n')
    body.extend(TELEGRAM_CHAT_ID.encode())
    body.extend(b"\r\n")
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(f'Content-Disposition: form-data; name="photo"; filename="{p.name}"\r\n'.encode())
    body.extend(b"Content-Type: image/png\r\n\r\n")
    body.extend(p.read_bytes())
    body.extend(b"\r\n")
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(b'Content-Disposition: form-data; name="caption"\r\n\r\n')
    body.extend(caption.encode())
    body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())
    import urllib.request
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    req = urllib.request.Request(url, data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read()).get("ok", False)
    except Exception as e:
        log(f"  ⚠️  Error TG photo: {e}")
        return False

def tg_send_animation(path: str, caption: str) -> bool:
    p = Path(path)
    if not p.exists():
        return False
    boundary = f"----boundary{uuid.uuid4().hex}"
    body = bytearray()
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(b'Content-Disposition: form-data; name="chat_id"\r\n\r\n')
    body.extend(TELEGRAM_CHAT_ID.encode())
    body.extend(b"\r\n")
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(f'Content-Disposition: form-data; name="animation"; filename="{p.name}"\r\n'.encode())
    body.extend(b"Content-Type: image/gif\r\n\r\n")
    body.extend(p.read_bytes())
    body.extend(b"\r\n")
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(b'Content-Disposition: form-data; name="caption"\r\n\r\n')
    body.extend(caption.encode())
    body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())
    import urllib.request
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendAnimation"
    req = urllib.request.Request(url, data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read()).get("ok", False)
    except Exception as e:
        log(f"  ⚠️  Error TG anim: {e}")
        return False

def tg_send_video(path: str, caption: str) -> bool:
    p = Path(path)
    if not p.exists():
        return False
    boundary = f"----boundary{uuid.uuid4().hex}"
    body = bytearray()
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(b'Content-Disposition: form-data; name="chat_id"\r\n\r\n')
    body.extend(TELEGRAM_CHAT_ID.encode())
    body.extend(b"\r\n")
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(f'Content-Disposition: form-data; name="video"; filename="{p.name}"\r\n'.encode())
    body.extend(b"Content-Type: video/mp4\r\n\r\n")
    body.extend(p.read_bytes())
    body.extend(b"\r\n")
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(b'Content-Disposition: form-data; name="caption"\r\n\r\n')
    body.extend(caption.encode())
    body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())
    import urllib.request
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
    req = urllib.request.Request(url, data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read()).get("ok", False)
    except Exception as e:
        log(f"  ⚠️  Error TG video: {e}")
        return False

def tg_send_message(text: str) -> bool:
    import urllib.request
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = json.dumps({"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read()).get("ok", False)
    except Exception as e:
        log(f"  ⚠️  Error TG msg: {e}")
        return False

# ── 1. BANNER ──
async def generar_banner(tema: str) -> dict:
    section(f"1. BANNER — Tema: {tema}")
    from hybrid.mcp_client import html_a_imagen

    html = f"""<!DOCTYPE html>
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
<div class="tag">{tema.upper()}</div>
<div class="line"></div>
<div class="title">Rancho Raíz</div>
<div class="sub">Barreal · San Juan · Argentina</div>
<div class="cta">Reservá tu experiencia →</div>
<div class="date">{datetime.now().strftime('%B %Y')}</div>
</body></html>"""

    out = str(OUTPUT_DIR / f"banner_{tema}_{datetime.now().strftime('%H%M%S')}.png")
    log("Lanzando Chromium via MCP...")
    t0 = time.time()
    result = await html_a_imagen(html=html, output_path=out)
    dt = time.time() - t0
    log(f"  ✅ Banner: {Path(out).name} ({result['size']//1024} KB, {dt:.1f}s)")
    timeline["banner"] = {"path": out, "size": result["size"], "tiempo_s": round(dt, 1)}
    return result

# ── 2. GIF ──
async def generar_gif(tema: str, total_frames: int = 4) -> str:
    section(f"2. GIF ANIMADO — {total_frames} frames, 2fps")
    from hybrid.mcp_client import html_a_imagen_bytes

    colors = ["#1a1a2e", "#16213e", "#0f3460", "#1a1a2e"]
    frames = []
    t0 = time.time()

    for i in range(total_frames):
        bg = colors[i % len(colors)]
        p = i / max(total_frames - 1, 1)
        bounce = int(abs(p * 2 - 1) * 30)
        opacity = 0.3 + 0.7 * (1 - abs(p * 2 - 1))

        html = f"""<!DOCTYPE html>
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

        log(f"  Frame {i+1}/{total_frames}...")
        png = await html_a_imagen_bytes(html=html)
        path = TEMP_DIR / f"frame_{i:03d}.png"
        path.write_bytes(png)
        frames.append(str(path))

    log("Componiendo GIF con FFmpeg...")
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

    dt = time.time() - t0
    size = Path(gif_out).stat().st_size
    log(f"  ✅ GIF: {Path(gif_out).name} ({size//1024} KB, {dt:.1f}s)")

    for f in frames:
        Path(f).unlink(missing_ok=True)
    palette.unlink(missing_ok=True)

    timeline["gif"] = {"path": gif_out, "size": size, "tiempo_s": round(dt, 1)}
    return gif_out

# ── 3. REEL CON AUDIO ──
async def generar_reel(tema: str) -> dict:
    section("3. REEL CON AUDIO — 1080×1920, 10s, Ken Burns + keyframes + audio")
    t0 = time.time()

    # Importar el modulo de experimentos (importlib porque empieza con numero)
    import importlib.util
    exp_path = Path.home() / "Documents/proyectos/test-mcp-render/experimentos"
    mod_path = exp_path / "04_frames_a_video.py"
    sys.path.insert(0, str(exp_path.parent))  # test-mcp-render/ para import server

    spec = importlib.util.spec_from_file_location("reel_generator", str(mod_path))
    reel_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reel_mod)

    # Elegir foto tematica (distinta a la default)
    fotos_dir = HERE / "simulators" / "integracion_publicidad" / "fotos"
    fotos = sorted(fotos_dir.glob("*.jpg"))

    # Foto 03 = atardecer montañas (default), usamos la 01 = noche paisaje rural
    foto_idx = 0 if tema == "barreal" else 3
    foto_path = str(fotos[foto_idx])

    # Audio: GreenLeaves (indice 2) es el default, usemos AutumnSunset (indice 1)
    audio_dir = HERE / "simulators" / "integracion_publicidad" / "audio"
    audios = sorted(audio_dir.glob("*.mp3"))
    audio_path = str(audios[1]) if len(audios) > 1 else None  # AutumnSunset

    output_path = str(OUTPUT_DIR / f"reel_{tema}_{datetime.now().strftime('%H%M%S')}.mp4")

    log(f"  Foto: {Path(foto_path).name}")
    log(f"  Audio: {Path(audio_path).name if audio_path else 'Ninguno'}")
    log(f"  Duracion: 10s @ 10fps")
    log(f"  Tagline: ESCAPATE A {tema.upper()}")

    result = await reel_mod.generar_reel(
        foto=foto_path,
        audio=audio_path,
        tagline=f"🏔️  ESCAPATE A {tema.upper()}  🏔️",
        title="Rancho Raíz",
        subtitle="Barreal · San Juan · Argentina",
        cta="Reservá tu experiencia →",
        duracion=10,
        fps=10,
        output_path=output_path,
    )

    dt = time.time() - t0
    log(f"  ✅ Reel: {Path(result['path']).name} ({result['size']//1024} KB, {dt:.1f}s)")
    timeline["reel"] = {"path": result["path"], "size": result["size"], "tiempo_s": round(dt, 1),
                        "resolucion": result["resolution"], "duracion": result["duration"]}
    return result

# ── 4. ENVIAR A TELEGRAM ──
async def enviar_resultados():
    section("4. ENVIANDO A TELEGRAM")

    # Mensaje de inicio
    tg_send_message(
        f"🏔️ <b>Laboratorio ARTE — {TEMA.upper()}</b>\n"
        f"Generando banner + GIF + reel con audio..."
    )

    resultados = []

    if "banner" in timeline:
        log("  Enviando banner...")
        ok = tg_send_photo(timeline["banner"]["path"],
            f"🏔️ Banner ARTE — {TEMA.upper()}\n{timeline['banner']['tiempo_s']}s · {timeline['banner']['size']//1024} KB")
        resultados.append(f"📸 Banner: {'✅' if ok else '❌'} ({timeline['banner']['size']//1024} KB, {timeline['banner']['tiempo_s']}s)")
        log(f"  → {'✅' if ok else '❌'}")

    if "gif" in timeline:
        log("  Enviando GIF...")
        ok = tg_send_animation(timeline["gif"]["path"],
            f"✨ GIF ARTE — {TEMA.upper()}\n{timeline['gif']['tiempo_s']}s · {timeline['gif']['size']//1024} KB")
        resultados.append(f"🎬 GIF: {'✅' if ok else '❌'} ({timeline['gif']['size']//1024} KB, {timeline['gif']['tiempo_s']}s)")
        log(f"  → {'✅' if ok else '❌'}")

    if "reel" in timeline:
        log("  Enviando reel...")
        ok = tg_send_video(timeline["reel"]["path"],
            f"🎬 Reel ARTE — {TEMA.upper()}\n{timeline['reel']['duracion']}s · {timeline['reel']['resolucion']} · {timeline['reel']['size']//1024} KB")
        resultados.append(f"🎥 Reel: {'✅' if ok else '❌'} ({timeline['reel']['size']//1024} KB, {timeline['reel']['tiempo_s']}s)")
        log(f"  → {'✅' if ok else '❌'}")

    # Resumen final
    total_s = sum(v.get("tiempo_s", 0) for v in timeline.values())
    summary = (
        f"📊 <b>Resumen Laboratorio ARTE — {TEMA.upper()}</b>\n"
        + "\n".join(resultados)
        + f"\n\n⏱ Total: {total_s:.1f}s"
    )
    tg_send_message(summary)
    print(f"\n{'='*65}")
    print(f"  📊 RESUMEN")
    print(f"{'='*65}")
    for r in resultados:
        print(f"  {r}")
    print(f"\n  ⏱ Total: {total_s:.1f}s")
    print(f"  📁 Assets en: {OUTPUT_DIR}")

# ── MAIN ──
async def main():
    print(f"\n{'='*65}")
    print(f"  🧪 LABORATORIO ARTE — Generacion completa")
    print(f"  Tema: {TEMA.upper()}  |  Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"{'='*65}")
    print(f"\n  Pipeline estandar (ARTE_OPENCODE.md):")
    print(f"    1. Banner 1080×1080 (HTML + Chromium + MCP)")
    print(f"    2. GIF animado 4 frames 2fps (HTML + Chromium + FFmpeg)")
    print(f"    3. Reel con audio 10s 1080×1920 (Ken Burns + keyframes + FFmpeg)")
    print(f"    4. Envío a Telegram")

    try:
        await generar_banner(TEMA)
    except Exception as e:
        log(f"  ❌ Error banner: {e}")

    try:
        await generar_gif(TEMA)
    except Exception as e:
        log(f"  ❌ Error GIF: {e}")

    try:
        await generar_reel(TEMA)
    except Exception as e:
        log(f"  ❌ Error reel: {e}")

    await enviar_resultados()

if __name__ == "__main__":
    asyncio.run(main())
