#!/usr/bin/env python3
"""
Pipeline v3: Fotos + Zira transparente con chromakey + sonidos naturaleza.
Zira aparece "flotando" sobre las fotos, cambia aspecto según contexto.
Versión optimizada: usa subprocess con list args, timeouts por comando.
"""
import subprocess, os, sys, json, shutil
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent.parent
FOTOS_DIR = PROJECT / "pipeline" / "fotos"
DB_PATH = PROJECT / "pipeline" / "db.json"
AUDIO_NAT_DIR = PROJECT / "pipeline" / "audio" / "naturaleza"
AUDIO_DIR = PROJECT / "pipeline" / "audio"
ZIRA_TP_DIR = PROJECT / "assets" / "zira"
OUTPUT_DIR = PROJECT / "assets" / "zira" / "completos"
TEMP_DIR = PROJECT / "pipeline" / ".temp"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# ─── MAPEO: tags → Zira transparente → sonido naturaleza ─────────────
TAG_MAP = [
    (["pileta", "piscina", "agua"],     "juguetona", "olas.mp3",       "RiverMeditation.mp3", "Pileta"),
    (["noche", "luna", "estrellas"],     "zen",       "grillos_noche.mp3", "PaperWings.mp3",  "Noche"),
    (["atardecer"],                      "magica",    "viento.mp3",     "AutumnSunset.mp3",   "Atardecer"),
    (["montaña", "montanas", "paisaje", "montana"], "clasica", "rio_ambiente.mp3", "GreenLeaves.mp3", "Montañas"),
    (["naturaleza", "bosque", "árboles"],"viva",      "pajaros_bosque.mp3", "RedwoodTrail.mp3", "Naturaleza"),
    (["logo", "marca", "ranchoraiz"],    "clasica",   "viento.mp3",     "AcousticGuitar1.mp3","Marca"),
    (["rustico", "rústico"],             "clasica",   "rio_ambiente.mp3","GreenLeaves.mp3",   "Rústico"),
    (["fuego", "fogata"],                "magica",    "fuego.mp3",      "OneFineDay.mp3",    "Fogata"),
    (["relax"],                          "zen",       "rio_grillos.mp3","RiverMeditation.mp3","Relax"),
    (["mediodía", "mediodia", "dia"],    "viva",      "pajaros_bosque.mp3", "RedwoodTrail.mp3","Día"),
]

DEFAULT_ZIRA = "clasica"
DEFAULT_SONIDO = "rio_ambiente.mp3"
DEFAULT_MUSICA = "GreenLeaves.mp3"

# Posiciones para overlay
POSICIONES = [
    ("inferior-izquierda", "40",        "H-h-40"),
    ("inferior-derecha",   "W-w-40",    "H-h-40"),
    ("inferior-centro",    "(W-w)/2",   "H-h-40"),
    ("superior-izquierda", "40",        "40"),
    ("superior-derecha",   "W-w-40",    "40"),
]

def log(msg):
    print(f"  {msg}", flush=True)

def ffmpeg(args, timeout=120):
    """Ejecuta ffmpeg con lista de args."""
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        if r.returncode != 0:
            err = r.stderr.strip()[-300:]
            if err:
                log(f"⚠️  {err}")
        return r.returncode == 0
    except subprocess.TimeoutExpired:
        log(f"⏰ Timeout ({timeout}s)")
        return False

def load_db():
    with open(DB_PATH) as f:
        return json.load(f)

def find_photos_by_tags(db, tag_list):
    fotos = db["fotos"]["_index"]
    matched = []
    for f in fotos:
        ftags = [t.lower().strip() for t in f.get("tags", [])]
        if any(t in ftags for t in tag_list):
            fname = f["archivo"]
            if (FOTOS_DIR / fname).exists():
                matched.append(f)
    return matched

def resolve_styles(foto_tags):
    ft = [t.lower().strip() for t in foto_tags]
    for match_tags, zira_style, sonido, musica, _ in TAG_MAP:
        if any(t in ft for t in match_tags):
            return zira_style, sonido, musica
    return DEFAULT_ZIRA, DEFAULT_SONIDO, DEFAULT_MUSICA

