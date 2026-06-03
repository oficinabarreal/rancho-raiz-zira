#!/usr/bin/env python3
"""Componer transparencias Zira sobre fondo oscuro + audio naturaleza para Instagram REELS."""
import os, sys, json, random, time, requests
from pathlib import Path
from cairosvg import svg2png

sys.path.insert(0, "/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3")
from dotenv import load_dotenv
load_dotenv("/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3/.env")

TOKEN = os.environ["CRM_INSTAGRAM_TOKEN"]
USER_ID = os.environ["CRM_INSTAGRAM_USER_ID"]
BASE_DIR = Path("/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3")

# Mapeo estilo -> sonido naturaleza
NAT_MAP = {
    "juguetona": "olas.mp3",
    "zen": "rio_grillos.mp3",
    "magica": "rio_ambiente.mp3",
    "viva": "pajaros_bosque.mp3",
    "clasica": "viento.mp3",
}

# Mapeo estilo -> emoji
EMOJI_MAP = {
    "juguetona": "💦",
    "zen": "🧘",
    "magica": "✨",
    "viva": "🌿",
    "clasica": "🏔️",
}

# Frase por estilo
FRASE_MAP = {
    "juguetona": "El agua me llama, el sol me despierta.",
    "zen": "En el silencio de los Andes encuentro mi centro.",
    "magica": "Cada atardecer es una promesa de un nuevo amanecer.",
    "viva": "Verde que te quiero verde. Los Andes me enseñaron a respirar.",
    "clasica": "Las montañas me criaron, el viento me peinó.",
}

# 1. Generar fondo PNG con estilo Zira
def generar_fondo(estilo, output_path):
    """Genera un fondo 1080x1080 con el estilo visual de Zira."""
    colores = {
        "juguetona": {"accent": "#f59e0b", "secondary": "#fbbf24"},
        "zen": {"accent": "#10b981", "secondary": "#34d399"},
        "magica": {"accent": "#8b5cf6", "secondary": "#a78bfa"},
        "viva": {"accent": "#10b981", "secondary": "#34d399"},
        "clasica": {"accent": "#3b82f6", "secondary": "#60a5fa"},
    }
    c = colores.get(estilo, colores["clasica"])
    
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1080">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="50%" stop-color="#1e293b"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </linearGradient>
    <linearGradient id="accent-line" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="rgba(16,185,129,0)"/>
      <stop offset="30%" stop-color="rgba(16,185,129,0.2)"/>
      <stop offset="70%" stop-color="rgba(16,185,129,0.2)"/>
      <stop offset="100%" stop-color="rgba(16,185,129,0)"/>
    </linearGradient>
    <filter id="star-glow"><feGaussianBlur stdDeviation="2"/></filter>
  </defs>
  <rect width="1080" height="1080" fill="url(#bg)"/>
  <g fill="#fff" opacity="0.12">
    <circle cx="120" cy="100" r="1.5"/><circle cx="300" cy="60" r="1"/>
    <circle cx="500" cy="130" r="1.5"/><circle cx="700" cy="50" r="1"/>
    <circle cx="900" cy="90" r="1.5"/><circle cx="1000" cy="200" r="1"/>
    <circle cx="150" cy="250" r="1"/><circle cx="850" cy="180" r="1.5"/>
    <circle cx="400" cy="200" r="1"/><circle cx="650" cy="160" r="1"/>
  </g>
  <g fill="#1e293b" opacity="0.3">
    <polygon points="0,1080 160,700 320,850 480,650 640,780 800,620 960,730 1080,680 1080,1080"/>
    <polygon points="0,1080 200,800 400,880 600,720 800,850 1000,750 1080,800 1080,1080" opacity="0.5"/>
  </g>
  <rect width="1080" height="2" fill="url(#accent-line)" y="0"/>
  <text x="540" y="1010" font-family="system-ui, sans-serif" font-size="14" fill="#64748b" text-anchor="middle" letter-spacing="2">RANCHO RAÍZ · BARREAL</text>
</svg>"""
    svg2png(bytestring=svg.encode(), write_to=str(output_path), output_width=1080, output_height=1080)
    return output_path

# 2. Componer video con ffmpeg
def componer_video(estilo, fondo_png, tp_video, output_mp4, nat_audio):
    """Compone Zira transparente sobre fondo + audio naturaleza."""
    cmd = (
        f'ffmpeg -y -loop 1 -i "{fondo_png}" '
        f'-i "{tp_video}" '
        f'-i "{nat_audio}" '
        f'-filter_complex '
        f'"[1:v]scale=700:700,format=rgba,colorkey=0x000000:0.01:0.1,format=rgba[zira];'
        f'[0:v][zira]overlay=(W-w)/2:(H-h)/2-30[vout]" '
        f'-map "[vout]" -map 2:a '
        f'-c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 128k '
        f'-t 5 -shortest -movflags +faststart "{output_mp4}"'
    )
    print(f"     ffmpeg compositing...")
    result = os.system(cmd)
    return result == 0

# 3. Postear a Instagram como REEL
def post_reel(video_path, estilo):
    """Postea un video como REEL en Instagram."""
    # Subir a GitHub primero (raw URL)
    # ... para simplificar, usamos el path local... 
    # No, Instagram requiere URL pública. 
    # Necesito pushear el video a GitHub.
    pass

OUT_DIR = BASE_DIR / "assets" / "zira" / "completos"
NAT_DIR = BASE_DIR / "pipeline" / "audio" / "naturaleza"
TP_DIR = BASE_DIR / "assets" / "zira"
FONDO_DIR = BASE_DIR / "pipeline" / "zira-frases" / "fondos"
FONDO_DIR.mkdir(exist_ok=True)

estilos = ["juguetona", "zen", "magica", "viva", "clasica"]

print("🎬 Componiendo Ziras transparentes para Instagram...\n")

videos_generados = []
for estilo in estilos:
    tp_file = TP_DIR / f"zira-tp-{estilo}.mp4"
    nat_file = NAT_DIR / NAT_MAP[estilo]
    fondo_file = FONDO_DIR / f"fondo-{estilo}.png"
    output_file = OUT_DIR / f"zira_{estilo}_reel.mp4"
    
    if not tp_file.exists():
        print(f"  ⏭️  {estilo}: no existe {tp_file.name}")
        continue
    if not nat_file.exists():
        print(f"  ⏭️  {estilo}: no existe {nat_file.name}")
        continue
    
    print(f"  🎨 {estilo.upper()} — {EMOJI_MAP[estilo]} \"{FRASE_MAP[estilo][:40]}...\"")
    print(f"     Fondo: generando...")
    generar_fondo(estilo, fondo_file)
    print(f"     Componiendo con {NAT_MAP[estilo]}...")
    
    if componer_video(estilo, fondo_file, tp_file, output_file, nat_file):
        size = output_file.stat().st_size / 1024
        print(f"     ✅ {output_file.name} ({size:.0f} KB)")
        videos_generados.append({"estilo": estilo, "archivo": output_file.name, "path": str(output_file)})
    else:
        print(f"     ❌ Falló composición")

print(f"\n🏁 {len(videos_generados)} videos compuestos en {OUT_DIR}/")

# Guardar manifest
manifest_path = OUT_DIR / "reels_manifest.json"
with open(manifest_path, "w") as f:
    json.dump(videos_generados, f, indent=2, ensure_ascii=False)
print(f"📋 Manifest: {manifest_path}")
