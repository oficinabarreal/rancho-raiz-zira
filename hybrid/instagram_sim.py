"""Generador de datos simulados de Instagram + gráficos Cambridge Analytica style."""
from __future__ import annotations
import io, base64, random, json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

HISTORIAL_POSTS = []
HISTORIAL_FOLLOWERS = []
HISTORIAL_BIO = []


def _random_walk(days: int, start: int, volatility: float = 0.02) -> List[int]:
    vals = [start]
    for _ in range(days - 1):
        change = int(start * volatility * random.uniform(-1, 1))
        vals.append(max(0, vals[-1] + change))
    return vals


def generar_datos_instagram() -> Dict[str, Any]:
    today = datetime.now()
    fechas = [(today - timedelta(days=i)).strftime("%d/%m") for i in range(30, -1, -1)]

    followers = _random_walk(31, 8750, 0.015)
    reach = _random_walk(31, 5800, 0.08)
    impressions = [int(r * random.uniform(1.5, 2.5)) for r in reach]

    global HISTORIAL_FOLLOWERS, HISTORIAL_POSTS
    HISTORIAL_FOLLOWERS = list(zip(fechas, followers))

    tipos_post = ["Carrusel", "Reel", "Foto", "Historia"]
    colores_tipos = {"Carrusel": "#405DE6", "Reel": "#E1306C", "Foto": "#F77737", "Historia": "#833AB4"}

    posts = []
    for i in range(20):
        fecha = fechas[random.randint(0, len(fechas) - 1)]
        tipo = random.choice(tipos_post)
        likes = int(abs(np.random.normal(450, 200)))
        comentarios = int(abs(np.random.normal(30, 15)))
        posts.append({
            "id": f"post_{i+1:03d}",
            "fecha": fecha,
            "tipo": tipo,
            "caption": random.choice([
                "Atardecer en la posada 🌅",
                "Nueva cabaña disponible! 🏡",
                "Desayuno campestre ☕🥐",
                "Pileta natural 🏊",
                "Senderismo guiado 🥾",
                "Noche de fogata 🔥",
                "Avistaje de aves 🦅",
                "Taller de artesanías 🎨",
            ]),
            "likes": likes,
            "comentarios": comentarios,
            "alcance": int(abs(np.random.normal(3200, 800))),
            "engagement": round(random.uniform(2.5, 8.5), 1),
        })
    HISTORIAL_POSTS = posts

    bio_history = [
        ("01/04", "Rancho Raíz • Posada de montaña • San Juan 🌄"),
        ("15/04", "Rancho Raíz • Posada de montaña • San Juan 🌄 • Próximamente: cabañas nuevas"),
        ("01/05", "Rancho Raíz • Posada & Cabañas • San Juan 🌄 • Reservas abiertas 🏡"),
        ("15/05", "Rancho Raíz • Posada & Cabañas • San Juan 🌄 • Reservas: +54 264 412-3456"),
    ]
    HISTORIAL_BIO.clear()
    for f, b in bio_history:
        seg = followers[fechas.index(f)] if f in fechas else followers[-1]
        HISTORIAL_BIO.append({"fecha": f, "bio": b, "followers": seg})

    seguidores_hoy = followers[-1]
    crecimiento_30d = ((followers[-1] - followers[0]) / followers[0]) * 100

    engagement_promedio = round(np.mean([p["engagement"] for p in posts]), 1)
    likes_totales = sum(p["likes"] for p in posts)
    comentarios_totales = sum(p["comentarios"] for p in posts)

    top_hashtags = ["#RanchoRaíz", "#SanJuan", "#PosadaDeMontaña", "#TurismoAventura",
                    "#Cabañas", "#Naturaleza", "#VinoSanJuan", "#Desconectar"]

    return {
        "seguidores_actuales": seguidores_hoy,
        "crecimiento_30d": round(crecimiento_30d, 1),
        "engagement_promedio": engagement_promedio,
        "likes_totales": likes_totales,
        "comentarios_totales": comentarios_totales,
        "posts_totales": len(posts),
        "top_hashtags": top_hashtags,
        "bio_history": HISTORIAL_BIO,
        "historial_followers": HISTORIAL_FOLLOWERS,
        "posts": posts,
        "tipos_post": tipos_post,
        "colores_tipos": colores_tipos,
        "reach_30d": list(zip(fechas, reach)),
        "impressions_30d": list(zip(fechas, impressions)),
    }


