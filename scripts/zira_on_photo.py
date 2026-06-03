#!/usr/bin/env python3
"""Zira sobre fotos reales — compone Zira sticker + foto real y publica en IG."""

import os, sys, json, random, requests, time, subprocess
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.environ.get("CRM_INSTAGRAM_TOKEN", "")
USER_ID = os.environ.get("CRM_INSTAGRAM_USER_ID", "")
PROJECT = Path(__file__).resolve().parent.parent
POSTS_DIR = PROJECT / "assets" / "zira" / "posts"
PUBLICIDAD = Path("/data/data/com.termux/files/home/publicidad")

# Mapeo de tags de foto → personalidad Zira con caption en su voz
PERSONALIDAD = {
    "noche": {
        "estilo": "zen",
        "emoji": "🌙",
        "voz": "La noche me abraza. Las estrellas me cuentan secretos que solo el viento sabe.",
        "frase": "Bajo el manto estrellado de Barreal, soy guardiana del silencio."
    },
    "luna": {
        "estilo": "zen",
        "emoji": "🌙",
        "voz": "La luna llena me ilumina, y yo sonrío desde la montaña.",
        "frase": "Las noches de luna en los Andes son mi momento favorito."
    },
    "pileta": {
        "estilo": "juguetona",
        "emoji": "💦",
        "voz": "¡El agua me hace cosquillas! Vení a refrescarte conmigo.",
        "frase": "La pileta me llama, el sol me despierta, el verano me sonríe."
    },
    "piscina": {
        "estilo": "juguetona",
        "emoji": "💦",
        "voz": "¡A chapotear! Que la vida también es refrescarse entre montañas.",
        "frase": "Un día de pileta con vista a los Andes no tiene precio."
    },
    "agua": {
        "estilo": "juguetona",
        "emoji": "💧",
        "voz": "El agua corre, el tiempo vuela, pero yo siempre estoy aquí.",
        "frase": "Agua que fluye, vida que sigue. Los Andes me enseñaron a fluir."
    },
    "atardecer": {
        "estilo": "magica",
        "emoji": "🌅",
        "voz": "Cuando el sol se despinta tras las montañas, mi corazón se tiñe de violeta.",
        "frase": "Cada atardecer es una promesa de un nuevo amanecer."
    },
    "montaña": {
        "estilo": "clasica",
        "emoji": "🏔️",
        "voz": "Soy parte de estas montañas, llevo los Andes en mi interior.",
        "frase": "Desde mi cima, el mundo se ve infinito y lleno de paz."
    },
    "montanas": {
        "estilo": "clasica",
        "emoji": "🏔️",
        "voz": "Las montañas me criaron, el viento me peinó, la nieve me coronó.",
        "frase": "Andes eternos, corazón de piedra, alma de glaciar."
    },
    "paisaje": {
        "estilo": "clasica",
        "emoji": "🏔️",
        "voz": "Miro el horizonte y veo hogar. Esto es Rancho Raíz.",
        "frase": "El paisaje habla por sí solo. Yo solo lo acompaño."
    },
    "naturaleza": {
        "estilo": "viva",
        "emoji": "🌿",
        "voz": "La naturaleza corre por mis venas de montaña.",
        "frase": "Verde que te quiero verde. Los Andes me enseñaron a respirar."
    },
    "relax": {
        "estilo": "zen",
        "emoji": "🧘",
        "voz": "Silencio. Paz. Montaña. Así recargo energía.",
        "frase": "En el silencio de los Andes, encuentro mi centro."
    },
    "fuego": {
        "estilo": "magica",
        "emoji": "🔥",
        "voz": "El fuego me hipnotiza. Las llamas bailan como yo.",
        "frase": "Fogata, estrellas y montaña. La combinación perfecta."
    },
    "fogata": {
        "estilo": "magica",
        "emoji": "🔥",
        "voz": "Sentate a mi lado, el fuego nos contará historias.",
        "frase": "Alrededor del fuego, el tiempo se detiene."
    },
    "marca": {
        "estilo": "retro",
        "emoji": "✨",
        "voz": "Soy la cara de Rancho Raíz, la sonrisa de los Andes.",
        "frase": "Rancho Raíz: donde las montañas te reciben con los brazos abiertos."
    },
    "logo": {
        "estilo": "viva",
        "emoji": "🌟",
        "voz": "Este es mi hogar. Bienvenidos a Rancho Raíz.",
        "frase": "Más que un logo, un abrazo de montaña."
    },
    "rústico": {
        "estilo": "retro",
        "emoji": "🏡",
        "voz": "Lo rústico me queda bien. Soy montaña, soy tierra, soy hogar.",
        "frase": "Rústico como los Andes, auténtico como Barreal."
    }
}

