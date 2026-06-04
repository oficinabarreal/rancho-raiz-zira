#!/usr/bin/env python3
"""
📊 Zira Analytics — Sistema de análisis de datos de Instagram.
Recolecta, almacena y visualiza métricas de @rancho.raiz.2026.
Estilo Cambridge Analytics: seguimiento de engagement, crecimiento, tendencias.
"""
import os, sys, json, csv, time
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

sys.path.insert(0, "/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3")
from dotenv import load_dotenv
load_dotenv("/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3/.env")

TOKEN = os.environ["CRM_INSTAGRAM_TOKEN"]
USER_ID = os.environ["CRM_INSTAGRAM_USER_ID"]
BASE = Path("/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3")

DATA_DIR = BASE / "analytics"
DATA_DIR.mkdir(exist_ok=True)
CSV_PATH = DATA_DIR / "instagram_metrics.csv"
SNAPSHOT_PATH = DATA_DIR / "latest_snapshot.json"

import requests

def fetch_all_posts():
    """Obtiene todos los posts del account con sus métricas."""
    posts = []
    url = f"https://graph.facebook.com/v22.0/{USER_ID}/media"
    params = {
        "fields": "id,media_type,caption,timestamp,like_count,comments_count,media_product_type",
        "access_token": TOKEN,
        "limit": 100,
    }
    
    while url:
        r = requests.get(url, params=params if "?" not in url else {}, timeout=30)
        if not r.ok:
            print(f"  Error: {r.status_code} {r.text[:200]}")
            break
        data = r.json()
        posts.extend(data.get("data", []))
        url = data.get("paging", {}).get("next", "")
        params = {}  # URL already has params in next
    
    return posts

def compute_metrics(posts):
    """Calcula métricas agregadas."""
    now = datetime.now(timezone.utc)
    
    # Clasificar posts
    by_type = defaultdict(list)
    by_day = defaultdict(list)
    
    for p in posts:
        ts = p.get("timestamp", "")
        day = ts[:10] if ts else "unknown"
        mtype = p.get("media_type", "UNKNOWN")
        by_type[mtype].append(p)
        by_day[day].append(p)
    
    total = len(posts)
    total_likes = sum(p.get("like_count", 0) for p in posts)
    total_comments = sum(p.get("comments_count", 0) for p in posts)
    total_engagement = total_likes + total_comments
    
    print(f"\n📈 MÉTRICAS AGREGADAS (@rancho.raiz.2026)")
    print(f"  {'='*40}")
    print(f"  Total posts:      {total}")
    print(f"  Total likes:      {total_likes}")
    print(f"  Total comments:   {total_comments}")
    print(f"  Total engagement: {total_engagement}")
    print(f"  Engagement/post:  {total_engagement/max(total,1):.1f}")
    print(f"  Likes/post:       {total_likes/max(total,1):.1f}")
    
    print(f"\n  Por tipo:")
    for t, plist in sorted(by_type.items()):
        t_likes = sum(p.get("like_count", 0) for p in plist)
        t_coms = sum(p.get("comments_count", 0) for p in plist)
        print(f"    {t:10s}: {len(plist):3d} posts, {t_likes} likes, {t_coms} coms")
    
    # Engagement por día (últimos 7)
    last_week = sorted(by_day.keys())[-7:]
    print(f"\n  Engagement últimos días:")
    for day in last_week:
        d_posts = by_day[day]
        d_likes = sum(p.get("like_count", 0) for p in d_posts)
        d_coms = sum(p.get("comments_count", 0) for p in d_posts)
        print(f"    {day}: {len(d_posts):2d} posts, {d_likes} likes, {d_coms} coms")
    
    # Top posts
    sorted_posts = sorted(posts, key=lambda p: p.get("like_count", 0) + p.get("comments_count", 0), reverse=True)
    print(f"\n  🏆 TOP 5 POSTS (por engagement):")
    for i, p in enumerate(sorted_posts[:5], 1):
        eng = p.get("like_count", 0) + p.get("comments_count", 0)
        cap = (p.get("caption", "") or "")[:60].replace("\n", " ")
        print(f"    {i}. [{p['media_type']}] eng={eng} | {p['timestamp'][:16]} | {cap}")
    
    return {
        "timestamp": now.isoformat(),
        "total_posts": total,
        "total_likes": total_likes,
        "total_comments": total_comments,
        "total_engagement": total_engagement,
        "engagement_per_post": round(total_engagement / max(total, 1), 2),
        "likes_per_post": round(total_likes / max(total, 1), 2),
    }

def save_snapshot(posts, metrics):
    """Guarda snapshot completo en JSON."""
    snapshot = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
        "posts_count": len(posts),
        "posts_by_type": dict((k, len(v)) for k, v in defaultdict(list, 
            [(t, [p for p in posts if p.get("media_type") == t]) for t in set(p.get("media_type", "?") for p in posts)]
        ).items()),
    }
    with open(SNAPSHOT_PATH, "w") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)
    return SNAPSHOT_PATH

def update_csv(posts):
    """Append metrics al CSV histórico."""
    now = datetime.now(timezone.utc)
    is_new = not CSV_PATH.exists()
    
    with open(CSV_PATH, "a", newline="") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(["fetch_date", "post_id", "media_type", "timestamp", "likes", "comments", "engagement"])
        
        for p in posts:
            ts = p.get("timestamp", "")[:19]
            eng = p.get("like_count", 0) + p.get("comments_count", 0)
            writer.writerow([
                now.isoformat()[:19],
                p["id"],
                p.get("media_type", ""),
                ts,
                p.get("like_count", 0),
                p.get("comments_count", 0),
                eng,
            ])

# ─── EJECUCIÓN ───
print("📊 ZIRA ANALYTICS — Recolectando datos de Instagram...")
print(f"  Cuenta: @rancho.raiz.2026")
print(f"  Fecha:  {datetime.now().strftime('%Y-%m-%d %H:%M')}")

print(f"\n📥 Obteniendo posts...")
posts = fetch_all_posts()
print(f"  {len(posts)} posts recolectados")

metrics = compute_metrics(posts)

snap = save_snapshot(posts, metrics)
update_csv(posts)
print(f"\n💾 Datos guardados:")
print(f"  Snapshot: {snap}")
print(f"  CSV histórico: {CSV_PATH}")
print(f"  Filas en CSV: {sum(1 for _ in open(CSV_PATH)) - 1 if CSV_PATH.exists() else 0}")
