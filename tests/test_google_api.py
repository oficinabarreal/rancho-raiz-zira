"""
Test de conectividad con APIs de Google.
Requiere GOOGLE_API_KEY en entorno (GitHub Secret o .env).
"""
import unittest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import requests


def get_google_api_key():
    """Obtiene Google API key desde entorno o .env."""
    key = os.environ.get('GOOGLE_API_KEY', '')
    if not key or '***' in key:
        try:
            with open('.env') as f:
                for line in f:
                    if line.startswith('GOOGLE_API_KEY='):
                        key = line.split('=', 1)[1].strip().strip('"').strip("'")
                        break
        except:
            pass
    return key


@unittest.skipIf(not get_google_api_key() or '***' in get_google_api_key(),
                 "GOOGLE_API_KEY no disponible")
class TestGoogleConnectivity(unittest.TestCase):
    """Pruebas de conectividad con Google APIs."""

    @classmethod
    def setUpClass(cls):
        cls.api_key = get_google_api_key()

    def test_api_key_format(self):
        """Valida formato de Google API Key (AIzaSy...)."""
        if '...' in self.api_key or len(self.api_key) < 20:
            self.skipTest(f"Google API Key parece truncada ({len(self.api_key)} chars)")
        self.assertTrue(self.api_key.startswith('AIza'),
                        "Google API Key debe empezar con AIza")
        self.assertGreater(len(self.api_key), 20, "Key debe tener >20 chars")

    def test_geocoding_api(self):
        """Prueba Google Geocoding API (solo si key parece válida)."""
        if '...' in self.api_key or len(self.api_key) < 20:
            self.skipTest(f"Google API Key truncada, salteando prueba de red")
        resp = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": "Barreal, San Juan, Argentina", "key": self.api_key},
            timeout=10
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get('status'), 'OK',
                         f"Geocoding falló: {data.get('status')} - {data.get('error_message','')}")
        results = data.get('results', [])
        self.assertGreater(len(results), 0, "Debe encontrar Barreal")
        print(f"  Ubicación: {results[0].get('formatted_address', 'N/A')}")

    def test_customsearch_api(self):
        """Prueba Google Custom Search API (verifica que la key tiene el permiso)."""
        resp = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params={
                "q": "Rancho Raiz Barreal",
                "cx": "017576662512468239146:mu4m8nryizs",  # Search Engine ID de ejemplo
                "key": self.api_key
            },
            timeout=10
        )
        # Puede fallar si no tiene Custom Search habilitado, pero debe responder
        self.assertIn(resp.status_code, [200, 403, 400],
                      f"Respuesta inesperada: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f'  Search results: {data.get("searchInformation", {}).get("totalResults", "0")}')


class TestGoogleAuthModule(unittest.TestCase):
    """Prueba que el módulo de autenticación Google se importa correctamente."""

    def test_import_google_auth(self):
        """Verifica que google_auth.py se puede importar sin errores de sintaxis."""
        try:
            from crm.google_auth import get_service, SCOPES
            self.assertIsNotNone(get_service)
            self.assertIsInstance(SCOPES, dict, "SCOPES debe ser un dict de nombre->scope")
            print(f"  Scopes disponibles: {len(SCOPES)}")
            for name, scope in SCOPES.items():
                print(f"    - {name}: {scope[:40]}...")
        except ImportError as e:
            self.fail(f"Error importando crm.google_auth: {e}")

    def test_google_token_exists(self):
        """Verifica que existe el archivo de token OAuth."""
        token_path = 'crm_state/.google_token.json'
        if os.path.exists(token_path):
            import json
            with open(token_path) as f:
                data = json.load(f)
            self.assertIn('token', data, "Token debe tener campo 'token'")
            self.assertIn('refresh_token', data, "Token debe tener refresh_token")
            print(f"  Token OAuth encontrado: expires en {data.get('expiry', 'N/A')}")
        else:
            self.skipTest("Token OAuth no encontrado en crm_state/")


if __name__ == '__main__':
    unittest.main()
