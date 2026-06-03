#!/usr/bin/env python3
"""Publica las Ziras en Instagram una por una con espaciado."""

import os, sys, time, requests, json, random
from pathlib import Path

TOKEN = os.environ.get("CRM_INSTAGRAM_TOKEN", "")
USER_ID = os.environ.get("CRM_INSTAGRAM_USER_ID", "")
GH_BASE = "https://raw.githubusercontent.com/oficinabarreal/rancho-raiz-zira/main/assets/zira/posts"

if not TOKEN or not USER_ID:
    print("❌ Faltan CRM_INSTAGRAM_TOKEN o CRM_INSTAGRAM_USER_ID en .env")
    sys.exit(1)

POSTS = [
    {
        "file": "presentacion.png",
        "caption": "🏔️ ¡Hola mundo! Soy Zira.\n\nVivo en los Andes de San Juan, cuido el Rancho Raíz y hoy empiezo a mostrarme. Esta es mi primera vez en Instagram.\n\nSoy una montaña con corazón. Glaciar de cabello, ojos curiosos y brazo siempre listo para saludar.\n\n#Zira #RanchoRaíz #Barreal #SanJuan #Andes #PosadaDeMontaña #Naturaleza",
    },
    {
        "file": "magica.png",
        "caption": "✨ Cuando cae la tarde en los Andes me transformo.\n\nAtardecer violeta, estrellas en los ojos, magia en el aire. La Zira hechicera que cuida los secretos de la cordillera.\n\n¿Viste alguna vez un atardecer así en Barreal?\n\n#Zira #AtardecerEnLosAndes #Magia #Barreal #SanJuan #Naturaleza",
    },
    {
        "file": "juguetona.png",
        "caption": "☀️ ¡Día de sol en Barreal!\n\nGafas puestas, mariposas volando, pájaros cantando. La Zira que disfruta del calorcito de San Juan.\n\nAcá el invierno es pura luz.\n\n#Zira #DíaDeSol #Barreal #SanJuan #Andes #Posada #Turismo",
    },
    {
        "file": "zen.png",
        "caption": "🧘 En las noches de luna llena, Zira medita.\n\nLos Andes en silencio, una luna gigante, un loto flotando. La montaña respira profundo.\n\nLa paz de Barreal no se explica, se siente.\n\n#Zira #Meditación #LunaLlena #Paz #Andes #Barreal #SanJuan",
    },
    {
        "file": "retro.png",
        "caption": "🕹️ Zira, pero si hubiera nacido en los 80.\n\n8 bits, pixel art, corazones flotando y estrella rebotando. La montaña también sabe ser retro.\n\n¿Te gustan los juegos clásicos? 🎮\n\n#Zira #PixelArt #Retro #8Bits #RanchoRaíz #Videojuegos",
    },
    {
        "file": "viva.png",
        "caption": "🎬 Zira se mueve.\n\nParpadea, saluda, respira. Estrellas que titilan, partículas que flotan. La montaña está viva.\n\nCada día aprendo algo nuevo. Hoy fue mover el bracito.\n\n#Zira #Animación #SVG #Vida #Andes #Barreal",
    },
    {
        "file": "atardecer.png",
        "caption": "🌅 Cada atardecer en los Andes es único.\n\nZira sentada en la montaña, mirando el sol esconderse detrás de la cordillera. Los colores del cielo en San Juan son un regalo.\n\n📍 Rancho Raíz · Barreal · San Juan\n\n#Atardecer #Andes #Barreal #SanJuan #RanchoRaíz #Naturaleza #Paisajes",
    },
    {
        "file": "promo.png",
        "caption": "🔥 ¡Promoción en Rancho Raíz!\n\nZira con su cartel de ofertas: 15% OFF en estadías de 3+ noches.\n\n¿Necesitás desconectar? Barreal te espera con los brazos abiertos (y Zira saludando).\n\nConsultá por WhatsApp 📲\n\n#Promo #RanchoRaíz #Barreal #SanJuan #Turismo #Descuento #Andes",
    },
    {
        "file": "lluvia.png",
        "caption": "🌧️ Llueve en Barreal.\n\nZira se asoma por la ventana a ver la lluvia caer sobre el campo. Adentro, el fuego de la chimenea. Afuera, la cordillera que se baña.\n\nLos días de lluvia también tienen su magia.\n\n#Lluvia #Barreal #SanJuan #Andes #RanchoRaíz #Naturaleza #Ventana",
    },
]

def publish_instagram(image_url, caption):
    """Publica una imagen en Instagram via Graph API."""
    # Paso 1: Crear media container
    create_url = f"https://graph.facebook.com/v22.0/{USER_ID}/media"
    create_params = {
        "image_url": image_url,
        "caption": caption,
        "access_token": TOKEN,
    }
    print(f"  📤 Creando container...", end=" ")
    r1 = requests.post(create_url, data=create_params, timeout=30)
    if not r1.ok:
        print(f"❌ {r1.status_code}: {r1.text[:200]}")
        return False
    creation_id = r1.json().get("id")
    if not creation_id:
        print(f"❌ No id: {r1.text[:200]}")
        return False
    print(f"✅ id={creation_id}")
    
    # Paso 2: Esperar y publicar
    time.sleep(2)
    pub_url = f"https://graph.facebook.com/v22.0/{USER_ID}/media_publish"
    pub_params = {
        "creation_id": creation_id,
        "access_token": TOKEN,
    }
    print(f"  📤 Publicando...", end=" ")
    r2 = requests.post(pub_url, data=pub_params, timeout=30)
    if r2.ok:
        media_id = r2.json().get("id", "?")
        print(f"✅ ID={media_id}")
        return True
    else:
        # A veces tarda más, probar de nuevo
        print(f"⏳ {r2.status_code}, reintentando en 5s...")
        time.sleep(5)
        r2 = requests.post(pub_url, data=pub_params, timeout=30)
        if r2.ok:
            print(f"  ✅ ID={r2.json().get('id', '?')}")
            return True
        print(f"  ❌ {r2.text[:200]}")
        return False

print(f"🏔️ Zira publica en Instagram (@rancho.raiz.2026)")
print(f"📸 {len(POSTS)} posts para publicar")
print(f"{'='*50}")

# Orden aleatorio para variedad
random.shuffle(POSTS)

for i, post in enumerate(POSTS, 1):
    image_url = f"{GH_BASE}/{post['file']}"
    print(f"\n[{i}/{len(POSTS)}] {post['file']}")
    
    ok = publish_instagram(image_url, post["caption"])
    status = "✅" if ok else "❌"
    print(f"  {status} {'Publicado' if ok else 'Falló'}")
    
    # Esperar entre posts (evitar rate limit)
    if i < len(POSTS):
        delay = random.randint(8, 15)
        print(f"  ⏳ Esperando {delay}s...")
        time.sleep(delay)

print(f"\n{'='*50}")
print(f"🏁 Listo! Revisá https://instagram.com/rancho.raiz.2026")