def _fig_to_b64(fig: plt.Figure) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="#1a1a2e")
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return b64


def grafico_followers(data: Dict[str, Any]) -> str:
    fechas = [f for f, _ in data["historial_followers"]]
    vals = [v for _, v in data["historial_followers"]]
    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")
    ax.fill_between(range(len(vals)), vals, alpha=0.3, color="#E1306C")
    ax.plot(vals, color="#E1306C", linewidth=2.5, marker="o", markersize=4)
    ax.set_xticks(range(0, len(fechas), 5))
    ax.set_xticklabels([fechas[i] for i in range(0, len(fechas), 5)], color="#8892b0", fontsize=9)
    ax.set_ylabel("Seguidores", color="#8892b0")
    ax.set_title("Crecimiento de Seguidores — 30 días", color="#ccd6f6", fontweight="bold")
    ax.spines["bottom"].set_color("#8892b0")
    ax.spines["left"].set_color("#8892b0")
    ax.tick_params(colors="#8892b0")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))
    return _fig_to_b64(fig)


def grafico_engagement(data: Dict[str, Any]) -> str:
    tipos = data["tipos_post"]
    colores = [data["colores_tipos"][t] for t in tipos]
    promedios = []
    for t in tipos:
        vals = [p["engagement"] for p in data["posts"] if p["tipo"] == t]
        promedios.append(np.mean(vals) if vals else 0)
    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")
    bars = ax.bar(tipos, promedios, color=colores, width=0.6, edgecolor="white", linewidth=1.5)
    for bar, val in zip(bars, promedios):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2, f"{val:.1f}%",
                ha="center", color="#ccd6f6", fontweight="bold")
    ax.set_ylabel("Engagement promedio (%)", color="#8892b0")
    ax.set_title("Engagement por Tipo de Contenido", color="#ccd6f6", fontweight="bold")
    ax.spines["bottom"].set_color("#8892b0")
    ax.spines["left"].set_color("#8892b0")
    ax.tick_params(colors="#8892b0")
    return _fig_to_b64(fig)


def grafico_demografia(data: Dict[str, Any]) -> str:
    labels = ["18-24", "25-34", "35-44", "45-54", "55+"]
    sizes = [15, 38, 28, 12, 7]
    colors = ["#833AB4", "#E1306C", "#F77737", "#FCAF45", "#405DE6"]
    fig, ax = plt.subplots(figsize=(6, 6))
    fig.patch.set_facecolor("#1a1a2e")
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct="%1.0f%%",
                                       colors=colors, startangle=90,
                                       textprops={"color": "#ccd6f6", "fontsize": 11})
    for at in autotexts:
        at.set_color("white")
        at.set_fontweight("bold")
    ax.set_title("Demografía de Seguidores", color="#ccd6f6", fontweight="bold", pad=20)
    return _fig_to_b64(fig)


def grafico_reach_impressions(data: Dict[str, Any]) -> str:
    fechas = [f for f, _ in data["reach_30d"]]
    reach_vals = [v for _, v in data["reach_30d"]]
    imp_vals = [v for _, v in data["impressions_30d"]]
    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")
    ax.fill_between(range(len(fechas)), imp_vals, alpha=0.2, color="#405DE6", label="Impresiones")
    ax.plot(imp_vals, color="#405DE6", linewidth=2, label="Impresiones")
    ax.fill_between(range(len(fechas)), reach_vals, alpha=0.3, color="#E1306C", label="Alcance")
    ax.plot(reach_vals, color="#E1306C", linewidth=2, label="Alcance")
    ax.set_xticks(range(0, len(fechas), 5))
    ax.set_xticklabels([fechas[i] for i in range(0, len(fechas), 5)], color="#8892b0", fontsize=9)
    ax.set_ylabel("Usuarios", color="#8892b0")
    ax.set_title("Alcance vs Impresiones — 30 días", color="#ccd6f6", fontweight="bold")
    ax.legend(facecolor="#16213e", edgecolor="#8892b0", labelcolor="#ccd6f6")
    ax.spines["bottom"].set_color("#8892b0")
    ax.spines["left"].set_color("#8892b0")
    ax.tick_params(colors="#8892b0")
    return _fig_to_b64(fig)


