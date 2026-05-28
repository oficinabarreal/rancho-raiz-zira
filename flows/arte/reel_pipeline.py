from __future__ import annotations
import importlib.util
import uuid
from pathlib import Path
from typing import Any, Dict
from flows.central_crm.models import GatewayResponse, Instruction


async def generar_reel(event_data: Dict[str, Any]) -> GatewayResponse:
    event_id = event_data.get("event_id", str(uuid.uuid4())[:8])
    exp_path = Path.home() / "Documents/proyectos/test-mcp-render/experimentos"
    mod_path = exp_path / "04_frames_a_video.py"

    if not mod_path.exists():
        return GatewayResponse(
            event_id=event_id,
            status="error",
            message=f"Pipeline de reels no encontrado: {mod_path}",
        )

    spec = importlib.util.spec_from_file_location("reel_generator", str(mod_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    try:
        result = await mod.generar_reel(
            foto=event_data.get("foto"),
            audio=event_data.get("audio"),
            tagline=event_data.get("tagline", "ESCAPATE A LA MONTAÑA"),
            title=event_data.get("title", "Rancho Raíz"),
            subtitle=event_data.get("subtitle", "Barreal · San Juan · Argentina"),
            cta=event_data.get("cta", "Reserva tu experiencia →"),
            duracion=float(event_data.get("duracion", 10)),
        )
    except Exception as e:
        return GatewayResponse(
            event_id=event_id,
            status="error",
            message=f"Error al generar reel: {e}",
        )

    instructions = []
    if event_data.get("send_telegram"):
        from hybrid.config import settings
        caption = event_data.get("caption", "")
        text = f"Reel generado"
        if event_data.get("tagline"):
            text += f"\n{event_data['tagline']}"
        text += f"\n{result['resolution']} · {result['duration']}s"
        text += f"\n{result['path']}"
        if caption:
            text += f"\n\n{caption}"
        instructions.append(Instruction(
            action="telegram.send_message",
            payload={"chat_id": settings.tg_chat_id, "text": text},
        ))

    return GatewayResponse(
        event_id=event_id,
        status="ok",
        message=f"Reel generado: {result['path']} ({result['size']} bytes)",
        instructions=instructions,
        state_updates={"reel": result},
    )
