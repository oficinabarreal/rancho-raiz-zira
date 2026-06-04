#!/usr/bin/env python3
"""
Pipeline unificado: fotos de Rancho Raíz + Zira animada + audio contextual.
Crea videos completos con Ken Burns, Zira overlay y música de fondo.
Zira cambia su estilo según el contexto (tags de foto + audio).
"""

import subprocess, os, sys, json, time, random, shutil
from pathlib import Path

# ─── Rutas ─────────────────────────────────────────────────────
PROJECT = Path(__file__).resolve().parent.parent.parent
FOTOS_DIR = PROJECT / "pipeline" / "fotos"
DB_PATH = PROJECT / "pipeline" / "db.json"
AUDIO_DIR = PROJECT / "pipeline" / "audio"
ZIRA_POSTS = PROJECT / "assets" / "zira" / "posts"
OUTPUT_DIR = PROJECT / "assets" / "zira" / "completos"
TEMP_DIR = PROJECT / "pipeline" / ".temp"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# ─── Mapeo: tags → Zira style → audio ─────────────────────────
TAG_MAP = [
    # (tags detectados, zira_style, audio_file, nombre_tema)
    (["pileta", "piscina", "agua"],     "juguetona", "RiverMeditation.mp3",   "Pileta"),
    (["noche", "luna", "estrellas"],     "zen",       "PaperWings.mp3",       "Noche"),
    (["atardecer"],                      "magica",    "AutumnSunset.mp3",     "Atardecer"),
    (["montaña", "montanas", "paisaje", "montana"], "clasica", "GreenLeaves.mp3", "Montañas"),
    (["naturaleza", "bosque", "árboles"],"viva",      "RedwoodTrail.mp3",     "Naturaleza"),
    (["logo", "marca", "ranchoraiz"],    "retro",     "AcousticGuitar1.mp3",  "Marca"),
    (["rústico", "rustico"],             "retro",     "AcousticGuitar1.mp3",  "Rústico"),
    (["fuego", "fogata"],                "magica",    "OneFineDay.mp3",       "Fogata"),
    (["relax"],                          "zen",       "RiverMeditation.mp3",  "Relax"),
]

# Fallback
DEFAULT_ZIRA = "clasica"
DEFAULT_AUDIO = "GreenLeaves.mp3"

# ─── Helper functions ──────────────────────────────────────────

