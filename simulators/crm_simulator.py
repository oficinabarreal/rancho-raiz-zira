#!/usr/bin/env python3
"""CRM flow simulator for client demos.

This is a deterministic replay tool. It does not touch live apps; it produces
the sequence of actions, classifications, and Telegram-ready summaries that the
real CRM automation would emit.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from textwrap import indent
from typing import Any, Dict, List


@dataclass(frozen=True)
class ScenarioStep:
    stage: str
    action: str
    detail: str


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    channel: str
    source: str
    summary: str
    entities: Dict[str, Any]
    steps: List[ScenarioStep]
    telegram: List[str]
    voice: str
    voice_es: str
    next_actions: List[str]


@dataclass(frozen=True)
class DialogueTurn:
    speaker: str
    text: str


SCENARIOS: List[Scenario] = [
    Scenario(
        id="gmail_starlink_payment_issue",
        title="Gmail: Starlink payment issue",
        channel="gmail",
        source="Inbox",
        summary="A payment failure email is detected and converted into a high-priority CRM alert.",
        entities={
            "customer": "Starlink",
            "category": "billing",
            "priority": "high",
            "intent": "payment_failed",
        },
        steps=[
            ScenarioStep("detect", "scan inbox", "A new billing-related email appears in Gmail."),
            ScenarioStep("classify", "label billing", "The message is marked as a payment issue."),
            ScenarioStep("extract", "capture fields", "Customer, issue type, and urgency are extracted."),
            ScenarioStep("register", "create CRM item", "A follow-up record is created in the CRM ledger."),
            ScenarioStep("notify", "send Telegram", "A concise summary is delivered to the operator."),
        ],
        telegram=[
            "New billing alert",
            "Customer: Starlink",
            "Issue: payment failed",
            "Priority: high",
            "Suggested next step: review payment method and reply",
        ],
        voice="Billing alert for Starlink. Payment failed. Priority high. Review payment method and reply.",
        voice_es="Alerta de facturación para Starlink. El pago falló. Prioridad alta. Revisar el medio de pago y responder.",
        next_actions=[
            "Open Gmail thread",
            "Draft a response",
            "Create a calendar reminder if follow-up is not immediate",
        ],
    ),
    Scenario(
        id="whatsapp_booking_lead",
        title="WhatsApp: booking lead",
        channel="whatsapp",
        source="Chat",
        summary="A WhatsApp message from a prospect is turned into a new lead with a suggested response.",
        entities={
            "lead_name": "Unknown prospect",
            "category": "sales",
            "priority": "medium",
            "intent": "booking_request",
        },
        steps=[
            ScenarioStep("detect", "observe chat", "A new message appears in WhatsApp."),
            ScenarioStep("classify", "tag lead", "The message is recognized as a sales inquiry."),
            ScenarioStep("extract", "capture contact", "Request, timing, and contact details are summarized."),
            ScenarioStep("register", "create lead", "A lead card is prepared for the CRM."),
            ScenarioStep("notify", "send Telegram", "The operator receives a short action note."),
        ],
        telegram=[
            "New WhatsApp lead",
            "Category: sales",
            "Priority: medium",
            "Suggested reply: share pricing and availability",
        ],
        voice="New WhatsApp lead. Sales inquiry. Medium priority. Share pricing and availability.",
        voice_es="Nuevo lead de WhatsApp. Consulta comercial. Prioridad media. Compartir precios y disponibilidad.",
        next_actions=[
            "Reply in WhatsApp",
            "Save contact",
            "Schedule follow-up if needed",
        ],
    ),
    Scenario(
        id="email_followup_reminder",
        title="Email: follow-up reminder",
        channel="gmail",
        source="Inbox",
        summary="A normal follow-up email is converted into a reminder and a CRM note.",
        entities={
            "category": "follow_up",
            "priority": "low",
            "intent": "check_status",
        },
        steps=[
            ScenarioStep("detect", "scan inbox", "The inbox reveals a follow-up message."),
            ScenarioStep("classify", "tag follow-up", "The message is not urgent, but requires tracking."),
            ScenarioStep("extract", "capture context", "Subject, sender, and due date hints are recorded."),
            ScenarioStep("register", "add reminder", "A task or calendar reminder is created."),
            ScenarioStep("notify", "send Telegram", "The operator gets a short status summary."),
        ],
        telegram=[
            "Follow-up detected",
            "Priority: low",
            "Action: review and respond when available",
        ],
        voice="Follow-up detected. Low priority. Review and respond when available.",
        voice_es="Seguimiento detectado. Prioridad baja. Revisar y responder cuando sea posible.",
        next_actions=[
            "Review the message later today",
            "Add a task if a response is needed",
        ],
    ),
    Scenario(
        id="email_digest_starlink",
        title="Email digest: Starlink billing",
        channel="gmail",
        source="Daily digest",
        summary="The daily email digest groups billing alerts and surfaces the most urgent item first.",
        entities={
            "category": "billing",
            "priority": "high",
            "queue": "email_digest",
        },
        steps=[
            ScenarioStep("fetch", "open IMAP cache", "The engine reads the inbox and cached summaries."),
            ScenarioStep("group", "categorize", "Emails are clustered into billing, social, and other buckets."),
            ScenarioStep("rank", "surface urgency", "The Starlink billing alert is raised above the rest."),
            ScenarioStep("notify", "send digest", "Telegram receives a compact digest for the operator."),
        ],
        telegram=[
            "Daily digest ready",
            "Top item: Starlink billing alert",
            "Other items grouped into AI/APIs, social, and misc",
        ],
        voice="Daily digest ready. Top item is a Starlink billing alert.",
        voice_es="Resumen diario listo. El primer elemento es una alerta de facturación de Starlink.",
        next_actions=[
            "Open the billing thread",
            "Reply or defer with a reminder",
        ],
    ),
    Scenario(
        id="instagram_lead_scoring",
        title="Instagram: lead scoring",
        channel="instagram",
        source="Comments and followers",
        summary="An Instagram comment is scored, profiled, and promoted into the lead pipeline.",
        entities={
            "channel": "instagram",
            "source": "comment",
            "priority": "medium",
            "intent": "lead_capture",
        },
        steps=[
            ScenarioStep("capture", "detect new engagement", "A new comment or follower event is observed."),
            ScenarioStep("profile", "scrape profile", "Public profile details are read for lead scoring."),
            ScenarioStep("score", "classify hotness", "The lead is scored as cold, warm, or hot."),
            ScenarioStep("persist", "append lead record", "The lead is written to the leads ledger."),
            ScenarioStep("notify", "telegram summary", "The operator gets a short lead brief."),
        ],
        telegram=[
            "New Instagram lead",
            "Profile scored and classified",
            "Suggested next step: reply or nurture",
        ],
        voice="New Instagram lead scored and classified. Suggested next step is reply or nurture.",
        voice_es="Nuevo lead de Instagram puntuado y clasificado. El siguiente paso sugerido es responder o nutrir.",
        next_actions=[
            "Review lead score",
            "Send a personalized reply if score is high",
            "Add to nurture sequence",
        ],
    ),
    Scenario(
        id="whatsapp_business_autoresponse",
        title="WhatsApp Business: auto-response",
        channel="whatsapp",
        source="Webhook",
        summary="A WhatsApp webhook receives a reservation question and returns a structured auto-response.",
        entities={
            "channel": "whatsapp_business",
            "priority": "high",
            "intent": "reservation",
        },
        steps=[
            ScenarioStep("receive", "webhook POST", "Meta delivers a new WhatsApp message to the webhook."),
            ScenarioStep("classify", "detect intent", "The message is marked as reservation, price, location, or schedule."),
            ScenarioStep("answer", "compose response", "A structured answer is prepared from canned templates."),
            ScenarioStep("send", "reply via API", "The response is sent back over the Graph API."),
            ScenarioStep("log", "save lead", "The conversation is stored in the lead log."),
        ],
        telegram=[
            "WhatsApp webhook triggered",
            "Intent: reservation",
            "Auto-response sent from template",
        ],
        voice="WhatsApp webhook triggered. Reservation intent. Auto-response sent from template.",
        voice_es="Webhook de WhatsApp activado. Intención de reserva. Respuesta automática enviada desde plantilla.",
        next_actions=[
            "Inspect the conversation log",
            "Escalate to manual review if needed",
        ],
    ),
    Scenario(
        id="bridge_task_routing",
        title="Agent bridge: task routing",
        channel="bridge",
        source="Task queue",
        summary="The agent bridge routes a task to code, UI, or auto repair depending on the content.",
        entities={
            "queue": "task_queue",
            "priority": "system",
            "intent": "routing",
        },
        steps=[
            ScenarioStep("enqueue", "receive task", "A task is written to the shared queue."),
            ScenarioStep("classify", "route by keywords", "The bridge decides between code, UI, or auto repair."),
            ScenarioStep("dispatch", "select executor", "OpenCode or OpenClaw gets the work."),
            ScenarioStep("report", "write result", "The outcome is stored back into the bridge folder."),
        ],
        telegram=[
            "Bridge task accepted",
            "Route selected based on task type",
            "Result written to the shared queue",
        ],
        voice="Bridge task accepted. Route selected based on task type.",
        voice_es="Tarea del puente aceptada. La ruta se seleccionó según el tipo de tarea.",
        next_actions=[
            "Inspect the result file",
            "Retry with a narrower task if needed",
        ],
    ),
    Scenario(
        id="video_marketing_pipeline",
        title="Video marketing: content to publish",
        channel="video",
        source="Training pipeline",
        summary="A marketing asset becomes a video draft, then a ready-to-post deliverable.",
        entities={
            "category": "video_marketing",
            "priority": "medium",
            "intent": "publish",
        },
        steps=[
            ScenarioStep("ingest", "load source asset", "An image or clip enters the training pipeline."),
            ScenarioStep("generate", "produce variations", "The system creates crops, pans, captions, or edits."),
            ScenarioStep("review", "prepare deliverable", "Ready-to-post assets are generated."),
            ScenarioStep("publish", "post or queue", "The item can be posted or staged for approval."),
        ],
        telegram=[
            "Video asset processed",
            "Ready-to-post deliverable generated",
            "Suggested next step: review and publish",
        ],
        voice="Video asset processed. Ready-to-post deliverable generated.",
        voice_es="Activo de video procesado. Se generó un entregable listo para publicar.",
        next_actions=[
            "Check the output folder",
            "Approve for publishing",
        ],
    ),
]


def scenario_map() -> Dict[str, Scenario]:
    return {item.id: item for item in SCENARIOS}


def load_external_scenarios() -> List[Scenario]:
    """Load additional scenarios from a sibling JSON file if present.

    Supported JSON format:
      {
        "scenarios": [
          {
            "id": "...",
            "title": "...",
            "channel": "...",
            "source": "...",
            "summary": "...",
            "entities": {...},
            "steps": [{"stage": "...", "action": "...", "detail": "..."}],
            "telegram": ["..."],
            "voice": "...",
            "next_actions": ["..."]
          }
        ]
      }
    """

    extra_path = Path(__file__).with_name("puente_flow_pack.json")
    if not extra_path.exists():
        return []

    try:
        raw = json.loads(extra_path.read_text(encoding="utf-8"))
    except Exception:
        return []

    loaded: List[Scenario] = []
    for item in raw.get("scenarios", []):
        try:
            loaded.append(
                Scenario(
                    id=item["id"],
                    title=item["title"],
                    channel=item.get("channel", "unknown"),
                    source=item.get("source", "external"),
                    summary=item.get("summary", ""),
                    entities=dict(item.get("entities", {})),
                    steps=[
                        ScenarioStep(step["stage"], step["action"], step["detail"])
                        for step in item.get("steps", [])
                    ],
                    telegram=list(item.get("telegram", [])),
                    voice=item.get("voice", ""),
                    voice_es=item.get("voice_es", item.get("voice", "")),
                    next_actions=list(item.get("next_actions", [])),
                )
            )
        except Exception:
            continue
    return loaded


def render_scenario(scenario: Scenario) -> str:
    lines: List[str] = []
    lines.append(f"Scenario: {scenario.title}")
    lines.append(f"ID: {scenario.id}")
    lines.append(f"Channel: {scenario.channel}")
    lines.append(f"Source: {scenario.source}")
    lines.append("")
    lines.append("Summary:")
    lines.append(indent(scenario.summary, "  "))
    lines.append("")
    lines.append("Entities:")
    for key, value in scenario.entities.items():
        lines.append(f"  - {key}: {value}")
    lines.append("")
    lines.append("Flow:")
    for idx, step in enumerate(scenario.steps, start=1):
        lines.append(f"  {idx}. [{step.stage}] {step.action} — {step.detail}")
    lines.append("")
    lines.append("Telegram draft:")
    for line in scenario.telegram:
        lines.append(f"  - {line}")
    lines.append("")
    lines.append("Voice draft:")
    lines.append(f"  {render_voice_es(scenario)}")
    lines.append("")
    lines.append("Suggested next actions:")
    for action in scenario.next_actions:
        lines.append(f"  - {action}")
    return "\n".join(lines)


def render_telegram(scenario: Scenario) -> str:
    return "\n".join(
        [
            f"*{scenario.title}*",
            f"• Channel: {scenario.channel}",
            f"• Summary: {scenario.summary}",
            "",
            *[f"• {item}" for item in scenario.telegram],
        ]
    )


def render_voice(scenario: Scenario) -> str:
    return scenario.voice


def render_voice_es(scenario: Scenario) -> str:
    return scenario.voice_es or scenario.voice


def render_session(scenarios: List[Scenario], session_name: str = "client_demo") -> str:
    lines: List[str] = []
    lines.append(f"Session: {session_name}")
    lines.append(f"Events: {len(scenarios)}")
    lines.append("")
    lines.append("Storyline:")
    for idx, scenario in enumerate(scenarios, start=1):
        lines.append(f"  {idx}. {scenario.title} [{scenario.channel} / {scenario.source}]")
    lines.append("")
    lines.append("Timeline:")
    for idx, scenario in enumerate(scenarios, start=1):
        lines.append(f"## {idx}. {scenario.title}")
        lines.append(f"- ID: {scenario.id}")
        lines.append(f"- Channel: {scenario.channel}")
        lines.append(f"- Source: {scenario.source}")
        lines.append(f"- Summary: {scenario.summary}")
        lines.append("")
        lines.append("Steps:")
        for step_idx, step in enumerate(scenario.steps, start=1):
            lines.append(f"  {idx}.{step_idx} [{step.stage}] {step.action} — {step.detail}")
        lines.append("")
        lines.append("Telegram:")
        for item in scenario.telegram:
            lines.append(f"  - {item}")
        lines.append("")
        lines.append("Voice:")
        lines.append(f"  {render_voice_es(scenario)}")
        lines.append("")
        lines.append("Next:")
        for action in scenario.next_actions:
            lines.append(f"  - {action}")
        lines.append("")
    lines.append("Mermaid:")
    lines.append("```mermaid")
    lines.append("flowchart LR")
    for idx, scenario in enumerate(scenarios, start=1):
        node = f"S{idx}"
        label = scenario.title.replace('"', "'")
        lines.append(f'  {node}["{label}"]')
        if idx > 1:
            lines.append(f"  S{idx-1} --> {node}")
    lines.append("```")
    return "\n".join(lines)


def render_session_telegram(scenarios: List[Scenario], session_name: str = "client_demo") -> str:
    lines: List[str] = []
    lines.append(f"CRM demo session: {session_name}")
    lines.append("")
    for idx, scenario in enumerate(scenarios, start=1):
        lines.append(f"{idx}. {scenario.title}")
        lines.append(f"channel: {scenario.channel} | source: {scenario.source}")
        lines.append(f"summary: {scenario.summary}")
        lines.append("steps:")
        for step_idx, step in enumerate(scenario.steps, start=1):
            lines.append(f"  {step_idx}) {step.stage} - {step.action} - {step.detail}")
        lines.append("telegram:")
        for item in scenario.telegram:
            lines.append(f"  - {item}")
        lines.append(f"voice: {render_voice_es(scenario)}")
        lines.append("next:")
        for action in scenario.next_actions:
            lines.append(f"  - {action}")
        lines.append("")
    return "\n".join(lines).strip()


def render_dialogue(turns: List[DialogueTurn], title: str = "zira_demo") -> str:
    lines: List[str] = []
    lines.append(f"Dialogue: {title}")
    lines.append("")
    for turn in turns:
        lines.append(f"{turn.speaker}: {turn.text}")
    return "\n".join(lines)


def build_zira_dialogue() -> List[DialogueTurn]:
    return [
        DialogueTurn("Cliente", "Hola, estoy buscando una posada en la cordillera. ¿Me pasas info?"),
        DialogueTurn(
            "Zira",
            "Hola. Sí, te puedo ayudar. Somos una posada en Barreal, Calingasta, San Juan, al pie de la Cordillera de los Andes.",
        ),
        DialogueTurn(
            "Cliente",
            "¿Qué incluye la estadía y cuántas personas entran?",
        ),
        DialogueTurn(
            "Zira",
            "La casa incluye living-comedor, cocina equipada, baño, habitación principal, WiFi, pileta, galería y parrillero. Aceptamos de 1 a 5 personas.",
        ),
        DialogueTurn(
            "Cliente",
            "¿Tenés disponibilidad para el finde largo?",
        ),
        DialogueTurn(
            "Zira",
            "Decime las fechas exactas y cuántas personas son, así te confirmo disponibilidad al toque.",
        ),
        DialogueTurn(
            "Cliente",
            "Te mando una foto de una habitación, quiero que la evalúes para un post.",
        ),
        DialogueTurn(
            "Zira",
            "Recibido. Voy a guardar la foto, prepararla para edición y dejarla lista para revisión antes de publicar.",
        ),
        DialogueTurn(
            "Cliente",
            "Perfecto, si está buena la subimos al feed.",
        ),
        DialogueTurn(
            "Zira",
            "Listo. La foto queda en cola para editar, aprobar y postear cuando me des el ok.",
        ),
        DialogueTurn(
            "Cliente",
            "Gracias. ¿Me mandás también los precios?",
        ),
        DialogueTurn(
            "Zira",
            "Sí. Puedo enviarte el tarifario completo y ayudarte a coordinar la reserva por Telegram.",
        ),
    ]


def render_zira_demo() -> str:
    turns = build_zira_dialogue()
    lines: List[str] = []
    lines.append("Zira demo")
    lines.append("")
    lines.append("Contexto:")
    lines.append("  Posada en Barreal, Calingasta, San Juan, en la Cordillera de los Andes.")
    lines.append("  El bot responde consultas, recibe fotos y prepara acciones de contenido.")
    lines.append("")
    lines.append("Diálogo:")
    for turn in turns:
        lines.append(f"{turn.speaker}: {turn.text}")
    lines.append("")
    lines.append("Flujo interno:")
    lines.append("  1. Cliente consulta hospedaje.")
    lines.append("  2. Zira responde con contexto de posada.")
    lines.append("  3. Cliente envía foto por Telegram.")
    lines.append("  4. Zira guarda, prepara edición y deja en cola de publicación.")
    lines.append("  5. Cliente confirma si se publica.")
    return "\n".join(lines)


def dump_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=True, indent=2)


def export_bundle(scenario: Scenario) -> Dict[str, Any]:
    return {
        "scenario": asdict(scenario),
        "telegram": render_telegram(scenario),
        "voice": render_voice(scenario),
        "voice_es": render_voice_es(scenario),
        "human": render_scenario(scenario),
    }


def export_session_bundle(scenarios: List[Scenario], session_name: str) -> Dict[str, Any]:
    return {
        "session": session_name,
        "events": [asdict(s) for s in scenarios],
        "telegram": [render_telegram(s) for s in scenarios],
        "voice": [render_voice(s) for s in scenarios],
        "voice_es": [render_voice_es(s) for s in scenarios],
        "human": render_session(scenarios, session_name=session_name),
        "telegram_session": render_session_telegram(scenarios, session_name=session_name),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay CRM demo scenarios.")
    parser.add_argument("--list", action="store_true", help="List available scenarios.")
    parser.add_argument("--scenario", help="Scenario id to render.")
    parser.add_argument("--session", help="Render a multi-scenario demo session.")
    parser.add_argument(
        "--format",
        choices=("text", "telegram", "telegram-session", "dialogue", "voice", "voice-es", "json"),
        default="text",
        help="Output format for a scenario.",
    )
    parser.add_argument(
        "--export",
        type=Path,
        help="Write a full scenario bundle to a JSON file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write rendered text/markdown to a file.",
    )
    parser.add_argument(
        "--with-external",
        action="store_true",
        help="Include scenarios from simulators/puente_flow_pack.json if present.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.with_external:
        extra = load_external_scenarios()
        if extra:
            existing = {scenario.id for scenario in SCENARIOS}
            SCENARIOS.extend(s for s in extra if s.id not in existing)

    lookup = scenario_map()

    if args.session:
        if args.session == "zira_demo":
            rendered = render_zira_demo()
            print(rendered)
            if args.output:
                args.output.write_text(rendered + "\n", encoding="utf-8")
                print(f"\nWrote dialogue markdown to {args.output}")
            if args.export:
                args.export.write_text(
                    dump_json({"session": "zira_demo", "dialogue": [asdict(t) for t in build_zira_dialogue()]}) + "\n",
                    encoding="utf-8",
                )
                print(f"Exported dialogue bundle to {args.export}")
            return 0

        if args.session == "client_demo":
            session_ids = [
                "email_digest_starlink",
                "instagram_lead_scoring",
                "whatsapp_business_autoresponse",
                "bridge_task_routing",
                "video_marketing_pipeline",
            ]
        else:
            session_ids = [item.strip() for item in args.session.split(",") if item.strip()]

        scenarios: List[Scenario] = []
        missing: List[str] = []
        for sid in session_ids:
            if sid in lookup:
                scenarios.append(lookup[sid])
            else:
                missing.append(sid)
        if missing:
            print("Unknown session scenario(s):")
            for sid in missing:
                print(f"  - {sid}")
            return 2

        rendered = render_session(scenarios, session_name=args.session)
        if args.format == "telegram-session":
            rendered = render_session_telegram(scenarios, session_name=args.session)
        print(rendered)

        if args.output:
            args.output.write_text(rendered + "\n", encoding="utf-8")
            print(f"\nWrote session markdown to {args.output}")

        if args.export:
            args.export.write_text(
                dump_json(export_session_bundle(scenarios, args.session)) + "\n",
                encoding="utf-8",
            )
            print(f"Exported session bundle to {args.export}")
        return 0

    if args.list:
        for scenario in SCENARIOS:
            print(f"{scenario.id}\t{scenario.title}")
        return 0

    if not args.scenario:
        print("Use --list to see scenarios or --scenario <id> to render one.")
        return 1

    if args.scenario not in lookup:
        print(f"Unknown scenario: {args.scenario}")
        print("Available:")
        for scenario in SCENARIOS:
            print(f"  - {scenario.id}")
        return 2

    scenario = lookup[args.scenario]
    rendered: str
    if args.format == "telegram":
        rendered = render_telegram(scenario)
    elif args.format == "telegram-session":
        rendered = render_session_telegram([scenario], session_name=scenario.id)
    elif args.format == "dialogue":
        rendered = render_zira_demo()
    elif args.format == "voice":
        rendered = render_voice(scenario)
    elif args.format == "voice-es":
        rendered = render_voice_es(scenario)
    elif args.format == "json":
        rendered = dump_json(export_bundle(scenario))
    else:
        rendered = render_scenario(scenario)

    print(rendered)

    if args.export:
        args.export.write_text(dump_json(export_bundle(scenario)) + "\n", encoding="utf-8")
        print(f"\nExported bundle to {args.export}")

    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(f"\nWrote output to {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
