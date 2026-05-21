#!/usr/bin/env python3
"""Minimal real Telegram bot for Zira.

Polls Telegram updates, responds to the inline menu, text queries, and photos.
It stores simple local state so the demo can later be upgraded into a real flow.
"""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path
import sys
from typing import Any, Dict, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from zira_telegram import (
    audio_hint_text,
    faq_text,
    availability_text,
    build_inline_keyboard,
    classify_text,
    ensure_dirs,
    photo_text,
    prices_text,
    record_lead,
    record_turn,
    load_offset,
    reserve_text,
    save_offset,
    welcome_text,
)
from zira_voice import synthesize_sync
from zira_photo_pipeline import process_photo


CONFIG_PATH = Path.home() / ".codex" / "telegram-bridge.json"


def load_config() -> tuple[str, int]:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
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


def send_message(token: str, chat_id: int, text: str, reply_markup: Optional[dict] = None) -> None:
    payload: Dict[str, Any] = {"chat_id": chat_id, "text": text}
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    telegram_api(token, "sendMessage", payload)


def send_photo_caption(token: str, chat_id: int, text: str, reply_markup: Optional[dict] = None) -> None:
    send_message(token, chat_id, text, reply_markup=reply_markup)


def send_photo(token: str, chat_id: int, photo_path: Path, caption: str = "", reply_markup: Optional[dict] = None) -> None:
    payload: Dict[str, Any] = {"chat_id": chat_id}
    if caption:
        payload["caption"] = caption
    if reply_markup is not None:
        payload["reply_markup"] = json.dumps(reply_markup, ensure_ascii=False)

    boundary = "----ziraphotoboundary"
    parts = []
    for key, value in payload.items():
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(f'Content-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
    parts.append(f"--{boundary}\r\n".encode())
    parts.append(f'Content-Disposition: form-data; name="photo"; filename="{photo_path.name}"\r\n'.encode())
    parts.append(b"Content-Type: image/jpeg\r\n\r\n")
    parts.append(photo_path.read_bytes())
    parts.append(f"\r\n--{boundary}--\r\n".encode())

    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    req = urllib.request.Request(
        url,
        data=b"".join(parts),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    if not payload.get("ok"):
        raise SystemExit(f"Telegram photo failed: {payload}")


def send_audio(token: str, chat_id: int, audio_path: Path, caption: str = "") -> None:
    payload: Dict[str, Any] = {"chat_id": chat_id}
    if caption:
        payload["caption"] = caption
    # Multipart upload for Telegram audio
    boundary = "----ziraaudioboundary"
    parts = []
    for key, value in payload.items():
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(f'Content-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
    parts.append(f"--{boundary}\r\n".encode())
    parts.append(b'Content-Disposition: form-data; name="audio"; filename="response.mp3"\r\n')
    parts.append(b"Content-Type: audio/mpeg\r\n\r\n")
    parts.append(audio_path.read_bytes())
    parts.append(f"\r\n--{boundary}--\r\n".encode())
    url = f"https://api.telegram.org/bot{token}/sendAudio"
    req = urllib.request.Request(
        url,
        data=b"".join(parts),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    if not payload.get("ok"):
        raise SystemExit(f"Telegram audio failed: {payload}")


def answer_callback(token: str, callback_id: str, text: str) -> None:
    telegram_api(token, "answerCallbackQuery", {"callback_query_id": callback_id, "text": text})


def maybe_send_audio_response(token: str, chat_id: int, key: str, text: str) -> None:
    tmp_dir = Path(__file__).with_name("zira_media")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    audio_path = tmp_dir / f"{key}.mp3"
    try:
        synthesize_sync(text, audio_path)
        send_audio(token, chat_id, audio_path, caption=audio_hint_text(key))
    except Exception as exc:
        send_message(token, chat_id, f"Audio no disponible ahora: {exc}", reply_markup=build_inline_keyboard())


def get_updates(token: str, offset: Optional[int] = None, limit: int = 25) -> list[dict]:
    params = {"limit": limit, "timeout": 20, "allowed_updates": ["message", "callback_query"]}
    if offset is not None:
        params["offset"] = offset
    query = urllib.parse.urlencode(params)
    url = f"https://api.telegram.org/bot{token}/getUpdates?{query}"
    with urllib.request.urlopen(url, timeout=40) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    if not payload.get("ok"):
        raise SystemExit(f"Telegram getUpdates failed: {payload}")
    updates = payload.get("result", [])
    return updates if isinstance(updates, list) else []


def download_telegram_file(token: str, file_id: str, target_dir: Path) -> Path:
    meta = telegram_api(token, "getFile", {"file_id": file_id})
    result = meta.get("result", {})
    if not isinstance(result, dict):
        raise SystemExit("Telegram getFile returned invalid result")
    file_path = result.get("file_path")
    if not isinstance(file_path, str):
        raise SystemExit("Telegram file_path missing")

    target_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(file_path).suffix or ".bin"
    target = target_dir / f"{int(time.time())}_{file_id[:8]}{ext}"
    url = f"https://api.telegram.org/file/bot{token}/{file_path}"
    with urllib.request.urlopen(url, timeout=60) as resp:
        target.write_bytes(resp.read())
    return target


def process_and_notify_photo(token: str, chat_id: int, saved: Path, caption: str) -> None:
    try:
        job = process_photo(saved, caption=caption)
        preview = next((Path(a.path) for a in job.artifacts if a.kind == "preview"), None)
        ready = next((Path(a.path) for a in job.artifacts if a.kind == "ready"), None)
        text = (
            "Foto procesada.\n\n"
            f"• Lista para revisar: {job.job_id}\n"
            f"• Caption sugerido: {job.suggested_caption}\n"
            f"• Hashtags: {' '.join(job.hashtags)}\n"
            f"• Estado: {job.status}"
        )
        send_message(token, chat_id, text, reply_markup=build_inline_keyboard())
        if preview and preview.exists():
            send_photo(
                token,
                chat_id,
                preview,
                caption="Preview de edición: original + square + feed + story",
                reply_markup=build_inline_keyboard(),
            )
        if ready and ready.exists():
            send_photo(
                token,
                chat_id,
                ready,
                caption="Versión lista para publicar (feed 4:5)",
                reply_markup=build_inline_keyboard(),
            )
        record_lead("photo_pipeline", {"chat_id": chat_id, "job": job.job_id, "preview": str(preview) if preview else "", "ready": str(ready) if ready else ""})
    except Exception as exc:
        send_message(
            token,
            chat_id,
            f"No pude procesar la foto automáticamente: {exc}",
            reply_markup=build_inline_keyboard(),
        )


def handle_message(token: str, message: dict) -> None:
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    if not isinstance(chat_id, int):
        return

    text = message.get("text")
    if isinstance(text, str):
        record_turn("Cliente", text)
        intent = classify_text(text)
        if text.strip() in {"/start", "/menu"}:
            send_message(token, chat_id, welcome_text(), reply_markup=build_inline_keyboard())
        elif intent in {"about", "location", "amenities"}:
            reply = faq_text(intent)
            send_message(token, chat_id, reply, reply_markup=build_inline_keyboard())
            maybe_send_audio_response(token, chat_id, intent, reply)
        elif intent == "prices":
            reply = prices_text()
            send_message(token, chat_id, reply, reply_markup=build_inline_keyboard())
            maybe_send_audio_response(token, chat_id, intent, reply)
        elif intent == "availability":
            reply = availability_text()
            send_message(token, chat_id, reply, reply_markup=build_inline_keyboard())
            maybe_send_audio_response(token, chat_id, intent, reply)
        elif intent == "reserve":
            reply = reserve_text()
            send_message(token, chat_id, reply, reply_markup=build_inline_keyboard())
            maybe_send_audio_response(token, chat_id, intent, reply)
        elif intent == "photo":
            reply = photo_text()
            send_message(token, chat_id, reply, reply_markup=build_inline_keyboard())
            maybe_send_audio_response(token, chat_id, intent, reply)
        else:
            send_message(token, chat_id, "Decime si querés precios, disponibilidad, reservar o subir una foto.")
        record_lead("text", {"chat_id": chat_id, "text": text, "intent": intent})
        return

    photos = message.get("photo")
    if isinstance(photos, list) and photos:
        last_photo = photos[-1]
        if isinstance(last_photo, dict) and isinstance(last_photo.get("file_id"), str):
            saved = download_telegram_file(token, last_photo["file_id"], Path(__file__).with_name("zira_media"))
            caption = message.get("caption") if isinstance(message.get("caption"), str) else ""
            record_turn("Cliente", "[foto enviada]")
            record_lead("photo", {"chat_id": chat_id, "file": str(saved), "caption": caption})
            process_and_notify_photo(token, chat_id, saved, caption)


def handle_callback(token: str, callback: dict) -> None:
    callback_id = callback.get("id")
    data = callback.get("data")
    message = callback.get("message", {})
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    if not isinstance(callback_id, str) or not isinstance(chat_id, int) or not isinstance(data, str):
        return

    if data == "zira:prices":
        answer_callback(token, callback_id, "Mostrando precios")
        reply = prices_text()
        send_message(token, chat_id, reply, reply_markup=build_inline_keyboard())
        maybe_send_audio_response(token, chat_id, "prices", reply)
    elif data == "zira:availability":
        answer_callback(token, callback_id, "Mostrando disponibilidad")
        reply = availability_text()
        send_message(token, chat_id, reply, reply_markup=build_inline_keyboard())
        maybe_send_audio_response(token, chat_id, "availability", reply)
    elif data == "zira:reserve":
        answer_callback(token, callback_id, "Mostrando reserva")
        reply = reserve_text()
        send_message(token, chat_id, reply, reply_markup=build_inline_keyboard())
        maybe_send_audio_response(token, chat_id, "reserve", reply)
    elif data == "zira:photo":
        answer_callback(token, callback_id, "Pedí una foto")
        reply = photo_text()
        send_message(token, chat_id, reply, reply_markup=build_inline_keyboard())
        maybe_send_audio_response(token, chat_id, "photo", reply)
    elif data.startswith("zira:faq:"):
        answer_callback(token, callback_id, "Mostrando FAQ")
        key = data.split("zira:faq:", 1)[1]
        reply = faq_text(key)
        send_message(token, chat_id, reply, reply_markup=build_inline_keyboard())
        maybe_send_audio_response(token, chat_id, key, reply)
    elif data == "zira:listen":
        answer_callback(token, callback_id, "Enviando audio")
        state_text = welcome_text()
        try:
            from zira_telegram import load_json, STATE_FILE
            state = load_json(STATE_FILE, {"turns": []})
            turns = state.get("turns", [])
            if turns:
                for item in reversed(turns):
                    if isinstance(item, dict) and isinstance(item.get("text"), str):
                        state_text = item["text"]
                        break
        except Exception:
            pass
        maybe_send_audio_response(token, chat_id, "listen", state_text)
        send_message(token, chat_id, "Te mandé un audio con la última respuesta disponible.", reply_markup=build_inline_keyboard())
    record_lead("callback", {"chat_id": chat_id, "data": data})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Zira Telegram bot.")
    parser.add_argument("--once", action="store_true", help="Process available updates once and exit.")
    parser.add_argument("--offset", type=int, default=None, help="Start from a specific update offset.")
    parser.add_argument("--menu", action="store_true", help="Send the interactive menu immediately and exit.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_dirs()
    token, default_chat_id = load_config()

    if args.menu:
        send_message(token, default_chat_id, welcome_text(), reply_markup=build_inline_keyboard())
        print(f"Sent menu to chat_id={default_chat_id}")
        return 0

    offset = args.offset if args.offset is not None else load_offset()
    while True:
        updates = get_updates(token, offset=offset)
        for update in updates:
            if not isinstance(update, dict):
                continue
            offset = max(offset or 0, int(update.get("update_id", 0)) + 1)
            save_offset(offset)
            if "callback_query" in update and isinstance(update["callback_query"], dict):
                handle_callback(token, update["callback_query"])
            elif "message" in update and isinstance(update["message"], dict):
                handle_message(token, update["message"])
        if args.once:
            break
        time.sleep(1)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
