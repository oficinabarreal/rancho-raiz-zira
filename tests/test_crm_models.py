"""
Tests del Core CRM — modelos, enums y estructura de datos.
Verifica que los dataclasses y enums se comporten como espera la arquitectura.
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from crm.models import (
    JourneyStage, Channel,
    CustomerProfile, CustomerJourney,
    Lead, PhotoAsset, CRMEvent
)


class TestEnums(unittest.TestCase):
    """Valida que los enums del CRM tengan los valores esperados."""

    def test_journey_stage_values(self):
        stages = [e.value for e in JourneyStage]
        self.assertIn('new', stages)
        self.assertIn('qualified', stages)
        self.assertIn('booked', stages)
        self.assertIn('pre_arrival', stages)
        self.assertIn('in_stay', stages)
        self.assertIn('post_stay', stages)
        self.assertIn('lost', stages)

    def test_channel_values(self):
        channels = [e.value for e in Channel]
        self.assertIn('telegram', channels)
        self.assertIn('whatsapp', channels)
        self.assertIn('instagram', channels)
        self.assertIn('gmail', channels)
        self.assertIn('web', channels)
        self.assertIn('phone', channels)


class TestCustomerProfile(unittest.TestCase):
    """Valida CustomerProfile dataclass."""

    def test_defaults(self):
        p = CustomerProfile()
        self.assertEqual(p.name, "")
        self.assertEqual(p.phone, "")
        self.assertEqual(p.email, "")
        self.assertEqual(p.tags, [])

    def test_with_data(self):
        p = CustomerProfile(
            name="Juan Perez",
            phone="+5492645123456",
            email="juan@example.com",
            tags=["instagram", "lead"]
        )
        self.assertEqual(p.name, "Juan Perez")
        self.assertIn("instagram", p.tags)


class TestCustomerJourney(unittest.TestCase):
    """Valida CustomerJourney dataclass."""

    def test_default_stage(self):
        j = CustomerJourney()
        self.assertEqual(j.stage, JourneyStage.NEW)

    def test_with_data(self):
        j = CustomerJourney(
            stage=JourneyStage.BOOKED,
            source_channel=Channel.INSTAGRAM,
            arrival_date="2026-06-15",
            guests=2
        )
        self.assertEqual(j.stage, JourneyStage.BOOKED)
        self.assertEqual(j.guests, 2)
        self.assertIsNotNone(j.last_touch)


class TestLead(unittest.TestCase):
    """Valida Lead dataclass."""

    def test_lead_creation(self):
        profile = CustomerProfile(name="Maria Garcia", email="maria@test.com")
        journey = CustomerJourney(source_channel=Channel.TELEGRAM)
        lead = Lead(
            lead_id="lead_test_001",
            profile=profile,
            journey=journey,
            source="instagram"
        )
        self.assertEqual(lead.lead_id, "lead_test_001")
        self.assertEqual(lead.profile.name, "Maria Garcia")
        self.assertEqual(lead.journey.source_channel, Channel.TELEGRAM)
        self.assertEqual(lead.source, "instagram")
        self.assertEqual(lead.status, "open")

    def test_touch_updates_timestamp(self):
        profile = CustomerProfile(name="Test")
        journey = CustomerJourney()
        lead = Lead(lead_id="lead_002", profile=profile, journey=journey)
        old_touch = lead.journey.last_touch
        lead.touch()
        self.assertNotEqual(lead.journey.last_touch, old_touch)

    def test_to_dict(self):
        profile = CustomerProfile(name="Ana")
        journey = CustomerJourney()
        lead = Lead(lead_id="lead_003", profile=profile, journey=journey)
        d = lead.to_dict()
        self.assertEqual(d['lead_id'], 'lead_003')
        self.assertEqual(d['profile']['name'], 'Ana')


class TestPhotoAsset(unittest.TestCase):
    """Valida PhotoAsset dataclass."""

    def test_creation(self):
        asset = PhotoAsset(
            asset_id="photo_001",
            path="/tmp/foto.jpg"
        )
        self.assertEqual(asset.asset_id, "photo_001")
        self.assertEqual(asset.path, "/tmp/foto.jpg")
        self.assertEqual(asset.status, "new")

    def test_with_caption(self):
        asset = PhotoAsset(
            asset_id="photo_002",
            path="/tmp/habitacion.jpg",
            caption="Habitacion suite con vista"
        )
        self.assertEqual(asset.caption, "Habitacion suite con vista")


class TestCRMEvent(unittest.TestCase):
    """Valida CRMEvent dataclass."""

    def test_creation(self):
        event = CRMEvent(
            event_id="evt_001",
            kind="nueva_reserva",
            source=Channel.WHATSAPP,
            payload={"habitacion": "suite", "noches": 3}
        )
        self.assertEqual(event.kind, "nueva_reserva")
        self.assertEqual(event.source, Channel.WHATSAPP)
        self.assertEqual(event.payload["noches"], 3)
        self.assertIsNotNone(event.created_at)


if __name__ == '__main__':
    unittest.main()
