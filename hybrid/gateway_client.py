from __future__ import annotations
from typing import Any, Dict, List
from models import Instruction
from config import settings


def enviar_instrucciones(instructions: List[Instruction]) -> List[Dict[str, Any]]:
    """Envía las instrucciones al Gateway de OpenClaw para que las ejecute."""
    if not instructions:
        return []

    import requests as http
    resultados = []

    for inst in instructions:
        try:
            r = http.post(
                f"{settings.gateway_url}/execute",
                json={"action": inst.action, "payload": inst.payload},
                timeout=15
            )
            resultados.append({
                "action": inst.action,
                "status": r.status_code,
                "ok": r.ok,
                "response": r.json() if r.ok else r.text[:100]
            })
        except Exception as e:
            resultados.append({
                "action": inst.action,
                "status": "error",
                "ok": False,
                "response": str(e)
            })

    return resultados
