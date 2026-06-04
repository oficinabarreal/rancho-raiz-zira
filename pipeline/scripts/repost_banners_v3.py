#!/usr/bin/env python3
"""
Borra los 14 banners viejos (Chromium tofu) de Instagram
y repostea los 15 nuevos con SVG shapes (cairosvg).
"""
import os, sys, json, time, requests
from pathlib import Path

sys.path.insert(0, "/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3")
from dotenv import load_dotenv
load_dotenv("/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3/.env")

TOKEN = os.environ["CRM_INSTAGRAM_TOKEN"]
USER_ID = os.environ["CRM_INSTAGRAM_USER_ID"]

BASE_URL = "https://raw.githubusercontent.com/oficinabarreal/rancho-raiz-zira/main/pipeline/zira-frases/png"

ESTILO_EMOJI = {
    "zen": "🧘",
    "clasica": "🏔️",
    "magica": "✨",
    "viva": "🌿",
}

manifest = json.loads(
    (Path("/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3/pipeline/zira-frases/manifest.json")).read_text()
)

# ─── PASO 1: Identificar banners viejos (16:14-16:19) ───
print("🔍 Buscando banners viejos en Instagram...")
r = requests.get(f"https://graph.facebook.com/v22.0/{USER_ID}/media", params={
    "fields": "id,media_type,caption,timestamp",
    "access_token": TOKEN,
    "limit": 100,
}, timeout=15)

all_posts = r.json().get("data", [])
old_banners = [p for p in all_posts 
               if p.get("media_type") == "IMAGE" 
               and p["timestamp"].startswith("2026-06-03T16")
               and '"' in (p.get("caption") or "")]

print(f"  Encontrados {len(old_banners)} banners viejos para borrar\n")

# ─── PASO 2: Borrar banners viejos ───
for i, post in enumerate(old_banners, 1):
    post_id = post["id"]
    r = requests.delete(f"https://graph.facebook.com/v22.0/{post_id}", params={
        "access_token": TOKEN,
    }, timeout=15)
    status = "✅" if r.ok else f"❌ {r.status_code}"
    print(f"  [{i}/{len(old_banners)}] Borrando {post_id}: {status}")
    if not r.ok:
        print(f"     {r.text[:100]}")
    time.sleep(0.5)

print(f"\n✅ {len(old_banners)} banners eliminados\n")

# ─── PASO 3: Publicar banners nuevos ───
print(f"📤 Publicando {len(manifest)} banners nuevos con SVG shapes...\n")

posted = 0
errors = 0
for i, item in enumerate(manifest, 1):
    png_name = item["archivo"].replace(".svg", ".png")
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
        data={"image_url": image_url, "caption": caption, "access_token": TOKEN},
        timeout=30,
    )
    if not r.ok:
        print(f"  ❌ [{i}] {png_name}: error container: {r.status_code} {r.text[:100]}")
        errors += 1
        continue
    
    creation_id = r.json()["id"]
    time.sleep(1.5)
    
    # 2. Publicar
    r = requests.post(
        f"https://graph.facebook.com/v22.0/{USER_ID}/media_publish",
        data={"creation_id": creation_id, "access_token": TOKEN},
        timeout=30,
    )
    if r.ok:
        media_id = r.json().get("id", "?")
        print(f"  ✅ [{i}] {png_name} → ID {media_id} | {estilo.upper()} | {frase[:30]}...")
        posted += 1
    else:
        print(f"  ❌ [{i}] {png_name}: error publish: {r.status_code} {r.text[:100]}")
        errors += 1
    
    time.sleep(2.5)  # rate limiting

print(f"\n🏁 {posted} publicados, {errors} errores de {len(manifest)} totales")
