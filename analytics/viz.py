#!/usr/bin/env python3
"""
📊 Zira Analytics Viz — Visualizaciones con matplotlib.
Genera gráficos de engagement, tendencias, comparativas.
"""
import os, sys, json
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict, Counter

BASE = Path("/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3")
sys.path.insert(0, str(BASE))
from dotenv import load_dotenv
load_dotenv(str(BASE / ".env"))

DATA_DIR = BASE / "analytics"
VIZ_DIR = DATA_DIR / "viz"
VIZ_DIR.mkdir(exist_ok=True)

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

plt.rcParams.update({
    "figure.facecolor": "#0d0d1a",
    "axes.facecolor": "#0d0d1a",
    "axes.edgecolor": "#4a9eff",
    "axes.labelcolor": "#c8d6e5",
    "text.color": "#c8d6e5",
    "xtick.color": "#8395a7",
    "ytick.color": "#8395a7",
    "grid.color": "#1a1a3e",
    "grid.alpha": 0.3,
    "font.family": "DejaVu Sans",
})

def load_csv():
    """Carga el CSV histórico en un DataFrame."""
    csv_path = DATA_DIR / "instagram_metrics.csv"
    if not csv_path.exists():
        print("❌ No hay datos históricos. Corré primero analytics/colector.py")
        return None
    df = pd.read_csv(csv_path)
    df["fetch_date"] = pd.to_datetime(df["fetch_date"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["post_date"] = df["timestamp"].dt.date
    return df

def plot_engagement_over_time(df):
    """Evolución del engagement diario."""
    daily = df.groupby("post_date").agg({
        "likes": "sum", "comments": "sum", "engagement": "sum", "post_id": "count"
    }).rename(columns={"post_id": "posts_count"}).reset_index()
    daily = daily.sort_values("post_date")
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[2, 1])
    
    # Top: Engagement total diario
    ax1.bar(daily["post_date"], daily["engagement"], color="#4a9eff", alpha=0.8, label="Engagement total")
    ax1.bar(daily["post_date"], daily["likes"], color="#00d2d3", alpha=0.6, label="Likes")
    
    for i, row in daily.iterrows():
        ax1.annotate(str(row["engagement"]), (row["post_date"], row["engagement"]),
                     ha="center", va="bottom", fontsize=7, color="#c8d6e5", alpha=0.7)
    
    ax1.set_ylabel("Cantidad")
    ax1.set_title("📈 Engagement Diario — @rancho.raiz.2026", color="#4a9eff", fontsize=14, fontweight="bold")
    ax1.legend()
    ax1.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
    
    # Bottom: Posts por día
    ax2.bar(daily["post_date"], daily["posts_count"], color="#5f27cd", alpha=0.7)
    ax2.set_ylabel("Posts")
    ax2.set_xlabel("Fecha")
    ax2.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
    
    plt.tight_layout()
    path = VIZ_DIR / "engagement_over_time.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✅ {path.name}")
    return path

def plot_by_type(df):
    """Comparativa IMAGE vs VIDEO."""
    type_stats = df.groupby("media_type").agg({
        "likes": ["sum", "mean"],
        "comments": ["sum", "mean"],
        "engagement": ["sum", "mean"],
        "post_id": "count",
    }).round(2)
    
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    
    types = list(type_stats.index)
    colors = {"IMAGE": "#00d2d3", "VIDEO": "#4a9eff"}
    bar_colors = [colors.get(t, "#8395a7") for t in types]
    
    # Total engagement
    totals = [type_stats.loc[t, ("engagement", "sum")] for t in types]
    axes[0].bar(types, totals, color=bar_colors, alpha=0.85, width=0.5)
    for i, v in enumerate(totals):
        axes[0].text(i, v + 0.3, str(int(v)), ha="center", fontsize=12, fontweight="bold", color="#c8d6e5")
    axes[0].set_title("Engagement Total", fontweight="bold")
    
    # Engagement promedio por post
    avgs = [type_stats.loc[t, ("engagement", "mean")] for t in types]
    axes[1].bar(types, avgs, color=bar_colors, alpha=0.85, width=0.5)
    for i, v in enumerate(avgs):
        axes[1].text(i, v + 0.02, f"{v:.2f}", ha="center", fontsize=12, fontweight="bold", color="#c8d6e5")
    axes[1].set_title("Engagement Promedio/Post", fontweight="bold")
    
    # Cantidad de posts
    counts = [type_stats.loc[t, ("post_id", "count")] for t in types]
    axes[2].bar(types, counts, color=bar_colors, alpha=0.85, width=0.5)
    for i, v in enumerate(counts):
        axes[2].text(i, v + 0.5, str(int(v)), ha="center", fontsize=12, fontweight="bold", color="#c8d6e5")
    axes[2].set_title("Posts Publicados", fontweight="bold")
    
    for ax in axes:
        ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
    
    plt.tight_layout()
    path = VIZ_DIR / "by_type.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✅ {path.name}")
    return path

