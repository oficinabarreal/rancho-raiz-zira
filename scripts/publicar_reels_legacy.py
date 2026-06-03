#!/usr/bin/env python3
"""Publica los 6 Reels legacy de ranchoraiz_reels en Instagram."""
import os, time, requests, random, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.environ.get("CRM_INSTAGRAM_TOKEN", "")
USER_ID = os.environ.get("CRM_INSTAGRAM_USER_ID", "")
GH = "https://raw.githubusercontent.com/oficinabarreal/rancho-raiz-zira/main/assets/reels"
PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REELS = [
    ("ranchoraiz_storytelling.mp4", "🏡 Rancho Raíz — la experiencia completa.\n\nDesde el logo hasta la noche estrellada, pasando por pileta, asado y montañas. Esto es Barreal, San Juan.\n\n#RanchoRaíz #Barreal #SanJuan #Turismo #Andes #Experiencia"),
    ("atardecer_reel.mp4", "🌅 Atardecer dorado en los Andes.\n\nEl sol escondiéndose tras la cordillera, la pileta reflejando el cielo. Así son las tardes en Barreal.\n\n#Atardecer #Andes #Barreal #SanJuan #Pileta #RanchoRaíz"),
    ("pileta_reel.mp4", "💦 Refrescá tus sentidos.\n\nPileta con vista a la cordillera. El lugar perfecto para desconectar.\n\n#Pileta #Refrescá #Barreal #SanJuan #RanchoRaíz #Naturaleza"),
    ("noche_reel.mp4", "✨ Noches mágicas bajo las estrellas.\n\nAstroturismo en San Juan. Fogata, cielo despejado, silencio de montaña.\n\n#Noche #Estrellas #Astroturismo #Barreal #SanJuan #RanchoRaíz"),
    ("montanas_reel.mp4", "🏔️ Montañas que abrazan.\n\nLos Andes desde Barreal. Paisajes que te hacen sentir vivo.\n\n#Montañas #Andes #Barreal #SanJuan #Naturaleza #RanchoRaíz"),
    ("brand_reel.mp4", "📍 Rancho Raíz · Barreal · San Juan.\n\nTu lugar en los Andes. Desconexión, naturaleza, montaña.\n\n#RanchoRaíz #Barreal #SanJuan #Andes #Turismo #Marca"),
]

def publish_video(video_url, caption):
    r = requests.post(f"https://graph.facebook.com/v22.0/{USER_ID}/media",
        data={"media_type": "REELS", "video_url": video_url, "caption": caption, "access_token": TOKEN}, timeout=60)
    if not r.ok:
        return False, f"create: {r.text[:100]}"
    cid = r.json()["id"]
    print(f"  📦 Container: {cid}", end="", flush=True)
    for _ in range(20):
        time.sleep(5)
        sr = requests.get(f"https://graph.facebook.com/v22.0/{cid}?fields=status_code&access_token={TOKEN}", timeout=15)
        s = sr.json().get("status_code", "") if sr.ok else ""
        print(".", end="", flush=True)
        if s == "FINISHED":
            print(" ✅")
            break
    else:
        print(" ⚠")
    
    r2 = requests.post(f"https://graph.facebook.com/v22.0/{USER_ID}/media_publish",
        data={"creation_id": cid, "access_token": TOKEN}, timeout=30)
    if r2.ok:
        return True, f"✅ ID={r2.json().get('id','?')}"
    time.sleep(10)
    r2 = requests.post(f"https://graph.facebook.com/v22.0/{USER_ID}/media_publish",
        data={"creation_id": cid, "access_token": TOKEN}, timeout=30)
    if r2.ok:
        return True, f"✅ ID={r2.json().get('id','?')}"
    return False, f"publish: {r2.text[:100]}"

random.shuffle(REELS)
print(f"🎬 Publicando {len(REELS)} Reels legacy en @rancho.raiz.2026")
print("="*50)

ok_count = 0
for i, (fname, caption) in enumerate(REELS, 1):
    url = f"{GH}/{fname}"
    print(f"\n[{i}/{len(REELS)}] {fname}")
    ok, msg = publish_video(url, caption)
    print(f"  {msg}")
    if ok:
        ok_count += 1
        if i < len(REELS):
            d = random.randint(8, 15)
            print(f"  ⏳ {d}s...")
            time.sleep(d)

print(f"\n{'='*50}")
print(f"🏁 {ok_count}/{len(REELS)} publicados en https://instagram.com/rancho.raiz.2026")
