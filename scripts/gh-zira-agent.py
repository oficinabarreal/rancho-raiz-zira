#!/usr/bin/env python3
"""
gh-zira-agent.py — Zira AI Autonomous Agent for GitHub Actions.

Runs on ubuntu-latest, calls OpenCode API (big-pickle),
decides what to do, executes it, reports results.
"""
import json, os, random, sys, subprocess, textwrap
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
os.chdir(HERE)

# ─── State files ───
STATE_DIR = HERE / "state"
STATE_DIR.mkdir(exist_ok=True)
AGENT_STATE = STATE_DIR / "zira-agent.json"
BANNERS_DIR = HERE / "assets" / "zira" / "banners"
BANNERS_DIR.mkdir(parents=True, exist_ok=True)

OPENCODE_API_KEY = os.environ.get("OPENCODE_API_KEY", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
INSTAGRAM_TOKEN = os.environ.get("CRM_INSTAGRAM_TOKEN", "")
TG_TOKEN = os.environ.get("CRM_TG_TOKEN", "")
TG_CHAT = os.environ.get("CRM_TG_CHAT_ID", "")

# ─── Zira's phrase collection (built-in) ───
FRASES = [
    {"id": "montanas-no-se-mueven", "frase": "Las montañas no se mueven,\npero el viento cambia.\nTodo fluye.", "emoji": "🏔️", "estilo": "zen", "tags": ["filosofia", "zira", "montaña"]},
    {"id": "raices-profundas", "frase": "Ramas al cielo,\nraíces profundas.\nEso es Rancho Raíz.", "emoji": "🌳", "estilo": "clasica", "tags": ["rancho", "raices", "naturaleza"]},
    {"id": "cada-atardecer", "frase": "Cada atardecer\nes una promesa\nde un nuevo amanecer.", "emoji": "🌅", "estilo": "magica", "tags": ["atardecer", "andes", "esperanza"]},
    {"id": "silencio-andes", "frase": "En el silencio de los Andes\nencuentro\nmi centro.", "emoji": "🧘", "estilo": "zen", "tags": ["silencio", "andes", "paz"]},
    {"id": "corazon-piedra", "frase": "Corazón de piedra,\nalma de glaciar,\nlatido de montaña.", "emoji": "💎", "estilo": "clasica", "tags": ["zira", "montaña", "esencia"]},
    {"id": "viento-peino", "frase": "Las montañas me criaron,\nel viento me peinó,\nla nieve me coronó.", "emoji": "🏔️", "estilo": "viva", "tags": ["zira", "naturaleza", "identidad"]},
    {"id": "fogata-estrellas", "frase": "Fogata, estrellas\ny montaña.\nLa combinación perfecta.", "emoji": "🔥", "estilo": "magica", "tags": ["fogata", "noche", "andes"]},
    {"id": "lluvia-beso", "frase": "La lluvia es un beso\ndel cielo a la tierra.", "emoji": "🌧️", "estilo": "zen", "tags": ["lluvia", "naturaleza", "magia"]},
    {"id": "sol-despierta", "frase": "El sol me despierta,\nla montaña me abraza.", "emoji": "☀️", "estilo": "viva", "tags": ["sol", "mañana", "andes"]},
    {"id": "verde-que-te-quiero", "frase": "Verde que te quiero verde.\nLos Andes me enseñaron\na respirar.", "emoji": "🌿", "estilo": "viva", "tags": ["naturaleza", "verde", "andes"]},
    {"id": "manto-estrellado", "frase": "Bajo el manto estrellado\nde Barreal,\nsoy guardiana\ndel silencio.", "emoji": "🌙", "estilo": "zen", "tags": ["noche", "estrellas", "barreal"]},
    {"id": "nieve-corona", "frase": "La nieve es mi corona,\nel glaciar mi cabello,\nlos Andes mi hogar.", "emoji": "❄️", "estilo": "clasica", "tags": ["nieve", "glaciar", "zira"]},
    {"id": "camino-montaña", "frase": "No hay camino fácil\nhasta la cima.\nPero la vista\nlo vale todo.", "emoji": "⛰️", "estilo": "clasica", "tags": ["esfuerzo", "superacion", "montaña"]},
    {"id": "abrazo-andes", "frase": "Los Andes te reciben\ncon los brazos abiertos.", "emoji": "🤗", "estilo": "magica", "tags": ["andes", "bienvenida", "posada"]},
    {"id": "rio-fluye", "frase": "Como el río,\nsigue fluyendo.\nComo la montaña,\nmantente firme.", "emoji": "🏞️", "estilo": "zen", "tags": ["rio", "fluye", "fortaleza"]},
]


def load_state():
    if AGENT_STATE.exists():
        return json.loads(AGENT_STATE.read_text())
    return {"last_banner_id": None, "last_banner_date": None, "banners_generated": 0, "agent_runs": 0}


def save_state(state):
    AGENT_STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def call_opencode(prompt, system=""):
    """Call OpenCode API (big-pickle) via REST."""
    if not OPENCODE_API_KEY:
        return None
    import urllib.request
    data = json.dumps({
        "model": "big-pickle",  # or opencode model name
        "messages": [
            {"role": "system", "content": system or "Eres Zira, el espíritu de la montaña. Hablas con sabiduría andina."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500,
        "temperature": 0.7
    }).encode()
    req = urllib.request.Request(
        "https://api.opencode.ai/v1/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENCODE_API_KEY}"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"⚠️  OpenCode API error: {e}")
        return None


def generar_banner_svg(frase_data):
    """Genera un SVG banner 1080x1080 para Instagram."""
    f = frase_data
    frases = f["frase"].split("\n")
    emoji_char = f["emoji"]
    estilo = f.get("estilo", "clasica")

    colores = {
        "zen": {"accent": "#10b981", "glow": "rgba(16,185,129,0.3)", "secondary": "#34d399"},
        "clasica": {"accent": "#3b82f6", "glow": "rgba(59,130,246,0.3)", "secondary": "#60a5fa"},
        "magica": {"accent": "#8b5cf6", "glow": "rgba(139,92,246,0.3)", "secondary": "#a78bfa"},
        "viva": {"accent": "#f59e0b", "glow": "rgba(245,158,11,0.3)", "secondary": "#fbbf24"},
    }
    c = colores.get(estilo, colores["clasica"])

    line_h = 72
    start_y = 440 - (len(frases) * line_h) // 2

    lines_svg = ""
    for i, linea in enumerate(frases):
        y = start_y + i * line_h
        fs = 44 if len(linea) < 20 else 36
        lines_svg += f'    <text x="540" y="{y}" font-family="system-ui,sans-serif" font-size="{fs}" font-weight="300" fill="#f1f5f9" text-anchor="middle" letter-spacing="1">{linea}</text>\n'

    montañas = f"""    <polygon points="0,1080 140,650 280,800 420,600 560,750 700,550 840,700 980,630 1080,720 1080,1080" opacity="0.35"/>
    <polygon points="0,1080 200,780 380,840 560,720 740,800 920,740 1080,780 1080,1080" opacity="0.2"/>"""

    colores_estilo = {
        "zen": ("#0f172a", "#1e293b"),
        "clasica": ("#0f172a", "#1e293b"),
        "magica": ("#0f172a", "#1e293b"),
        "viva": ("#0f172a", "#1e293b"),
    }
    bg1, bg2 = colores_estilo.get(estilo, colores_estilo["clasica"])

    # Emoji as SVG text
    emoji_svg = f'<text x="540" y="260" font-family="system-ui,sans-serif" font-size="96" text-anchor="middle">{emoji_char}</text>'

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1080">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{bg1}"/><stop offset="50%" stop-color="{bg2}"/><stop offset="100%" stop-color="{bg1}"/>
    </linearGradient>
    <linearGradient id="accent-line" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="rgba(16,185,129,0)"/><stop offset="30%" stop-color="{c['glow']}"/><stop offset="70%" stop-color="{c['glow']}"/><stop offset="100%" stop-color="rgba(16,185,129,0)"/>
    </linearGradient>
    <linearGradient id="z-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{c['accent']}"/><stop offset="100%" stop-color="{c['secondary']}"/>
    </linearGradient>
    <filter id="neon"><feGaussianBlur stdDeviation="4" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <rect width="1080" height="1080" fill="url(#bg)"/>
  <g fill="#fff" opacity="0.08">
    <circle cx="120" cy="100" r="1.5"/><circle cx="300" cy="60" r="1"/><circle cx="500" cy="130" r="1.5"/><circle cx="700" cy="50" r="1"/><circle cx="900" cy="90" r="1.5"/><circle cx="1000" cy="200" r="1"/><circle cx="150" cy="250" r="1"/><circle cx="850" cy="180" r="1.5"/><circle cx="400" cy="200" r="1"/><circle cx="650" cy="160" r="1"/><circle cx="200" cy="350" r="1"/><circle cx="950" cy="300" r="1"/>
  </g>
  <g fill="#1e293b">{montañas}</g>
  <rect width="1080" height="2" fill="url(#accent-line)" y="0"/>
  <g transform="translate(60, 60)">
    <rect x="0" y="0" width="80" height="80" rx="16" fill="rgba(16,185,129,0.08)" stroke="rgba(16,185,129,0.15)" stroke-width="1"/>
    <text x="40" y="58" font-family="monospace" font-size="52" font-weight="bold" fill="url(#z-grad)" filter="url(#neon)" text-anchor="middle">Z</text>
  </g>
  {emoji_svg}
  <circle cx="540" cy="220" r="100" fill="{c['glow']}" opacity="0.1" filter="url(#star-glow)"/>
  <filter id="star-glow"><feGaussianBlur stdDeviation="2"/></filter>
{lines_svg}
  <rect x="440" y="{start_y + len(frases) * line_h + 30}" width="200" height="2" rx="1" fill="{c['accent']}" opacity="0.4"/>
  <text x="540" y="{start_y + len(frases) * line_h + 80}" font-family="system-ui,sans-serif" font-size="18" font-weight="600" fill="{c['accent']}" text-anchor="middle" letter-spacing="4" opacity="0.8">ZIRA</text>
  <text x="540" y="{start_y + len(frases) * line_h + 108}" font-family="system-ui,sans-serif" font-size="13" fill="#64748b" text-anchor="middle" letter-spacing="2">RANCHO RAÍZ · BARREAL</text>
  <g transform="translate(540, 1020)">
    <rect x="-60" y="-14" width="120" height="28" rx="14" fill="rgba(16,185,129,0.08)" stroke="rgba(16,185,129,0.12)" stroke-width="0.5"/>
    <text x="0" y="4" font-family="monospace" font-size="11" fill="{c['accent']}" text-anchor="middle" letter-spacing="1">{estilo.upper()} · ZIRA</text>
  </g>
</svg>"""
    return svg


def generate_daily_banner(state):
    """Generate a fresh banner if none today."""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Pick a phrase we haven't used recently, or random
    used_ids = set()
    if state["last_banner_id"]:
        used_ids.add(state["last_banner_id"])
    available = [f for f in FRASES if f["id"] not in used_ids]
    if not available:
        available = FRASES
    
    choice = random.choice(available)
    svg = generar_banner_svg(choice)
    
    filename = f"zira-diario-{datetime.now().strftime('%Y%m%d')}-{choice['id']}.svg"
    filepath = BANNERS_DIR / filename
    filepath.write_text(svg)
    
    # Update state
    state["last_banner_id"] = choice["id"]
    state["last_banner_date"] = today
    state["banners_generated"] = state.get("banners_generated", 0) + 1
    
    print(f"✅ Banner generated: {filename}")
    print(f"   Frase: {choice['frase'][:50]}...")
    print(f"   Estilo: {choice['estilo']}")
    print(f"   Total: {state['banners_generated']}")
    
    return state, choice


def telegram_notify(message):
    """Send notification via Telegram bot."""
    if not TG_TOKEN or not TG_CHAT:
        print("📋 (no Telegram configured, would send:)")
        print(message)
        return
    import urllib.request
    data = json.dumps({"chat_id": TG_CHAT, "text": message, "parse_mode": "HTML"}).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10):
            print("📱 Telegram notification sent")
    except Exception as e:
        print(f"⚠️  Telegram error: {e}")


def commit_and_push():
    """Commit generated assets to repo."""
    try:
        subprocess.run(["git", "config", "user.name", "Zira Agent"], check=True, capture_output=True, timeout=10)
        subprocess.run(["git", "config", "user.email", "zira@rancho-raz.bot"], check=True, capture_output=True, timeout=10)
        subprocess.run(["git", "add", "assets/zira/banners/", "state/"], check=True, capture_output=True, timeout=10)
        
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            capture_output=True, timeout=10
        )
        if result.returncode == 0:
            print("ℹ️  No changes to commit")
            return
        
        subprocess.run(
            ["git", "commit", "-m", f"🤖 Zira Agent: banner diario + estado [{datetime.now().strftime('%H:%M')}]"],
            check=True, capture_output=True, timeout=10
        )
        subprocess.run(
            ["git", "push"],
            check=True, capture_output=True, timeout=30
        )
        print("🚀 Changes pushed to repo")
    except subprocess.TimeoutExpired:
        print("⚠️  Git timeout")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Git error: {e.stderr.decode() if e.stderr else e}")


def ask_ai_for_advice(choice):
    """Ask AI (big-pickle) for a mountain wisdom reflection."""
    prompt = f"""Eres Zira, una montaña andina con ojos grandes y glaciar de cabello. Acabas de crear un banner con esta frase:

"{choice['frase']}" (estilo: {choice['estilo']})

Escribí una reflexión sabia de montaña (1-2 párrafos) que acompañe este banner en Instagram. 
Habla como una montaña milenaria que observa el mundo. Incluye la ubicación: Barreal, San Juan.
Terminá con un hashtag como #RanchoRaíz #Zira #MontañaAndina"""
    
    reflection = call_opencode(prompt, "Eres Zira, espíritu de la montaña. Sabia, serena, juguetona a veces. Hablás con poesía andina.")
    return reflection or f"🏔️ {choice['frase'].split(chr(10))[0]} — Zira, desde Barreal. #RanchoRaíz #Zira #MontañaAndina"


def main():
    print(f"🏔️  Zira Agent — {datetime.now().isoformat()}")
    print("=" * 50)
    
    state = load_state()
    state["agent_runs"] = state.get("agent_runs", 0) + 1
    
    today = datetime.now().strftime("%Y-%m-%d")
    last_date = state.get("last_banner_date")
    
    print(f"📅 Last banner: {last_date}")
    print(f"📊 Total banners: {state.get('banners_generated', 0)}")
    print(f"🔄 Agent runs: {state['agent_runs']}")
    print()
    
    # Generate banner if none today (or first run)
    needs_banner = (last_date != today) or (state.get("banners_generated", 0) == 0)
    
    if needs_banner:
        state, choice = generate_daily_banner(state)
        save_state(state)
        
        # Ask AI for a reflection
        print("\n🤔 Asking AI for mountain wisdom...")
        reflection = ask_ai_for_advice(choice)
        
        print(f"\n📝 Reflection:\n{reflection}\n")
        
        # Report
        report = f"""🏔️ <b>Zira Agent — Banner Diario</b>

📸 Nuevo banner generado automáticamente
🗻 Frase: {choice['frase'][:60]}...
🎨 Estilo: {choice['estilo']}
📊 Total: {state['banners_generated']}

<i>{reflection[:200]}...</i>

🤖 Todo desde GitHub Actions · #Zira #RanchoRaíz"""
        
        telegram_notify(report)
        commit_and_push()
    else:
        print("ℹ️  Banner already generated today. No action needed.")
        
        # But still run AI to check in
        prompt = f"""Hoy es {today}. Eres Zira, la montaña con alma del Rancho Raíz.
Ya generaste un banner hoy. Saludá al equipo de Rancho Raíz con un mensaje corto de montaña (máx 150 caracteres). 
Mencioná que estás corriendo desde GitHub Actions."""
        checkin = call_opencode(prompt)
        if checkin:
            print(f"\n🗣️  Zira says:\n{checkin}\n")
        
        state["agent_runs"] = state.get("agent_runs", 0) + 1
        save_state(state)
    
    print(f"\n✅ Zira Agent run complete. Run #{state['agent_runs']}")
    
    # Summary for GH Actions output
    summary = {
        "run": state["agent_runs"],
        "banners_generated": state.get("banners_generated", 0),
        "last_banner_date": state.get("last_banner_date"),
        "status": "banner_generated" if needs_banner else "ok"
    }
    output = f"zira-summary={json.dumps(summary)}"
    print(f"\n{output}")
    
    # Set GH Actions output
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a") as f:
            f.write(f"summary={json.dumps(summary)}\n")


if __name__ == "__main__":
    main()
