#!/usr/bin/env python3
"""
Example usage of the notification system for hola-3 project.
"""
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from asistente.utils.notification import (
    send_notification,
    notify_task_reminder,
    notify_api_available,
    notify_process_status
)

def demo_notifications():
    """Demonstrate various notification types."""
    
    print("Sending demo notifications...")
    
    # 1. Simple test notification
    send_notification(
        title="Hermes Agent",
        content="Sistema de notificaciones inicializado correctamente",
        action="termux-exec bash -c 'cd /data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3 && exec bash'"
    )
    print("✓ Test notification sent")
    
    # 2. Task reminder
    notify_task_reminder("Revisar respuestas de Telegram bot", "hola-3")
    print("✓ Task reminder sent")
    
    # 3. API availability alert (example)
    notify_api_available("OpenCode Zen")
    print("✓ API available notification sent")
    
    # 4. Process status
    notify_process_status("Telegram Bot", "Activo y escuchando comandos")
    print("✓ Process status notification sent")
    
    print("\nTodas las notificaciones han sido enviadas.")
    print("Desliza hacia abajo desde la parte superior de la pantalla para verlas.")
    print("Al hacer clic en cualquiera, se abrirá Termux en el directorio del proyecto.")

if __name__ == "__main__":
    demo_notifications()