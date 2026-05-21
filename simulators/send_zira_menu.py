#!/usr/bin/env python3
"""Send the Zira interactive menu to Telegram."""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from zira_telegram import build_inline_keyboard, welcome_text


def load_config() -> tuple[str, int]:
    config_path = Path.home() / ".codex" / "telegram-bridge.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    token = config["botToken"]
    chat_id = (config.get("chatIds") or [None])[0]
    if chat_id is None:
        raise SystemExit("No chat id configured in ~/.codex/telegram-bridge.json")
    return token, int(chat_id)


def telegram_api(token: str, method: str, data: dict) -> dict:
    url = f"https://api.telegram.org/bot{token}/{method}"
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    if not payload.get("ok"):
        raise SystemExit(f"Telegram API {method} failed: {payload}")
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send Zira interactive menu.")
    parser.add_argument("--text", default=welcome_text())
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    token, chat_id = load_config()
    telegram_api(
        token,
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": args.text,
            "reply_markup": build_inline_keyboard(),
        },
    )
    print(f"Sent Zira menu to chat_id={chat_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
