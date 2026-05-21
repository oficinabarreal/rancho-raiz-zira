from __future__ import annotations

import json
import hashlib
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

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
from .models import Channel, CRMEvent, CustomerJourney, CustomerProfile, JourneyStage, Lead, PhotoAsset
from .photo_pipeline import PhotoPipeline
from .store import CRMStore


class CRMOrchestrator:
    def __init__(self, root: Path | str, connectors: Dict[str, Any], dry_run: bool = True):
        self.store = CRMStore(root)
        self.connectors = connectors
        self.dry_run = dry_run
        self.photo_pipeline = PhotoPipeline(self.store.root)

    def _lead_id(self, profile: CustomerProfile, source: str) -> str:
        basis = "|".join([profile.email, profile.phone, profile.name, source]).strip("|")
        if not basis:
            basis = f"anon|{source}"
        return hashlib.sha1(basis.encode("utf-8")).hexdigest()[:12]

    def _default_profile(self, source: str, payload: Dict[str, Any]) -> CustomerProfile:
        return CustomerProfile(
            name=payload.get("name", ""),
            phone=payload.get("phone", ""),
            email=payload.get("email", ""),
            origin=source,
            notes=payload.get("notes", ""),
            tags=list(payload.get("tags", [])),
            metadata=dict(payload.get("metadata", {})),
        )

    def ingest_event(self, source: Channel | str, payload: Dict[str, Any]) -> Lead:
        source_name = source.value if isinstance(source, Channel) else str(source)
        profile = self._default_profile(source_name, payload)
        lead_id = self._lead_id(profile, source_name)
        source_channel = self._resolve_channel(source_name)
        journey = CustomerJourney(
            stage=JourneyStage.NEW,
            source_channel=source_channel,
            arrival_date=payload.get("arrival_date"),
            departure_date=payload.get("departure_date"),
            guests=int(payload.get("guests", 0) or 0),
            preferences=dict(payload.get("preferences", {})),
        )
        lead = Lead(
            lead_id=lead_id,
            profile=profile,
            journey=journey,
            score=int(payload.get("score", 0) or 0),
            status=payload.get("status", "open"),
            source=source_name,
            context=dict(payload.get("context", {})),
        )
        lead.interactions.append(
            {
                "ts": datetime.utcnow().isoformat() + "Z",
                "kind": "ingest",
                "source": source_name,
                "payload": payload,
            }
        )
        self.store.upsert_lead(lead)
        self.store.record_event(
            CRMEvent(
                event_id=lead_id,
                kind="ingest",
                source=source_channel,
                payload=payload,
            )
        )
        return lead

    def _resolve_channel(self, source_name: str) -> Channel:
        for channel in Channel:
            if channel.value == source_name:
                return channel
        return Channel.WEB

    def qualify_lead(self, lead: Lead) -> Lead:
        score = lead.score
        if not score:
            score = 20
            if lead.profile.email:
                score += 10
            if lead.profile.phone:
                score += 10
            if lead.journey.guests:
                score += 10
            if lead.journey.arrival_date:
                score += 10
        lead.score = min(score, 100)
        if lead.score >= 80:
            lead.journey.stage = JourneyStage.BOOKED
        elif lead.score >= 50:
            lead.journey.stage = JourneyStage.QUALIFIED
        else:
            lead.journey.stage = JourneyStage.NEW
        lead.touch()
        self.store.upsert_lead(lead)
        return lead

    def schedule_pre_arrival(self, lead: Lead) -> Dict[str, Any]:
        start_date = lead.journey.arrival_date
        if not start_date:
            return {"scheduled": False, "reason": "missing arrival_date"}
        when = f"{start_date}T18:00:00"
        end_when = f"{start_date}T18:30:00"
        calendar = self.connectors.get("calendar")
        sheet = self.connectors.get("sheets")
        event = {
            "summary": f"Check-in follow-up for {lead.profile.name or lead.lead_id}",
            "start": when,
            "end": end_when,
            "description": "Remind the guest, share arrival instructions and hospitality touchpoints.",
        }
        calendar_result = calendar.create_event(**event) if calendar else None
        sheet_result = sheet.append_row(
            "crm_journey",
            [lead.lead_id, "pre_arrival", lead.profile.name, lead.journey.arrival_date, lead.profile.email, lead.profile.phone],
        ) if sheet else None
        lead.journey.stage = JourneyStage.PRE_ARRIVAL
        lead.touch()
        self.store.upsert_lead(lead)
        return {
            "scheduled": True,
            "calendar": asdict(calendar_result) if calendar_result else None,
            "sheet": asdict(sheet_result) if sheet_result else None,
        }

    def handle_photo(self, photo: PhotoAsset, lead: Optional[Lead] = None) -> Dict[str, Any]:
        try:
            processed = self.photo_pipeline.process(photo.path, photo.asset_id, caption=photo.caption)
            photo.metadata.update({"pipeline": processed})
            photo.status = "processed"
        except Exception as exc:
            photo.metadata.update({"pipeline_error": str(exc)})
            photo.status = "needs_review"
        self.store.upsert_asset(photo)
        notion = self.connectors.get("notion")
        drive = self.connectors.get("drive")
        kommo = self.connectors.get("kommo")
        telegram = self.connectors.get("telegram")
        results: Dict[str, Any] = {"asset_id": photo.asset_id}

        if drive:
            results["drive"] = asdict(drive.upload(photo.path, folder="crm/photos"))
        if notion:
            results["notion"] = asdict(
                notion.create_page(
                    title=f"Photo asset {photo.asset_id}",
                    content=f"Caption: {photo.caption}\nPath: {photo.path}\nStatus: {photo.status}",
                    database="crm_photo_assets",
                    )
                )
        if kommo and lead:
            results["kommo"] = asdict(kommo.update_status(lead.lead_id, "content_review"))
        if telegram and "pipeline" in photo.metadata:
            preview_path = photo.metadata["pipeline"]["variants"]["preview"]["path"]
            caption = photo.caption or f"Foto procesada {photo.asset_id}"
            try:
                results["telegram"] = asdict(telegram.send_photo(preview_path, caption=caption))
            except Exception as exc:
                results["telegram"] = {"ok": False, "error": str(exc), "preview": preview_path}
        if "pipeline" in photo.metadata:
            results["pipeline"] = photo.metadata["pipeline"]
        return results

    def notify_guest(self, lead: Lead, message: str) -> Dict[str, Any]:
        telegram = self.connectors.get("telegram")
        whatsapp = self.connectors.get("whatsapp")
        results: Dict[str, Any] = {}
        if telegram:
            results["telegram"] = asdict(telegram.send_message(message))
        if whatsapp and lead.profile.phone:
            results["whatsapp"] = asdict(whatsapp.send_message(lead.profile.phone, message))
        if not results:
            results["local"] = {"ok": True, "channel": "simulated", "message": message}
        return results

    def publish_lead_to_kommo(self, lead: Lead) -> Dict[str, Any]:
        kommo = self.connectors.get("kommo")
        notion = self.connectors.get("notion")
        result: Dict[str, Any] = {}
        if kommo:
            result["kommo"] = asdict(
                kommo.create_lead(
                    title=lead.profile.name or lead.lead_id,
                    payload={
                        "lead_id": lead.lead_id,
                        "stage": lead.journey.stage.value,
                        "score": lead.score,
                    },
                )
            )
        if notion:
            result["notion"] = asdict(
                notion.create_page(
                    title=f"Lead {lead.profile.name or lead.lead_id}",
                    content=json_dumps_safe(lead.to_dict()),
                    database="crm_leads",
                )
            )
        return result

    def simulate_guest_journey(
        self,
        payload: Dict[str, Any],
        source: Channel | str = Channel.WEB,
        photo_path: Optional[str] = None,
        photo_caption: str = "",
    ) -> Dict[str, Any]:
        lead = self.ingest_event(source, payload)
        lead = self.qualify_lead(lead)
        journey: Dict[str, Any] = {
            "lead": lead.to_dict(),
            "brief": self.guest_experience_brief(lead),
            "kommo_notion": self.publish_lead_to_kommo(lead),
            "pre_arrival": self.schedule_pre_arrival(lead),
            "welcome": self.notify_guest(
                lead,
                "Hola, soy Zira. Te acompaño antes de llegar, durante la estadía y después del check-out.",
            ),
        }
        if photo_path:
            journey["photo"] = self.ingest_photo_asset(photo_path, caption=photo_caption, lead=lead)
        return journey

    def ingest_photo_asset(self, path: str, caption: str = "", lead: Optional[Lead] = None) -> Dict[str, Any]:
        asset_id = hashlib.sha1(path.encode("utf-8")).hexdigest()[:12]
        photo = PhotoAsset(asset_id=asset_id, path=path, caption=caption)
        result = self.handle_photo(photo, lead=lead)
        photo.status = "ready_for_review" if "pipeline" in photo.metadata else photo.status
        self.store.upsert_asset(photo)
        return result

    def ingest_gmail_digest(self, limit: int = 10) -> Dict[str, Any]:
        gmail = self.connectors.get("gmail")
        telegram = self.connectors.get("telegram")
        if not gmail:
            return {"error": "gmail connector missing"}
        resp = gmail.list_messages(max_results=limit)
        if not resp.ok:
            return {"error": resp.error}
        if resp.data.get("dry_run"):
            return {"dry_run": True, "messages": resp.data.get("payload", {}).get("messages", [])}
        emails = resp.data.get("messages", [])
        result: List[Dict[str, Any]] = []
        for email in emails:
            subject = email.get("subject", "")
            snippet = email.get("snippet", "")
            sender = email.get("from", "")
            lead_seed = {
                "name": extract_name(sender),
                "email": extract_email(sender),
                "notes": subject,
                "context": {"snippet": snippet, "sender": sender, "subject": subject},
            }
            if self._is_booking_email(subject, snippet):
                lead_seed["score"] = 65
                lead_seed["status"] = "open"
            lead = self.ingest_event(
                Channel.GMAIL,
                lead_seed,
            )
            lead = self.qualify_lead(lead)
            if lead.score >= 50:
                self.publish_lead_to_kommo(lead)
                if lead.journey.arrival_date:
                    self.schedule_pre_arrival(lead)
            result.append({"lead_id": lead.lead_id, "subject": subject, "score": lead.score})
        if telegram:
            telegram.send_message(self.render_digest(result))
        return {"count": len(result), "items": result}

    def _is_booking_email(self, subject: str, snippet: str) -> bool:
        text = f"{subject} {snippet}".lower()
        keywords = [
            "reserva",
            "booking",
            "availability",
            "disponibilidad",
            "consulta",
            "precio",
            "estadía",
            "estadía",
            "hospedaje",
            "check in",
            "check-in",
        ]
        return any(word in text for word in keywords)

    def render_digest(self, items: List[Dict[str, Any]]) -> str:
        lines = ["CRM digest listo", ""]
        for item in items[:8]:
            lines.append(f"- {item.get('subject', '')} | score {item.get('score', 0)}")
        return "\n".join(lines)

    def guest_experience_brief(self, lead: Lead) -> str:
        parts = [
            "Experiencia de la posada",
            f"Cliente: {lead.profile.name or 'sin nombre'}",
            f"Etapa: {lead.journey.stage.value}",
            f"Fechas: {lead.journey.arrival_date or 'pendiente'} → {lead.journey.departure_date or 'pendiente'}",
            f"Huéspedes: {lead.journey.guests or 'pendiente'}",
            f"Preferencias: {lead.journey.preferences or {}}",
            f"Canal: {lead.journey.source_channel.value}",
            "Puedo ayudar antes de la llegada, durante la estadía y después del check-out.",
        ]
        return "\n".join(parts)


def json_dumps_safe(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def extract_email(sender: str) -> str:
    if "<" in sender and ">" in sender:
        return sender.split("<", 1)[1].split(">", 1)[0].strip()
    if "@" in sender:
        return sender.strip()
    return ""


def extract_name(sender: str) -> str:
    if "<" in sender:
        return sender.split("<", 1)[0].strip().strip('"')
    if "@" in sender:
        return sender.split("@", 1)[0].replace(".", " ").replace("_", " ").title()
    return sender.strip() or "Cliente"
