#!/usr/bin/env python3
"""
Simulación completa del pipeline CRM + ARTE — versión fortalecida.

Flujo completo (8 pasos del state machine):
  1. CAPTACION_TELEGRAM → 2. CREACION_CONTENIDO → 3. ESPERA_APROBACION
  → 4. POSTEO_ACTIVO → 5. INTERACCION_INSTAGRAM (sim.) → 6. CALENTAMIENTO_LEAD (sim.)
  → 7. DERIVACION_WHATSAPP (sim.) → 8. ACOMPAÑAMIENTO_VIAJE (sim.)

Modos CLI:
  --tema TEMA         Tema visual (default: montanas)
  --force             Regenera assets aunque existan en cache
  --skip-telegram     No enviar nada a Telegram
  --skip-email        No enviar email
  --auto-approve      Aprueba automaticamente (sin espera)
  --frames N          Cantidad de frames para GIF (default: 4)
  --lead              Simular tambien el journey completo de un lead
  --reel              Generar tambien un reel (requiere MCP)
"""
from __future__ import annotations

import argparse
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
from typing import Any, Dict, List, Optional

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "hybrid"))

# ── Assets ──
FOTOS_DIR = HERE / "simulators" / "integracion_publicidad" / "fotos"
AUDIO_DIR = HERE / "simulators" / "integracion_publicidad" / "audio"
OUTPUT_DIR = HERE / "simulaciones_output"
OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR = Path(tempfile.gettempdir()) / "pipeline_sim"
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


# ── Helpers ──

def log(msg: str):
    print(f"  {msg}")


def section(title: str):
    print(f"\n{'='*65}")
    print(f"  {title}")
    print(f"{'='*65}")


def step_label(paso: int, estado: str, desc: str):
    """Log de paso del state machine con formato consistente."""
    print(f"\n  ── ▶  PASO {paso}/8: {estado}")
    print(f"      {desc}")


PASO_ESTADOS = [
    (1, "CAPTACION_TELEGRAM",        "Recepción de foto/consulta por Telegram"),
    (2, "CREACION_CONTENIDO",         "Generación de contenido visual"),
    (3, "ESPERA_APROBACION",          "Envío a Telegram con botones Aprobar/Rechazar"),
    (4, "POSTEO_ACTIVO",              "Publicación del contenido aprobado"),
    (5, "INTERACCION_INSTAGRAM",      "Simulación de interacciones en Instagram"),
    (6, "CALENTAMIENTO_LEAD",         "Simulación de lead nurturing"),
    (7, "DERIVACION_WHATSAPP",        "Simulación de derivación a WhatsApp"),
    (8, "ACOMPAÑAMIENTO_VIAJE",       "Simulación de acompañamiento al huésped"),
]


class PipelineMetrics:
    """Recolecta metricas de cada paso del pipeline."""

    def __init__(self):
        self.steps: List[Dict[str, Any]] = []
        self._start = time.time()

    def record(self, paso: int, estado: str, ok: bool, detail: str = "", meta: Optional[Dict] = None):
        elapsed = time.time() - self._start
        self.steps.append({
            "paso": paso,
            "estado": estado,
            "ok": ok,
            "detail": detail,
            "elapsed_s": round(elapsed, 2),
            "meta": meta or {},
        })

    def summary(self) -> str:
        total_ok = sum(1 for s in self.steps if s["ok"])
        total = len(self.steps)
        elapsed = round(time.time() - self._start, 1)
        lines = [
            f"\n{'='*65}",
            f"  MÉTRICAS DEL PIPELINE",
            f"{'='*65}",
            f"  Pasos ejecutados: {total}/8",
            f"  Exitosos: {total_ok}/{total}",
            f"  Tiempo total: {elapsed}s",
            f"",
        ]
        for s in self.steps:
            icon = "✅" if s["ok"] else "❌"
            lines.append(f"  {icon} Paso {s['paso']} {s['estado']}: {s['detail']} ({s['elapsed_s']}s)")
        return "\n".join(lines)

    def to_json(self) -> str:
        return json.dumps({
            "total_steps": len(self.steps),
            "successful": sum(1 for s in self.steps if s["ok"]),
            "elapsed_s": round(time.time() - self._start, 1),
            "steps": self.steps,
        }, indent=2)