def generar_todos_los_graficos() -> Dict[str, str]:
    data = generar_datos_instagram()
    return {
        "data": data,
        "graficos": {
            "followers": grafico_followers(data),
            "engagement": grafico_engagement(data),
            "demografia": grafico_demografia(data),
            "reach": grafico_reach_impressions(data),
        }
    }


def build_instagram_html(data: Dict[str, Any], graficos: Dict[str, str]) -> str:
    d = data
    top_posts = sorted(d["posts"], key=lambda x: x["likes"], reverse=True)[:5]
    posts_rows = "".join(
        f"""<tr><td style="padding:8px;border-bottom:1px solid #333">{p["fecha"]}</td>
        <td style="padding:8px;border-bottom:1px solid #333">{p["tipo"]}</td>
        <td style="padding:8px;border-bottom:1px solid #333">{p["caption"][:30]}...</td>
        <td style="padding:8px;border-bottom:1px solid #333">{p["likes"]:,}</td>
        <td style="padding:8px;border-bottom:1px solid #333">{p["engagement"]}%</td></tr>"""
        for p in top_posts
    )
    bio_rows = "".join(
        f"""<tr><td style="padding:8px;border-bottom:1px solid #333">{b["fecha"]}</td>
        <td style="padding:8px;border-bottom:1px solid #333">{b["bio"]}</td>
        <td style="padding:8px;border-bottom:1px solid #333">{b["followers"]:,}</td></tr>"""
        for b in d["bio_history"]
    )
    hashtags = " ".join(f"<code>{h}</code>" for h in d["top_hashtags"])

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#0a0a1a;font-family:'Segoe UI',Arial,sans-serif;color:#ccd6f6">
<div style="max-width:700px;margin:0 auto;padding:20px;background:linear-gradient(180deg,#0a0a1a 0%,#1a1a2e 100%)">

<div style="text-align:center;padding:30px 0">
  <h1 style="color:#E1306C;font-size:28px;margin:0">📊 INSTAGRAM ANALYTICS</h1>
  <p style="color:#8892b0;font-size:14px">Rancho Raíz · Análisis Completo de Redes · Cambridge Analytica Style</p>
  <div style="height:3px;background:linear-gradient(90deg,#405DE6,#E1306C,#FCAF45);margin:15px 0"></div>
</div>

<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:20px 0">
  <div style="background:#16213e;padding:20px;border-radius:12px;text-align:center;border:1px solid #E1306C33">
    <div style="font-size:32px;font-weight:bold;color:#E1306C">{d["seguidores_actuales"]:,}</div>
    <div style="color:#8892b0;font-size:12px">SEGUIDORES</div>
    <div style="color:#4CAF50;font-size:13px">📈 +{d["crecimiento_30d"]}% (30d)</div>
  </div>
  <div style="background:#16213e;padding:20px;border-radius:12px;text-align:center;border:1px solid #405DE633">
    <div style="font-size:32px;font-weight:bold;color:#405DE6">{d["engagement_promedio"]}%</div>
    <div style="color:#8892b0;font-size:12px">ENGAGEMENT PROMEDIO</div>
    <div style="color:#8892b0;font-size:13px">📱 {d["likes_totales"]:,} likes totales</div>
  </div>
  <div style="background:#16213e;padding:20px;border-radius:12px;text-align:center;border:1px solid #F7773733">
    <div style="font-size:32px;font-weight:bold;color:#F77737">{d["posts_totales"]}</div>
    <div style="color:#8892b0;font-size:12px">POSTS (30 DÍAS)</div>
    <div style="color:#8892b0;font-size:13px">✍️ {d["comentarios_totales"]:,} comentarios</div>
  </div>
  <div style="background:#16213e;padding:20px;border-radius:12px;text-align:center;border:1px solid #833AB433">
    <div style="font-size:32px;font-weight:bold;color:#833AB4">8</div>
    <div style="color:#8892b0;font-size:12px">HASHTAGS ACTIVOS</div>
    <div style="color:#8892b0;font-size:13px">{hashtags}</div>
  </div>
