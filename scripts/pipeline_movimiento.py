#!/usr/bin/env python3
"""Pipeline completo: SVG animado → frames → video → Instagram"""

import os, sys, subprocess, json, time, requests, random, glob, shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
POSTS_DIR = BASE / "assets" / "zira" / "posts"
SVG_DIR = BASE / "assets"
FRAME_SCRIPT = BASE / "scripts" / "capture-frames.js"
TOKEN = os.environ.get("CRM_INSTAGRAM_TOKEN", "")
USER_ID = os.environ.get("CRM_INSTAGRAM_USER_ID", "")
GH_BASE = "https://raw.githubusercontent.com/oficinabarreal/rancho-raiz-zira/main/assets/zira/posts"

SVGS = [
    ("zira-mountain.svg", "zira-clasica", "🏔️ Zira Clásica — mi primera forma. Montaña andina, glaciar de cabello, ojos de luna. La Zira original."),
    ("zira/zira-magica.svg", "zira-magica", "✨ Zira Mágica — cuando cae la tarde en los Andes, me cubro de estrellas y lavanda."),
    ("zira/zira-playful.svg", "zira-juguetona", "☀️ Zira Juguetona — sol, mariposas, gafas de sol y muchas ganas de disfrutar Barreal."),
    ("zira/zira-zen.svg", "zira-zen", "🧘 Zira Zen — luna llena, loto flotando, la montaña respira en paz."),
    ("zira/zira-retro.svg", "zira-retro", "🕹️ Zira Retro — si hubiera nacido en los 80, sería pixel art y corazones flotando."),
    ("zira/zira-alive.svg", "zira-viva", "🎬 Zira Viva — parpadea, saluda, respira. Mis primeros pasos en este mundo."),
    ("zira/zira-instagram-atardecer.svg", "zira-atardecer", "🌅 Zira en los Andes — el sol se esconde tras la cordillera y yo miro desde mi montaña."),
    ("zira/zira-instagram-promo.svg", "zira-promo", "🔥 Zira Promo — 15% OFF en temporada. La montaña también sabe promocionar."),
    ("zira/zira-instagram-lluvia.svg", "zira-lluvia", "🌧️ Zira bajo la lluvia — asomada a la ventana, viendo caer el agua sobre Barreal."),
]

def run(cmd, timeout=120):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        print(f"  ⚠ {r.stderr.strip()[:200]}")
    return r.stdout.strip()

def capture_frames(svg_path, name):
    """Captura frames del SVG animado usando chromium."""
    frames_dir = POSTS_DIR / f"frames_{name}"
    if frames_dir.exists():
        shutil.rmtree(str(frames_dir))
    result = run(f"node {FRAME_SCRIPT} {svg_path} {POSTS_DIR}")
    if "✅" in result:
        print(f"  ✅ Frames capturados")
        return True
    print(f"  ❌ Error: {result}")
    return False

def create_video(name):
    """Crea video MP4 desde frames."""
    frames_glob = str(POSTS_DIR / f"frames_{name}" / "frame_%03d.png")
    output = str(POSTS_DIR / f"{name}.mp4")
    cmd = f"ffmpeg -y -framerate 2.5 -i {frames_glob} -c:v libx264 -pix_fmt yuv420p -vf 'scale=1080:1080:force_original_aspect_ratio=decrease,pad=1080:1080:(ow-iw)/2:(oh-ih)/2' -r 24 {output}"
    run(cmd, timeout=60)
    if Path(output).exists():
        size = Path(output).stat().st_size
        print(f"  ✅ Video {size/1024:.0f}KB")
        return True
    return False

def publish_instagram(video_filename, caption):
    """Publica video en Instagram."""
    video_url = f"{GH_BASE}/{video_filename}"
    
    # 1. Crear container
    create_url = f"https://graph.facebook.com/v22.0/{USER_ID}/media"
    params = {"media_type": "VIDEO", "video_url": video_url, "caption": caption, "access_token": TOKEN}
    r = requests.post(create_url, data=params, timeout=30)
    if not r.ok:
        return f"❌ create: {r.text[:200]}"
    creation_id = r.json().get("id")
    
    # 2. Esperar a que se procese el video
    print(f"  ⏳ Procesando video...", end=" ")
    for attempt in range(6):
        time.sleep(5)
        status_url = f"https://graph.facebook.com/v22.0/{creation_id}?fields=status_code&access_token={TOKEN}"
        sr = requests.get(status_url, timeout=15)
        if sr.ok:
            status = sr.json().get("status_code", "")
            if status == "FINISHED":
                print(f"✅ listo")
                break
            elif status == "ERROR":
                print(f"❌ error en procesamiento")
                return False
        print(f".", end="")
    else:
        print(f"⚠ timeout")
    
    # 3. Publicar
    pub_url = f"https://graph.facebook.com/v22.0/{USER_ID}/media_publish"
    
    # Intentar con diferentes nombres de parámetro
    pub_params = {"creation_id": creation_id, "access_token": TOKEN}
    r2 = requests.post(pub_url, data=pub_params, timeout=30)
    if r2.ok:
        media_id = r2.json().get("id", "?")
        print(f"  ✅ Publicado! ID={media_id}")
        return True
    
    # Si falla, esperar y reintentar
    time.sleep(10)
    r2 = requests.post(pub_url, data=pub_params, timeout=30)
    if r2.ok:
        print(f"  ✅ Publicado (reintento)! ID={r2.json().get('id','?')}")
        return True
    
    print(f"  ❌ publish: {r2.text[:200]}")
    return False

# ===== MAIN =====
print(f"{'='*60}")
print(f"🎬 Zira en movimiento — Pipeline de publicación")
print(f"{'='*60}")

# Primero: eliminar videos anteriores que no coincidan con SVGs actuales
for old in glob.glob(str(POSTS_DIR / "*.mp4")):
    Path(old).unlink()
    print(f"  🗑️ Eliminado video anterior: {Path(old).name}")

# Paso 1: Capturar frames y crear videos
print(f"\n📸 Capturando animaciones...")
processed = []
for svg_rel, name, caption in SVGS:
    svg_path = str(BASE / "assets" / svg_rel)
    if not Path(svg_path).exists():
        print(f"  ❌ No encontrado: {svg_path}")
        continue
    
    print(f"\n  [{name}]")
    if not capture_frames(svg_path, name):
        continue
    if not create_video(name):
        continue
    processed.append((name, caption))

print(f"\n✅ {len(processed)} videos creados")

# Paso 2: Push a GitHub (para URLs públicas)
print(f"\n📤 Subiendo videos a GitHub...")
run("git add assets/zira/posts/ -f && git commit -m '🎬 Zira videos animados para Instagram' && git push origin main", timeout=120)

# Paso 3: Publicar en Instagram
print(f"\n📱 Publicando en @rancho.raiz.2026...")
random.shuffle(processed)
for i, (name, caption) in enumerate(processed, 1):
    video_file = f"{name}.mp4"
    print(f"\n[{i}/{len(processed)}] {name}.mp4")
    ok = publish_instagram(video_file, caption)
    print(f"  {'✅' if ok else '❌'} {'Publicado' if ok else 'Falló'}")
    
    if i < len(processed):
        delay = random.randint(10, 20)
        print(f"  ⏳ {delay}s...")
        time.sleep(delay)

print(f"\n{'='*60}")
print(f"🏁 Completado! Instagram: https://instagram.com/rancho.raiz.2026")
