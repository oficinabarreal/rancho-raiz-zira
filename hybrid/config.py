from __future__ import annotations
import os
from pathlib import Path
from typing import Optional


BASE_DIR = Path(__file__).resolve().parent
STATE_DIR = BASE_DIR / "crm_state"


class Settings:
    # Server
    host: str = "127.0.0.1"
    port: int = 8081

    # Gateway (OpenClaw) — where to send instructions back
    gateway_url: str = "http://127.0.0.1:8082"

    # Telegram — only for identifying the bot/group, no API calls
    tg_chat_id: str = ""
    tg_bot_username: str = "RanchoRaizBot"

    # Kommo — only pipeline ID, no token
    kommo_pipeline_id: int = 13768223

    # Google — only sheet ID, no auth
    sheet_reservas: str = "1JwcJs_MfcSfvMrrOIznobsIXBcHHAUGbPC2jLIMRjYU"

    # IA Parser (OpenCode Zen) — internal NLP call
    ia_endpoint: str = ""
    ia_api_key: str = ""
    ia_model: str = ""

    # Report email (who receives daily informe)
    report_email: str = "oficinabarreal@gmail.com"

    # Equipo
    equipo_path: Path = STATE_DIR / "equipo.json"

    def __init__(self):
        self._load_env()

    def _load_env(self):
        env_file = BASE_DIR / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

        self.ia_endpoint = os.environ.get("CRM_IA_ENDPOINT", "")
        self.ia_api_key = os.environ.get("CRM_IA_API_KEY", "")
        self.ia_model = os.environ.get("CRM_IA_MODEL", "")
        self.tg_chat_id = os.environ.get("CRM_TG_CHAT_ID", "")
        self.gateway_url = os.environ.get("CRM_GATEWAY_URL", self.gateway_url)
        self.port = int(os.environ.get("CRM_SERVER_PORT", str(self.port)))
        self.report_email = os.environ.get("CRM_REPORT_EMAIL", self.report_email)

    @property
    def ia_available(self) -> bool:
        return bool(self.ia_endpoint and self.ia_api_key and self.ia_model)


settings = Settings()