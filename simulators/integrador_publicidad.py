#!/usr/bin/env python3
"""
integrador_publicidad.py — Simulación integración publicidad → CRM

Flujo completo:
  1. Elegir reel (existente o generar nuevo)
  2. Enviar video a Telegram para aprobación
  3. Si aprobado → email a oficinabarreal@gmail.com + simular posteo IG
  4. Mensaje "Posteo realizado" vía Telegram

Modos:
  --reels             Listar reels ya creados en ~/ranchoraiz_reels/
  --usar-reel=FILE    Usar un reel existente (sin generar)
  --auto              Generar reel automáticamente (elige tema + params)
  --tema=NOMBRE       Tema específico (pileta, noche, atardecer, montanas, logo)
  --manual=F1,F2,...  Fotos específicas por número
  --listar            Listar temas, fotos y opciones disponibles
  --batch=N           Generar N reels sin aprobación
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import subprocess
import sys
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── Rutas ───────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
ASSETS_DIR = SCRIPT_DIR / "integracion_publicidad"
DB_PATH = ASSETS_DIR / "db.json"
FOTOS_DIR = ASSETS_DIR / "fotos"
AUDIO_DIR = ASSETS_DIR / "audio"
LOGS_DIR = ASSETS_DIR / "logs"
PUBLICIDAD_DIR = Path("/data/data/com.termux/files/home/publicidad")
LAB_JS = PUBLICIDAD_DIR / "ranchocut" / "lab.js"
REELS_DIR = Path.home() / "ranchoraiz_reels"
EMAIL_TO = ["oficinabarreal@gmail.com"]  # Temporal: solo pruebas. Agregar ltelloraiz, Ramonleandrotello cuando indique

# ── Tablas de contenido ─────────────────────────────────────────────
TEMA_FOTOS: Dict[str, List[int]] = {
    "pileta":    [6, 7, 8, 9, 10, 11, 19, 20, 21, 22],
    "noche":     [1, 2, 6, 7],
    "atardecer": [3, 5, 11, 22],
    "montanas":  [2, 3, 4, 5, 8, 9, 13, 17, 19, 20],
    "logo":      [16, 17, 18],
}

TEMA_AUDIO: Dict[str, str] = {
    "pileta":    "RiverMeditation.mp3",
    "noche":     "PaperWings.mp3",
    "atardecer": "AutumnSunset.mp3",
    "montanas":  "GreenLeaves.mp3",
    "logo":      "AcousticGuitar1.mp3",
}

TEMA_TEXTO: Dict[str, str] = {
    "pileta":    "REFRESCA TUS SENTIDOS",
    "noche":     "BAJO LAS ESTRELLAS",
    "atardecer": "ATARDECER DORADO",
    "montanas":  "VISTAS QUE ENAMORAN",
    "logo":      "RANCHO RAÍZ",
}

KENBURNS_TIPOS = [
    "center", "top_left", "top_right", "bottom_left", "bottom_right",
    "top", "bottom", "pan_left_to_right", "pan_right_to_left",
    "pan_top_to_bottom", "pan_bottom_to_top", "zoom_out",
]

ESTILOS = ["fade", "slide_up", "slide_left", "pulse"]


# ── Carga de assets ──────────────────────────────────────────────────

def cargar_db() -> List[Dict[str, Any]]:
    if not DB_PATH.exists():
        print(f"  ✗ db.json no encontrado en {DB_PATH}")
        return []
    data = json.loads(DB_PATH.read_text(encoding="utf-8"))
    index = data.get("fotos", {}).get("_index", [])
    return index if isinstance(index, list) else []


def buscar_foto(numero: int, db: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    prefijo = f"{numero:02d}_"
    for f in db:
        if f.get("numero_original") == numero:
            return f
        nid = f.get("id", "")
        if nid.startswith(prefijo):
            return f
    return None


def listar_temas(db: List[Dict[str, Any]]):
    print("\n📋 Temas disponibles:\n")
    for tema, fotos in TEMA_FOTOS.items():
        fotos_info = []
        for n in fotos:
            f = buscar_foto(n, db)
            if f:
                desc = (f.get("descripcion") or f.get("tags", ""))[:50]
                fotos_info.append(f"#{n}: {desc}")
        print(f"  🏷️  {tema.upper()} ({len(fotos)} fotos)")
        for info in fotos_info:
            print(f"       {info}")
        print(f"     Audio: {TEMA_AUDIO.get(tema, '—')}")
        print(f"     Texto: {TEMA_TEXTO.get(tema, '—')}")
        print()

    print("  Ken Burns disponibles:")
    for k in KENBURNS_TIPOS:
        print(f"     • {k}")
    print()
    print("  Estilos de texto:")
    for e in ESTILOS:
        print(f"     • {e}")
    print()


# ── Reels existentes ─────────────────────────────────────────────────

def listar_reels() -> List[Dict[str, Any]]:
    if not REELS_DIR.exists():
        print(f"  ✗ Directorio de reels no encontrado: {REELS_DIR}")
        return []

    reels = []
    for f in sorted(REELS_DIR.glob("*.mp4"), key=os.path.getmtime, reverse=True):
        name = f.name
        size = f.stat().st_size
        size_str = f"{size / 1024:.0f} KB" if size < 1024 * 1024 else f"{size / (1024 * 1024):.1f} MB"
        # Inferir tema del nombre
        tema_inferido = "—"
        for t in TEMA_FOTOS:
            if t in name.lower():
                tema_inferido = t
                break
        reels.append({
            "nombre": name,
            "path": str(f),
            "tamano": size_str,
            "tema": tema_inferido,
        })

    return reels


def mostrar_reels(reels: List[Dict[str, Any]]):
    print(f"\n📁 Reels existentes en {REELS_DIR}:\n")
    for i, r in enumerate(reels, 1):
        print(f"  {i:2d}. {r['nombre']}")
        print(f"      📦 {r['tamano']}  |  🏷️  {r['tema']}")
    print()
    print(f"  Total: {len(reels)} reels")
    print()


def elegir_reel_interactivo(reels: List[Dict[str, Any]]) -> Optional[str]:
    mostrar_reels(reels)
    try:
        idx = input(f"  Elegí un reel (1-{len(reels)}, Enter = el primero, 0 = cancelar): ").strip()
    except (KeyboardInterrupt, EOFError):
        print()
        return None
    if not idx:
        return reels[0]["path"] if reels else None
    try:
        n = int(idx)
        if 1 <= n <= len(reels):
            return reels[n - 1]["path"]
    except ValueError:
        pass
    return None


# ── Telegram (API directa, sin conflicto con bot polling) ────────────

CHAT_ID_PUBLICIDAD = "8272684219"


def _cargar_env():
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"\''))


def _chat_id() -> str:
    return os.environ.get("CRM_TG_CHAT_ID", CHAT_ID_PUBLICIDAD)


def _telegram_api(method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    token = os.environ.get("CRM_TG_TOKEN", "")
    url = f"https://api.telegram.org/bot{token}/{method}"
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def enviar_video_telegram(
    video_path: str,
    caption: str = "",
    reply_markup: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    path = Path(video_path)
    if not path.exists():
        return {"ok": False, "error": f"video no encontrado: {video_path}"}

    token = os.environ.get("CRM_TG_TOKEN", "")
    chat_id = _chat_id()
    url = f"https://api.telegram.org/bot{token}/sendVideo"
    boundary = f"----Integrador{uuid.uuid4().hex}"

    fields: List[Tuple[str, str, Optional[str]]] = [
        ("chat_id", chat_id, None),
        ("supports_streaming", "true", None),
    ]
    if caption:
        fields.append(("caption", caption, None))
    if reply_markup is not None:
        fields.append(("reply_markup", json.dumps(reply_markup, ensure_ascii=False), None))

    content_type = mimetypes.guess_type(path.name)[0] or "video/mp4"

    body = bytearray()
    for key, value, _ in fields:
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"))
        body.extend(str(value).encode("utf-8"))
        body.extend(b"\r\n")
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(f'Content-Disposition: form-data; name="video"; filename="{path.name}"\r\n'.encode("utf-8"))
    body.extend(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
    body.extend(path.read_bytes())
    body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode("utf-8"))

    req = urllib.request.Request(
        url,
        data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return payload


def enviar_mensaje_telegram(text: str, reply_markup: Optional[Dict] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "chat_id": _chat_id(),
        "text": text,
        "parse_mode": "HTML",
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return _telegram_api("sendMessage", payload)


# ── Email por Gmail ──────────────────────────────────────────────────

def enviar_email_notificacion(
    video_name: str,
    caption: str,
    tamano: str,
    tema: str,
) -> Dict[str, Any]:
    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        from crm.connectors import GmailConnector
        gmail = GmailConnector()
    except Exception as e:
        print(f"  ⚠️  No se pudo inicializar GmailConnector: {e}")
        return {"ok": False, "error": str(e)}

    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    subject = f"🎬 Nuevo reel aprobado para publicar — {video_name}"
    body = f"""
