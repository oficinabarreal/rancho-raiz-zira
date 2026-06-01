import sys
import os
import re
import json
import logging
import requests
from pathlib import Path
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from asistente.mail_utils import send_gmail_mime
except ImportError:
    from mail_utils import send_gmail_mime
try:
    from asistente.google.gmail import GmailConnector
except ImportError:
    from google.gmail import GmailConnector

# ---- Helper: read env from file ----
def get_env_value(filepath: str, varname: str) -> str:
    try:
        with open(filepath) as f:
            for line in f:
                if line.startswith(varname + '='):
                    return line.split('=', 1)[1].strip('"\' ')
    except Exception:
        pass
    return os.getenv(varname, '')

# ---- LLM-based parser with fallback across providers ----
def call_llm_parse_email(text: str):
    # Try multiple providers in order: OpenCode, NVIDIA, OpenRouter, Google
    providers = [
        {
            'name': 'OpenCode Zen',
            'key': get_env_value(PROJECT_ROOT / '.env', 'OPENCODE_API_KEY'),
            'url': get_env_value(PROJECT_ROOT / '.env', 'OPENCODE_BASE_URL'),
            'model': 'gpt-5.1-codex-mini',  # Using a lightweight fast model
        },
        {
            'name': 'NVIDIA',
            'key': get_env_value(PROJECT_ROOT / '.env', 'NVIDIA_API_KEY'),
            'url': get_env_value(PROJECT_ROOT / '.env', 'NVIDIA_BASE_URL'),
            'model': 'nemotron-3-super-120b-a12b:free',  # Free lightweight model
        },
        {
            'name': 'OpenRouter',
            'key': get_env_value(PROJECT_ROOT / '.env', 'OPENROUTER_API_KEY'),
            'url': 'https://openrouter.ai/api/v1',
            'model': 'google/gemini-3-flash-preview',  # Flash is fast and cheap
        },
        {
            'name': 'Google Gemini',
            'key': get_env_value(PROJECT_ROOT / '.env', 'GOOGLE_API_KEY'),
            'url': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent',
            'model': 'gemini-1.5-flash',  # Flash version is fast
        }
    ]
    
    for provider in providers:
        if not provider['key'] or not provider['url']:
            continue
            
        try:
            if provider['name'] == 'Google Gemini':
                # Gemini API has different endpoint structure
                url = f"{provider['url']}?key={provider['key']}"
                headers = {'Content-Type': 'application/json'}
                payload = {
                    "contents": [{
                        "parts": [{
                            "text": f"Eres un experto en búsqueda de correos. Convierte la petición del usuario en una query de Gmail API y el número de resultados (max_results). Responde solo en JSON con keys 'query' y 'max_results' (int). Petición: {text}"
                        }]
                    }],
                    "generationConfig": {
                        "temperature": 0.1,
                        "maxOutputTokens": 60,
                    }
                }
                resp = requests.post(url, headers=headers, json=payload, timeout=10)
            else:
                # Standard OpenAI-compatible API
                url = f"{provider['url']}/chat/completions"
                headers = {
                    'Authorization': f'Bearer {provider["key"]}',
                    'Content-Type': 'application/json'
                }
                payload = {
                    'model': provider['model'],
                    'messages': [
                        {'role': 'system', 'content': f'Eres un experto en búsqueda de correos. Convierte la petición del usuario en una query de Gmail API y el número de resultados (max_results). Responde solo en JSON con keys "query" y "max_results" (int). Petición: {text}'}
                    ],
                    'max_tokens': 60,
                }
                resp = requests.post(url, headers=headers, json=payload, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                if provider['name'] == 'Google Gemini':
                    # Extract text from Gemini response
                    content = data['candidates'][0]['content']['parts'][0]['text']
                else:
                    content = data['choices'][0]['message']['content']
                
                cleaned = content.strip()
                if cleaned.startswith('```json'):
                    cleaned = cleaned.split('```json\n', 1)[-1].split('```', 1)[0]
                elif cleaned.startswith('```'):
                    cleaned = cleaned.split('```\n', 1)[-1].split('```', 1)[0]
                parsed = json.loads(cleaned)
                query = parsed.get('query', 'is:unread')
                max_results = int(parsed.get('max_results', 5))
                logging.getLogger(__name__).info(f"LLM parsed via {provider['name']}: query='{query}', max_results={max_results}")
                return query, max_results
            elif resp.status_code == 429:
                logging.getLogger(__name__).info(f"{provider['name']} rate-limited (429), trying next provider")
                continue
            else:
                logging.getLogger(__name__).warning(f"{provider['name']} API error: {resp.status_code}")
                continue
        except Exception as e:
            logging.getLogger(__name__).warning(f"{provider['name']} call failed: {e}")
            continue
    
    # All providers failed, return None to fall back to heuristic
    logging.getLogger(__name__).info("All LLM providers unavailable, falling back to heuristic parser")
    return None

# ---- Heuristic parser (always works, no internet required) ----
def heuristic_parse_email(user_text: str) -> tuple[str, int]:
    t = user_text.lower()
    max_results = 5
    if any(w in t for w in ["ultimo", "último", "reciente", "últimos"]):
        max_results = 1
    # Pass-through for raw Gmail operators
    if any(c in user_text for c in [':', '@']):
        return user_text.strip(), max_results

    stopwords = {"dame","envíame","enviar","envía","mandame","mándame","quiero","muestra","muestrame","lista",
                 "por","favor","me","el","la","los","las","un","una","de","del","al","y","o","en","a","con",
                 "que","qué","quien","quién","cuál","cual","donde","dónde","cuando","cuándo","como","cómo",
                 "si","no","hay","tengo","tener","ver","mostrar","correo","email","mensaje","para","sin","leer",
                 "leido","leído","ha","han","estoy","soy","son","?","!","enviame"}
    tokens = re.findall(r'\b\w+\b', t)
    filtered = [tok for tok in tokens if tok not in stopwords]
    parts = []
    if "adjunto" in t or "adjuntos" in t:
        parts.append("has:attachment")
    if "no leido" in t or "no leído" in t or "sin leer" in t:
        parts.append("is:unread")
    if filtered:
        parts.append(" ".join(filtered))
    query = " ".join(parts).strip()
    if not query:
        query = "is:unread"
    return query, max_results

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🛡️ Asistente Rancho Raíz activado.\n\nComandos disponibles:\n"
        "/emails [consulta] - Buscar correos (ej: 'dame el último no leído')\n"
        "/status - Ver estado del sistema\n"
        "/send <to> <subject> <body> - Enviar correo"
    )