def run(cmd, desc="", timeout=180):
    """Ejecuta comando y muestra resultado."""
    if desc:
        print(f"\n  🎬 {desc}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        err = result.stderr.strip()[:300]
        print(f"     ⚠️  {err}")
    return result.returncode == 0, result.stdout.strip(), result.stderr.strip()

def load_db():
    with open(DB_PATH) as f:
        return json.load(f)

def find_photos_by_tags(db, tag_list):
    """Encuentra fotos que coincidan con al menos un tag."""
    fotos = db["fotos"]["_index"]
    matched = []
    for f in fotos:
        ftags = [t.lower().strip() for t in f.get("tags", [])]
        if any(t in ftags for t in tag_list):
            # check if file exists
            fname = f["archivo"]
            fpath = FOTOS_DIR / fname
            if fpath.exists():
                matched.append(f)
    return matched

def resolve_style_and_audio(foto_tags):
    """Determina qué estilo de Zira y qué audio usar según tags de la foto."""
    ftags_lower = [t.lower().strip() for t in foto_tags]
    for match_tags, zira_style, audio_file, _ in TAG_MAP:
        if any(t in ftags_lower for t in match_tags):
            return zira_style, audio_file
    return DEFAULT_ZIRA, DEFAULT_AUDIO

def zira_mp4_path(style):
    """Ruta al MP4 de Zira para un estilo dado."""
    # Map style names to actual filenames
    style_map = {
        "clasica":  "zira-clasica.mp4",
        "magica":   "zira-magica.mp4",
        "juguetona":"zira-juguetona.mp4",
        "zen":      "zira-zen.mp4",
        "retro":    "zira-retro.mp4",
        "viva":     "zira-viva.mp4",
        "atardecer":"zira-atardecer.mp4",
        "promo":    "zira-promo.mp4",
        "lluvia":   "zira-lluvia.mp4",
    }
    fname = style_map.get(style, "zira-clasica.mp4")
    return ZIRA_POSTS / fname

def audio_path(name):
    p = AUDIO_DIR / name
    return p if p.exists() else None

def render_ken_burns_slideshow(photos, output_path, dur_per_foto=4, dur_trans=0.8):
    """
    Crea un slideshow Ken Burns a partir de fotos usando FFmpeg.
    Cada foto: zoom lento (1.0 → 1.08) con centro por defecto.
    Transiciones: fade entre fotos.
    """
    if not photos:
        print("     ❌ No hay fotos")
        return False

    slides = []
    for i, foto in enumerate(photos):
        fpath = FOTOS_DIR / foto["archivo"]
        if not fpath.exists():
            continue
        temp = TEMP_DIR / f"slide_{i:02d}.mp4"
        slides.append((temp, str(fpath)))
        
        # Ken Burns: zoompan lento
        # 1080x1920 portrait, zoom from 1.0 to 1.08
        cmd = (
            f'ffmpeg -y -loop 1 -i "{fpath}" '
            f'-vf "zoompan=z=\'min(zoom+0.0008,1.08)\':'
            f'x=\'(iw-iw/zoom)*0.5\':'
            f'y=\'(ih-ih/zoom)*0.5\':'
            f'd={dur_per_foto*30}:s=1080x1920:fps=30,'
            f'format=yuv420p" '
            f'-c:v libx264 -t {dur_per_foto} "{temp}" 2>/dev/null'
        )
        ok, _, _ = run(cmd, f"Ken Burns: {foto['archivo'][:40]}...")
        if not ok:
            print(f"     ⚠️  Falló slide {i}")

    # Filter out failed slides
    slides = [(t, p) for t, p in slides if t.exists()]
    if not slides:
        return False

    if len(slides) == 1:
        shutil.copy(slides[0][0], output_path)
        return True

    # Concatenate with xfade transitions
    # Build filter_complex
    filter_parts = []
    for i, (temp, _) in enumerate(slides):
        filter_parts.append(f"[{i}:v]")

    # On each adjacent pair, apply xfade
    # Simpler: use concat with fade transitions
    # Using xfade between consecutive clips
    # First, create segments with fades

    # Actually, let's use the simpler concat approach with fades between
    # Create a concat file list
    concat_file = TEMP_DIR / "concat_list.txt"
    with open(concat_file, "w") as f:
        for temp, _ in slides:
            f.write(f"file '{temp}'\n")

    cmd = (
        f'ffmpeg -y -f concat -safe 0 -i "{concat_file}" '
        f'-c:v libx264 -pix_fmt yuv420p "{output_path}" 2>/dev/null'
    )
    ok, _, _ = run(cmd, "Uniendo slides...")
    
    if output_path.exists():
        return True
    
    # If concat fails (different resolutions etc.), try a different approach
    # Just filter_complex xfade approach
    return False

def create_zira_overlay(zira_mp4, duration, output_overlay):
    """
    Prepara Zira para overlay: loopea para que dure lo mismo que el video base,
    escala a tamaño adecuado (25% del ancho) y centra verticalmente.
    """
    if not zira_mp4.exists():
        print(f"     ⚠️  Zira MP4 no encontrado: {zira_mp4}")
        return False

    # Scale Zira to 25% of 1080 = 270px width, keep aspect
    # Position: bottom-right corner
    overlay_w = 270
    cmd = (
        f'ffmpeg -y -stream_loop -1 -i "{zira_mp4}" '
        f'-vf "scale={overlay_w}:-2" '
        f'-c:v libx264 -t {duration} -pix_fmt yuv420p '
        f'"{output_overlay}" 2>/dev/null'
    )
    ok, _, _ = run(cmd, f"Preparando overlay Zira ({zira_mp4.name})...")
    return ok and output_overlay.exists()

def composite_videos(base_video, overlay_video, output_path):
    """
    Compone: base_video (fondo) + overlay_video (Zira en esquina).
    Zira posicionada en bottom-right con margen.
    """
    # Get overlay dimensions for positioning
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=width,height",
         "-of", "default=noprint_wrappers=1:nokey=1", str(overlay_video)],
        capture_output=True, text=True, timeout=10
    )
    dims = probe.stdout.strip().split("\n")
    ow, oh = 270, 270  # defaults
    if len(dims) >= 2:
        try:
            ow = int(dims[0])
            oh = int(dims[1])
        except:
            pass

    # Position: bottom-right, 40px margin
    pos_x = f"1080-{ow}-40"
    pos_y = f"1920-{oh}-40"

    cmd = (
        f'ffmpeg -y -i "{base_video}" -i "{overlay_video}" '
        f'-filter_complex '
        f'"[0:v][1:v]overlay={pos_x}:{pos_y}[v]" '
        f'-map "[v]" -map 0:a? -c:v libx264 -pix_fmt yuv420p -c:a copy '
        f'"{output_path}" 2>/dev/null'
    )
    ok, _, _ = run(cmd, "Componiendo Zira + fondo...")
    return ok and output_path.exists()

def add_audio(video_path, audio_path, output_path, vol=0.25):
    """Agrega audio de fondo al video."""
    if not audio_path or not audio_path.exists():
        print(f"     ⚠️  Audio no encontrado, saltando")
        return False
    
    cmd = (
        f'ffmpeg -y -i "{video_path}" -i "{audio_path}" '
        f'-filter_complex '
        f'"[1:a]volume={vol},aloop=loop=-1:size=2e9[a1];'
        f'[0:a][a1]amix=inputs=2:duration=first[aout]" '
        f'-map 0:v -map "[aout]" '
        f'-c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 128k '
        f'-shortest -movflags +faststart '
        f'"{output_path}" -y 2>/dev/null'
    )
    ok, _, _ = run(cmd, f"Agregando audio: {audio_path.name}")
    return ok and output_path.exists()

