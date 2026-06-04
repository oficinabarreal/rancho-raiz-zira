#!/usr/bin/env python3
"""
Generador de banners Zira con frases filosóficas montaña para Instagram.
Genera SVGs cuadrados 1080x1080 con el estilo visual de Zira.
"""
import os, sys, json
from pathlib import Path

OUT_DIR = Path("/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3/pipeline/zira-frases")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Import SVG emoji shapes
sys.path.insert(0, str(OUT_DIR.parent.parent))
from scripts.svg_emoji_components import EMOJI_SVG

# ─── COLECCIÓN DE FRASES ZIRA ───
FRASES = [
    {
        "id": "montanas-no-se-mueven",
        "frase": "Las montañas no se mueven,\npero el viento cambia.\nTodo fluye.",
        "emoji": "🏔️",
        "estilo": "zen",
        "tags": ["filosofia", "zira", "montaña", "reflexion"],
    },
    {
        "id": "raices-profundas",
        "frase": "Ramas al cielo,\nraíces profundas.\nEso es Rancho Raíz.",
        "emoji": "🌳",
        "estilo": "clasica",
        "tags": ["rancho", "raices", "naturaleza"],
    },
    {
        "id": "cada-atardecer",
        "frase": "Cada atardecer\nes una promesa\nde un nuevo amanecer.",
        "emoji": "🌅",
        "estilo": "magica",
        "tags": ["atardecer", "andes", "esperanza"],
    },
    {
        "id": "silencio-andes",
        "frase": "En el silencio de los Andes\nencuentro\nmi centro.",
        "emoji": "🧘",
        "estilo": "zen",
        "tags": ["silencio", "andes", "paz", "meditacion"],
    },
    {
        "id": "corazon-piedra",
        "frase": "Corazón de piedra,\nalma de glaciar,\nlatido de montaña.",
        "emoji": "💎",
        "estilo": "clasica",
        "tags": ["zira", "montaña", "esencia"],
    },
    {
        "id": "viento-peino",
        "frase": "Las montañas me criaron,\nel viento me peinó,\nla nieve me coronó.",
        "emoji": "🏔️",
        "estilo": "viva",
        "tags": ["zira", "naturaleza", "identidad"],
    },
    {
        "id": "fogata-estrellas",
        "frase": "Fogata, estrellas\ny montaña.\nLa combinación perfecta.",
        "emoji": "🔥",
        "estilo": "magica",
        "tags": ["fogata", "noche", "andes", "magia"],
    },
    {
        "id": "lluvia-beso",
        "frase": "La lluvia es un beso\ndel cielo a la tierra.\nQue empiece la magia.",
        "emoji": "🌧️",
        "estilo": "zen",
        "tags": ["lluvia", "naturaleza", "magia"],
    },
    {
        "id": "sol-despierta",
        "frase": "El sol me despierta,\nla montaña me abraza,\nel viento me cuenta\nhistorias.",
        "emoji": "☀️",
        "estilo": "viva",
        "tags": ["sol", "mañana", "andes", "vida"],
    },
    {
        "id": "verde-que-te-quiero",
        "frase": "Verde que te quiero verde.\nLos Andes me enseñaron\na respirar.",
        "emoji": "🌿",
        "estilo": "viva",
        "tags": ["naturaleza", "verde", "andes", "vida"],
    },
    {
        "id": "manto-estrellado",
        "frase": "Bajo el manto estrellado\nde Barreal,\nsoy guardiana\ndel silencio.",
        "emoji": "🌙",
        "estilo": "zen",
        "tags": ["noche", "estrellas", "barreal", "guardiana"],
    },
    {
        "id": "nieve-corona",
        "frase": "La nieve es mi corona,\nel glaciar mi cabello,\nlos Andes mi hogar.",
        "emoji": "❄️",
        "estilo": "clasica",
        "tags": ["nieve", "glaciar", "zira", "montaña"],
    },
    {
        "id": "camino-montaña",
        "frase": "No hay camino fácil\nhasta la cima.\nPero la vista\nlo vale todo.",
        "emoji": "⛰️",
        "estilo": "clasica",
        "tags": ["esfuerzo", "superacion", "montaña", "motivacion"],
    },
    {
        "id": "abrazo-andes",
        "frase": "Los Andes te reciben\ncon los brazos abiertos.\nSolo hace falta\ndejarse abrazar.",
        "emoji": "🤗",
        "estilo": "magica",
        "tags": ["andes", "bienvenida", "posada", "calidez"],
    },
    {
        "id": "rio-fluye",
        "frase": "Como el río,\nsigue fluyendo.\nComo la montaña,\nmantente firme.",
        "emoji": "🏞️",
        "estilo": "zen",
        "tags": ["rio", "fluye", "fortaleza", "naturaleza"],
    },
]

