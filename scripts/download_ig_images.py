#!/usr/bin/env python3
"""Download remaining Instagram images and set up everything."""
import json, os, sys
sys.path.insert(0, '/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3')
from hermes_tools import terminal
from crm.google_auth import get_service

BASE = '/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3'
ASSETS = os.path.join(BASE, 'assets/images')
os.makedirs(ASSETS, exist_ok=True)

# Read Instagram JSON
with open(os.path.join(BASE, 'scripts/ig_raw.json')) as f:
    data = json.loads(f.read(), strict=False)

posts = data['data']['user']['edge_owner_to_timeline_media']['edges']
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

print(f"Total clean images: {len(clean)}")

# Download ALL clean images (up to 10)
images_map = {}
for i, (url, sc, cap) in enumerate(clean[:10]):
    fname = f"ig_{sc}_{i+1}.jpg"
    path = os.path.join(ASSETS, fname)
    if not os.path.exists(path):
        r = terminal(f'curl -sL -H "User-Agent: Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36" -H "Referer: https://www.instagram.com/" "{url}" -o assets/images/{fname}', timeout=30, workdir=BASE)
    size = os.path.getsize(path)
    cap_short = cap.replace('\n', ' ')[:80]
    images_map[fname] = {'caption': cap_short, 'shortcode': sc, 'size': size}
    print(f"  {fname} ({size} bytes) — {cap_short}")

# Delete old generic names
for old in ['ig_1.jpg', 'ig_2.jpg', 'ig_3.jpg', 'ig_4.jpg', 'ig_5.jpg', 'ig_6.jpg']:
    p = os.path.join(ASSETS, old)
    if os.path.exists(p):
        os.remove(p)
        print(f"  Removed old: {old}")

print(f"\nImages ready in assets/images/")
for fname, info in images_map.items():
    print(f"  https://oficinabarreal.github.io/rancho-raiz-zira/assets/images/{fname}")
    print(f"    {info['caption']}")
