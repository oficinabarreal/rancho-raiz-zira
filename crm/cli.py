from __future__ import annotations

import argparse
import os
from pathlib import Path

from .connectors import (
    CalendarConnector,
    DriveConnector,
    GmailConnector,
    InstagramConnector,
    KommoConnector,
    NotionConnector,
    SheetsConnector,
    TelegramConnector,
    WhatsAppConnector,
)
from .models import Channel
from .orchestrator import CRMOrchestrator
from .google_auth import _token_path


def build_connectors() -> dict:
    connectors: dict = {
        "drive": DriveConnector(),
        "calendar": CalendarConnector(),
        "sheets": SheetsConnector(),
        "whatsapp": WhatsAppConnector(),
        "instagram": InstagramConnector(),
        "kommo": KommoConnector(),
        "notion": NotionConnector(),
    }

    connectors["gmail"] = GmailConnector()

    tg_token = os.environ.get("CRM_TG_TOKEN")
    tg_chat = os.environ.get("CRM_TG_CHAT_ID")
    if tg_token and tg_chat:
        connectors["telegram"] = TelegramConnector(tg_token, int(tg_chat))

    return connectors


def check_connectors(connectors: dict) -> dict:
    status = {}
    for name, conn in connectors.items():
        if name in ("gmail", "telegram"):
            status[name] = "real" if conn.enabled else "disabled"
        else:
            svc = getattr(conn, "_service", None) if hasattr(conn, "_svc") else None
            if svc and svc() is not None:
                status[name] = "real"
            elif getattr(conn, "access_token", "") or getattr(conn, "token", ""):
                status[name] = "configured"
            else:
                status[name] = "dry-run"
    return status


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CRM CLI for Rancho Raíz / Zira")
    parser.add_argument("--root", default="crm_state", help="Storage root for CRM JSON state")
    parser.add_argument("--gmail-digest", action="store_true", help="Fetch Gmail digest and qualify leads")
    parser.add_argument("--limit", type=int, default=10, help="Limit for Gmail digest")
    parser.add_argument("--brief", action="store_true", help="Print a short guest-experience brief")
    parser.add_argument("--lead-name", help="Seed a lead name for a demo")
    parser.add_argument("--arrival-date", help="Arrival date YYYY-MM-DD")
    parser.add_argument("--departure-date", help="Departure date YYYY-MM-DD")
    parser.add_argument("--guests", type=int, default=0, help="Guest count")
    parser.add_argument("--phone", default="", help="Phone number")
    parser.add_argument("--email", default="", help="Email")
    parser.add_argument("--photo", help="Path to a photo asset to process")
    parser.add_argument("--photo-caption", default="", help="Caption for the photo asset")
    parser.add_argument("--photo-only", action="store_true", help="Only process the photo and exit")
    parser.add_argument("--journey-demo", action="store_true", help="Run an end-to-end guest journey demo")
    parser.add_argument("--demo-photo", default="simulators/_test_photo.jpg", help="Photo to use for the journey demo")
    parser.add_argument("--check-connectors", action="store_true", help="Show connector status (real vs dry-run)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    connectors = build_connectors()

    if args.check_connectors:
        print("=== Estado de conectores ===")
        for name, conn in connectors.items():
            token_attrs = ("access_token", "token", "app_password")
            has_token = any(getattr(conn, a, "") for a in token_attrs)
            if name in ("drive", "calendar", "sheets"):
                print(f"  {name}: {'OAuth configurado' if Path(_token_path()).exists() else 'dry-run (falta auth)'}")
            elif has_token:
                print(f"  {name}: configurado")
            else:
                print(f"  {name}: dry-run (sin credenciales)")
        return 0

    orchestrator = CRMOrchestrator(Path(args.root), connectors, dry_run=True)

    if args.gmail_digest:
        result = orchestrator.ingest_gmail_digest(limit=args.limit)
        print(result)
        return 0

    if args.journey_demo:
        payload = {
            "name": args.lead_name or "Cliente demo",
            "phone": args.phone,
            "email": args.email,
            "arrival_date": args.arrival_date or "2026-06-01",
            "departure_date": args.departure_date or "2026-06-05",
            "guests": args.guests or 2,
            "notes": "Demo end-to-end del flujo del huésped",
            "context": {"source": "journey_demo"},
        }
        demo = orchestrator.simulate_guest_journey(
            payload,
            source=Channel.GMAIL if (args.email or args.phone) else Channel.WEB,
            photo_path=args.photo or args.demo_photo,
            photo_caption=args.photo_caption or "Foto de demo para revisar y publicar",
        )
        print(demo["brief"])
        print(demo["kommo_notion"])
        print(demo["pre_arrival"])
        print(demo["welcome"])
        if "photo" in demo:
            print(demo["photo"])
        return 0

    lead = orchestrator.ingest_event(
        Channel.WEB,
        {
            "name": args.lead_name or "Cliente demo",
            "phone": args.phone,
            "email": args.email,
            "arrival_date": args.arrival_date,
            "departure_date": args.departure_date,
            "guests": args.guests,
            "notes": "Demo lead",
            "context": {"source": "cli"},
        },
    )
    lead = orchestrator.qualify_lead(lead)

    if args.photo:
        print(orchestrator.ingest_photo_asset(args.photo, caption=args.photo_caption, lead=lead))
        if args.photo_only:
            return 0

    if args.brief:
        print(orchestrator.guest_experience_brief(lead))
    else:
        print(lead.to_dict())

    print(orchestrator.publish_lead_to_kommo(lead))
    print(orchestrator.schedule_pre_arrival(lead))
    print(orchestrator.notify_guest(lead, "Hola, soy Zira. Te acompaño antes de llegar, durante la estadía y después del check-out."))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