def choose_personality(tags, hora):
    """Elige personalidad y caption según tags + hora de la foto."""
    # Match prioritario por tags
    best = {"estilo": "clasica", "emoji": "🏔️", "voz": "", "frase": ""}
    for tag in tags:
        if tag in PERSONALIDAD:
            best = PERSONALIDAD[tag]
            break
    # Fallback por hora
    if hora == "noche" and best["estilo"] == "clasica":
        best = {"estilo": "zen", "emoji": "🌙", "voz": "La noche me envuelve en su manto de estrellas.", "frase": "Noches mágicas en los Andes."}
    elif hora == "atardecer" and best["estilo"] == "clasica":
        best = {"estilo": "magica", "emoji": "🌅", "voz": "Me fundo con el atardecer.", "frase": "El sol se despide, yo sonrío."}
    return best

def composite_zira_on_photo(photo_path, zira_style, output_path, personality, position="bottom-right"):
    """Superpone Zira sticker sobre una foto real."""
    # Convertir SVG sticker a PNG temporal con fondo transparente
    zira_svg = PROJECT / "assets" / "zira" / f"zira-sticker.svg"
    zira_tmp = POSTS_DIR / f"zira_sticker_tmp.png"
    
    subprocess.run([
        sys.executable, "-c",
        f"from cairosvg import svg2png; svg2png(url='file://{zira_svg}', write_to='{zira_tmp}', output_width=200, output_height=200)"
    ], timeout=30, capture_output=True)
    
    if not zira_tmp.exists():
        print(f"  ❌ No se pudo generar Zira sticker")
        return False
    
    # Componer con Pillow
    from PIL import Image, ImageOps
    photo = Image.open(photo_path).convert("RGBA")
    
    # Forzar ratio 4:5 (Instagram acepta: 1:1 a 4:5)
    target_ratio = 4/5  # portrait
    w, h = photo.size
    current_ratio = w / h
    
    if current_ratio > 1:  # landscape → letterbox
        new_w = w
        new_h = int(w / target_ratio)
        letterbox = Image.new("RGBA", (new_w, new_h), (0, 0, 0, 255))
        y_offset = (new_h - h) // 2
        letterbox.paste(photo, (0, y_offset))
        photo = letterbox
    elif current_ratio < target_ratio:  # muy vertical → crop a 4:5
        new_h = int(w / target_ratio)
        y_offset = (h - new_h) // 2
        photo = photo.crop((0, y_offset, w, y_offset + new_h))
    # si ya está en 4:5 o 1:1, no se modifica
    
    zira = Image.open(zira_tmp).convert("RGBA")
    
    # Redimensionar Zira al 20% del ancho de la foto
    zira_w = int(photo.width * 0.2)
    zira_h = int(zira_w * zira.height / zira.width)
    zira = zira.resize((zira_w, zira_h), Image.LANCZOS)
    
    # Posicionar
    margin = int(photo.width * 0.03)
    if position == "bottom-right":
        x = photo.width - zira_w - margin
        y = photo.height - zira_h - margin
    elif position == "bottom-left":
        x = margin
        y = photo.height - zira_h - margin
    elif position == "top-right":
        x = photo.width - zira_w - margin
        y = margin
    else:  # top-left
        x = margin
        y = margin
    
    photo.paste(zira, (x, y), zira)
    photo.convert("RGB").save(output_path, "JPEG", quality=92)
    
    # Limpiar temp
    zira_tmp.unlink(missing_ok=True)
    
    size_kb = os.path.getsize(output_path) / 1024
    print(f"  📸 Compuesto: {output_path.name} ({size_kb:.0f} KB)")
    return True

