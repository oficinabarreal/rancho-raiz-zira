#!/usr/bin/env python3
"""
Project monitoring script that uses Google AI Studio API to analyze project context
and generate intelligent notifications every 30 minutes.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
import urllib.request
import urllib.error

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables from .env file
env_path = PROJECT_ROOT / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                try:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
                except ValueError:
                    pass

# Google AI Studio API configuration
API_KEY = os.environ.get('GOOGLE_API_KEY')
if not API_KEY:
    print("ERROR: GOOGLE_API_KEY no está configurada en .env")
    print("Agrega GOOGLE_API_KEY=tu_key al archivo .env")
    sys.exit(1)
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

def call_gemini_api(prompt):
    """Call the Google Gemini API with the given prompt."""
    headers = {
        "Content-Type": "application/json",
    }

    data = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 1024,
        }
    }

    try:
        url_with_key = f"{API_URL}?key={API_KEY}"
        req = urllib.request.Request(url_with_key, data=json.dumps(data).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode('utf-8'))

        if 'candidates' in result and len(result['candidates']) > 0:
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            return "Error: No response from API"
    except Exception as e:
        return f"Error calling API: {str(e)}"

def get_project_context():
    """Gather context about the current project state."""
    context = []
    
    # Check recent activity
    try:
        # Get git status
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            if result.stdout.strip():
                context.append(f"Cambios pendientes en git:\n{result.stdout}")
            else:
                context.append("Repositorio git limpio")
        else:
            context.append("No se pudo obtener estado de git")
    except:
        context.append("Error al verificar git")
    
    # Check for important files
    important_files = [
        'ROADMAP.md',
        'AGENT.md',
        'asistente/google/gmail.py',
        'asistente/telegram/telegram_bot.py',
        'demo_notifications.py'
    ]
    
    file_status = []
    for file_path in important_files:
        full_path = PROJECT_ROOT / file_path
        if full_path.exists():
            file_status.append(f"✓ {file_path}")
        else:
            file_status.append(f"✗ {file_path} (no encontrado)")
    
    context.append("Estado de archivos clave:\n" + "\n".join(file_status))
    
    # Check recent notifications
    try:
        notification_log = PROJECT_ROOT / 'notification_log.txt'
        if notification_log.exists():
            recent = notification_log.read_text()[-500:]  # Last 500 chars
            context.append(f"Historial reciente de notificaciones:\n{recent}")
        else:
            context.append("No hay historial de notificaciones previo")
    except:
        context.append("No se pudo leer historial de notificaciones")
    
    # Check for running processes (optional)
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            # Look for our processes
            our_processes = [line for line in result.stdout.split('\n') 
                           if 'hola-3' in line or 'telegram' in line or 'python' in line]
            if our_processes:
                context.append(f"Procesos relacionados encontrados ({len(our_processes)}):\n" + 
                             "\n".join(our_processes[:5]))  # Limit to 5
            else:
                context.append("No se encontraron procesos activos de hola-3")
        else:
            context.append("No se pudo verificar procesos")
    except:
        context.append("Error al verificar procesos")
    
    return "\n\n".join(context)

def generate_notification_message(context):
    """Generate an intelligent notification message based on project context."""
    prompt = f"""
Eres un asistente inteligente que monitorea el proyecto hola-3, un sistema de automatización de CRM para Rancho Raíz.

Contexto actual del proyecto:
{context}

Basándote en este contexto, genera una notificación útil y concisa (máximo 200 caracteres) que pueda incluir:
- Un recordatorio de tarea pendiente importante
- Una sugerencia de mejora basada en lo observado
- Una idea para avanzar en el proyecto
- Una observación sobre el estado actual
- Un consejo técnico relevante

La notificación debe ser amigable, útil y accionable. Si no hay nada particularmente importante que reportar, 
puede ser un mensaje motivatorio o una observación ligera.

Responde SOLO con el texto de la notificación, sin explicaciones adicionales.
"""
    
    return call_gemini_api(prompt)

def send_notification(title, content):
    """Send notification using termux-notification."""
    try:
        # Default action: open termux in project directory
        action = f"termux-exec bash -c 'cd {PROJECT_ROOT} && exec bash'"
        
        subprocess.run([
            "termux-notification",
            "--title", title,
            "--content", content,
            "--action", action
        ], check=True, timeout=10)
        return True
    except Exception as e:
        print(f"Error sending notification: {e}")
        return False

def log_notification(content):
    """Log notification to file for history."""
    log_file = PROJECT_ROOT / 'notification_log.txt'
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {content}\n")
    except Exception as e:
        print(f"Error logging notification: {e}")

def main():
    """Main function to run the project monitor."""
    print("Iniciando monitoreo del proyecto hola-3...")
    
    # Get project context
    context = get_project_context()
    print("Contexto del proyecto obtenido")
    
    # Generate notification message
    message = generate_notification_message(context)
    print(f"Mensaje generado: {message}")
    
    # Send notification
    title = "Monitor hola-3"
    if send_notification(title, message):
        print("Notificación enviada correctamente")
        log_notification(message)
    else:
        print("Error al enviar notificación")
        # Fallback: print to console
        print(f"NOTIFICACIÓN: {title} - {message}")

if __name__ == "__main__":
    main()