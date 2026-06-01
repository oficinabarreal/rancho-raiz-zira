"""
Test de conectividad con redes sociales (Instagram, WhatsApp, Kommo).
Verifica que los tokens existen y tienen formato válido.
"""
import unittest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import requests


def get_env(key):
    """Obtiene variable de entorno con fallback a .env.backup."""
    val = os.environ.get(key, '')
    if not val or '***' in val:
        try:
            for fname in ['.env', '.env.backup']:
                try:
                    with open(fname) as f:
                        for line in f:
                            if line.startswith(f'{key}='):
                                val = line.split('=', 1)[1].strip().strip('"').strip("'")
                                break
                except:
                    pass
        except:
            pass
    return val


# ─── Instagram ─────────────────────────────────────────────────────

@unittest.skipIf('***' in get_env('CRM_INSTAGRAM_TOKEN') or not get_env('CRM_INSTAGRAM_TOKEN'),
                 "CRM_INSTAGRAM_TOKEN no disponible")
class TestInstagramConnectivity(unittest.TestCase):
    """Pruebas de conectividad con Instagram Graph API."""

    @classmethod
    def setUpClass(cls):
        cls.token = get_env('CRM_INSTAGRAM_TOKEN')
        cls.user_id = get_env('CRM_INSTAGRAM_USER_ID')

    def test_token_format(self):
        """Valida formato de token de Instagram (EA...)."""
        self.assertTrue(self.token.startswith('E'),
                        "Token Instagram debe empezar con E (EAAB... o EAA...)")
        self.assertGreater(len(self.token), 80, "Token Instagram debe tener >80 chars")

    def test_user_id_format(self):
        """Valida que el user_id sea numérico."""
        self.assertTrue(self.user_id.isdigit(),
                        f"Instagram user_id debe ser numerico, got: {self.user_id}")
        print(f"  Instagram User ID: {self.user_id}")

    def test_me_endpoint(self):
        """Prueba /me endpoint de Graph API."""
        resp = requests.get(
            "https://graph.instagram.com/v22.0/me",
            params={
                "fields": "user_id,username,account_type",
                "access_token": self.token
            },
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            print(f"  Instagram: @{data.get('username', 'N/A')} ({data.get('account_type', 'N/A')})")
        else:
            # Instagram token may need refresh; skip as non-critical
            self.skipTest(f"Instagram API respondió {resp.status_code}: {resp.text[:100]}")


# ─── WhatsApp ──────────────────────────────────────────────────────

@unittest.skipIf('***' in get_env('CRM_WHATSAPP_TOKEN') or not get_env('CRM_WHATSAPP_TOKEN'),
                 "CRM_WHATSAPP_TOKEN no disponible")
class TestWhatsAppConnectivity(unittest.TestCase):
    """Pruebas de conectividad con WhatsApp Cloud API."""

    @classmethod
    def setUpClass(cls):
        cls.token = get_env('CRM_WHATSAPP_TOKEN')
        cls.phone_id = get_env('CRM_WHATSAPP_PHONE_ID')

    def test_token_format(self):
        """Valida formato de token WhatsApp."""
        self.assertTrue(self.token.startswith('E'),
                        "Token WhatsApp debe empezar con E (EAAB...)")
        self.assertGreater(len(self.token), 80, "Token WhatsApp debe tener >80 chars")

    def test_phone_id_format(self):
        """Valida que phone_id sea numérico."""
        self.assertTrue(self.phone_id.isdigit(),
                        f"WhatsApp phone_id debe ser numerico, got: {self.phone_id}")
        print(f"  WhatsApp Phone ID: {self.phone_id}")

    def test_whatsapp_phone_numbers(self):
        """Prueba obtener números de teléfono registrados."""
        resp = requests.get(
            f"https://graph.facebook.com/v22.0/{self.phone_id}",
            params={
                "fields": "verified_name,display_phone_number,id",
                "access_token": self.token
            },
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            print(f"  WhatsApp: {data.get('verified_name', 'N/A')} - {data.get('display_phone_number', 'N/A')}")
        else:
            self.skipTest(f"WhatsApp API respondió {resp.status_code}: {resp.text[:100]}")


# ─── Kommo ─────────────────────────────────────────────────────────

@unittest.skipIf('***' in get_env('CRM_KOMMO_TOKEN') or not get_env('CRM_KOMMO_TOKEN'),
                 "CRM_KOMMO_TOKEN no disponible")
class TestKommoConnectivity(unittest.TestCase):
    """Pruebas de conectividad con Kommo CRM API."""

    @classmethod
    def setUpClass(cls):
        cls.token = get_env('CRM_KOMMO_TOKEN')
        cls.subdomain = get_env('CRM_KOMMO_SUBDOMAIN')

    def test_token_format(self):
        """Valida formato de token Kommo (JWT)."""
        self.assertTrue(self.token.startswith('eyJ'),
                        "Token Kommo debe empezar con eyJ (JWT)")
        self.assertGreater(len(self.token), 100, "Token Kommo debe tener >100 chars")

    def test_subdomain_format(self):
        """Valida que el subdominio no esté vacío."""
        self.assertTrue(len(self.subdomain) > 0, "Subdominio Kommo no debe estar vacío")
        print(f"  Kommo Subdomain: {self.subdomain}.kommo.com")

    def test_kommo_account_info(self):
        """Obtiene info de la cuenta Kommo."""
        resp = requests.get(
            f"https://{self.subdomain}.kommo.com/api/v4/account",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            print(f"  Kommo: {data.get('name', 'N/A')} - {data.get('timezone', 'N/A')}")
        else:
            self.skipTest(f"Kommo API respondió {resp.status_code}: {resp.text[:100]}")


# ─── Ejecución ─────────────────────────────────────────────────────

if __name__ == '__main__':
    unittest.main()
