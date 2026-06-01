#!/usr/bin/env python3
"""
main.py — Punto de entrada para el bot de mensajería.

Uso:
    # Telegram (producción)
    python -m mensajeria.main --channel telegram --token TOKEN --chat-id ID

    # Telegram con .env
    python -m mensajeria.main

    # Consola (prueba)
    python -m mensajeria.main --channel console --once
    python -m mensajeria.main --channel console  # interactivo
"""

from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path


def load_token_from_env() -> tuple:
    """Carga token y chat_id desde .env en la raíz del proyecto."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key, val)

    token = os.environ.get("CRM_TG_TOKEN", "")
    chat_id_str = os.environ.get("CRM_TG_CHAT_ID", "")
    chat_id = int(chat_id_str) if chat_id_str.strip() else 0
    return token, chat_id


def main():
    parser = argparse.ArgumentParser(description="Zira Bot — Mensajería Modular")
    parser.add_argument("--channel", default="telegram", choices=["telegram", "console"])
    parser.add_argument("--token", default="", help="Telegram Bot Token")
    parser.add_argument("--chat-id", type=int, default=0, help="Telegram Chat ID")
    parser.add_argument("--once", action="store_true", help="Procesar updates pendientes y salir")
    args = parser.parse_args()

    if args.channel == "telegram":
        token = args.token
        chat_id = args.chat_id
        if not token or not chat_id:
            token, chat_id = load_token_from_env()
        if not token or not chat_id:
            print("❌ Se necesita --token y --chat-id para Telegram, o configurar .env")
            print("   CRM_TG_TOKEN=...")
            print("   CRM_TG_CHAT_ID=...")
            sys.exit(1)

        from mensajeria.bot import create_telegram_bot, run_bot
        bot = create_telegram_bot(token, chat_id)
        print(f"[Main] Bot listo. Modo por defecto para este chat: leads (prospectos)")
        print(f"[Main] Para cambiar modo: editar mensajeria/modes/registry.py o state/users.json")
        run_bot(bot, once=args.once)

    elif args.channel == "console":
        from mensajeria.bot import Bot, run_bot
        from mensajeria.channels.console import ConsoleChannel

        if args.once:
            # Modo once: probar un mensaje
            channel = ConsoleChannel()
            bot = Bot(channel)
            channel.inject("precios")
            run_bot(bot, once=True)
        else:
            # Modo interactivo
            channel = ConsoleChannel()
            bot = Bot(channel)
            print("=== Zira Bot (modo consola) ===")
            print("Escribí 'salir' para terminar")
            print()
            while True:
                try:
                    text = input("Tú: ")
                except (EOFError, KeyboardInterrupt):
                    break
                if text.lower() in ("salir", "exit", "quit"):
                    break
                channel.inject(text)
                run_bot(bot, once=True)
            print("Chau!")


if __name__ == "__main__":
    main()
