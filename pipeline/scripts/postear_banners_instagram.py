#!/usr/bin/env python3
"""Postear todos los banners Zira frase a Instagram."""
import os, sys, json, time, random, requests
from pathlib import Path

sys.path.insert(0, "/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3")
from dotenv import load_dotenv
load_dotenv("/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3/.env")

TOKEN = os.environ["CRM_INSTAGRAM_TOKEN"]
USER_ID = os.environ["CRM_INSTAGRAM_USER_ID"]
BASE_URL = "https://raw.githubusercontent.com/oficinabarreal/rancho-raiz-zira/main/pipeline/zira-frases/png"

MANIFEST = json.loads(
    (Path("/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3/pipeline/zira-frases/manifest.json")).read_text()
)

# Emoji por estilo para caption
ESTILO_EMOJI = {
    "zen": "🧘",
    "clasica": "🏔️",
    "magica": "✨",
    "viva": "🌿",
}

def post_image(png_name, item):
    """Postear un banner como IMAGE en Instagram."""
    image_url = f"{BASE_URL}/{png_name}"
    
    estilo = item["estilo"]
    emoji_estilo = ESTILO_EMOJI.get(estilo, "🏔️")
    frase = item["frase"]
    emoji = item["emoji"]
    tags = item["tags"]
    
    caption = (
        f'{emoji} "{frase}"\n\n'
        f'{emoji_estilo} Filosofía Zira — {estilo.capitalize()}\n\n'
        f"#Zira #RanchoRaíz #Barreal #Andes #{tags[0].capitalize()}"
    )
    
    # 1. Crear container
    r = requests.post(
        f"https://graph.facebook.com/v22.0/{USER_ID}/media",
        data={
            "image_url": image_url,
            "caption": caption,
            "access_token": TOKEN,
        },
        timeout=30,
    )
    if not r.ok:
        raise Exception(f"❌ Error creating container: {r.status_code} {r.text}")
    
    creation_id = r.json()["id"]
    time.sleep(2)
    
    # 2. Publicar
    r = requests.post(
        f"https://graph.facebook.com/v22.0/{USER_ID}/media_publish",
        data={"creation_id": creation_id, "access_token": TOKEN},
        timeout=30,
    )
    if not r.ok:
        raise Exception(f"❌ Error publishing: {r.status_code} {r.text}")
    
    media_id = r.json().get("id")
    return media_id

# Postear en orden aleatorio para que el feed se vea orgánico
items = list(MANIFEST)
random.shuffle(items)

print(f"🏔️  Posteando {len(items)} banners Zira a Instagram...\n")
for i, item in enumerate(items, 1):
    png_name = item["archivo"].replace(".svg", ".png")
    frase_corta = item["frase"][:50]
    
    try:
        media_id = post_image(png_name, item)
        print(f"  ✅ [{i}/{len(items)}] {item['estilo'].upper()} — \"{frase_corta}...\"")
        print(f"     ID: {media_id}")
    except Exception as e:
        print(f"  ❌ [{i}/{len(items)}] {png_name}: {e}")
        # Si falla uno, seguimos con el resto
    
    # Esperar entre posts (rate limiting)
    if i < len(items):
        delay = random.randint(8, 15)
        print(f"     ⏱  Esperando {delay}s...")
        time.sleep(delay)

print(f"\n🏁 ¡Listo! {len(items)} banners publicados.")
