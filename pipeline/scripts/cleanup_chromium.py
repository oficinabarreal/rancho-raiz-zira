#!/usr/bin/env python3
"""Delete Chromium tofu banners, post missing SVG banner."""
import os, sys, json, time, requests
sys.path.insert(0, "/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3")
from dotenv import load_dotenv
load_dotenv("/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3/.env")

TOKEN = os.environ["CRM_INSTAGRAM_TOKEN"]
USER_ID = os.environ["CRM_INSTAGRAM_USER_ID"]

# Step 1: Find & delete Chromium banners
r = requests.get(f"https://graph.facebook.com/v22.0/{USER_ID}/media", params={
    "fields": "id,media_type,caption,timestamp,like_count",
    "access_token": TOKEN, "limit": 100,
}, timeout=15)

img = [p for p in r.json().get("data", []) if p.get("media_type") == "IMAGE"]
img.sort(key=lambda x: x["timestamp"])

chromium = [p for p in img if ('"' in (p.get("caption") or "") or "Filosofía Zira" in (p.get("caption") or "")) and p["timestamp"].startswith("2026-06-03T16:1")]
svg_new = [p for p in img if ('"' in (p.get("caption") or "") or "Filosofía Zira" in (p.get("caption") or "")) and p["timestamp"].startswith("2026-06-04")]

print(f"📊 Chromium (tofu): {len(chromium)} | SVG (nuevos): {len(svg_new)}")

print(f"\n🗑️  Borrando Chromium banners...")
ok = 0
for p in chromium:
    r = requests.delete(f"https://graph.facebook.com/v22.0/{p['id']}", params={"access_token": TOKEN}, timeout=15)
    status = "✅" if r.ok else f"❌ {r.status_code}"
    print(f"  {status} {p['id']} | likes={p.get('like_count',0)}")
    if not r.ok:
        print(f"     {r.text[:100]}")
    time.sleep(0.8)
    if r.ok:
        ok += 1

print(f"\n  {ok}/{len(chromium)} deleted")

# Step 2: Post missing banner
print(f"\n📤 Posteando camino-montaña...")
BASE_URL = "https://raw.githubusercontent.com/oficinabarreal/rancho-raiz-zira/main/pipeline/zira-frases/png"
png = "zira-frase-camino-montaña.png"

# Check if file exists on GitHub
r = requests.head(f"{BASE_URL}/{png}", timeout=10)
if r.status_code != 200:
    print(f"  ⚠️  GitHub URL returned {r.status_code} - trying alternative name...")
    # The emoji ⛰️ might have been replaced differently - check png-v3 dir
    alt = "https://raw.githubusercontent.com/oficinabarreal/rancho-raiz-zira/main/pipeline/zira-frases/png-v3/zira-frase-camino-montaña.png"
    r = requests.head(alt, timeout=10)
    if r.ok:
        BASE_URL = "https://raw.githubusercontent.com/oficinabarreal/rancho-raiz-zira/main/pipeline/zira-frases/png-v3"
        print(f"  ✅ Found in png-v3")
else:
    print(f"  ✅ Found in png")

frase = "Las montañas tienen un camino,\nel viento una dirección,\nyo tengo un destino."
emoji = "⛰️"
caption = f'{emoji} "{frase}"\n\n🏔️ Filosofía Zira — Clasica\n\n#Zira #RanchoRaíz #Barreal #Andes #Montaña'

r = requests.post(f"https://graph.facebook.com/v22.0/{USER_ID}/media",
    data={"image_url": f"{BASE_URL}/{png}", "caption": caption, "access_token": TOKEN}, timeout=30)

if r.ok:
    cid = r.json()["id"]
    print(f"  ✅ Container created: {cid}")
    time.sleep(2)
    r2 = requests.post(f"https://graph.facebook.com/v22.0/{USER_ID}/media_publish",
        data={"creation_id": cid, "access_token": TOKEN}, timeout=30)
    if r2.ok:
        print(f"  ✅ Publicado! ID: {r2.json().get('id','?')}")
    else:
        print(f"  ❌ Publish error: {r2.text[:150]}")
else:
    print(f"  ❌ Container error: {r.text[:200]}")