def publish_ig(image_path, caption):
    """Publica imagen en Instagram."""
    # Subir imagen a GitHub primero
    gh_url = f"https://raw.githubusercontent.com/oficinabarreal/rancho-raiz-zira/main/assets/zira/posts/{image_path.name}"
    
    # Crear container IMAGE
    r = requests.post(f"https://graph.facebook.com/v22.0/{USER_ID}/media",
        data={"image_url": gh_url, "caption": caption, "access_token": TOKEN}, timeout=30)
    if not r.ok:
        return False, f"create: {r.text[:100]}"
    
    cid = r.json()["id"]
    print(f"  📦 Container: {cid}", end="", flush=True)
    time.sleep(3)
    
    r2 = requests.post(f"https://graph.facebook.com/v22.0/{USER_ID}/media_publish",
        data={"creation_id": cid, "access_token": TOKEN}, timeout=30)
    if r2.ok:
        return True, f"✅ ID={r2.json().get('id','?')}"
    return False, f"publish: {r2.text[:100]}"

# ===== MAIN =====
if __name__ == "__main__":
    # Cargar db.json
    db_path = PUBLICIDAD / "ranchocut" / "assets" / "db.json"
    with open(db_path) as f:
        db = json.load(f)
    
    fotos = db["fotos"]["_index"]
    
    # Seleccionar 1 foto aleatoria de exterior con tags variados
    valid = [f for f in fotos if f["categoria"] == "exterior"]
    selected = random.choice(valid)
    
    photo_file = PUBLICIDAD / "lab" / "imgs" / selected["archivo"]
    tags = selected["tags"]
    hora = selected["hora"]
    
    print(f"📸 Foto: {selected['id']}")
    print(f"   Tags: {', '.join(tags[:5])}")
    print(f"   Hora: {hora}")
    
    # Elegir personalidad Zira según contexto
    personality = choose_personality(tags, hora)
    style = personality["estilo"]
    print(f"   🏔️ Zira {style} {personality['emoji']}")
    print(f"   🗣️ \"{personality['voz']}\"")
    
    # Componer
    output = POSTS_DIR / f"zira_on_photo_{selected['id'][:20]}.jpg"
    ok = composite_zira_on_photo(photo_file, style, output, personality)
    if not ok:
        sys.exit(1)
    
    # Subir a GitHub
    print(f"  📤 Subiendo a GitHub...")
    subprocess.run(["git", "add", str(output), "-f"], cwd=str(PROJECT), capture_output=True)
    subprocess.run(["git", "commit", "-m", f"📸 Zira on photo: {selected['id'][:30]}"], cwd=str(PROJECT), capture_output=True)
    subprocess.run(["git", "push", "origin", "main"], cwd=str(PROJECT), timeout=30, capture_output=True)
    
    # Publicar en IG con voz de Zira
    caption = f"{personality['emoji']} \"{personality['voz']}\"\n\n{personality['frase']}\n\n🌄 Rancho Raíz · Barreal · San Juan\n\n#Zira #{personality['estilo'].capitalize()} #RanchoRaíz #Barreal #SanJuan #Andes #{' #'.join(tags[:3])}"
    
    print(f"  📱 Publicando en IG...")
    time.sleep(5)  # Esperar CDN
    ok, msg = publish_ig(output, caption)
    print(f"  {msg}")
    
    print(f"\n🏁 Listo! https://instagram.com/rancho.raiz.2026")
