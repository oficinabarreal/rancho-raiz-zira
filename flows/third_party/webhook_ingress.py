"""
Endpoint de entrada universal para webhooks de terceros.
Recibe JSON estandarizado de ManyChat, HubSpot, Typeform, etc.
y lo traduce al modelo interno del CRM.
"""
from __future__ import annotations
from typing import Any, Dict, Optional
from flows.central_crm.models import GatewayResponse, Instruction
from flows.central_crm import store
import uuid


def webhook_ingress_handler(event_data: Dict[str, Any]) -> GatewayResponse:
    """Procesa webhooks entrantes de plataformas externas.

    Schema esperado:
    {
        "source": "manychat|hubspot|typeform|web",
        "external_id": "id_en_plataforma_origen",
        "channel": "instagram_dm|whatsapp|web_form",
        "customer": {
            "name": "...",
            "phone": "...",
            "email": "...",
            "username": "..."
        },
        "current_step": "INTERACCION_INSTAGRAM",
        "raw": { ... datos originales ... }
    }
    """
    event_id = event_data.get("event_id", str(uuid.uuid4())[:8])
    source = event_data.get("source", "unknown")
    external_id = event_data.get("external_id", "")
    customer = event_data.get("customer", {})
    current_step = event_data.get("current_step", "CAPTACION_TELEGRAM")

    lead_data = {
        "id": external_id or str(uuid.uuid4())[:8],
        "source": source,
        "channel": event_data.get("channel", ""),
        "customer": customer,
        "pipeline_step": current_step,
        "raw": event_data.get("raw", event_data),
        "created_at": __import__("datetime").datetime.now().isoformat(),
    }

    store.append("leads.json", lead_data)

    return GatewayResponse(
        event_id=event_id,
        status="ok",
        message=f"Lead recibido desde {source}: {customer.get('name', '?')}",
        instructions=[
            Instruction(action="telegram.send_message", payload={
                "chat_id": __import__("hybrid.config", fromlist=["settings"]).settings.tg_chat_id,
                "text": (
                    f"Nuevo lead desde {source}\n"
                    f"Nombre: {customer.get('name', '?')}\n"
                    f"Telefono: {customer.get('phone', '?')}\n"
                    f"Paso: {current_step}"
                ),
            }),
        ],
        state_updates={"lead": lead_data},
    )
