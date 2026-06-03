#!/usr/bin/env python3
"""
Zira en Fotos Reales — Compositor de Ziras transparentes sobre fotos de la posada.
Genera imágenes híbridas (Zira + paisaje real) listas para Instagram.
"""
import os, sys, json, random, time
from pathlib import Path
from PIL import Image
from cairosvg import svg2png

sys.path.insert(0, "/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3")
from dotenv import load_dotenv
load_dotenv("/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3/.env")

TOKEN = os.environ.get("CRM_INSTAGRAM_TOKEN")
USER_ID = os.environ.get("CRM_INSTAGRAM_USER_ID")
BASE = Path("/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3")

FOTOS_DIR = BASE / "pipeline" / "fotos"
ZIRA_SVGS = BASE / "assets" / "zira"
OUT_DIR = BASE / "assets" / "zira" / "on-photo"
OUT_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR = BASE / "pipeline" / "zira-frases" / "tmp_stickers"
TMP_DIR.mkdir(exist_ok=True)

# db.json metadata
db_path = BASE / "pipeline" / "db.json"
db = json.loads(db_path.read_text())
fotos_index = db.get("fotos", {}).get("_index", [])

# Mapeo tags -> estilo Zira
TAG_TO_STYLE = {
    "pileta": "juguetona", "piscina": "juguetona", "pool": "juguetona",
    "fuego": "magica", "fogata": "magica", "fire": "magica", "asado": "magica",
    "noche": "zen", "night": "zen", "luna": "zen", "moon": "zen", "estrellas": "zen",
    "atardecer": "magica", "sunset": "magica",
    "montañas": "clasica", "montaña": "clasica", "andes": "clasica", "mountain": "clasica",
    "naturaleza": "viva", "verde": "viva", "bosque": "viva", "árboles": "viva", "nature": "viva",
    "relax": "zen", "rústico": "clasica", "rustico": "clasica",
    "logo": "clasica", "marca": "clasica",
}

STYLE_INFO = {
    "juguetona": {"emoji": "💦", "frase": "El agua me llama, el sol me despierta."},
    "zen":      {"emoji": "🧘", "frase": "En el silencio de los Andes encuentro mi centro."},
    "magica":   {"emoji": "✨", "frase": "Cada atardecer es una promesa de un nuevo amanecer."},
    "viva":     {"emoji": "🌿", "frase": "Verde que te quiero verde. Los Andes me enseñaron a respirar."},
    "clasica":  {"emoji": "🏔️", "frase": "Las montañas me criaron, el viento me peinó."},
}

def choose_style(tags):
    for tag in tags:
        for key, style in TAG_TO_STYLE.items():
            if key in tag.lower():
                return style
    return "clasica"

def render_zira_sticker(style, size=300):
    """Render Zira SVG sticker a PNG con transparencia."""
    svg_path = ZIRA_SVGS / f"zira-transparente-{style}.svg"
    if not svg_path.exists():
        print(f"     ⚠️  No existe {svg_path.name}, usando clasica")
        svg_path = ZIRA_SVGS / "zira-transparente-clasica.svg"
    
    png_path = TMP_DIR / f"sticker_{style}.png"
    svg2png(bytestring=svg_path.read_bytes(), write_to=str(png_path),
            output_width=size, output_height=size)
    return png_path

def process_photo(foto_data):
    """Compone Zira sobre una foto real."""
    filename = foto_data["archivo"]
    tags = foto_data.get("tags", [])
    style = choose_style(tags)
    info = STYLE_INFO[style]
    
    photo_path = FOTOS_DIR / filename
    if not photo_path.exists():
        return None
    
    # 1. Cargar foto
    photo = Image.open(photo_path).convert("RGBA")
    
    # 2. Redimensionar/cortar a cuadrado 1:1 (Instagram-friendly)
    size = min(photo.size)
    left = (photo.width - size) // 2
    top = (photo.height - size) // 2
    photo = photo.crop((left, top, left + size, top + size))
    photo = photo.resize((1080, 1080), Image.LANCZOS)
    
    # 3. Renderizar Zira sticker
    sticker_size = 280  # ~26% del ancho
    sticker_path = render_zira_sticker(style, sticker_size)
    sticker = Image.open(sticker_path).convert("RGBA")
    
    # 4. Posición: esquina inferior-derecha con margen
    margin = 40
    x = photo.width - sticker.width - margin
    y = photo.height - sticker.height - margin
    
    # 5. Componer
    composite = photo.copy()
    composite.paste(sticker, (x, y), sticker)
    
    # 6. Guardar
    out_name = f"zira-on_{filename.rsplit('.',1)[0]}_{style}.png"
    out_path = OUT_DIR / out_name
    composite.convert("RGB").save(out_path, "PNG")
    
    return {
        "archivo": out_name,
        "path": str(out_path),
        "foto_original": filename,
        "estilo": style,
        "tags": tags,
        "emoji": info["emoji"],
        "frase": info["frase"],
    }

# ─── PROCESAR FOTOS ───
print("🏔️  Zira en Fotos Reales — Compositor\n")

# Seleccionar fotos con metadata
resultados = []
for f in fotos_index[:10]:  # Primeras 10
    print(f"  📷 {f['archivo']}...")
    result = process_photo(f)
    if result:
        size_kb = Path(result["path"]).stat().st_size / 1024
        print(f"     ✅ Zira {result['estilo']} ({size_kb:.0f} KB)")
        resultados.append(result)
    else:
        print(f"     ⏭️  Foto no encontrada")

print(f"\n🏁 {len(resultados)} imágenes compuestas en {OUT_DIR}/")

# Guardar manifest
manifest_path = OUT_DIR / "manifest_on_photo.json"
with open(manifest_path, "w") as f:
    json.dump(resultados, f, indent=2, ensure_ascii=False)
print(f"📋 Manifest: {manifest_path}")
