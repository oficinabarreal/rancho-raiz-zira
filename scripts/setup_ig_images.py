#!/usr/bin/env python3
"""Download Instagram images, push to repo, and update Sheet."""
import json, os, subprocess, sys, urllib.request

BASE = '/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3'
ASSETS = os.path.join(BASE, 'assets/images')
os.makedirs(ASSETS, exist_ok=True)

# Read Instagram JSON
with open(os.path.join(BASE, 'scripts/ig_raw.json')) as f:
    data = json.loads(f.read(), strict=False)

posts = data['data']['user']['edge_owner_to_timeline_media']['edges']

# Collect non-people images
clean = []
for post in posts:
    node = post['node']
    tagged = node.get('edge_media_to_tagged_user', {}).get('edges', [])
    if tagged:
        continue
    typename = node.get('__typename', '')
    if typename == 'GraphSidecar':
        for child in node.get('edge_sidecar_to_children', {}).get('edges', []):
            cn = child['node']
            if not cn.get('is_video', False):
                url = cn.get('display_url', '')
                cap = node.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', '')
                clean.append((url, node['shortcode'], cap))
    elif not node.get('is_video', False):
        url = node.get('display_url', '')
        cap = node.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', '')
        clean.append((url, node['shortcode'], cap))

print(f"Total images without people tags: {len(clean)}")

# Download all
images = []
for i, (url, sc, cap) in enumerate(clean):
    fname = f"{sc}_{i+1}.jpg"
    path = os.path.join(ASSETS, fname)
    if not os.path.exists(path):
        cmd = f'curl -sL -H "User-Agent: Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36" -H "Referer: https://www.instagram.com/" "{url}" -o "{path}"'
        subprocess.run(cmd, shell=True, timeout=30, cwd=BASE)
    size = os.path.getsize(path)
    cap_short = cap.replace('\n', ' ')[:100]
    url_public = f"https://oficinabarreal.github.io/rancho-raiz-zira/assets/images/{fname}"
    images.append({'file': fname, 'url': url_public, 'caption': cap_short, 'size': size})
    print(f"  {fname} ({size}b)")

print(f"\nAll images saved to {ASSETS}/")

# Now update the Google Sheet galeria tab
sys.path.insert(0, BASE)
from crm.google_auth import get_service

svc = get_service('sheets', 'v4', 'sheets')
SHEET_ID = "1dd2sVgDAHPITFcE83QGP00eTNs8qiv1pFT3PmJaNikI"

# Build galeria rows: [nombre, descripcion, imagen_url, activo, orden]
galeria_rows = [['nombre', 'descripcion', 'imagen_url', 'activo', 'orden']]

for idx, img in enumerate(images):
    desc = img['caption'] if img['caption'] else f'Foto {idx+1}'
    galeria_rows.append([
        f'Foto {idx+1}',
        desc,
        img['url'],
        'SI',
        str(idx + 1)
    ])

# Update galeria tab
result = svc.spreadsheets().values().update(
    spreadsheetId=SHEET_ID,
    range="'galeria'!A1:E50",
    valueInputOption='USER_ENTERED',
    body={'values': galeria_rows}
).execute()
print(f"\n✅ Galería actualizada: {result.get('updatedCells', 0)} celdas")

# Also assign first room image to habitaciones
# Read habitaciones tab
habs = svc.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range="'habitaciones'!A1:I50"
).execute()
hab_rows = habs.get('values', [])

if len(hab_rows) > 1:
    # Update imagen_url for each habitacion (column E = 5th column)
    room_imgs = [img for img in images if 'madera' in img['caption'].lower() or 'detalle' in img['caption'].lower() or 'hogar' in img['caption'].lower()]
    for i in range(1, len(hab_rows)):
        if i - 1 < len(room_imgs):
            hab_rows[i][4] = room_imgs[i-1]['url']  # imagen_url column
    
    result2 = svc.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range="'habitaciones'!A1:I50",
        valueInputOption='USER_ENTERED',
        body={'values': hab_rows}
    ).execute()
    print(f"✅ Habitaciones actualizadas: {result2.get('updatedCells', 0)} celdas")

print("\n✅ Done! Run 'python scripts/generar_web_cms.py' to regenerate the site.")
