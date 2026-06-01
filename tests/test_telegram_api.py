"""
Test de conectividad con Telegram Bot API.
Requiere CRM_TG_TOKEN en entorno (GitHub Secret o .env).
"""
import unittest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import requests


def get_token():
    """Obtiene el token de Telegram desde el entorno."""
    token = os.environ.get('CRM_TG_TOKEN', '')
    if not token or '***' in token:
        # Intentar desde .env
        try:
            with open('.env') as f:
                for line in f:
                    if line.startswith('CRM_TG_TOKEN='):
                        token = line.split('=', 1)[1].strip().strip('"').strip("'")
                        break
        except:
            pass
    return token


@unittest.skipIf(not get_token() or '***' in get_token(),
                 "CRM_TG_TOKEN no disponible en este entorno")
class TestTelegramConnectivity(unittest.TestCase):
    """Pruebas de conectividad con Telegram Bot API."""

    @classmethod
    def setUpClass(cls):
        cls.token = get_token()
        cls.base = f"https://api.telegram.org/bot{cls.token}"

    def test_token_format(self):
        """Valida que el token tenga formato bot123:secret."""
        parts = self.token.split(':')
        self.assertEqual(len(parts), 2, "Token debe tener formato 'bot_id:secret'")
        self.assertTrue(parts[0].isdigit(), "Prefijo del token debe ser numérico")
        self.assertGreater(len(parts[1]), 20, "Parte secreta del token debe tener >20 chars")

    def test_get_me(self):
        """Llama a getMe() para verificar que el token funciona."""
        resp = requests.get(f"{self.base}/getMe", timeout=10)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('ok'), f"getMe falló: {data}")
        bot = data.get('result', {})
        print(f"  Bot: @{bot.get('username', 'N/A')} — {bot.get('first_name', 'N/A')}")
        self.assertIsNotNone(bot.get('id'), "Bot debe tener ID")

    def test_get_updates_format(self):
        """Verifica que el endpoint getUpdates responde con el formato esperado."""
        resp = requests.get(f"{self.base}/getUpdates?offset=0&limit=1", timeout=10)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('ok', data)
        self.assertIn('result', data)


@unittest.skipIf(not os.environ.get('CRM_TG_CHAT_ID'),
                 "CRM_TG_CHAT_ID no disponible")
class TestTelegramChat(unittest.TestCase):
    """Pruebas que requieren chat_id configurado."""

    @classmethod
    def setUpClass(cls):
        cls.token = get_token()
        cls.base = f"https://api.telegram.org/bot{cls.token}"
        cls.chat_id = os.environ.get('CRM_TG_CHAT_ID', '')

    def test_send_message(self):
        """Envía un mensaje de prueba al chat configurado."""
        resp = requests.post(f"{self.base}/sendMessage", json={
            "chat_id": self.chat_id,
            "text": "🧪 CRM Robot Inspector - Test de conectividad exitoso",
            "parse_mode": "HTML"
        }, timeout=10)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('ok'), f"sendMessage falló: {data}")
        msg = data.get('result', {})
        print(f"  Mensaje enviado: chat={msg.get('chat',{}).get('id')} msg_id={msg.get('message_id')}")


if __name__ == '__main__':
    unittest.main()
