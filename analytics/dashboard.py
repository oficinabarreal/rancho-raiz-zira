#!/usr/bin/env python3
"""
Dashboard Zira Analytics — Genera HTML+JS con Chart.js.
No requiere matplotlib. Visualizaciones interactivas en el navegador.
"""
import os, sys, json
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

BASE = Path("/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3")
sys.path.insert(0, str(BASE))
from dotenv import load_dotenv
load_dotenv(str(BASE / ".env"))

TOKEN = os.environ.get("CRM_INSTAGRAM_TOKEN")
USER_ID = os.environ.get("CRM_INSTAGRAM_USER_ID")

DATA_DIR = BASE / "analytics"
VIZ_DIR = DATA_DIR / "viz"
VIZ_DIR.mkdir(exist_ok=True)

import pandas as pd

def load_csv():
    csv_path = DATA_DIR / "instagram_metrics.csv"
    if not csv_path.exists():
        print("❌ No hay datos. Corré primero analytics/colector.py")
        return None
    df = pd.read_csv(csv_path)
    df["fetch_date"] = pd.to_datetime(df["fetch_date"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["post_date"] = df["timestamp"].dt.date
    return df

def build_dashboard():
    df = load_csv()
    if df is None:
        return
    
    # ── Métricas clave ──
    total_posts = len(df)
    total_likes = int(df["likes"].sum())
    total_comments = int(df["comments"].sum())
    total_eng = total_likes + total_comments
    avg_eng = round(total_eng / max(total_posts, 1), 2)
    
    type_counts = df["media_type"].value_counts()
    img_count = int(type_counts.get("IMAGE", 0))
    vid_count = int(type_counts.get("VIDEO", 0))
    
    post_days = df["post_date"].nunique()
    first_date = df["post_date"].min()
    days_active = (datetime.now().date() - first_date).days
    
    # ── Datos para gráficos ──
    # Engagement diario
    daily = df.groupby("post_date").agg({
        "likes": "sum", "comments": "sum", "engagement": "sum", "post_id": "count"
    }).rename(columns={"post_id": "posts_count"}).reset_index().sort_values("post_date")
    
    daily_labels = [str(d) for d in daily["post_date"]]
    daily_eng = daily["engagement"].tolist()
    daily_likes = daily["likes"].tolist()
    daily_posts = daily["posts_count"].tolist()
    
    # Por tipo
    img_eng = int(df[df["media_type"] == "IMAGE"]["engagement"].sum()) if img_count else 0
    vid_eng = int(df[df["media_type"] == "VIDEO"]["engagement"].sum()) if vid_count else 0
    img_avg = round(img_eng / max(img_count, 1), 2)
    vid_avg = round(vid_eng / max(vid_count, 1), 2)
    
    # Top posts (engagement)
    post_stats = df.groupby("post_id").agg({
        "likes": "max", "comments": "max", "engagement": "max",
        "timestamp": "first", "media_type": "first",
    }).reset_index()
    top10 = post_stats.nlargest(10, "engagement")
    
    top_labels = []
    top_vals = []
    top_colors = []
    for _, row in top10.iterrows():
        ts = pd.Timestamp(row["timestamp"])
        label = f"{ts.strftime('%m/%d')} {row['media_type']}"
        top_labels.append(label)
        top_vals.append(int(row["engagement"]))
        top_colors.append("rgba(0, 210, 211, 0.8)" if row["media_type"] == "IMAGE" else "rgba(74, 158, 255, 0.8)")
    
    top_labels.reverse()
    top_vals.reverse()
    top_colors.reverse()
    
    # Heatmap data (weekday vs hour)
    df["weekday"] = df["timestamp"].dt.day_name()
    df["hour"] = df["timestamp"].dt.hour
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday_short = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    
    heat_grid = []
    total_heat = 0
    for i, wd in enumerate(weekday_order):
        row = []
        for h in range(24):
            count = len(df[(df["weekday"] == wd) & (df["hour"] == h)])
            row.append(count)
            total_heat += count
        heat_grid.append(row)
    
    heat_max = max(max(r) for r in heat_grid) if any(any(r) for r in heat_grid) else 1
    
    # Stats adicionales
    # Engagement por día de semana
    weekday_eng = df.groupby("weekday")["engagement"].sum().reindex(weekday_order).fillna(0)
    
    # Traducción nombres
    eng_labels_translated = {
        "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
        "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo"
    }
    
    # ── Generar HTML ──
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ZIRA · Analytics Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;600;700&display=swap');
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        background: #0a0a1a;
        color: #c8d6e5;
        font-family: 'Space Grotesk', 'Segoe UI', sans-serif;
        padding: 1.5rem;
        max-width: 1300px;
        margin: 0 auto;
    }}
    .header {{
        text-align: center;
        padding: 2rem 0 2.5rem;
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
    .header .sub {{ color: #8395a7; font-size: 0.95rem; }}
    .stats-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 0.8rem;
        margin-bottom: 2rem;
    }}
    .stat-card {{
        background: linear-gradient(135deg, rgba(74,158,255,0.08), rgba(0,210,211,0.03));
        border: 1px solid #1a1a3e;
        border-radius: 14px;
        padding: 1.2rem;
        text-align: center;
        transition: transform 0.2s;
    }}
    .stat-card:hover {{ transform: translateY(-2px); border-color: #4a9eff; }}
    .stat-card .value {{ font-size: 1.8rem; font-weight: 700; color: #4a9eff; }}
    .stat-card .label {{ font-size: 0.78rem; color: #8395a7; margin-top: 0.2rem; text-transform: uppercase; letter-spacing: 1px; }}
    .stat-card.alt .value {{ color: #00d2d3; }}
    .stat-card.purple .value {{ color: #5f27cd; }}
    .stat-card.red .value {{ color: #ff6b6b; }}
    .stat-card.gold .value {{ color: #feca57; }}
    .section {{
        background: rgba(13,13,26,0.7);
        border: 1px solid #1a1a3e;
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }}
    .section h2 {{
        font-size: 1.1rem;
        font-weight: 600;
        color: #4a9eff;
        margin-bottom: 1rem;
        border-left: 3px solid #4a9eff;
        padding-left: 0.8rem;
    }}
    .chart-container {{ position: relative; height: 300px; width: 100%; }}
    .chart-container.tall {{ height: 400px; }}
    .row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }}
    .heatmap-container {{ overflow-x: auto; }}
    .heatmap {{
        display: grid;
        grid-template-columns: 40px repeat(24, 1fr);
        gap: 2px;
        min-width: 700px;
    }}
    .heatmap .label {{
        font-size: 0.7rem;
        color: #8395a7;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        padding-right: 6px;
    }}
    .heatmap .hour-label {{
        font-size: 0.6rem;
        color: #576574;
        text-align: center;
    }}
    .heatmap .cell {{
        aspect-ratio: 1;
        border-radius: 3px;
        min-width: 22px;
        min-height: 22px;
    }}
    .heatmap .cell:hover {{ outline: 2px solid #4a9eff; cursor: pointer; }}
    .heatmap-legend {{ display: flex; align-items: center; gap: 0.5rem; margin-top: 0.8rem; font-size: 0.75rem; color: #8395a7; }}
    .heatmap-legend .bar {{ height: 12px; width: 120px; border-radius: 4px; background: linear-gradient(to right, #0d0d1a, #4a9eff, #00d2d3); }}
    .footer {{
        text-align: center;
        padding: 2rem 0;
        color: #576574;
        font-size: 0.8rem;
        border-top: 1px solid #1a1a3e;
        margin-top: 2rem;
    }}
    .footer .zira {{ color: #4a9eff; font-weight: 600; }}
    .update-badge {{
        display: inline-block;
        background: rgba(74,158,255,0.15);
        color: #4a9eff;
        border: 1px solid rgba(74,158,255,0.3);
        padding: 0.25rem 0.8rem;
        border-radius: 20px;
        font-size: 0.75rem;
        margin-top: 0.5rem;
    }}
    @media (max-width: 768px) {{
        .row {{ grid-template-columns: 1fr; }}
        .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
        body {{ padding: 0.8rem; }}
    }}
</style>
</head>
<body>
<div class="header">
    <div class="logo">🏔️</div>
    <h1>ZIRA · Instagram Analytics</h1>
    <p class="sub">@rancho.raiz.2026 — Reporte del {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
    <div class="update-badge">📊 {total_posts} posts · {days_active} días de datos</div>
</div>

<div class="stats-grid">
    <div class="stat-card"><div class="value">{total_posts}</div><div class="label">Posts Totales</div></div>
    <div class="stat-card alt"><div class="value">{total_likes}</div><div class="label">Likes Totales</div></div>
    <div class="stat-card purple"><div class="value">{total_comments}</div><div class="label">Comentarios</div></div>
    <div class="stat-card gold"><div class="value">{avg_eng}</div><div class="label">Engagement/Post</div></div>
    <div class="stat-card alt"><div class="value">{img_count}</div><div class="label">Fotos</div></div>
    <div class="stat-card purple"><div class="value">{vid_count}</div><div class="label">Videos</div></div>
    <div class="stat-card"><div class="value">{post_days}</div><div class="label">Días Activos</div></div>
    <div class="stat-card red"><div class="value">{days_active}</div><div class="label">Días desde 1er Post</div></div>
</div>

<div class="row">
    <div class="section">
        <h2>📈 Engagement Diario</h2>
        <div class="chart-container"><canvas id="chartEngagement"></canvas></div>
    </div>
    <div class="section">
        <h2>📊 IMAGE vs VIDEO</h2>
        <div class="chart-container"><canvas id="chartTypeCompare"></canvas></div>
    </div>
</div>

<div class="row">
    <div class="section">
        <h2>🏆 Top 10 Posts por Engagement</h2>
        <div class="chart-container"><canvas id="chartTopPosts"></canvas></div>
    </div>
    <div class="section">
        <h2>📅 Engagement por Día de la Semana</h2>
        <div class="chart-container"><canvas id="chartWeekday"></canvas></div>
    </div>
</div>

<div class="section">
    <h2>🗓️ Actividad de Posts — Día vs Hora</h2>
    <div class="heatmap-container">
        <div class="heatmap" id="heatmap">
            <div></div>
            {''.join(f'<div class="hour-label">{h}:00</div>' for h in range(24))}
            {''.join(
                f'<div class="label">{weekday_short[i]}</div>' +
                ''.join(
                    f'<div class="cell" style="background:rgba(74,158,255,{min(heat_grid[i][h]/heat_max, 1)});" title="{weekday_short[i]} {h}:00 — {heat_grid[i][h]} posts"></div>'
                    for h in range(24)
                )
                for i in range(7)
            )}
        </div>
    </div>
    <div class="heatmap-legend">
        <span>0</span>
        <div class="bar"></div>
        <span>{heat_max}</span>
        <span style="margin-left:auto;">🎯 {total_heat} posts</span>
    </div>
</div>

<div class="footer">
    <span class="zira">⚡ ZIRA · Rancho Raíz · Barreal</span><br>
    Generado automáticamente — {datetime.now().strftime('%d/%m/%Y')}<br>
    <span style="font-size:0.7rem;">Datasets: {total_posts} registros · {post_days} días</span>
</div>

<script>
// === Gráfico 1: Engagement Diario ===
new Chart(document.getElementById('chartEngagement'), {{
    type: 'bar',
    data: {{
        labels: {json.dumps(daily_labels)},
        datasets: [
            {{
                label: 'Engagement',
                data: {json.dumps(daily_eng)},
                backgroundColor: 'rgba(74, 158, 255, 0.7)',
                borderColor: '#4a9eff',
                borderWidth: 1,
                borderRadius: 4,
            }},
            {{
                label: 'Likes',
                data: {json.dumps(daily_likes)},
                backgroundColor: 'rgba(0, 210, 211, 0.5)',
                borderColor: '#00d2d3',
                borderWidth: 1,
                borderRadius: 4,
            }}
        ]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{ legend: {{ labels: {{ color: '#c8d6e5' }} }} }},
        scales: {{
            x: {{ ticks: {{ color: '#8395a7' }}, grid: {{ color: '#1a1a3e' }} }},
            y: {{ ticks: {{ color: '#8395a7' }}, grid: {{ color: '#1a1a3e' }}, beginAtZero: true }}
        }}
    }}
}});

// === Gráfico 2: IMAGE vs VIDEO ===
new Chart(document.getElementById('chartTypeCompare'), {{
    type: 'radar',
    data: {{
        labels: ['Cantidad', 'Likes Total', 'Engagement Total', 'Engagement Promedio'],
        datasets: [
            {{
                label: 'IMAGE',
                data: [{img_count}, {int(df[df['media_type']=='IMAGE']['likes'].sum())}, {img_eng}, {img_avg}],
                backgroundColor: 'rgba(0, 210, 211, 0.2)',
                borderColor: '#00d2d3',
                borderWidth: 2,
                pointBackgroundColor: '#00d2d3',
            }},
            {{
                label: 'VIDEO',
                data: [{vid_count}, {int(df[df['media_type']=='VIDEO']['likes'].sum())}, {vid_eng}, {vid_avg}],
                backgroundColor: 'rgba(74, 158, 255, 0.2)',
                borderColor: '#4a9eff',
                borderWidth: 2,
                pointBackgroundColor: '#4a9eff',
            }}
        ]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{ legend: {{ labels: {{ color: '#c8d6e5' }} }} }},
        scales: {{
            r: {{
                angleLines: {{ color: '#1a1a3e' }},
                grid: {{ color: '#1a1a3e' }},
                pointLabels: {{ color: '#c8d6e5' }},
                ticks: {{ color: '#8395a7', backdropColor: 'transparent' }}
            }}
        }}
    }}
}});

// === Gráfico 3: Top 10 Posts ===
new Chart(document.getElementById('chartTopPosts'), {{
    type: 'bar',
    data: {{
        labels: {json.dumps(top_labels)},
        datasets: [{{
            label: 'Engagement',
            data: {json.dumps(top_vals)},
            backgroundColor: {json.dumps(top_colors)},
            borderColor: 'transparent',
            borderRadius: 4,
        }}]
    }},
    options: {{
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{ legend: {{ display: false }} }},
        scales: {{
            x: {{ ticks: {{ color: '#8395a7' }}, grid: {{ color: '#1a1a3e' }}, beginAtZero: true }},
            y: {{ ticks: {{ color: '#c8d6e5', font: {{ size: 10 }} }}, grid: {{ display: false }} }}
        }}
    }}
}});

// === Gráfico 4: Engagement por Día de la Semana ===
new Chart(document.getElementById('chartWeekday'), {{
    type: 'polarArea',
    data: {{
        labels: ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'],
        datasets: [{{
            data: [{int(weekday_eng['Monday'])}, {int(weekday_eng['Tuesday'])}, {int(weekday_eng['Wednesday'])}, {int(weekday_eng['Thursday'])}, {int(weekday_eng['Friday'])}, {int(weekday_eng['Saturday'])}, {int(weekday_eng['Sunday'])}],
            backgroundColor: [
                'rgba(74, 158, 255, 0.6)',
                'rgba(0, 210, 211, 0.6)',
                'rgba(95, 39, 205, 0.6)',
                'rgba(254, 202, 87, 0.6)',
                'rgba(255, 107, 107, 0.6)',
                'rgba(46, 213, 115, 0.6)',
                'rgba(255, 159, 67, 0.6)',
            ],
            borderColor: '#0a0a1a',
            borderWidth: 2,
        }}]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{ legend: {{ position: 'right', labels: {{ color: '#c8d6e5' }} }} }},
        scales: {{ r: {{ grid: {{ color: '#1a1a3e' }}, ticks: {{ color: '#8395a7', backdropColor: 'transparent' }} }} }}
    }}
}});
</script>
</body>
</html>"""
    
    html_path = DATA_DIR / "dashboard.html"
    with open(html_path, "w") as f:
        f.write(html)
    print(f"✅ Dashboard generado: {html_path}")
    print(f"   Abrílo con: termux-open {html_path}")

if __name__ == "__main__":
    build_dashboard()
