#!/usr/bin/env python3
"""Extract image URLs from Instagram profile."""
import json
import urllib.request
import sys

url = "https://i.instagram.com/api/v1/users/web_profile_info/?username=ranchoraiz.barreal"
req = urllib.request.Request(url, headers={"User-Agent": "Instagram 100.0.0.0.0"})

try:
    resp = urllib.request.urlopen(req, timeout=15)
    raw = resp.read().decode('utf-8', errors='replace')
    
    # Fix common JSON issues from Instagram
    data = json.loads(raw, strict=False)
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)

user = data['data']['user']
posts = user['edge_owner_to_timeline_media']['edges']

print(f"Profile: @{user['username']} — {user['full_name']}")
print(f"{user['edge_followed_by']['count']} followers, {user['edge_follow']['count']} following")
print(f"Posts: {len(posts)}\n")

all_images = []

for i, post in enumerate(posts):
    node = post['node']
    captions = node.get('edge_media_to_caption', {}).get('edges', [])
    caption = captions[0]['node']['text'] if captions else ''
    shortcode = node.get('shortcode', 'N/A')
    typename = node.get('__typename', 'N/A')
    has_video = node.get('is_video', False)
    tagged = node.get('edge_media_to_tagged_user', {}).get('edges', [])
    has_people_tags = len(tagged) > 0
    display_url = node.get('display_url', '')

    print(f"POST {i+1}: @{shortcode} ({typename}){' 📹' if has_video else ''}{' 👥' if has_people_tags else ''}")
    desc = caption.replace('\n', ' | ')[:120]
    print(f"  {desc}")

    if typename == 'GraphSidecar':
        children = node.get('edge_sidecar_to_children', {}).get('edges', [])
        for j, child in enumerate(children):
            cn = child['node']
            if not cn.get('is_video', False):
                img_url = cn.get('display_url', '')
                all_images.append({
                    'url': img_url,
                    'caption': caption,
                    'shortcode': shortcode,
                    'index': j+1,
                    'has_tags': has_people_tags
                })
    elif not has_video:
        all_images.append({
            'url': display_url,
            'caption': caption,
            'shortcode': shortcode,
            'index': 0,
            'has_tags': has_people_tags
        })

print(f"\n{'='*80}")
print(f"TOTAL IMAGES: {len(all_images)}")
print(f"{'='*80}")

for img in all_images:
    tag = " [TIENE PERSONAS ETIQUETADAS]" if img['has_tags'] else ""
    print(f"\n{img['shortcode']}#{img['index']}{tag}")
    print(f"  {img['caption'][:120]}")
    print(f"  URL: {img['url']}")
