from __future__ import annotations
import uuid
from typing import Any, Dict
from flows.central_crm.models import GatewayResponse, Instruction
from flows.mensajeria.gateway import mcp_html_a_imagen


async def generar_banner(event_data: Dict[str, Any]) -> GatewayResponse:
    event_id = event_data.get("event_id", str(uuid.uuid4())[:8])
    html = event_data.get("html", "")
    width = int(event_data.get("width", 1080))
    height = int(event_data.get("height", 1080))
    fmt = event_data.get("format", "png").lower().replace("jpg", "jpeg")
    quality = int(event_data.get("quality", 90))
    output_name = event_data.get("output_name", f"banner_{event_id}")
    caption = event_data.get("caption", "")
    send_telegram = event_data.get("send_telegram", False)
    campaign = event_data.get("campaign", "")

    if not html.strip():
        return GatewayResponse(
            event_id=event_id,
            status="error",
            message="El campo 'html' es obligatorio y no puede estar vacio.",
        )

    try:
        result = await mcp_html_a_imagen(
            html=html, width=width, height=height, fmt=fmt, quality=quality,
        )
    except Exception as e:
        return GatewayResponse(
            event_id=event_id,
            status="error",
            message=f"Error al generar imagen: {e}",
        )

    instructions = []
    state_updates = {"banner": result}

    if send_telegram and result.get("path"):
        from hybrid.config import settings
        text = f"Banner generado"
        if campaign:
            text += f"\nCampania: {campaign}"
        text += f"\n{result['width']}x{result['height']} · {result['format']}"
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
        message=f"Banner generado: {result['path']} ({result['size']} bytes)",
        instructions=instructions,
        state_updates=state_updates,
    )