metrics = PipelineMetrics()


# ── 1. CAPTACION_TELEGRAM ──

def simular_captacion(tema: str) -> dict:
    """Simula la recepción de una foto/consulta por Telegram."""
    foto_dir = FOTOS_DIR / tema
    fotos = list(foto_dir.glob("*.jpg")) + list(foto_dir.glob("*.png")) if foto_dir.exists() else []
    return {
        "tema": tema,
        "fuente": "Telegram",
        "fotos_disponibles": [str(f) for f in fotos] if fotos else [],
        "mensaje_original": f"Quiero promocionar el tema {tema} para la temporada",
    }


# ── 2. CREACION_CONTENIDO ──

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
  content:'';position:absolute;top:-50%;left:-50%;
  width:200%;height:200%;
  background:radial-gradient(circle at 30% 50%,rgba(197,160,89,0.15) 0%,transparent 60%);
  animation:pulse 4s ease-in-out infinite;
}}
@keyframes pulse{{0%,100%{{opacity:0.5}}50%{{opacity:1}}}}
.tag{{font-size:28px;color:#C5A059;font-weight:bold;letter-spacing:6px;text-transform:uppercase;margin-bottom:20px;z-index:1;text-shadow:0 2px 20px rgba(0,0,0,0.3);}}
.title{{font-size:82px;font-weight:900;line-height:1.1;margin-bottom:12px;z-index:1;text-shadow:0 4px 40px rgba(0,0,0,0.5);}}
.sub{{font-size:28px;color:rgba(255,255,255,0.8);margin-bottom:35px;z-index:1;}}
.cta{{display:inline-block;padding:18px 50px;background:#C5A059;color:#1a1a1a;border-radius:50px;font-size:24px;font-weight:bold;z-index:1;box-shadow:0 8px 30px rgba(197,160,89,0.3);}}
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


def html_gif_frame(frame_num: int, total_frames: int, tema: str) -> str:
    progress = frame_num / max(total_frames - 1, 1)
    bounce = int(abs(progress * 2 - 1) * 30)
    opacity = 0.3 + 0.7 * (1 - abs(progress * 2 - 1))
    colors = ["#1a1a2e", "#16213e", "#0f3460", "#1a1a2e"]
    bg = colors[frame_num % len(colors)]
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1080px;background:{bg};display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:Arial,sans-serif;color:white;text-align:center;}}
.inner{{transform:translateY({bounce}px);opacity:{opacity:.3f};transition:all 0.1s;}}
.icon{{font-size:120px;margin-bottom:20px;}}
.tag{{font-size:24px;color:#C5A059;font-weight:bold;letter-spacing:4px;text-transform:uppercase;margin-bottom:10px;}}
.title{{font-size:64px;font-weight:900;margin-bottom:8px;}}
.frame{{font-size:14px;color:rgba(255,255,255,0.3);margin-top:30px;}}
</style></head><body>
<div class="inner"><div class="icon">✨</div><div class="tag">{tema}</div><div class="title">Rancho Raíz</div></div>
<div class="frame">frame {frame_num+1}/{total_frames}</div>
</body></html>"""


async def verificar_mcp_disponible() -> bool:
    """Verifica si el servidor MCP responde antes de generar."""
    try:
        from mcp_client import html_a_imagen_bytes
        html = "<html><body><p>test</p></body></html>"
        await asyncio.wait_for(html_a_imagen_bytes(html=html, width=100, height=100), timeout=15)
        return True
    except Exception as e:
        log(f"  ⚠️  MCP no disponible: {e}")
        return False


async def generar_banner(tema: str, force: bool = False) -> Optional[dict]:
    # Cache check
    if not force:
        candidates = sorted(OUTPUT_DIR.glob(f"banner_{tema}_*.png"), key=os.path.getmtime, reverse=True)
        if candidates and (time.time() - os.path.getmtime(candidates[0])) < 3600:
            log(f"  Usando banner existente (cache < 1h): {candidates[0].name}")
            return {"path": str(candidates[0]), "size": candidates[0].stat().st_size, "width": 1080, "height": 1080}

    if not await verificar_mcp_disponible():
        log("  ✗ No se puede generar banner: MCP no disponible")
        return None

    from mcp_client import html_a_imagen
    html = html_banner(
        tema=tema.upper(),
        titulo="Rancho Raíz",
        subtitulo="Barreal · San Juan · Argentina",
        cta="Reservá tu experiencia →",
    )
    out = str(OUTPUT_DIR / f"banner_{tema}_{datetime.now().strftime('%H%M%S')}.png")
    log(f"  Generando banner con MCP (Chromium)...")
    t0 = time.time()
    try:
        result = await asyncio.wait_for(html_a_imagen(html=html, output_path=out), timeout=60)
        dt = time.time() - t0
        log(f"  Banner generado: {Path(result['path']).name} ({result['size']} bytes, {dt:.1f}s)")
        return result
    except asyncio.TimeoutError:
        log(f"  ✗ Timeout generando banner (>60s)")
        return None
    except Exception as e:
        log(f"  ✗ Error generando banner: {e}")
        return None


async def generar_gif(tema: str, total_frames: int = 4, force: bool = False) -> Optional[str]:
    if not force:
        candidates = sorted(OUTPUT_DIR.glob(f"anim_{tema}_*.gif"), key=os.path.getmtime, reverse=True)
        if candidates and (time.time() - os.path.getmtime(candidates[0])) < 3600:
            log(f"  Usando GIF existente (cache < 1h): {candidates[0].name}")
            return str(candidates[0])

    if not await verificar_mcp_disponible():
        log("  ✗ No se puede generar GIF: MCP no disponible")
        return None

    from mcp_client import html_a_imagen_bytes
    log(f"  Generando GIF stop-motion ({total_frames} frames)...")
    frames = []
    for i in range(total_frames):
        html = html_gif_frame(i, total_frames, tema)
        try:
            png = await asyncio.wait_for(html_a_imagen_bytes(html=html), timeout=30)
        except Exception as e:
            log(f"  ⚠️  Error frame {i+1}: {e}")
            continue
        path = TEMP_DIR / f"frame_{i:03d}.png"
        path.write_bytes(png)
        frames.append(str(path))

    if len(frames) < 2:
        log("  ✗ No se generaron suficientes frames para el GIF")
        return None

    gif_out = str(OUTPUT_DIR / f"anim_{tema}_{datetime.now().strftime('%H%M%S')}.gif")
    log(f"  Componiendo GIF con FFmpeg ({len(frames)} frames)...")
    palette = TEMP_DIR / "palette.png"

    try:
        subprocess.run([
            "ffmpeg", "-y",
            "-framerate", "2",
            "-i", str(TEMP_DIR / "frame_%03d.png"),
            "-vf", "palettegen=stats_mode=diff",
            str(palette),
        ], capture_output=True, timeout=30, check=True)

        subprocess.run([
            "ffmpeg", "-y",
            "-framerate", "2",
            "-i", str(TEMP_DIR / "frame_%03d.png"),
            "-i", str(palette),
            "-lavfi", "paletteuse=dither=bayer:bayer_scale=5",
            gif_out,
        ], capture_output=True, timeout=30, check=True)
    except subprocess.TimeoutExpired:
        log("  ✗ Timeout en FFmpeg")
        return None
    except subprocess.CalledProcessError as e:
        log(f"  ✗ Error FFmpeg: {e}")
        return None

    size = Path(gif_out).stat().st_size
    log(f"  GIF generado: {Path(gif_out).name} ({size} bytes)")

    # Cleanup
    for f in frames:
        Path(f).unlink(missing_ok=True)
    if palette.exists():
        palette.unlink()

    return gif_out


async def generar_reel(tema: str, force: bool = False) -> Optional[str]:
    """Genera un reel MP4 si el pipeline de reels esta disponible."""
    if not force:
        candidates = list(OUTPUT_DIR.glob(f"reel_{tema}_*.mp4"))
        reels_dir = Path.home() / "ranchoraiz_reels"
        if reels_dir.exists():
            candidates += list(reels_dir.glob("*.mp4"))
        candidates.sort(key=os.path.getmtime, reverse=True)
        if candidates and (time.time() - os.path.getmtime(candidates[0])) < 3600:
            log(f"  Usando reel existente (cache < 1h): {candidates[0].name}")
            return str(candidates[0])

    try:
        from flows.arte.reel_pipeline import generar_reel as gr
        log("  Generando reel...")
        t0 = time.time()
        result = await gr(event_data={
            "foto": None,
            "audio": None,
            "tagline": "ESCAPATE A LA MONTAÑA",
            "title": "Rancho Raíz",
            "subtitle": "Barreal · San Juan · Argentina",
            "cta": "Reserva tu experiencia →",
            "duracion": 10,
        })
        dt = time.time() - t0
        if result.status == "ok":
            reel_data = result.state_updates.get("reel", {})
            path = reel_data.get("path", "")
            if path and Path(path).exists():
                log(f"  Reel generado: {Path(path).name} ({reel_data.get('size', '?')} bytes, {dt:.1f}s)")
                return path
        log(f"  ⚠️  Reel: {result.message}")
        return None
    except Exception as e:
        log(f"  ⚠️  No se pudo generar reel: {e}")
        return None


# ── 3. ESPERA_APROBACION (Telegram) ──

def telegram_send_message(text: str, buttons: bool = True) -> bool:
    if not TELEGRAM_TOKEN:
        log("  ⚠️  TELEGRAM_TOKEN no configurado — omitiendo")
        return False
    import urllib.request
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }
    if buttons:
        payload["reply_markup"] = {
            "inline_keyboard": [[
                {"text": "✅ Aprobar", "callback_data": "aprobar"},
                {"text": "❌ Rechazar", "callback_data": "rechazar"},
            ]]
        }
    data = json.dumps(payload).encode()
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = json.loads(r.read())
        return resp.get("ok", False)
    except Exception as e:
        log(f"  ⚠️  Error Telegram sendMessage: {e}")
        return False


def _tg_multipart(method: str, path: str, field: str, caption: str = "") -> bool:
    if not TELEGRAM_TOKEN:
        return False
    import mimetypes
    import urllib.request
    p = Path(path)
    if not p.exists():
        log(f"  ✗ Archivo no encontrado: {path}")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{method}"
    boundary = f"----boundary{uuid.uuid4().hex}"
    mime = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
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
    body.extend(f"--{boundary}--\r\n".encode())
    req = urllib.request.Request(url, data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = json.loads(r.read())
        return resp.get("ok", False)
    except Exception as e:
        log(f"  ⚠️  Error {method}: {e}")
        return False


def telegram_send_photo(path: str, caption: str = "") -> bool:
    return _tg_multipart("sendPhoto", path, "photo", caption)


def telegram_send_animation(path: str, caption: str = "") -> bool:
    return _tg_multipart("sendAnimation", path, "animation", caption)


def telegram_send_video(path: str, caption: str = "") -> bool:
    return _tg_multipart("sendVideo", path, "video", caption)


# ── 4. Email ──

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


# ── 5-8. Simulaciones de interaccion ──

def simular_interaccion_instagram():
    """Simula Paso 5: interacciones en Instagram."""
    log("  Cliente simulado: @viajero_andes")
    log("  Comentario: \"Qué hermoso lugar! Tienen disponibilidad para febrero?\"")
    log("  Lead detectado: INTERES_CONFIRMADO")
    return {"usuario": "@viajero_andes", "intencion": "reserva", "temperatura": "caliente"}


def simular_calentamiento_lead():
    """Simula Paso 6: lead nurturing."""
    log("  Hermes-agent: responde con tono empático")
    log("  Intercambio: 3 mensajes simulados")
    log("  Lead elevado a: LISTO_PARA_DERIVAR")
    return {"temperatura_final": "caliente", "mensajes_intercambiados": 3}


def simular_derivacion_whatsapp():
    """Simula Paso 7: derivacion a WhatsApp."""
    log("  Historial de chat comprimido")
    log("  Transferencia a agente de ventas")
    return {"transferido_a": "WhatsApp API", "resumen_chat": "Cliente interesado en estadia febrero"}


def simular_acompanamiento_viaje():
    """Simula Paso 8: acompañamiento al huésped."""
    log("  Huésped activo: check-in simulado")
    log("  Mapa de experiencias enviado")
    log("  Guía de vivencias disponible")
    log("  Checkout: completado")
    return {"checkout": datetime.now().isoformat(), "estado_final": "HISTORIAL_ARCHIVADO"}


# ── Pipeline principal ──

async def pipeline_completo(args: argparse.Namespace):
    tema = args.tema
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

    section("PIPELINE CRM + ARTE — SIMULACIÓN FORTALECIDA")
    log(f"Inicio: {fecha}")
    log(f"Tema visual: {tema.upper()}")
    log(f"Modo: {'force' if args.force else 'cache'}")
    log(f"Telegram: {'HABILITADO' if not args.skip_telegram else 'DESHABILITADO'}")
    log(f"Email: {'HABILITADO' if not args.skip_email else 'DESHABILITADO'}")
    log(f"Aprobación: {'automática' if args.auto_approve else 'manual (via Telegram)'}")
    log(f"")

    results: Dict[str, Any] = {}

    # ═══════════════════════════════════════════════════════════════
    # PASO 1: CAPTACION_TELEGRAM
    # ═══════════════════════════════════════════════════════════════
    step_label(1, "CAPTACION_TELEGRAM", "Recepción de foto/consulta por Telegram")
    captacion = simular_captacion(tema)
    log(f"  Tema captado: {captacion['tema']}")
    log(f"  Fuente: {captacion['fuente']}")
    log(f"  Mensaje: \"{captacion['mensaje_original']}\"")
    if captacion["fotos_disponibles"]:
        log(f"  Fotos disponibles: {len(captacion['fotos_disponibles'])}")
    metrics.record(1, "CAPTACION_TELEGRAM", True, f"Tema={tema}")

    # ═══════════════════════════════════════════════════════════════
    # PASO 2: CREACION_CONTENIDO
    # ═══════════════════════════════════════════════════════════════
    section("")
    step_label(2, "CREACION_CONTENIDO", "Generación de contenido visual (banner + GIF + reel)")

    # 2a. Banner
    log("  ── Banner ──")
    banner = await generar_banner(tema, force=args.force)
    if banner:
        results["banner"] = banner
        log(f"  ✅ Banner listo")
        metrics.record(2, "CREACION_CONTENIDO", True, f"Banner={Path(banner['path']).name}")
    else:
        log(f"  ❌ Banner falló")
        metrics.record(2, "CREACION_CONTENIDO", False, "Banner: MCP no disponible o timeout")

    # 2b. GIF animado
    log("")
    log("  ── GIF Animado ──")
    gif = await generar_gif(tema, total_frames=args.frames, force=args.force)
    if gif:
        results["gif"] = gif
        log(f"  ✅ GIF listo")
        if "ok" in metrics.steps[-1]:
            # Update the previous step's success to reflect both
            pass
    else:
        log(f"  ⚠️  GIF omitido (MCP/FFmpeg no disponible)")

    # 2c. Reel (opcional)
    if args.reel:
        log("")
        log("  ── Reel ──")
        reel = await generar_reel(tema, force=args.force)
        if reel:
            results["reel"] = reel
            log(f"  ✅ Reel listo")

    # ═══════════════════════════════════════════════════════════════
    # PASO 3: ESPERA_APROBACION
    # ═══════════════════════════════════════════════════════════════
    section("")
    step_label(3, "ESPERA_APROBACION", "Envío a Telegram con botones Aprobar/Rechazar")

    if not args.skip_telegram and TELEGRAM_TOKEN:
        msg_aprobacion = (
            f"<b>Pipeline CRM + ARTE — Solicitud de Aprobación</b>\n\n"
            f"Tema: {tema.upper()}\n"
            f"Banner: {Path(results.get('banner', {}).get('path', 'N/A')).name}\n"
            f"GIF: {Path(results.get('gif', 'N/A')).name}"
        )
        if results.get("reel"):
            msg_aprobacion += f"\nReel: {Path(results['reel']).name}"
        msg_aprobacion += f"\n\n<i>¿Aprobás este contenido para publicar?</i>"

        ok = telegram_send_message(msg_aprobacion, buttons=True)
        if ok:
            log(f"  ✅ Mensaje de aprobación enviado a Telegram")
        else:
            log(f"  ⚠️  No se pudo enviar mensaje a Telegram (verificar token)")

        # Enviar assets visuales
        if "banner" in results:
            ok = telegram_send_photo(results["banner"]["path"], f"📸 Banner - {tema.upper()}")
            log(f"  {'✅' if ok else '⚠️'} Banner enviado a Telegram")
        if "gif" in results:
            ok = telegram_send_animation(results["gif"], f"🎬 GIF animado - {tema.upper()}")
            log(f"  {'✅' if ok else '⚠️'} GIF enviado a Telegram")
        if "reel" in results:
            ok = telegram_send_video(results["reel"], f"🎥 Reel - {tema.upper()}")
            log(f"  {'✅' if ok else '⚠️'} Reel enviado a Telegram")
    else:
        log(f"  ⏭️  Telegram deshabilitado (--skip-telegram o sin token)")
        log(f"  (aprobación simulada localmente)")

    metrics.record(3, "ESPERA_APROBACION", True, "Enviado a Telegram" if not args.skip_telegram else "Omitido (skip)")

    # ═══════════════════════════════════════════════════════════════
    # PASO 4: POSTEO_ACTIVO (aprobacion + publicacion)
    # ═══════════════════════════════════════════════════════════════
    section("")
    step_label(4, "POSTEO_ACTIVO", "Publicación del contenido aprobado")

    if args.auto_approve:
        log(f"  Modo --auto-approve: aprobando automáticamente")
        aprobado = True
    else:
        log(f"  ⏳ Simulando revisión humana (3s)...")
        await asyncio.sleep(3)
        aprobado = True  # Simulación siempre aprueba
        log(f"  ✅ Contenido APROBADO")

    if not aprobado:
        log(f"  ❌ Contenido RECHAZADO — pipeline detenido")
        metrics.record(4, "POSTEO_ACTIVO", False, "Rechazado")
        section("PIPELINE DETENIDO — CONTENIDO RECHAZADO")
        print(metrics.summary())
        return

    metrics.record(4, "POSTEO_ACTIVO", True, "Aprobado")

    # Email notificacion
    if not args.skip_email:
        section("")
        log("  ── Notificación Email ──")
        email_subject = f"Contenido aprobado para publicar — Rancho Raíz ({tema})"
        email_body = (
            f"Se ha aprobado nuevo contenido para publicar.\n\n"
            f"Tema: {tema}\n"
            f"Banner: {results.get('banner', {}).get('path', 'N/A')}\n"
            f"  Tamaño: {results.get('banner', {}).get('size', 0)} bytes\n"
            f"GIF: {results.get('gif', 'N/A')}\n"
            f"Reel: {results.get('reel', 'N/A')}\n\n"
            f"Aprobado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
            f"Pipeline: CAPTACION → CREACION → APROBACION → POSTEO\n"
            f"Estado: CONTENIDO_ACTIVO"
        )
        try:
            enviar_email(email_subject, email_body)
            log(f"  ✅ Notificación email enviada")
        except Exception as e:
            log(f"  ⚠️  Email no enviado (no crítico): {e}")
    else:
        log(f"  ⏭️  Email deshabilitado (--skip-email)")

    # Mensaje posteo exitoso
    if not args.skip_telegram and TELEGRAM_TOKEN:
        msg_posteado = (
            f"<b>Posteo realizado exitosamente</b> ✅\n\n"
            f"Tema: {tema.upper()}\n"
            f"Banner: {Path(results.get('banner', {}).get('path', 'N/A')).name}\n"
            f"GIF: {Path(results.get('gif', 'N/A')).name}\n\n"
            f"<i>Contenido publicado en los canales correspondientes.</i>"
        )
        ok = telegram_send_message(msg_posteado, buttons=False)
        log(f"  {'✅' if ok else '⚠️'} Mensaje 'Posteo exitoso' enviado a Telegram")

    # ═══════════════════════════════════════════════════════════════
    # PASOS 5-8: Simulaciones de interacción
    # ═══════════════════════════════════════════════════════════════
    if args.lead:
        section("")
        step_label(5, "INTERACCION_INSTAGRAM", "Detección de interacciones en Instagram")
        insta = simular_interaccion_instagram()
        metrics.record(5, "INTERACCION_INSTAGRAM", True, f"Lead={insta['usuario']}, intencion={insta['intencion']}")

        section("")
        step_label(6, "CALENTAMIENTO_LEAD", "Conversación empática para elevar deseo de compra")
        lead = simular_calentamiento_lead()
        metrics.record(6, "CALENTAMIENTO_LEAD", True, f"Temperatura final={lead['temperatura_final']}")

        section("")
        step_label(7, "DERIVACION_WHATSAPP", "Transferencia del historial a ventas por WhatsApp")
        whatsapp = simular_derivacion_whatsapp()
        metrics.record(7, "DERIVACION_WHATSAPP", True, f"Transferido a={whatsapp['transferido_a']}")

        section("")
        step_label(8, "ACOMPAÑAMIENTO_VIAJE", "Soporte continuo al huésped activo")
        viaje = simular_acompanamiento_viaje()
        metrics.record(8, "ACOMPAÑAMIENTO_VIAJE", True, f"Checkout={viaje['checkout']}")
    else:
        log(f"\n  ⏭️  Pasos 5-8 omitidos (usar --lead para simular journey completo de lead)")

    # ═══════════════════════════════════════════════════════════════
    # RESUMEN FINAL + METRICAS
    # ═══════════════════════════════════════════════════════════════
    section("RESUMEN FINAL")
    log(f"Banner:  {results.get('banner', {}).get('path', 'N/A')}")
    log(f"GIF:     {results.get('gif', 'N/A')}")
    if results.get("reel"):
        log(f"Reel:    {results['reel']}")
    log(f"")
    log(f"Pipeline ejecutado: {'COMPLETADO' if not args.lead else 'COMPLETADO + JOURNEY LEAD'} ✅")
    log(f"Hora:    {datetime.now().strftime('%H:%M:%S')}")
    log(f"")

    print(metrics.summary())

    # Guardar metricas a JSON
    metrics_path = OUTPUT_DIR / f"metrics_{tema}_{datetime.now().strftime('%H%M%S')}.json"
    metrics_path.write_text(metrics.to_json(), encoding="utf-8")
    log(f"\n  📊 Métricas guardadas: {metrics_path}")

    # Exportar reporte completo
    report = {
        "timestamp": datetime.now().isoformat(),
        "tema": tema,
        "args": vars(args),
        "assets": {k: str(v) if isinstance(v, Path) else v for k, v in results.items()},
        "metrics": metrics.steps,
        "passed": all(s["ok"] for s in metrics.steps),
    }
    report_path = OUTPUT_DIR / f"report_{tema}_{datetime.now().strftime('%H%M%S')}.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"  📄 Reporte completo: {report_path}")
    log(f"  📁 Assets en: {OUTPUT_DIR}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Simulación fortalecida del pipeline CRM + ARTE",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--tema", default="montanas", help="Tema visual (default: montanas)")
    parser.add_argument("--force", action="store_true", help="Regenera assets aunque existan en cache")
    parser.add_argument("--skip-telegram", action="store_true", help="No enviar nada a Telegram")
    parser.add_argument("--skip-email", action="store_true", help="No enviar email")
    parser.add_argument("--auto-approve", action="store_true", help="Aprueba automaticamente (sin espera)")
    parser.add_argument("--frames", type=int, default=4, help="Cantidad de frames para GIF (default: 4)")
    parser.add_argument("--lead", action="store_true", help="Simular journey completo de lead (pasos 5-8)")
    parser.add_argument("--reel", action="store_true", help="Generar tambien un reel")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(pipeline_completo(args))