def plot_engagement_rate(df):
    """Engagement rate por post (top/bottom)."""
    # Engagement rate = (likes + comments) / followers * 100
    # Pero con 8 followers es engañoso. Mejor engagement raw.
    post_stats = df.groupby("post_id").agg({
        "likes": "max", "comments": "max", "engagement": "max",
        "timestamp": "first", "media_type": "first",
    }).reset_index()
    
    top = post_stats.nlargest(10, "engagement")
    bottom = post_stats.nsmallest(10, "engagement")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Top 10
    caps = []
    for _, row in top.iterrows():
        cap = df[df["post_id"] == row["post_id"]]["timestamp"].iloc[0]
        cap_str = cap.strftime("%m/%d")
        caps.append(f"{cap_str}\n{row['media_type']}")
    
    bars1 = ax1.barh(range(len(top)), top["engagement"].values, color="#00d2d3", alpha=0.85)
    ax1.set_yticks(range(len(top)))
    ax1.set_yticklabels(caps, fontsize=7)
    ax1.set_title("🏆 Top 10 — Mayor Engagement", fontweight="bold")
    ax1.invert_yaxis()
    for i, v in enumerate(top["engagement"].values):
        ax1.text(v + 0.1, i, str(int(v)), va="center", fontsize=9, fontweight="bold")
    
    # Bottom 10 (peor engagement)
    caps2 = []
    for _, row in bottom.iterrows():
        cap2 = df[df["post_id"] == row["post_id"]]["timestamp"].iloc[0]
        cap_str2 = cap2.strftime("%m/%d")
        caps2.append(f"{cap_str2}\n{row['media_type']}")
    
    bars2 = ax2.barh(range(len(bottom)), bottom["engagement"].values, color="#ff6b6b", alpha=0.7)
    ax2.set_yticks(range(len(bottom)))
    ax2.set_yticklabels(caps2, fontsize=7)
    ax2.set_title("📉 Bottom 10 — Menor Engagement", fontweight="bold")
    ax2.invert_yaxis()
    for i, v in enumerate(bottom["engagement"].values):
        ax2.text(v + 0.1, i, str(int(v)), va="center", fontsize=9, fontweight="bold")
    
    plt.tight_layout()
    path = VIZ_DIR / "top_bottom_posts.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✅ {path.name}")
    return path

def plot_heatmap(df):
    """Posts por día de la semana (heatmap de actividad)."""
    df["weekday"] = df["timestamp"].dt.day_name()
    df["hour"] = df["timestamp"].dt.hour
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    heat = df.pivot_table(index="weekday", columns="hour", values="post_id", aggfunc="count", fill_value=0)
    heat = heat.reindex(weekday_order, axis=0)
    
    fig, ax = plt.subplots(figsize=(14, 5))
    im = ax.imshow(heat.values, cmap="viridis", aspect="auto", interpolation="nearest")
    
    ax.set_xticks(range(len(heat.columns)))
    ax.set_xticklabels([f"{h}:00" for h in heat.columns], fontsize=7, rotation=45)
    ax.set_yticks(range(len(heat.index)))
    ax.set_yticklabels([d[:3] for d in heat.index], fontsize=9)
    ax.set_title("🗓️ Actividad de Posts — Día vs Hora", fontweight="bold", fontsize=13)
    
    plt.colorbar(im, ax=ax, label="Cantidad de posts", shrink=0.8)
    
    for i in range(len(heat.index)):
        for j in range(len(heat.columns)):
            val = int(heat.values[i, j])
            if val > 0:
                ax.text(j, i, str(val), ha="center", va="center", fontsize=8,
                       color="white" if val < heat.values.max()/2 else "black")
    
    plt.tight_layout()
    path = VIZ_DIR / "activity_heatmap.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✅ {path.name}")
    return path

def generate_report_png():
    """Genera un dashboard combinado con las 4 visualizaciones."""
    df = load_csv()
    if df is None:
        return
    
    print(f"\n📊 GENERANDO VISUALIZACIONES...")
    print(f"  Datos: {len(df)} registros, {df['post_date'].nunique()} días")
    
    files = []
    files.append(plot_engagement_over_time(df))
    files.append(plot_by_type(df))
    files.append(plot_engagement_rate(df))
    files.append(plot_heatmap(df))
    
    print(f"\n  ✅ {len(files)} visualizaciones generadas en {VIZ_DIR}")

