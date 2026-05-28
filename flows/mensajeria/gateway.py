"""
Gateway de mensajeria: enrutamiento y dispatch de instrucciones,
mas el puente MCP para HTML a imagen.
"""
from __future__ import annotations
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict


async def mcp_html_a_imagen(
    html: str, width: int = 1080, height: int = 1080,
    fmt: str = "png", quality: int = 90,
) -> Dict[str, Any]:
    """Convierte HTML a imagen via servidor MCP local (Chromium)."""
    from hybrid.mcp_client import html_a_imagen
    return await html_a_imagen(html=html, width=width, height=height, fmt=fmt, quality=quality)


def enviar_instrucciones(instructions: list) -> list:
    """Envia instrucciones al Gateway (OpenClaw) via HTTP."""
    import requests
    from hybrid.config import settings
    results = []
    for inst in instructions:
        try:
            resp = requests.post(
                f"{settings.gateway_url}/execute",
                json={"action": inst.action, "payload": inst.payload},
                timeout=30,
            )
            results.append(resp.json())
        except Exception as e:
            results.append({"ok": False, "error": str(e)})
    return results
