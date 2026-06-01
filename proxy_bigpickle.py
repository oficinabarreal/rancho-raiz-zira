#!/usr/bin/env python3
"""
Proxy minimo: traduce OpenAI Chat Completions -> OpenCode Zen API.
OpenClaw cree que habla con OpenAI; detras esta big-pickle.
"""
from __future__ import annotations

import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import Request, urlopen
from urllib.error import URLError

OPENCODE_API_KEY = os.environ.get(
    "OPENCODE_API_KEY",
    "sk-Acdgb0kW8l0FzBdNPVd1u3XSLEo521fp3x5r856B0ck2rNN6LxWqYNVOAHIIOw3p",
)
OPENCODE_BASE = "https://opencode.ai/zen/v1"
MODEL = "opencode/big-pickle"
PORT = int(os.environ.get("PROXY_PORT", "4000"))


class ProxyHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        if self.path not in ("/chat/completions", "/v1/chat/completions"):
            self.send_error(404, f"Not found: {self.path}")
            return

        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return

        opencode_payload = {
            "model": MODEL,
            "messages": data.get("messages", []),
            "max_tokens": data.get("max_tokens", 4096),
            "temperature": data.get("temperature", 0.7),
            "stream": False,
        }
        if data.get("tools"):
            opencode_payload["tools"] = data["tools"]
        if data.get("tool_choice"):
            opencode_payload["tool_choice"] = data["tool_choice"]

        req = Request(
            f"{OPENCODE_BASE}/chat/completions",
            data=json.dumps(opencode_payload).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {OPENCODE_API_KEY}",
            },
        )

        try:
            resp = urlopen(req, timeout=120)
            result = json.loads(resp.read())
        except URLError as e:
            self.send_error(502, f"OpenCode error: {e.reason if hasattr(e,'reason') else str(e)}")
            return
        except Exception as e:
            self.send_error(502, f"Proxy error: {e}")
            return

        # Normalize response to OpenAI format
        openai_response = {
            "id": result.get("id", "proxy-unknown"),
            "object": "chat.completion",
            "created": result.get("created", 0),
            "model": result.get("model", MODEL),
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": result["choices"][0]["message"]["content"],
                    },
                    "finish_reason": result["choices"][0].get("finish_reason", "stop"),
                }
            ],
            "usage": result.get("usage", {}),
        }

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(openai_response).encode())

    def log_message(self, fmt, *args):
        print(f"[proxy] {args[0]} {args[1]} {args[2]}")


def main():
    server = HTTPServer(("0.0.0.0", PORT), ProxyHandler)
    print(f"[proxy] big-pickle proxy on http://0.0.0.0:{PORT}")
    print(f"[proxy] forwarding to {OPENCODE_BASE} model={MODEL}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[proxy] shutting down")
        server.server_close()


if __name__ == "__main__":
    main()