# ─── GENERADOR SVG ───

def generar_svg(frase_data):
    f = frase_data
    frases = f["frase"].split("\n")
    emoji_char = f["emoji"]
    emoji_svg = EMOJI_SVG.get(emoji_char, 
        f'<text x="540" y="260" font-family="system-ui, sans-serif" font-size="96" text-anchor="middle">{emoji_char}</text>')
    estilo = f["estilo"]
    
    # Colores según estilo
    colores = {
        "zen": {"accent": "#10b981", "glow": "rgba(16,185,129,0.3)", "secondary": "#34d399"},
        "clasica": {"accent": "#3b82f6", "glow": "rgba(59,130,246,0.3)", "secondary": "#60a5fa"},
        "magica": {"accent": "#8b5cf6", "glow": "rgba(139,92,246,0.3)", "secondary": "#a78bfa"},
        "viva": {"accent": "#f59e0b", "glow": "rgba(245,158,11,0.3)", "secondary": "#fbbf24"},
    }
    c = colores.get(estilo, colores["clasica"])
    
    # Altura para cada línea de frase
    line_h = 72
    start_y = 440 - (len(frases) * line_h) // 2
    
    lines_svg = ""
    for i, linea in enumerate(frases):
        y = start_y + i * line_h
        lines_svg += f'    <text x="540" y="{y}" font-family="system-ui, sans-serif" font-size="{44 if len(linea) < 20 else 36}" font-weight="300" fill="#f1f5f9" text-anchor="middle" letter-spacing="1">{linea}</text>\n'
    
    # Tipo de montaña según estilo
    if estilo == "zen":
        montañas = """    <polygon points="0,1080 160,700 320,850 480,650 640,780 800,620 960,730 1080,680 1080,1080" opacity="0.3"/>
    <polygon points="0,1080 200,800 400,880 600,720 800,850 1000,750 1080,800 1080,1080" opacity="0.15"/>"""
    elif estilo == "magica":
        montañas = """    <polygon points="0,1080 120,620 280,750 440,550 600,680 760,500 920,650 1040,580 1080,700 1080,1080" opacity="0.3"/>
    <polygon points="0,1080 180,750 360,820 540,680 720,780 900,700 1080,740 1080,1080" opacity="0.15"/>"""
    elif estilo == "viva":
        montañas = """    <polygon points="0,1080 100,680 240,780 380,600 520,720 660,560 800,700 940,620 1040,740 1080,660 1080,1080" opacity="0.3"/>
    <polygon points="0,1080 220,800 400,860 580,740 760,820 940,760 1080,800 1080,1080" opacity="0.15"/>"""
    else:  # clasica
        montañas = """    <polygon points="0,1080 140,650 280,800 420,600 560,750 700,550 840,700 980,630 1080,720 1080,1080" opacity="0.35"/>
    <polygon points="0,1080 200,780 380,840 560,720 740,800 920,740 1080,780 1080,1080" opacity="0.2"/>"""
    
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1080">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="50%" stop-color="#1e293b"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </linearGradient>
    <linearGradient id="accent-line" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="rgba(16,185,129,0)"/>
      <stop offset="30%" stop-color="{c['glow']}"/>
      <stop offset="70%" stop-color="{c['glow']}"/>
      <stop offset="100%" stop-color="rgba(16,185,129,0)"/>
    </linearGradient>
    <linearGradient id="z-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{c['accent']}"/>
      <stop offset="100%" stop-color="{c['secondary']}"/>
    </linearGradient>
    <filter id="neon">
      <feGaussianBlur stdDeviation="4" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
    <filter id="star-glow">
      <feGaussianBlur stdDeviation="2"/>
    </filter>
  </defs>

  <!-- Background -->
  <rect width="1080" height="1080" fill="url(#bg)"/>

  <!-- Subtle stars -->
  <g fill="#fff" opacity="0.15">
    <circle cx="120" cy="100" r="1.5"/>
    <circle cx="300" cy="60" r="1"/>
    <circle cx="500" cy="130" r="1.5"/>
    <circle cx="700" cy="50" r="1"/>
    <circle cx="900" cy="90" r="1.5"/>
    <circle cx="1000" cy="200" r="1"/>
    <circle cx="150" cy="250" r="1"/>
    <circle cx="850" cy="180" r="1.5"/>
    <circle cx="400" cy="200" r="1"/>
    <circle cx="650" cy="160" r="1"/>
    <circle cx="200" cy="350" r="1"/>
    <circle cx="950" cy="300" r="1"/>
    <circle cx="80" cy="180" r="1"/>
    <circle cx="1040" cy="120" r="1.5"/>
  </g>

  <!-- Mountains -->
  <g fill="#1e293b">
{montañas}
  </g>

  <!-- Top accent line -->
  <rect width="1080" height="2" fill="url(#accent-line)" y="0"/>

  <!-- Z logo top-left -->
  <g transform="translate(60, 60)">
    <rect x="0" y="0" width="80" height="80" rx="16" fill="rgba(16,185,129,0.08)" stroke="rgba(16,185,129,0.15)" stroke-width="1"/>
    <text x="40" y="58" font-family="monospace" font-size="52" font-weight="bold" fill="url(#z-grad)" filter="url(#neon)" text-anchor="middle">Z</text>
  </g>

  <!-- Emoji grande (SVG shapes en vez de texto emoji) -->
  {emoji_svg}
  <circle cx="540" cy="220" r="100" fill="{c['glow']}" opacity="0.1" filter="url(#star-glow)"/>

  <!-- Zira phrase -->
{lines_svg}

  <!-- Barra decorativa -->
  <rect x="440" y="{start_y + len(frases) * line_h + 30}" width="200" height="2" rx="1" fill="{c['accent']}" opacity="0.4"/>

  <!-- Footer: Zira + Rancho Raíz -->
  <text x="540" y="{start_y + len(frases) * line_h + 80}" font-family="system-ui, sans-serif" font-size="18" font-weight="600" fill="{c['accent']}" text-anchor="middle" letter-spacing="4" opacity="0.8">ZIRA</text>
  <text x="540" y="{start_y + len(frases) * line_h + 108}" font-family="system-ui, sans-serif" font-size="13" fill="#64748b" text-anchor="middle" letter-spacing="2">RANCHO RAÍZ · BARREAL</text>

  <!-- Badge estilo -->
  <g transform="translate(540, 1020)">
    <rect x="-60" y="-14" width="120" height="28" rx="14" fill="rgba(16,185,129,0.08)" stroke="rgba(16,185,129,0.12)" stroke-width="0.5"/>
    <text x="0" y="4" font-family="monospace" font-size="11" fill="{c['accent']}" text-anchor="middle" letter-spacing="1">{estilo.upper()} · ZIRA</text>
  </g>
</svg>"""
    return svg

# ─── GENERAR TODOS ───
print(f"🏔️  Generando {len(FRASES)} banners Zira para Instagram...\n")

manifest = []
for f in FRASES:
    svg_content = generar_svg(f)
    filename = f"zira-frase-{f['id']}.svg"
    filepath = OUT_DIR / filename
    filepath.write_text(svg_content)
    size_kb = len(svg_content) / 1024
    manifest.append({
        "id": f["id"],
        "frase": f["frase"].replace("\n", " "),
        "emoji": f["emoji"],
        "estilo": f["estilo"],
        "archivo": filename,
        "tags": f["tags"],
    })
    print(f"  ✅ {filename} ({size_kb:.0f} KB) — {f['estilo'].upper()} — {f['frase'][:40]}...")

# Guardar manifest
manifest_path = OUT_DIR / "manifest.json"
manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
print(f"\n📋 Manifest guardado: {manifest_path}")
print(f"\n🏁 {len(FRASES)} banners generados en {OUT_DIR}/")
