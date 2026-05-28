"""
Cliente IA compartido entre Hermes y OpenClaw.
Usa opencode CLI para acceder al modelo big-pickle (contexto masivo 200K).
Falla a OpenCode Zen API para consultas simples.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

OPencode_CLI = "/data/data/com.termux/files/usr/bin/opencode"
ZEN_ENDPOINT = os.environ.get("CRM_IA_ENDPOINT", "https://opencode.ai/zen/v1/chat/completions")
ZEN_API_KEY = os.environ.get("CRM_IA_API_KEY", "")
ZEN_MODEL = os.environ.get("CRM_IA_MODEL", "opencode/big-pickle")
TEMPERATURE = float(os.environ.get("CRM_IA_TEMPERATURE", "0.2"))
MAX_TOKENS = int(os.environ.get("CRM_IA_MAX_TOKENS", "4096"))


def query(prompt: str, system: str = "", use_cli: bool = True) -> str:
    """Consulta big-pickle via opencode CLI (recomendado) o fallback a Zen API."""
    # Intentar CLI primero (big-pickle nativo)
    if use_cli and Path(OPencode_CLI).exists():
        return _query_cli(prompt, system)
    # Fallback a Zen API
    return _query_zen(prompt, system)


def _query_cli(prompt: str, system: str = "") -> str:
    """Usa opencode CLI para consultar big-pickle."""
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    try:
        result = subprocess.run(
            [OPencode_CLI, "prompt", full_prompt],
            capture_output=True, text=True, timeout=300,
            env={**os.environ, "OPENCODE_MODE": "noninteractive"},
        )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        if result.returncode != 0:
            return f"CLI Error ({result.returncode}): {stderr[:200]}"
        return stdout or "(respuesta vacia)"
    except subprocess.TimeoutExpired:
        return "Error: timeout 300s"
    except FileNotFoundError:
        return "Error: opencode CLI no encontrado"
    except Exception as e:
        return f"Error: {e}"


def _query_zen(prompt: str, system: str = "") -> str:
    """Fallback: OpenCode Zen API (modelo configurado en .env)."""
    if not ZEN_API_KEY:
        return "Zen API no configurada (falta CRM_IA_API_KEY)"
    import urllib.request
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    payload = json.dumps({
        "model": ZEN_MODEL,
        "messages": messages,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
    }).encode()
    req = urllib.request.Request(
        ZEN_ENDPOINT,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ZEN_API_KEY}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
        return result.get("choices", [{}])[0].get("message", {}).get("content", "(vacio)")
    except Exception as e:
        return f"Zen Error: {e}"


if __name__ == "__main__":
    test = " ".join(sys.argv[1:]) or "Deci hola en una palabra."
    print(query(test, system="Respondé con una sola palabra."))