async def emails(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🔍 Buscando correos...")
    try:
        if not context.args:
            query = "is:unread"
            max_results = 5
        else:
            user_text = " ".join(context.args)
            # Try LLM with fallback across providers, then heuristic
            llm_result = call_llm_parse_email(user_text)
            if llm_result:
                query, max_results = llm_result
            else:
                query, max_results = heuristic_parse_email(user_text)
        
        # Execute the search
        gmail = GmailConnector()
        result = gmail.list_messages(query=query, max_results=max_results)
        if not result.ok or not result.data.get('messages'):
            await update.message.reply_text("📭 No se encontraron mensajes.")
            return
        
        resumen_lines = []
        for m in result.data['messages']:
            subject = m.get('subject', 'Sin asunto')
            sender = m.get('from', 'Desconocido')
            date = m.get('date', '').split()[:3]
            date_str = " ".join(date) if date else ''
            if len(subject) > 50:
                subject = subject[:47] + "..."
            resumen_lines.append(f"• {subject} – {sender} – {date_str}")
        texto = f"📬 Correos encontrados (top {max_results}):\n" + "\n".join(resumen_lines)
        await update.message.reply_text(texto)
    except Exception as e:
        logging.getLogger(__name__).exception("Error en /emails")
        await update.message.reply_text(f"❌ Error: {e}")

async def send_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 3:
        await update.message.reply_text(
            "Uso: /send <destinatario> <asunto> <cuerpo>\n"
            "Ejemplo: /send juan@ejemplo.com Hola Esto es una prueba"
        )
        return
    to = context.args[0]
    subject = context.args[1]
    body = " ".join(context.args[2:])
    try:
        resp = send_gmail_mime(to=to, subject=subject, body_text=body)
        await update.message.reply_text(
            f"✅ Correo enviado a {to}.\nID mensaje: {resp.get('id')}"
        )
    except Exception as e:
        logging.getLogger(__name__).exception("Error en /send")
        await update.message.reply_text(f"❌ Error: {e}")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    token_path = PROJECT_ROOT / "crm_state" / ".google_token.json"
    tg_token_env = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("CRM_TG_TOKEN")
    lines = [
        "🔍 Estado del asistente:",
        f"- Token Gmail: {'✅' if token_path.exists() else '❌'}",
        f"- Token Telegram: {'✅' if tg_token_env else '❌ (no configurado)'}",
        f"- Proyecto: Rancho Raíz CRM",
        f"- Bot: activo"
    ]
    await update.message.reply_text("\n".join(lines))

def obtener_token() -> str:
    token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("CRM_TG_TOKEN")
    if token:
        return token
    creds_path = PROJECT_ROOT / "CREDENCIALES.md"
    if creds_path.exists():
        with open(creds_path) as f:
            for line in f:
                if line.startswith("TELEGRAM_BOT_TOKEN="):
                    token = line.strip().split("=", 1)[1]
                    if token:
                        return token
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("TELEGRAM_BOT_TOKEN=") or line.startswith("CRM_TG_TOKEN="):
                    token = line.split("=", 1)[1].strip()
                    if token:
                        return token
    raise RuntimeError(
        "Token de Telegram no encontrado. Define TELEGRAM_BOT_TOKEN o CRM_TG_TOKEN en variables de entorno, en CREDENCIALES.md o en .env."
    )


async def codigl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manual command to show system information"""
    await update.message.reply_text("🔧 Ejecutando diagnóstico manual del sistema...")
    try:
        # Importar lo necesario
        from pathlib import Path
        import platform
        import sys
        
        # Define project root (same as in main())
        BASE_DIR = Path(__file__).resolve().parent
        PROJECT_ROOT = BASE_DIR.parents[1]
        
        info_lines = [
            "🖥️  Información del Sistema:",
            f"- Sistema: {platform.system()} {platform.release()}",
            f"- Arquitectura: {platform.machine()}",
            f"- Python: {sys.version.split()[0]}",
            f"- Directorio: {Path.cwd()}",
            "",
            "🤖 Estado de Zira:",
        ]
        
        # Verificar configuración de Hermes
        hermes_config = Path.home() / '.hermes' / 'config.yaml'
        if hermes_config.exists():
            info_lines.append("- Configuración Hermes: ✅ Encontrada")
        else:
            info_lines.append("- Configuración Hermes: ❌ No encontrada")
            
        # Verificar .env
        hermes_env = Path.home() / '.hermes' / '.env'
        if hermes_env.exists():
            info_lines.append("- Archivo .env: ✅ Encontrado")
            # Contar líneas no vacías y no comentadas
            with open(hermes_env) as f:
                env_lines = [l.strip() for l in f.readlines() if l.strip() and not l.startswith('#')]
                info_lines.append(f"  - Variables configuradas: {len(env_lines)}")
        else:
            info_lines.append("- Archivo .env: ❌ No encontrado")
            
        # Verificar proyecto hola-3
        if PROJECT_ROOT.exists():
            info_lines.append("- Proyecto hola-3: ✅ Encontrado")
            # Verificar algunos archivos clave
            key_files = ['asistente/telegram/telegram_bot.py', 'asistente/mail_utils.py']
            for kf in key_files:
                if (PROJECT_ROOT / kf).exists():
                    info_lines.append(f"  - {kf}: ✅")
                else:
                    info_lines.append(f"  - {kf}: ❌")
        else:
            info_lines.append("- Proyecto hola-3: ❌ No encontrado")
            
        # Verificar token de Telegram
        tg_token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("CRM_TG_TOKEN")
        if tg_token:
            info_lines.append("- Token Telegram: ✅ Configurado")
        else:
            info_lines.append("- Token Telegram: ❌ No configurado en variables de entorno")
            
        # Verificar estado del gateway
        info_lines.append("")
        info_lines.append("🔌 Estado de Conexiones:")
        info_lines.append("- Gateway Hermes: Estado desconocido (usar 'hermes gateway status')")
        
        await update.message.reply_text("\n".join(info_lines))
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error en diagnóstico: {e}")
        import traceback
        print(f"Error detallado: {traceback.format_exc()}")
def main() -> None:
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    logger = logging.getLogger(__name__)
    token = obtener_token()
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("emails", emails))
    application.add_handler(CommandHandler("send", send_email))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("codigl", codigl))
    logger.info("Bot de Telegram iniciado, esperando comandos...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()