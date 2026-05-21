#!/usr/bin/env python3
"""Generate Spanish demo audio from CRM simulator scenarios."""

from __future__ import annotations

import argparse
import asyncio
import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from crm_simulator import build_zira_dialogue, render_voice_es, scenario_map


def build_session_text(session_name: str, with_external: bool) -> str:
    lookup = scenario_map()
    if with_external:
        # `crm_simulator.py` handles external loading; here we use the built-ins only
        # because the session demo already references the same scenario ids.
        pass

    if session_name == "zira_demo":
        lines = ["Hola. Soy Zira, el bot de la posada."]
        for turn in build_zira_dialogue():
            if turn.speaker == "Cliente":
                continue
            lines.append(turn.text)
        lines.append("Fin de la demostración.")
        return " ".join(lines)

    if session_name == "client_demo":
        session_ids = [
            "email_digest_starlink",
            "instagram_lead_scoring",
            "whatsapp_business_autoresponse",
            "bridge_task_routing",
            "video_marketing_pipeline",
        ]
    else:
        session_ids = [item.strip() for item in session_name.split(",") if item.strip()]

    scenarios = []
    for sid in session_ids:
        if sid in lookup:
            scenarios.append(lookup[sid])

    lines = ["Hola. Este es el demo del CRM automatizado."]
    for idx, scenario in enumerate(scenarios, start=1):
        lines.append(f"Paso {idx}. {scenario.title}.")
        lines.append(render_voice_es(scenario))
    lines.append("Fin del demo.")
    return " ".join(lines)


async def synthesize(text: str, output: Path, voice: str) -> None:
    try:
        import edge_tts
    except ImportError as exc:
        raise SystemExit(f"edge-tts no está disponible: {exc}")

    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(str(output))


def send_telegram_audio(audio_path: Path, caption: str, chat_id: int | None = None) -> None:
    import json
    import urllib.request

    config_path = Path.home() / ".codex" / "telegram-bridge.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    token = config["botToken"]
    chat = chat_id or (config.get("chatIds") or [None])[0]
    if not chat:
        raise SystemExit("No chat id configured in ~/.codex/telegram-bridge.json")

    url = f"https://api.telegram.org/bot{token}/sendAudio"
    boundary = "----crmvoiceboundary"
    parts = []
    def add_field(name: str, value: str) -> None:
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())

    add_field("chat_id", str(chat))
    add_field("caption", caption)
    parts.append(f"--{boundary}\r\n".encode())
    parts.append(b'Content-Disposition: form-data; name="audio"; filename="demo.mp3"\r\n')
    parts.append(b"Content-Type: audio/mpeg\r\n\r\n")
    parts.append(audio_path.read_bytes())
    parts.append(f"\r\n--{boundary}--\r\n".encode())

    body = b"".join(parts)
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode("utf-8")
    payload = json.loads(raw)
    if not payload.get("ok"):
        raise SystemExit(f"Telegram audio failed: {payload}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Spanish CRM demo voice.")
    parser.add_argument("--session", default="client_demo", help="Session name or comma-separated scenario ids.")
    parser.add_argument("--output", type=Path, default=Path("simulators/client_demo_es.mp3"))
    parser.add_argument("--voice", default="es-ES-ElviraNeural")
    parser.add_argument("--send", action="store_true", help="Send the generated audio to Telegram.")
    parser.add_argument("--caption", default="Demo CRM en español")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    text = build_session_text(args.session, with_external=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(synthesize(text, args.output, args.voice))
    print(f"Generated: {args.output}")
    print(text)
    if args.send:
        send_telegram_audio(args.output, args.caption)
        print("Sent audio to Telegram")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