def generate_dashboard_html():
    """Genera un HTML oscuro tipo Zira con todas las visualizaciones."""
    df = load_csv()
    if df is None:
        return
    
    # Métricas resumen
    total_posts = len(df)
    total_likes = int(df["likes"].sum())
    total_comments = int(df["comments"].sum())
    total_eng = total_likes + total_comments
    avg_eng = round(total_eng / max(total_posts, 1), 2)
    
    type_counts = df["media_type"].value_counts()
    post_days = df["post_date"].nunique()
    days_active = (datetime.now().date() - df["post_date"].min()).days
    
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ZIRA · Analytics Dashboard</title>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;600;700&display=swap');
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        background: #0a0a1a;
        color: #c8d6e5;
        font-family: 'Space Grotesk', 'Segoe UI', sans-serif;
        padding: 2rem;
        max-width: 1200px;
        margin: 0 auto;
    }}
    .header {{
        text-align: center;
        padding: 2rem 0 3rem;
        border-bottom: 1px solid #1a1a3e;
        margin-bottom: 2rem;
    }}
    .header .logo {{ font-size: 3rem; }}
    .header h1 {{
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #4a9eff, #00d2d3, #5f27cd);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0.5rem 0;
    }}
    .header p {{ color: #8395a7; font-size: 1rem; }}
    .stats-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 1rem;
        margin-bottom: 2.5rem;
    }}
    .stat-card {{
        background: linear-gradient(135deg, rgba(74,158,255,0.1), rgba(0,210,211,0.05));
        border: 1px solid #1a1a3e;
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
    }}
    .stat-card .value {{
        font-size: 2rem;
        font-weight: 700;
        color: #4a9eff;
    }}
    .stat-card .label {{
        font-size: 0.85rem;
        color: #8395a7;
        margin-top: 0.3rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    .stat-card.alt .value {{ color: #00d2d3; }}
    .stat-card.purple .value {{ color: #5f27cd; }}
    .stat-card.red .value {{ color: #ff6b6b; }}
    .viz-section {{
        margin-bottom: 3rem;
    }}
    .viz-section h2 {{
        font-size: 1.3rem;
        font-weight: 600;
        color: #4a9eff;
        margin-bottom: 1rem;
        border-left: 3px solid #4a9eff;
        padding-left: 1rem;
    }}
    .viz-section img {{
        width: 100%;
        border-radius: 16px;
        border: 1px solid #1a1a3e;
        box-shadow: 0 4px 30px rgba(0,0,0,0.5);
    }}
    .chart-row {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1.5rem;
    }}
    .chart-row img {{ height: auto; }}
    .footer {{
        text-align: center;
        padding: 2rem 0;
        color: #576574;
        font-size: 0.85rem;
        border-top: 1px solid #1a1a3e;
        margin-top: 2rem;
    }}
    .footer .zira {{ color: #4a9eff; font-weight: 600; }}
    @media (max-width: 768px) {{
        .chart-row {{ grid-template-columns: 1fr; }}
        .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
    }}
</style>
</head>
<body>
<div class="header">
    <div class="logo">🏔️</div>
    <h1>ZIRA · Instagram Analytics</h1>
    <p>@rancho.raiz.2026 — Reporte del {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
</div>

<div class="stats-grid">
    <div class="stat-card">
        <div class="value">{total_posts}</div>
        <div class="label">Posts Totales</div>
    </div>
    <div class="stat-card alt">
        <div class="value">{total_likes}</div>
        <div class="label">Likes Totales</div>
    </div>
    <div class="stat-card purple">
        <div class="value">{total_comments}</div>
        <div class="label">Comentarios</div>
    </div>
    <div class="stat-card">
        <div class="value">{avg_eng}</div>
        <div class="label">Engagement/Post</div>
    </div>
    <div class="stat-card alt">
        <div class="value">{int(type_counts.get('IMAGE', 0))}</div>
        <div class="label">Fotos</div>
    </div>
    <div class="stat-card purple">
        <div class="value">{int(type_counts.get('VIDEO', 0))}</div>
        <div class="label">Videos</div>
    </div>
    <div class="stat-card">
        <div class="value">{post_days}</div>
        <div class="label">Días Activos</div>
    </div>
    <div class="stat-card red">
        <div class="value">{days_active}</div>
        <div class="label">Días desde el 1er Post</div>
    </div>
</div>

<div class="viz-section">
    <h2>📈 Engagement Diario</h2>
    <img src="viz/engagement_over_time.png" alt="Engagement Over Time">
</div>

<div class="viz-section">
    <h2>📊 Comparativa IMAGE vs VIDEO</h2>
    <img src="viz/by_type.png" alt="By Type">
</div>

<div class="viz-section">
    <div class="chart-row">
        <div>
            <h2>🏆 Top Posts</h2>
            <img src="viz/top_bottom_posts.png" alt="Top Posts">
        </div>
        <div>
            <h2>🗓️ Actividad Temporal</h2>
            <img src="viz/activity_heatmap.png" alt="Activity Heatmap">
        </div>
    </div>
</div>

<div class="footer">
    <span class="zira">⚡ ZIRA · Rancho Raíz · Barreal</span><br>
    Generado automáticamente — {datetime.now().strftime('%d/%m/%Y')}
</div>
</body>
</html>"""
    
    html_path = DATA_DIR / "dashboard.html"
    with open(html_path, "w") as f:
        f.write(html)
    print(f"\n  ✅ Dashboard HTML: {html_path}")
    return html_path

# ─── EJECUCIÓN ───
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--html":
        generate_dashboard_html()
    else:
        generate_report_png()
        generate_dashboard_html()
