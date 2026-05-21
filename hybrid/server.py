from __future__ import annotations
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from models import GatewayEvent, GatewayResponse
from handlers.crm_flows import (
    init_parser, nueva_reserva, procesar_incidente,
    procesar_pago, generar_informe
)
from gateway_client import enviar_instrucciones
import parser as parser_mod
import store

app = FastAPI(title="CRM Rancho Raíz - Hybrid Server", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    init_parser()
    print(f"🚀 CRM Hybrid Server iniciado en {settings.host}:{settings.port}")
    print(f"   Gateway: {settings.gateway_url}")
    print(f"   IA Parser: {'✅' if settings.ia_available else '❌'} {settings.ia_model}")
    print(f"   Crm state: {store.BASE}")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "ia_parser": bool(parser_mod.IA_ENDPOINT),
        "ia_model": parser_mod.IA_MODEL,
        "ia_rate_limit": parser_mod.IA_LAST_RATE_LIMIT,
        "gateway": settings.gateway_url,
    }


@app.post("/webhook/reserva", response_model=GatewayResponse)
async def webhook_reserva(event: GatewayEvent):
    resp = nueva_reserva(event.data | {"source": event.source, "event_id": event.event_id})
    if resp.instructions:
        resp.state_updates["instrucciones_enviadas"] = enviar_instrucciones(resp.instructions)
    return resp


@app.post("/webhook/reserva/raw", response_model=GatewayResponse)
async def webhook_reserva_raw(request: Request):
    """Endpoint simple: recibe texto plano y lo parsea."""
    body = await request.body()
    text = body.decode("utf-8")
    import uuid
    event = GatewayEvent(
        event_id=str(uuid.uuid4())[:8],
        type="nueva_reserva",
        source="raw",
        data={"raw_text": text}
    )
    return await webhook_reserva(event)


@app.post("/webhook/incidente", response_model=GatewayResponse)
async def webhook_incidente(event: GatewayEvent):
    resp = procesar_incidente(event.dict() if hasattr(event, "dict") else event.model_dump())
    if resp.instructions:
        enviar_instrucciones(resp.instructions)
    return resp


@app.post("/webhook/pago", response_model=GatewayResponse)
async def webhook_pago(event: GatewayEvent):
    resp = procesar_pago(event.dict() if hasattr(event, "dict") else event.model_dump())
    if resp.instructions:
        enviar_instrucciones(resp.instructions)
    return resp


@app.post("/webhook/informe", response_model=GatewayResponse)
async def webhook_informe(event: GatewayEvent = GatewayEvent(type="informe_diario", data={})):
    resp = generar_informe(event.dict() if hasattr(event, "dict") else event.model_dump())
    if resp.instructions:
        enviar_instrucciones(resp.instructions)
    return resp


@app.post("/gateway/response")
async def gateway_response(data: dict):
    """Recibe confirmación de ejecución del Gateway."""
    store.append("gateway_responses.json", data)
    return {"status": "ok"}


@app.get("/state/{collection}")
async def get_state(collection: str):
    data = store.read(f"{collection}.json", [])
    return {"collection": collection, "count": len(data) if isinstance(data, list) else 1, "data": data}


if __name__ == "__main__":
    uvicorn.run(app, host=settings.host, port=settings.port)
