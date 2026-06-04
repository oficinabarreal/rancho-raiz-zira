from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = {
    "drive": "https://www.googleapis.com/auth/drive.file",
    "calendar": "https://www.googleapis.com/auth/calendar",
    "sheets": "https://www.googleapis.com/auth/spreadsheets",
    "gmail": "https://www.googleapis.com/auth/gmail.modify",
    "gmail_settings": "https://www.googleapis.com/auth/gmail.settings.basic",
    "docs": "https://www.googleapis.com/auth/documents",
}


def _token_path() -> Path:
    return Path(os.environ.get("CRM_STATE_DIR", "crm_state")) / ".google_token.json"


def _creds_path() -> Path | None:
    raw = os.environ.get("CRM_GOOGLE_CREDS")
    if raw:
        p = Path(raw)
        if p.exists():
            return p
    default = Path("credentials.json")
    if default.exists():
        return default
    return None


def _all_scopes() -> list[str]:
    return list(SCOPES.values())


def get_service(api_name: str, api_version: str, scope_key: str) -> Any | None:
    if scope_key not in SCOPES:
        return None

    creds = None
    token_file = _token_path()
    if token_file.exists():
        try:
            with open(token_file) as f:
                stored = json.load(f)
            stored_scopes = stored.get("scopes", [])
            needed = SCOPES[scope_key]
            if needed not in stored_scopes:
                return None
            # Normalizar: algunos flujos guardan "token" en vez de "access_token"
            if "token" in stored and "access_token" not in stored:
                stored["access_token"] = stored.pop("token")
                token_file.write_text(json.dumps(stored, indent=2))
            # Normalizar inverso: algunos json tienen "access_token" pero no "token"
            if "access_token" in stored and "token" not in stored:
                stored["token"] = stored["access_token"]
                token_file.write_text(json.dumps(stored, indent=2))
            creds = Credentials.from_authorized_user_file(str(token_file), stored_scopes)
        except Exception:
            creds = None

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            token_file.parent.mkdir(parents=True, exist_ok=True)
            token_file.write_text(json.dumps(json.loads(creds.to_json())))
        except Exception:
            creds = None

    if not creds or not creds.valid:
        client_file = _creds_path()
        if not client_file:
            return None
        # Si hay client_file pero creds no es válido, necesita re-autenticación
        return None

    return build(api_name, api_version, credentials=creds)