def zira_tp_path(style):
    p = ZIRA_TP_DIR / f"zira-tp-{style}.mp4"
    return p if p.exists() else ZIRA_TP_DIR / "zira-tp-clasica.mp4"

def sonido_path(name):
    p = AUDIO_NAT_DIR / name
    if p.exists():
        return p, "naturaleza"
    p = AUDIO_DIR / name
    if p.exists():
        return p, "musica"
    return None, None

def render_slideshow(photos, output_path, dur_por_foto=3.5):
    """Ken Burns slideshow con lista de args."""
    if not photos:
        return False
    slides = []
    for i, foto in enumerate(photos):
        fpath = FOTOS_DIR / foto["archivo"]
        if not fpath.exists():
            continue
        temp = TEMP_DIR / f"slide_{i:02d}.mp4"
        slides.append(temp)
        ok = ffmpeg([
            "ffmpeg", "-y", "-loop", "1", "-i", str(fpath),
            "-vf", f"zoompan=z='min(zoom+0.001,1.10)':x='(iw-iw/zoom)*0.5':y='(ih-ih/zoom)*0.5':d={dur_por_foto*30}:s=1080x1920:fps=30,format=yuv420p",
            "-c:v", "libx264", "-t", str(dur_por_foto), str(temp)
        ], timeout=60)
        if not ok:
            log(f"Falló slide {i}")
    slides = [s for s in slides if s.exists()]
    if not slides:
        return False
    if len(slides) == 1:
        shutil.copy(slides[0], output_path)
        return True
    # Concat
    cl = TEMP_DIR / "concat.txt"
    with open(cl, "w") as f:
        for s in slides:
            f.write(f"file '{s}'\n")
    ok = ffmpeg([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(cl),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(output_path)
    ], timeout=60)
    return output_path.exists()

def composite_with_chromakey(base_video, zira_video, output_path, pos_nombre="inferior-izquierda", scale_pct=25):
    """Compone con chromakey. Zira sobre fondo verde se vuelve transparente."""
    pos_map = {n: (x, y) for n, x, y in POSICIONES}
    if pos_nombre not in pos_map:
        pos_nombre = "inferior-izquierda"
    pos_x, pos_y = pos_map[pos_nombre]
    overlay_w = int(1080 * scale_pct / 100)

    ok = ffmpeg([
        "ffmpeg", "-y",
        "-i", str(base_video),
        "-i", str(zira_video),
        "-filter_complex",
        f"[1:v]scale={overlay_w}:-2,colorkey=0x00FF00:0.08:0.1[zira_tp];"
        f"[0:v][zira_tp]overlay={pos_x}:{pos_y}[v]",
        "-map", "[v]", "-map", "0:a?",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-shortest",
        str(output_path)
    ], timeout=120)
    return ok and output_path.exists()

def add_audio_mix(video_path, sonido_path, musica_path, output_path):
    """Mezcla sonido naturaleza + música de fondo, ambos en loop."""
    inputs = [str(video_path)]
    filters = []
    stream_idx = 1

    if sonido_path and sonido_path.exists():
        inputs.append(str(sonido_path))
        filters.append(f"[{stream_idx}:a]volume=0.45,aloop=loop=-1:size=2e9[a_nat]")
        stream_idx += 1
    if musica_path and musica_path.exists():
        inputs.append(str(musica_path))
        filters.append(f"[{stream_idx}:a]volume=0.15,aloop=loop=-1:size=2e9[a_mus]")
        stream_idx += 1

    if not filters:
        shutil.copy(video_path, output_path)
        return True

    if len(filters) == 1:
        amix = f"[0:a][a_nat]amix=inputs=2:duration=first[aout]"
    else:
        amix = f"[0:a][a_nat][a_mus]amix=inputs=3:duration=first:dropout_transition=2[aout]"

    filter_str = ";".join(filters) + ";" + amix

    args = [
        "ffmpeg", "-y",
        *sum([["-i", inp] for inp in inputs], []),
        "-filter_complex", filter_str,
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest", "-movflags", "+faststart",
        str(output_path)
    ]
    ok = ffmpeg(args, timeout=120)
    return ok and output_path.exists()