def build_theme_videos(db, output_dir):
    """Construye videos por cada tema/grupo de fotos."""
    results = []
    
    for match_tags, zira_style, audio_file, theme_name in TAG_MAP:
        print(f"\n{'='*60}")
        print(f"🎯 TEMA: {theme_name} (Zira: {zira_style}, Audio: {audio_file})")
        print(f"{'='*60}")

        # Find photos
        photos = find_photos_by_tags(db, match_tags)
        if not photos:
            print(f"   ⏭️  Sin fotos para este tema")
            continue

        # Limit to max 5 photos per theme to keep videos short
        fotos_usar = photos[:5]
        print(f"   📸 {len(photos)} fotos encontradas, usando {len(fotos_usar)}")

        # Verify Zira MP4 exists
        zira_mp4 = zira_mp4_path(zira_style)
        if not zira_mp4.exists():
            print(f"   ⚠️  Zira MP4 no encontrado: {zira_mp4.name}, usando clasica")
            zira_mp4 = zira_mp4_path("clasica")

        # Verify audio exists
        audio = audio_path(audio_file)
        if not audio:
            print(f"   ⚠️  Audio no encontrado: {audio_file}, continuando sin audio")
        
        # Duration: 4s per photo + transitions
        duration = len(fotos_usar) * 4 + (len(fotos_usar) - 1) * 0.8
        
        # Temp files
        slideshow_no_zira = TEMP_DIR / f"base_{theme_name.lower()}.mp4"
        overlay_loop = TEMP_DIR / f"zira_loop_{theme_name.lower()}.mp4"
        composited = TEMP_DIR / f"comp_{theme_name.lower()}.mp4"
        final = output_dir / f"zira_{theme_name.lower()}.mp4"
        
        # Step 1: Render Ken Burns slideshow
        ok = render_ken_burns_slideshow(fotos_usar, slideshow_no_zira, dur_per_foto=4)
        if not ok:
            print(f"   ❌ Falló slideshow para {theme_name}")
            continue
        
        # Step 2: Prepare Zira overlay (looped, scaled)
        ok = create_zira_overlay(zira_mp4, duration, overlay_loop)
        if not ok:
            print(f"   ❌ Falló overlay Zira para {theme_name}")
            continue
        
        # Step 3: Composite
        ok = composite_videos(slideshow_no_zira, overlay_loop, composited)
        if not ok:
            print(f"   ❌ Falló composición para {theme_name}")
            continue
        
        # Step 4: Add audio
        if audio:
            ok = add_audio(composited, audio, final)
            if ok:
                size_mb = final.stat().st_size / (1024*1024)
                print(f"\n   ✅ {final.name} ({size_mb:.1f} MB, ~{duration:.0f}s)")
                results.append((theme_name, str(final), zira_style, audio_file))
            else:
                # Fallback: without audio
                shutil.copy(composited, final)
                size_mb = final.stat().st_size / (1024*1024)
                print(f"\n   ⚠️ {final.name} sin audio ({size_mb:.1f} MB)")
                results.append((theme_name, str(final), zira_style, "sin audio"))
        else:
            shutil.copy(composited, final)
            size_mb = final.stat().st_size / (1024*1024)
            print(f"\n   ⚠️ {final.name} sin audio ({size_mb:.1f} MB)")
            results.append((theme_name, str(final), zira_style, "sin audio"))
    
    return results


def cleanup():
    """Limpia archivos temporales."""
    if TEMP_DIR.exists():
        shutil.rmtree(str(TEMP_DIR))
        TEMP_DIR.mkdir(parents=True, exist_ok=True)


# ─── MAIN ──────────────────────────────────────────────────────

if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════╗")
    print("║  🏔️  ZIRA VIDEO PIPELINE v2                       ║")
    print("║  Fotos + Zira animada + Audio contextual         ║")
    print("╚══════════════════════════════════════════════════╝")
    
    # Cargar DB
    db = load_db()
    print(f"📊 {len(db['fotos']['_index'])} fotos en catálogo")
    print(f"🎵 {len(list(AUDIO_DIR.glob('*.mp3')))} audios disponibles")
    print(f"🏔️  {len(list(ZIRA_POSTS.glob('zira-*.mp4')))} estilos Zira")
    
    # Construir videos por tema
    print(f"\n{'='*60}")
    print("🎬 CONSTRUYENDO VIDEOS POR TEMA...")
    print(f"{'='*60}")
    
    results = build_theme_videos(db, OUTPUT_DIR)
    
    # Limpiar
    cleanup()
    
    # Resultados
    print(f"\n{'='*60}")
    print(f"🏁 COMPLETADO: {len(results)} videos")
    print(f"{'='*60}")
    print()
    for name, path, zira, audio in results:
        print(f"   🌄 {name:<15} → Zira: {zira:<10} | Audio: {audio:<20}")
        print(f"      {path}")
    print()
    print(f"📁 Output: {OUTPUT_DIR}")
