from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class JourneyStage(str, Enum):
    NEW = "new"
    QUALIFIED = "qualified"
    BOOKED = "booked"
    PRE_ARRIVAL = "pre_arrival"
    IN_STAY = "in_stay"
    POST_STAY = "post_stay"
    LOST = "lost"


class Channel(str, Enum):
    GMAIL = "gmail"
    WHATSAPP = "whatsapp"
    INSTAGRAM = "instagram"
    TELEGRAM = "telegram"
    PHONE = "phone"
    WEB = "web"


@dataclass
class CustomerProfile:
    name: str = ""
    phone: str = ""
    email: str = ""
    origin: str = ""
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CustomerJourney:
    stage: JourneyStage = JourneyStage.NEW
    source_channel: Channel = Channel.WEB
    arrival_date: Optional[str] = None
    departure_date: Optional[str] = None
    guests: int = 0
    preferences: Dict[str, Any] = field(default_factory=dict)
    last_touch: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


@dataclass
class Lead:
    lead_id: str
    profile: CustomerProfile
    journey: CustomerJourney
    score: int = 0
    status: str = "open"
    source: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    interactions: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def touch(self) -> None:
        self.updated_at = datetime.utcnow().isoformat() + "Z"
        self.journey.last_touch = self.updated_at

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PhotoAsset:
    asset_id: str
    path: str
    caption: str = ""
    status: str = "new"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


@dataclass
class CRMEvent:
    event_id: str
    kind: str
    source: Channel
    payload: Dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