def build_videos(db):
    results = []
    for match_tags, zira_style, sonido_name, musica_name, theme_name in TAG_MAP:
        print(f"\n{'='*55}")
        print(f"🎯 TEMA: {theme_name}")
        print(f"   Zira: {zira_style} | Naturaleza: {sonido_name} | Música: {musica_name}")
        print(f"{'='*55}")

        photos = find_photos_by_tags(db, match_tags)
        if not photos:
            log("⏭️  Sin fotos")
            continue

        fotos_usar = photos[:5]
        log(f"📸 {len(fotos_usar)} fotos")

        zira_tp = zira_tp_path(zira_style)
        sonido, _ = sonido_path(sonido_name)
        musica, _ = sonido_path(musica_name) if musica_name else (None, None)

        duration = len(fotos_usar) * 3.5 + (len(fotos_usar) - 1) * 0.8
        log(f"⏱  Duración ~{duration:.0f}s")

        # Slideshow base
        slideshow = TEMP_DIR / f"base_{theme_name.lower()}.mp4"
        log(f"🎞️  Renderizando slideshow...")
        if not render_slideshow(fotos_usar, slideshow, dur_por_foto=3.5):
            log("❌ Falló slideshow")
            continue

        # Probar 2 posiciones
        if theme_name == "Pileta":
            posiciones = ["inferior-izquierda", "superior-izquierda"]
        elif theme_name in ("Noche", "Zen"):
            posiciones = ["inferior-izquierda", "inferior-derecha"]
        else:
            posiciones = ["inferior-izquierda", "inferior-derecha"]

        for pos_nombre in posiciones:
            composited = TEMP_DIR / f"comp_{theme_name.lower()}_{pos_nombre}.mp4"
            log(f"🎬 Componiendo ({pos_nombre})...")
            ok = composite_with_chromakey(slideshow, zira_tp, composited, pos_nombre, scale_pct=25)
            if not ok:
                log(f"❌ Falló composición {pos_nombre}")
                continue

            # Audio: intentar naturaleza + música, fallback a solo naturaleza
            final = OUTPUT_DIR / f"zira_{theme_name.lower()}_{pos_nombre}.mp4"
            ok = add_audio_mix(composited, sonido, musica, final)
            if ok and final.exists():
                size_mb = final.stat().st_size / (1024*1024)
                log(f"✅ {final.name} ({size_mb:.1f} MB)")
                results.append((theme_name, pos_nombre, str(final), zira_style))
            else:
                # Fallback solo naturaleza
                final2 = OUTPUT_DIR / f"zira_{theme_name.lower()}_{pos_nombre}_nat.mp4"
                ok2 = add_audio_mix(composited, sonido, None, final2)
                if ok2:
                    size_mb = final2.stat().st_size / (1024*1024)
                    log(f"✅ {final2.name} (solo naturaleza) ({size_mb:.1f} MB)")
                    results.append((theme_name, pos_nombre + " (solo nat)", str(final2), zira_style))

        # Liberar slideshow
        if slideshow.exists():
            slideshow.unlink()

    return results

def cleanup():
    if TEMP_DIR.exists():
        shutil.rmtree(str(TEMP_DIR))
        TEMP_DIR.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════╗")
    print("║  🏔️  ZIRA PIPELINE v3 — Chromakey + Naturaleza       ║")
    print("╚══════════════════════════════════════════════════════╝")

    db = load_db()
    print(f"📊 {len(db['fotos']['_index'])} fotos")
    print(f"🔊 {len(list(AUDIO_NAT_DIR.glob('*.mp3')))} sonidos naturaleza")
    print(f"🔊 {len(list(AUDIO_DIR.glob('*.mp3')))} tracks música")
    print(f"🏔️  {len(list(ZIRA_TP_DIR.glob('zira-tp-*.mp4')))} Ziras transparentes")

    results = build_videos(db)
    cleanup()

    print(f"\n{'='*55}")
    print(f"🏁 COMPLETADO: {len(results)} videos")
    print(f"{'='*55}\n")
    for name, pos, path, style in results:
        print(f"   🌄 {name:<15} | {pos:<25} | Zira: {style}")
        print(f"      {path}")
    print(f"\n📁 Output: {OUTPUT_DIR}")