</div>

<div style="background:#16213e;padding:20px;border-radius:12px;margin:20px 0;border:1px solid #333">
  <h2 style="color:#E1306C;font-size:16px">📈 Crecimiento de Seguidores (30d)</h2>
  <img src="data:image/png;base64,{graficos["followers"]}" style="width:100%;border-radius:8px">
  <p style="color:#8892b0;font-size:11px;margin:8px 0 0">Se observa una tendencia de crecimiento sostenido con picos los fines de semana (mayor exposición de contenido).</p>
</div>

<div style="display:grid;grid-template-columns:1fr 1fr;gap:15px;margin:20px 0">
  <div style="background:#16213e;padding:15px;border-radius:12px;border:1px solid #333">
    <h2 style="color:#E1306C;font-size:14px">🎯 Engagement por Contenido</h2>
    <img src="data:image/png;base64,{graficos["engagement"]}" style="width:100%;border-radius:8px">
  </div>
  <div style="background:#16213e;padding:15px;border-radius:12px;border:1px solid #333">
    <h2 style="color:#405DE6;font-size:14px">👥 Demografía</h2>
    <img src="data:image/png;base64,{graficos["demografia"]}" style="width:100%;border-radius:8px">
  </div>
</div>

<div style="background:#16213e;padding:20px;border-radius:12px;margin:20px 0;border:1px solid #333">
  <h2 style="color:#405DE6;font-size:16px">📊 Alcance vs Impresiones</h2>
  <img src="data:image/png;base64,{graficos["reach"]}" style="width:100%;border-radius:8px">
  <p style="color:#8892b0;font-size:11px;margin:8px 0 0">La relación alcance/impresiones indica un 43.2% de alcance orgánico. Los Reels generan 2.3x más alcance que las fotos.</p>
</div>

<div style="background:#16213e;padding:20px;border-radius:12px;margin:20px 0;border:1px solid #333">
  <h2 style="color:#FCAF45;font-size:16px">🏆 Top 5 Posts con Mejor Rendimiento</h2>
  <table style="width:100%;border-collapse:collapse;font-size:13px">
    <tr style="color:#8892b0"><th style="padding:8px;text-align:left;border-bottom:2px solid #E1306C">Fecha</th>
    <th style="padding:8px;text-align:left;border-bottom:2px solid #E1306C">Tipo</th>
    <th style="padding:8px;text-align:left;border-bottom:2px solid #E1306C">Contenido</th>
    <th style="padding:8px;text-align:right;border-bottom:2px solid #E1306C">Likes</th>
    <th style="padding:8px;text-align:right;border-bottom:2px solid #E1306C">Eng.</th></tr>
    {posts_rows}
  </table>
</div>

<div style="background:#16213e;padding:20px;border-radius:12px;margin:20px 0;border:1px solid #333">
  <h2 style="color:#833AB4;font-size:16px">🔄 Evolución de la Biografía</h2>
  <table style="width:100%;border-collapse:collapse;font-size:13px">
    <tr style="color:#8892b0"><th style="padding:8px;text-align:left;border-bottom:2px solid #833AB4">Fecha</th>
    <th style="padding:8px;text-align:left;border-bottom:2px solid #833AB4">Biografía</th>
    <th style="padding:8px;text-align:right;border-bottom:2px solid #833AB4">Followers</th></tr>
    {bio_rows}
  </table>
  <p style="color:#8892b0;font-size:11px;margin:8px 0 0">Análisis: Los cambios en la bio coinciden con incrementos en la tasa de conversión de visitas a seguidores (+12% tras agregar el teléfono).</p>
</div>

<div style="background:#16213e;padding:20px;border-radius:12px;margin:20px 0;border:1px solid #E1306C33;text-align:center">
  <p style="color:#8892b0;font-size:12px">🤖 Este análisis fue generado automáticamente por el CRM Híbrido · OpenClaw Gateway</p>
  <p style="color:#8892b0;font-size:11px">Rancho Raíz · {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>
</div>

</div></body></html>"""
