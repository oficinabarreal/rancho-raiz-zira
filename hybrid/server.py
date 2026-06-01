from __future__ import annotations
import uuid
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from flows.central_crm.models import GatewayEvent, GatewayResponse
from flows.central_crm.engine import (
    init_parser, nueva_reserva, procesar_incidente,
    procesar_pago, generar_informe,
)
from flows.central_crm import parser as parser_mod
from flows.central_crm import store
from flows.arte.banner_flows import generar_banner
from flows.arte.reel_pipeline import generar_reel as generar_reel_handler
from gateway_client import enviar_instrucciones

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
        resp.state_updates["instrucciones_enviadas"] = enviar_instrucciones(resp.instructions)
    return resp


@app.post("/webhook/pago", response_model=GatewayResponse)
async def webhook_pago(event: GatewayEvent):
    resp = procesar_pago(event.dict() if hasattr(event, "dict") else event.model_dump())
    if resp.instructions:
        resp.state_updates["instrucciones_enviadas"] = enviar_instrucciones(resp.instructions)
    return resp


@app.post("/webhook/informe", response_model=GatewayResponse)
async def webhook_informe(event: GatewayEvent = None):
    if event is None:
        event = GatewayEvent(type="informe_diario", data={})
    resp = generar_informe(event.dict() if hasattr(event, "dict") else event.model_dump())
    if resp.instructions:
        resp.state_updates["instrucciones_enviadas"] = enviar_instrucciones(resp.instructions)
    return resp


@app.post("/webhook/banner", response_model=GatewayResponse)
async def webhook_banner(event: GatewayEvent):
    """Genera un banner/imagen desde HTML/CSS usando el servidor MCP local."""
    data = event.data | {"source": event.source, "event_id": event.event_id}
    resp = await generar_banner(data)
    if resp.instructions:
        resp.state_updates["instrucciones_enviadas"] = enviar_instrucciones(resp.instructions)
    return resp


@app.post("/webhook/banner/raw", response_model=GatewayResponse)
async def webhook_banner_raw(request: Request):
    """Endpoint raw: recibe JSON plano con html, width, height, etc."""
    body = await request.json()
    event = GatewayEvent(
        event_id=str(uuid.uuid4())[:8],
        type="generar_banner",
        source=body.get("source", "raw"),
        data=body,
    )
    return await webhook_banner(event)


@app.post("/webhook/reel", response_model=GatewayResponse)
async def webhook_reel(event: GatewayEvent):
    """Genera un reel (video) usando HTML+FFmpeg pipeline."""
    data = event.data | {"source": event.source, "event_id": event.event_id}
    resp = await generar_reel_handler(data)
    if resp.instructions:
        resp.state_updates["instrucciones_enviadas"] = enviar_instrucciones(resp.instructions)
    return resp


@app.post("/webhook/reel/raw", response_model=GatewayResponse)
async def webhook_reel_raw(request: Request):
    """Endpoint raw: recibe JSON plano con tagline, title, subtitle, cta, duracion, etc."""
    body = await request.json()
    event = GatewayEvent(
        event_id=str(uuid.uuid4())[:8],
        type="generar_reel",
        source=body.get("source", "raw"),
        data=body,
    )
    return await webhook_reel(event)


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