Hola,

Se ha aprobado un nuevo reel para publicar en Instagram.

📹 Video: {video_name}
📦 Tamaño: {tamano}
🏷️  Tema: {tema}
📝 Caption: {caption}
🕐 Aprobado el: {fecha}

---

Este es un mensaje automático del simulador de integración.
Próximamente: publicación real en Instagram.

--
Zira 🤖
Rancho Raíz — CRM Autónomo
*(Zira = anagrama de Raíz)*
"""
    print("  📧 Enviando email de notificación...")
    ok = True
    results = []
    for to in EMAIL_TO:
        try:
            result = gmail.send_message(to, subject, body.strip())
            if result.ok:
                print(f"  ✅ Email enviado a {to}")
                results.append({"to": to, "ok": True, "data": result.data})
            else:
                print(f"  ⚠️  Error al enviar email a {to}: {result.error}")
                results.append({"to": to, "ok": False, "error": result.error})
                ok = False
        except Exception as e:
            print(f"  ⚠️  Error al enviar email a {to}: {e}")
            results.append({"to": to, "ok": False, "error": str(e)})
            ok = False
    return {"ok": ok, "results": results}


# ── Simulación de publicación Instagram ──────────────────────────────

def simular_publicacion_instagram(
    video_path: str,
    caption: str,
    tema: str = "",
    video_name: str = "",
    tamano: str = "",
) -> Dict[str, Any]:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    resultado = {
        "timestamp": timestamp,
        "accion": "PUBLICACION_SIMULADA",
        "plataforma": "Instagram",
        "tipo": "Reel",
        "video": video_name or Path(video_path).name,
        "caption": caption,
        "tema": tema,
        "tamano": tamano or _tamano(video_path),
        "status": "publicado_simulado",
    }

    log_file = LOGS_DIR / "publicaciones.json"
    historial = []
    if log_file.exists():
        historial = json.loads(log_file.read_text(encoding="utf-8"))
    historial.append(resultado)
    log_file.write_text(json.dumps(historial, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print()
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║  📱  PUBLICACIÓN SIMULADA EN INSTAGRAM      ║")
    print("  ╠══════════════════════════════════════════════╣")
    print(f"  ║  Hora:    {timestamp}")
    print(f"  ║  Video:   {resultado['video']}")
    print(f"  ║  Tamaño:  {resultado['tamano']}")
    print(f"  ║  Caption: {caption[:60]}")
    print(f"  ║  Tema:    {tema or '—'}")
    print("  ╚══════════════════════════════════════════════╝")
    print()
    print(f"  📝 Log guardado en: {log_file}")
    print()

    notificar_posteado(video_name or Path(video_path).name, caption)

    return resultado


def notificar_posteado(video_name: str, caption: str):
    msg = (
        f"📱 <b>Posteo realizado en Instagram</b> ✅\n\n"
        f"🎬 {video_name}\n"
        f"🏷️  {caption}\n\n"
        f"⏳ Próximo paso: implementar publicación real vía Instagram Graph API"
    )
    try:
        resp = enviar_mensaje_telegram(msg)
        if resp.get("ok"):
            print("  ✅ Mensaje 'Posteo realizado' enviado a Telegram")
        else:
            print("  ⚠️  No se pudo enviar mensaje a Telegram")
    except Exception:
        print("  ⚠️  No se pudo enviar mensaje a Telegram")


# ── Generación de reel ───────────────────────────────────────────────

def generar_reel(
    fotos: List[int],
    kenburns: str = "pan_left_to_right",
    estilo: str = "slide_up",
    audio: str = "",
    duracion: int = 4,
) -> Optional[str]:
    if not LAB_JS.exists():
        print(f"  ✗ lab.js no encontrado en {LAB_JS}")
        return None

    output_dir = ASSETS_DIR / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / f"reel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")

    cmd = [
        "node", str(LAB_JS),
        f"--manual={','.join(str(f) for f in fotos)}",
        f"--kenburns={kenburns}",
        f"--estilo={estilo}",
        "--overlay=cinematic",
        f"--duracion={duracion}",
        f"--output={output_path}",
    ]
    if audio:
        audio_path = AUDIO_DIR / audio
        if audio_path.exists():
            cmd.append(f"--audio={audio}")

    print(f"  🔧 Generando reel...")
    print(f"     Fotos: {fotos}  |  Ken Burns: {kenburns}  |  Estilo: {estilo}  |  Audio: {audio or 'sin audio'}")
    print()

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300,
            env={**os.environ, "NODE_PATH": str(PUBLICIDAD_DIR / "ranchocut" / "node_modules")},
        )
    except subprocess.TimeoutExpired:
        print("  ✗ Timeout: la generación tomó más de 5 minutos")
        return None
    except FileNotFoundError:
        print("  ✗ node no encontrado")
        return None

    log_path = output_dir / f"generacion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_path.write_text(f"CMD: {' '.join(cmd)}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}")

    if result.returncode != 0:
        print(f"  ✗ Error FFmpeg (código {result.returncode})")
        print(f"     {result.stderr[-300:]}")
        return None

    if Path(output_path).exists():
        print(f"  ✅ Reel generado: {output_path}")
        return output_path

    lab_output_dir = Path.home() / "downloads" / "rancho-raiz-publicidad" / "_WORKING_CYCLE"
    if lab_output_dir.exists():
        archivos = sorted(lab_output_dir.glob("*.mp4"), key=os.path.getmtime, reverse=True)
        if archivos:
            print(f"  ✅ Reel generado: {archivos[0].name}")
            return str(archivos[0])

    print(f"  ✗ No se encontró el archivo de salida")
    return None


def _tamano(path: str) -> str:
    size = Path(path).stat().st_size
    if size < 1024 * 1024:
        return f"{size / 1024:.0f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


# ── Flujo de aprobación ──────────────────────────────────────────────

def flujo_aprobacion(
    video_path: str,
    tema: str,
    video_name: str,
) -> Any:
    caption = (
        f"🎬 <b>Reel: {video_name}</b>\n"
        f"🏷️  {tema.upper() if tema else 'Sin tema'}\n"
        f"📦 {_tamano(video_path)}\n\n"
        f"🤔 <b>¿Aprobás este reel para publicar en Instagram?</b>"
    )

    approve_kb = {
        "inline_keyboard": [
            [
                {"text": "✅ Aprobar", "callback_data": "aprobar"},
                {"text": "❌ Rechazar", "callback_data": "rechazar"},
            ]
        ]
    }

    print("  📤 Enviando video a Telegram...")
    try:
        tg_resp = enviar_video_telegram(video_path, caption=caption, reply_markup=approve_kb)
        tg_ok = tg_resp.get("ok", False)
    except Exception as e:
        print(f"  ⚠️  No se pudo enviar a Telegram: {e}")
        tg_ok = False

    if not tg_ok:
        print("  ↪️  Usando aprobación por terminal")
        return _aprobacion_terminal(tema, video_name)

    print("  ✅ Video enviado a Telegram. Esperando decisión...")
    print()
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║  Responde en la terminal:                   ║")
    print("  ╠══════════════════════════════════════════════╣")
    print("  ║  [a] Aprobar  → email + simular posteo IG  ║")
    print("  ║  [r] Rechazar → descartar este reel        ║")
    print("  ║  [s] Saltar   → seguir sin publicar        ║")
    print("  ╚══════════════════════════════════════════════╝")
    print()

    for intento in range(3):
        try:
            resp = input(f"  [{intento+1}/3] Decisión (a/r/s): ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\n  ⚠️  Operación cancelada")
            return False

        if resp in ("a", "aprobar"):
            return True
        elif resp in ("r", "rechazar"):
            print("  ❌ Reel rechazado. Descartado.")
            return False
        elif resp in ("s", "saltar"):
            print("  ⏭️  Saltado sin publicar")
            return False
        else:
            print("  Opción inválida. Usa: a=aprobar, r=rechazar, s=saltar")

    print("  ⚠️  Demasiados intentos. Reel descartado.")
    return False


def _aprobacion_terminal(tema: str, video_name: str) -> bool:
    print()
    print(f"  Aprobar reel '{video_name}' ({tema or 'sin tema'})?")
    resp = input("  [S/n]: ").strip().lower()
    return resp in ("", "s", "si", "y", "yes")


# ── Pipeline completo ────────────────────────────────────────────────

def pipeline_completo(video_path: str, tema: str, caption: str):
    video_name = Path(video_path).name
    tamano = _tamano(video_path)

    print(f"\n{'='*60}")
    print(f"  🎬 PIPELINE: PUBLICIDAD → CRM")
    print(f"  Video: {video_name}")
    print(f"  Tema:  {tema.upper() if tema else '—'}")
    print(f"{'='*60}\n")

    decision = flujo_aprobacion(video_path, tema, video_name)

    if decision is True:
        print("\n  ✅ Reel APROBADO. Ejecutando pipeline de publicación...\n")

        paso1 = enviar_email_notificacion(video_name, caption, tamano, tema)
        if paso1.get("ok"):
            print()

            paso2 = simular_publicacion_instagram(
                video_path, caption, tema=tema,
                video_name=video_name, tamano=tamano,
            )

            print(f"\n  {'='*50}")
            print(f"  🎉 Pipeline completado exitosamente!")
            print(f"  {'='*50}")
            print(f"    1. ✅ Video enviado a Telegram para aprobación")
            print(f"    2. ✅ Emails enviados a {len(EMAIL_TO)} destinatarios")
            print(f"    3. ✅ Publicación simulada en Instagram")
            print(f"    4. ✅ Notificación 'Posteo realizado' en Telegram")
            print(f"  {'='*50}")
            print()
        else:
            print("  ⚠️  Pipeline detenido: no se pudo enviar email")
            print("     Revisá que el token de Gmail sea válido\n")
    elif decision == "regenerar":
        print("\n  🔄 Regenerando...\n")
        return "regenerar"
    else:
        print("  ❌ Pipeline cancelado\n")


# ── CLI ──────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Integrador Publicidad → CRM — Simulación de pipeline completo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--reels", action="store_true", help="Listar reels existentes y elegir uno")
    parser.add_argument("--usar-reel", default="", help="Usar un reel existente (nombre en ~/ranchoraiz_reels/)")
    parser.add_argument("--auto", action="store_true", help="Generar reel automático")
    parser.add_argument("--tema", default="", help="Tema: pileta, noche, atardecer, montanas, logo")
    parser.add_argument("--manual", default="", help="Fotos manuales: 6,11,19,8")
    parser.add_argument("--kenburns", default="", help="Tipo Ken Burns")
    parser.add_argument("--estilo", default="", help="Estilo texto: fade, slide_up, slide_left, pulse")
    parser.add_argument("--audio", default="", help="Archivo de audio")
    parser.add_argument("--duracion", type=int, default=4, help="Duración por foto (segundos)")
    parser.add_argument("--listar", action="store_true", help="Listar temas, fotos y opciones")
    parser.add_argument("--batch", type=int, default=0, help="Generar N reels sin aprobación")
    parser.add_argument("--caption", default="", help="Caption para la publicación")
    return parser.parse_args()


def main():
    _cargar_env()

    if not os.environ.get("CRM_TG_TOKEN"):
        print("  ✗ CRM_TG_TOKEN no configurado en .env")
        sys.exit(1)

    db = cargar_db()
    args = parse_args()

    if args.listar:
        listar_temas(db)
        listar_reels()
        return

    # Mostrar reels disponibles y elegir
    if args.reels:
        reels = listar_reels()
        if not reels:
            return
        video = elegir_reel_interactivo(reels)
        if not video:
            print("  ✗ No se seleccionó ningún reel")
            return
        tema = Path(video).stem
        for t in TEMA_FOTOS:
            if t in tema.lower():
                tema = t
                break
        caption = args.caption or TEMA_TEXTO.get(tema, f"Rancho Raíz - {Path(video).name}")
        pipeline_completo(video, tema, caption)
        return

    # Usar reel específico por nombre
    if args.usar_reel:
        video_path = REELS_DIR / args.usar_reel
        if not video_path.exists():
            print(f"  ✗ Reel no encontrado: {video_path}")
            print(f"     Usá --reels para ver los disponibles")
            return
        tema = args.tema or ""
        if not tema:
            for t in TEMA_FOTOS:
                if t in args.usar_reel.lower():
                    tema = t
                    break
        caption = args.caption or TEMA_TEXTO.get(tema, f"Rancho Raíz - {args.usar_reel}")
        pipeline_completo(str(video_path), tema, caption)
        return

    # Batch mode
    if args.batch > 0:
        import random
        temas = list(TEMA_FOTOS.keys())
        for i in range(args.batch):
            tema = random.choice(temas)
            fotos = TEMA_FOTOS[tema]
            k = random.choice(KENBURNS_TIPOS)
            e = random.choice(ESTILOS)
            a = TEMA_AUDIO.get(tema, "")
            print(f"\n{'#'*60}")
            print(f"  #{i+1}/{args.batch} — Generando reel de {tema}")
            print(f"{'#'*60}")
            video = generar_reel(fotos, k, e, a, args.duracion)
            if video:
                cap = args.caption or TEMA_TEXTO.get(tema, f"{tema.upper()} - Rancho Raíz")
                simular_publicacion_instagram(video, cap, tema=tema)
        return

    # Generar nuevo reel
    tema = args.tema.lower() if args.tema else ""
    fotos: List[int] = []

    if args.manual:
        fotos = [int(f.strip()) for f in args.manual.split(",") if f.strip().isdigit()]
        tema = tema or "manual"
    elif tema in TEMA_FOTOS:
        fotos = TEMA_FOTOS[tema]
    elif args.auto or not tema:
        import random
        tema = random.choice(list(TEMA_FOTOS.keys()))
        fotos = TEMA_FOTOS[tema]
        print(f"  🎲 Selección automática: tema = {tema}")
    else:
        print(f"  ✗ Tema '{tema}' no válido")
        print(f"     Opciones: {', '.join(TEMA_FOTOS.keys())}")
        sys.exit(1)

    fotos_validas = [f for f in fotos if buscar_foto(f, db)]
    if not fotos_validas:
        print(f"  ✗ No se encontraron fotos válidas en la base de datos")
        sys.exit(1)

    kenburns = args.kenburns if args.kenburns in KENBURNS_TIPOS else "pan_left_to_right"
    estilo = args.estilo if args.estilo in ESTILOS else "slide_up"
    audio = args.audio or TEMA_AUDIO.get(tema, "")

    for intento in range(3):
        video = generar_reel(fotos_validas, kenburns, estilo, audio, args.duracion)
        if not video:
            break
        caption = args.caption or TEMA_TEXTO.get(tema, f"{tema.upper()} - Rancho Raíz")
        resultado = pipeline_completo(video, tema, caption)
        if resultado != "regenerar":
            break
        import random
        kenburns = random.choice(KENBURNS_TIPOS)
        estilo = random.choice(ESTILOS)
        print(f"  🔄 Reintento #{intento+1}: {kenburns} + {estilo}")


if __name__ == "__main__":
    main()
