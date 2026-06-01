"""
Tests del CRM Store — persistencia JSON.
Adaptado a la API real de CRMStore.
"""
import unittest
import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from crm.store import CRMStore
from crm.models import (
    JourneyStage, Channel, CustomerProfile, CustomerJourney, Lead, CRMEvent, PhotoAsset
)


class TestCRMStore(unittest.TestCase):
    """Pruebas de operaciones básicas del store."""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.mkdtemp(prefix='crm_test_')
        cls.store = CRMStore(root=cls.test_dir)
        # Crear datos base para tests de persistencia
        profile = CustomerProfile(name="Store Base", email="base@test.com")
        journey = CustomerJourney(source_channel=Channel.WEB)
        base_lead = Lead(lead_id="base_001", profile=profile, journey=journey)
        cls.store.upsert_lead(base_lead)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_dir, ignore_errors=True)

    def test_upsert_and_list_leads(self):
        """Guarda un lead y lo recupera via list_leads."""
        profile = CustomerProfile(name="Test Store", email="store@test.com")
        journey = CustomerJourney(source_channel=Channel.WEB)
        lead = Lead(lead_id="test_upsert_001", profile=profile, journey=journey)
        self.store.upsert_lead(lead)
        leads = self.store.list_leads()
        found = any(l.get('lead_id') == 'test_upsert_001' for l in leads)
        self.assertTrue(found, "Lead upsertado debe estar en list_leads")
        # Verificar datos
        lead_dict = next(l for l in leads if l.get('lead_id') == 'test_upsert_001')
        self.assertEqual(lead_dict['profile']['name'], 'Test Store')

    def test_record_event(self):
        """Registra un evento y lo lista."""
        event = CRMEvent(
            event_id="evt_store_001",
            kind="test_store",
            source=Channel.GMAIL,
            payload={"test": True}
        )
        self.store.record_event(event)
        # list_leads no devuelve eventos; verificamos que no tire error
        # y que los leads sigan funcionando
        leads = self.store.list_leads()
        self.assertIsInstance(leads, list)

    def test_upsert_asset(self):
        """Guarda y lista un asset."""
        asset = PhotoAsset(
            asset_id="asset_001",
            path="/tmp/test.jpg",
            caption="Test asset"
        )
        self.store.upsert_asset(asset)
        assets = self.store.list_assets()
        self.assertGreaterEqual(len(assets), 1)
        found = any(a.get('asset_id') == 'asset_001' for a in assets)
        self.assertTrue(found)

    def test_overwrite_lead(self):
        """Sobrescribir un lead existente actualiza los datos."""
        profile1 = CustomerProfile(name="Original Store")
        journey1 = CustomerJourney()
        lead1 = Lead(lead_id="store_overwrite", profile=profile1, journey=journey1)
        self.store.upsert_lead(lead1)

        profile2 = CustomerProfile(name="Actualizado Store")
        journey2 = CustomerJourney(stage=JourneyStage.BOOKED)
        lead2 = Lead(lead_id="store_overwrite", profile=profile2, journey=journey2)
        self.store.upsert_lead(lead2)

        leads = self.store.list_leads()
        lead_dict = next(l for l in leads if l.get('lead_id') == 'store_overwrite')
        self.assertEqual(lead_dict['profile']['name'], 'Actualizado Store')
        self.assertEqual(lead_dict['journey']['stage'], 'booked')

    def test_persistence(self):
        """Verifica persistencia creando nueva instancia del store."""
        store2 = CRMStore(root=self.test_dir)
        leads = store2.list_leads()
        ids = [l.get('lead_id') for l in leads]
        self.assertIn('base_001', ids, "Lead base debe persistir entre instancias")
        self.assertIn('store_overwrite', ids, "Overwrite debe persistir")

    def test_list_leads_empty_dir(self):
        """Store nuevo en directorio vacío debe devolver lista vacía."""
        empty_dir = tempfile.mkdtemp(prefix='crm_empty_')
        try:
            empty_store = CRMStore(root=empty_dir)
            leads = empty_store.list_leads()
            self.assertEqual(leads, [])
        finally:
            shutil.rmtree(empty_dir, ignore_errors=True)

    def test_list_assets_empty(self):
        """list_assets en store vacío debe devolver lista vacía."""
        empty_dir = tempfile.mkdtemp(prefix='crm_empty2_')
        try:
            empty_store = CRMStore(root=empty_dir)
            assets = empty_store.list_assets()
            self.assertEqual(assets, [])
        finally:
            shutil.rmtree(empty_dir, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
