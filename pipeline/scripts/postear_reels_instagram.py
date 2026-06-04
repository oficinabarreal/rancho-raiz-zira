#!/usr/bin/env python3
"""Postear los 5 Zira Reels a Instagram como REELS."""
import os, sys, time, random, requests
from pathlib import Path

sys.path.insert(0, "/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3")
from dotenv import load_dotenv
load_dotenv("/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3/.env")

TOKEN = os.environ["CRM_INSTAGRAM_TOKEN"]
USER_ID = os.environ["CRM_INSTAGRAM_USER_ID"]
BASE_URL = "https://raw.githubusercontent.com/oficinabarreal/rancho-raiz-zira/main/assets/zira/completos"

REELS = [
    {
        "estilo": "juguetona", "emoji": "💦",
        "frase": "El agua me llama, el sol me despierta.",
        "tags": ["zira", "juguetona", "pileta", "RanchoRaíz"],
    },
    {
        "estilo": "zen", "emoji": "🧘",
        "frase": "En el silencio de los Andes encuentro mi centro.",
        "tags": ["zira", "zen", "silencio", "andes"],
    },
    {
        "estilo": "magica", "emoji": "✨",
        "frase": "Cada atardecer es una promesa de un nuevo amanecer.",
        "tags": ["zira", "magica", "atardecer", "magia"],
    },
    {
        "estilo": "viva", "emoji": "🌿",
        "frase": "Verde que te quiero verde. Los Andes me enseñaron a respirar.",
        "tags": ["zira", "viva", "naturaleza", "verde"],
    },
    {
        "estilo": "clasica", "emoji": "🏔️",
        "frase": "Las montañas me criaron, el viento me peinó.",
        "tags": ["zira", "clasica", "montaña", "andes"],
    },
]

def post_reel(video_filename, data):
    """Postear un REEL en Instagram."""
    video_url = f"{BASE_URL}/{video_filename}"
    
    caption = (
        f'{data["emoji"]} Zira {data["estilo"].capitalize()}  \n'
        f'🎵 "{data["frase"]}"\n\n'
        f"#Zira #{data['estilo'].capitalize()} #{' #'.join(t.capitalize() for t in data['tags'][1:])} #RanchoRaíz"
    )
    
    print(f"     Video URL: {video_url}")
    
    # 1. Crear container REELS
    r = requests.post(
        f"https://graph.facebook.com/v22.0/{USER_ID}/media",
        data={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "access_token": TOKEN,
        },
        timeout=30,
    )
    if not r.ok:
        raise Exception(f"Error creating REEL: {r.status_code} {r.text}")
    
    creation_id = r.json()["id"]
    print(f"     Container: {creation_id}")
    
    # 2. Esperar procesamiento (más que IMAGE)
    for attempt in range(15):
        time.sleep(4)
        sr = requests.get(
            f"https://graph.facebook.com/v22.0/{creation_id}?fields=status_code&access_token={TOKEN}",
            timeout=15,
        )
        status = sr.json().get("status_code", "") if sr.ok else ""
        print(f"     Status: {status}")
        if status == "FINISHED":
            break
    else:
        raise Exception("REEL never finished processing")
    
    # 3. Publicar
    r = requests.post(
        f"https://graph.facebook.com/v22.0/{USER_ID}/media_publish",
        data={"creation_id": creation_id, "access_token": TOKEN},
        timeout=30,
    )
    if not r.ok:
        raise Exception(f"Error publishing REEL: {r.status_code} {r.text}")
    
    return r.json().get("id")

print(f"🎬 Posteando 5 Zira Reels a Instagram...\n")

for i, reel in enumerate(REELS, 1):
    filename = f"zira_{reel['estilo']}_reel.mp4"
    print(f"  [{i}/5] {reel['estilo'].upper()} — \"{reel['frase'][:40]}...\"")
    
    try:
        media_id = post_reel(filename, reel)
        print(f"     ✅ Publicado! ID: {media_id}")
    except Exception as e:
        print(f"     ❌ Error: {e}")
    
    if i < len(REELS):
        delay = random.randint(10, 15)
        print(f"     ⏱  Esperando {delay}s...")
        time.sleep(delay)

print(f"\n🏁 5 Reels publicados!")
