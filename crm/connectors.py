from __future__ import annotations

import base64
import json
import logging
import mimetypes
import os
import time
from datetime import datetime
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from .google_auth import get_service

logger = logging.getLogger(__name__)


@dataclass
class ConnectorResult:
    ok: bool
    data: Dict[str, Any]
    error: str = ""


class BaseConnector:
    name = "base"
    enabled = True

    def dry_run(self, action: str, payload: Dict[str, Any]) -> ConnectorResult:
        return ConnectorResult(ok=True, data={"action": action, "payload": payload, "connector": self.name, "dry_run": True})


# ── Gmail (via Gmail API / OAuth) ──────────────────────────────────

class GmailConnector(BaseConnector):
    name = "gmail"

    def __init__(self, user: str = "", app_password: str = ""):
        self._service = None

    def _svc(self):
        if self._service is None:
            self._service = get_service("gmail", "v1", "gmail")
        return self._service

    def list_messages(self, max_results: int = 20, query: str = "") -> ConnectorResult:
        svc = self._svc()
        if not svc:
            return self.dry_run("list_messages", {"max_results": max_results, "query": query})
        try:
            resp = svc.users().messages().list(userId="me", maxResults=max_results, q=query).execute()
            msgs = resp.get("messages", [])
            out = []
            for m in msgs[:max_results]:
                meta = svc.users().messages().get(userId="me", id=m["id"], format="metadata", metadataHeaders=["From", "Subject", "Date"]).execute()
                headers = {h["name"]: h["value"] for h in meta.get("payload", {}).get("headers", [])}
                out.append({
                    "id": m["id"],
                    "thread_id": meta.get("threadId", ""),
                    "from": headers.get("From", ""),
                    "subject": headers.get("Subject", ""),
                    "date": headers.get("Date", ""),
                    "snippet": meta.get("snippet", ""),
                })
            return ConnectorResult(ok=True, data={"messages": out})
        except Exception as e:
            return ConnectorResult(ok=False, data={}, error=str(e))

    def send_message(self, to: str, subject: str, body_text: str) -> ConnectorResult:
        svc = self._svc()
        if not svc:
            return self.dry_run("send_message", {"to": to, "subject": subject})
        try:
            from email.mime.text import MIMEText
            import base64
            msg = MIMEText(body_text)
            msg["To"] = to
            msg["Subject"] = subject
            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            resp = svc.users().messages().send(userId="me", body={"raw": raw}).execute()
            return ConnectorResult(ok=True, data={"message_id": resp["id"], "thread_id": resp.get("threadId", "")})
        except Exception as e:
            return ConnectorResult(ok=False, data={}, error=str(e))


# ── Telegram ─────────────────────────────────────────────────────────

class TelegramConnector(BaseConnector):
    name = "telegram"

    def __init__(self, token: str = "", chat_id: int = 0):
        self.token = token or os.environ.get("CRM_TG_TOKEN", "")
        self.chat_id = int(chat_id) if chat_id else int(os.environ.get("CRM_TG_CHAT_ID", "0"))

    def _api(self, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"https://api.telegram.org/bot{self.token}/{method}"
        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        return payload

    def send_message(self, text: str, reply_markup: Optional[dict] = None) -> ConnectorResult:
        payload: Dict[str, Any] = {"chat_id": self.chat_id, "text": text}
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup
        resp = self._api("sendMessage", payload)
        return ConnectorResult(ok=bool(resp.get("ok")), data=resp)

    def send_photo(self, photo_path: str, caption: str = "", reply_markup: Optional[dict] = None) -> ConnectorResult:
        path = Path(photo_path)
        if not path.exists():
            return ConnectorResult(ok=False, data={"photo_path": photo_path}, error="photo not found")
        url = f"https://api.telegram.org/bot{self.token}/sendPhoto"
        boundary = f"----CodexBoundary{uuid.uuid4().hex}"
        fields: list[tuple[str, str, str | None]] = [
            ("chat_id", str(self.chat_id), None),
        ]
        if caption:
            fields.append(("caption", caption, None))
        if reply_markup is not None:
            fields.append(("reply_markup", json.dumps(reply_markup, ensure_ascii=False), None))
        content_type = mimetypes.guess_type(path.name)[0] or "image/jpeg"

        body = bytearray()
        for key, value, extra in fields:
            body.extend(f"--{boundary}\r\n".encode("utf-8"))
            body.extend(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"))
            body.extend(value.encode("utf-8"))
            body.extend(b"\r\n")
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="photo"; filename="{path.name}"\r\n'.encode("utf-8"))
        body.extend(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
        body.extend(path.read_bytes())
        body.extend(b"\r\n")
        body.extend(f"--{boundary}--\r\n".encode("utf-8"))

        req = urllib.request.Request(url, data=bytes(body), headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        return ConnectorResult(ok=bool(payload.get("ok")), data=payload)


# ── Google Drive ──────────────────────────────────────────────────────

class DriveConnector(BaseConnector):
    name = "drive"

    def __init__(self):
        self._service = None

    def _svc(self):
        if self._service is None:
            self._service = get_service("drive", "v3", "drive")
        return self._service

    def upload(self, local_path: str, folder: str = "") -> ConnectorResult:
        svc = self._svc()
        if not svc:
            return self.dry_run("upload", {"local_path": local_path, "folder": folder})
        from googleapiclient.http import MediaFileUpload

        path = Path(local_path)
        if not path.exists():
            return ConnectorResult(ok=False, data={}, error=f"file not found: {local_path}")

        try:
            parent_id = None
            if folder:
                parent_id = self._ensure_folder(folder)

            media = MediaFileUpload(str(path), resumable=True)
            metadata: Dict[str, Any] = {"name": path.name}
            if parent_id:
                metadata["parents"] = [parent_id]

            file = svc.files().create(body=metadata, media_body=media, fields="id,name,mimeType,webViewLink").execute()
            return ConnectorResult(ok=True, data={"file_id": file["id"], "name": file["name"], "webViewLink": file.get("webViewLink", "")})
        except Exception as e:
            return ConnectorResult(ok=False, data={}, error=str(e))

    def _ensure_folder(self, name: str) -> str | None:
        svc = self._svc()
        if not svc:
            return None
        try:
            query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            existing = svc.files().list(q=query, fields="files(id)").execute()
            files = existing.get("files", [])
            if files:
                return files[0]["id"]
            folder = svc.files().create(body={"name": name, "mimeType": "application/vnd.google-apps.folder"}, fields="id").execute()
            return folder["id"]
        except Exception:
            return None

    def list_files(self, folder: str = "") -> ConnectorResult:
        svc = self._svc()
        if not svc:
            return self.dry_run("list_files", {"folder": folder})
        try:
            query = "trashed=false"
            if folder:
                parent_id = self._ensure_folder(folder)
                if parent_id:
                    query = f"'{parent_id}' in parents and trashed=false"
            results = svc.files().list(q=query, fields="files(id,name,mimeType,webViewLink)", pageSize=50).execute()
            return ConnectorResult(ok=True, data={"files": results.get("files", [])})
        except Exception as e:
            return ConnectorResult(ok=False, data={}, error=str(e))


# ── Google Calendar ──────────────────────────────────────────────────

class CalendarConnector(BaseConnector):
    name = "calendar"

    def __init__(self):
        self._service = None

    def _svc(self):
        if self._service is None:
            self._service = get_service("calendar", "v3", "calendar")
        return self._service

    def create_event(self, summary: str, start: str, end: str, description: str = "", attendees: Optional[List[str]] = None) -> ConnectorResult:
        svc = self._svc()
        if not svc:
            return self.dry_run("create_event", {"summary": summary, "start": start, "end": end, "description": description})

        try:
            event = {
                "summary": summary,
                "description": description,
                "start": {"dateTime": start, "timeZone": "America/Argentina/San_Juan"},
                "end": {"dateTime": end, "timeZone": "America/Argentina/San_Juan"},
            }
            if attendees:
                event["attendees"] = [{"email": a} for a in attendees]

            created = svc.events().insert(calendarId="primary", body=event).execute()
            return ConnectorResult(ok=True, data={"event_id": created["id"], "htmlLink": created.get("htmlLink", ""), "summary": created["summary"]})
        except Exception as e:
            return ConnectorResult(ok=False, data={}, error=str(e))

    def list_upcoming(self, max_results: int = 10) -> ConnectorResult:
        svc = self._svc()
        if not svc:
            return self.dry_run("list_upcoming", {"max_results": max_results})
        try:
            now = datetime.utcnow().isoformat() + "Z"
            events = svc.events().list(calendarId="primary", timeMin=now, maxResults=max_results, singleEvents=True, orderBy="startTime").execute()
            items = []
            for e in events.get("items", []):
                items.append({"id": e["id"], "summary": e.get("summary", ""), "start": e["start"].get("dateTime", e["start"].get("date", "")), "link": e.get("htmlLink", "")})
            return ConnectorResult(ok=True, data={"events": items})
        except Exception as e:
            return ConnectorResult(ok=False, data={}, error=str(e))


# ── Google Sheets ────────────────────────────────────────────────────

class SheetsConnector(BaseConnector):
    name = "sheets"

    def __init__(self):
        self._service = None

    def _svc(self):
        if self._service is None:
            self._service = get_service("sheets", "v4", "sheets")
        return self._service

    def _ensure_spreadsheet(self, title: str) -> str | None:
        svc = self._svc()
        if not svc:
            return None
        try:
            existing = svc.spreadsheets().get(spreadsheetId=title, fields="spreadsheetId").execute()
            if existing.get("spreadsheetId"):
                return title
        except Exception:
            pass
        try:
            sheet = svc.spreadsheets().create(body={"properties": {"title": title}}).execute()
            return sheet["spreadsheetId"]
        except Exception:
            return None

    def _sheet_name(self, svc, spreadsheet_id: str) -> str:
        try:
            meta = svc.spreadsheets().get(spreadsheetId=spreadsheet_id, fields="sheets.properties.title").execute()
            sheets = meta.get("sheets", [])
            if sheets:
                return sheets[0]["properties"]["title"]
        except Exception:
            pass
        return "Sheet1"

    def append_row(self, sheet: str, row: List[Any]) -> ConnectorResult:
        svc = self._svc()
        if not svc:
            return self.dry_run("append_row", {"sheet": sheet, "row": row})

        try:
            spreadsheet_id = self._ensure_spreadsheet(sheet)
            if not spreadsheet_id:
                return ConnectorResult(ok=False, data={}, error=f"could not create/open sheet: {sheet}")

            sheet_name = self._sheet_name(svc, spreadsheet_id)
            range_name = f"{sheet_name}!A:A"
            body = {"values": [row]}
            result = svc.spreadsheets().values().append(spreadsheetId=spreadsheet_id, range=range_name, valueInputOption="USER_ENTERED", body=body).execute()
            return ConnectorResult(ok=True, data={"updated": result.get("updates", {}).get("updatedRows", 0), "spreadsheet_id": spreadsheet_id})
        except Exception as e:
            return ConnectorResult(ok=False, data={}, error=str(e))

    def read(self, sheet: str, range_name: str = "") -> ConnectorResult:
        svc = self._svc()
        if not svc:
            return self.dry_run("read", {"sheet": sheet, "range": range_name})
        try:
            sheet_name = range_name if range_name else self._sheet_name(svc, sheet)
            result = svc.spreadsheets().values().get(spreadsheetId=sheet, range=sheet_name).execute()
            return ConnectorResult(ok=True, data={"values": result.get("values", [])})
        except Exception as e:
            return ConnectorResult(ok=False, data={}, error=str(e))


# ── Google Docs ─────────────────────────────────────────────────────

class DocsConnector(BaseConnector):
    name = "docs"

    def __init__(self):
        self._service = None

    def _svc(self):
        if self._service is None:
            self._service = get_service("docs", "v1", "docs")
        return self._service

    def read(self, document_id: str) -> ConnectorResult:
        svc = self._svc()
        if not svc:
            return self.dry_run("read", {"document_id": document_id})
        try:
            doc = svc.documents().get(documentId=document_id).execute()
            content = doc.get("body", {}).get("content", [])
            lines = []
            for elem in content:
                for para in elem.get("paragraph", {}).get("elements", []):
                    for run in para.get("textRun", {}).get("content", ""):
                        lines.append(para["textRun"]["content"])
                    if "textRun" in para.get("paragraphStyle", {}):
                        pass
            text = "".join(
                elem.get("paragraph", {}).get("elements", [{}])[0]
                .get("textRun", {})
                .get("content", "")
                for elem in content if elem.get("paragraph")
            )
            return ConnectorResult(ok=True, data={"title": doc.get("title", ""), "document_id": document_id, "content": text})
        except Exception as e:
            return ConnectorResult(ok=False, data={}, error=str(e))

    def create(self, title: str, content: str = "") -> ConnectorResult:
        svc = self._svc()
        if not svc:
            return self.dry_run("create", {"title": title, "content": content})
        try:
            doc = svc.documents().create(body={"title": title}).execute()
            doc_id = doc.get("documentId")
            if content and doc_id:
                svc.documents().batchUpdate(
                    documentId=doc_id,
                    body={
                        "requests": [{
                            "insertText": {
                                "location": {"index": 1},
                                "text": content
                            }
                        }]
                    }
                ).execute()
            return ConnectorResult(ok=True, data={"document_id": doc_id, "title": doc.get("title", ""), "url": f"https://docs.google.com/document/d/{doc_id}"})
        except Exception as e:
            return ConnectorResult(ok=False, data={}, error=str(e))

    def append(self, document_id: str, text: str) -> ConnectorResult:
        svc = self._svc()
        if not svc:
            return self.dry_run("append", {"document_id": document_id, "text": text})
        try:
            doc = svc.documents().get(documentId=document_id).execute()
            end_index = doc.get("body", {}).get("content", [{}])[-1].get("endIndex", 1)
            svc.documents().batchUpdate(
                documentId=document_id,
                body={
                    "requests": [{
                        "insertText": {
                            "location": {"index": end_index - 1},
                            "text": "\n" + text
                        }
                    }]
                }
            ).execute()
            return ConnectorResult(ok=True, data={"document_id": document_id})
        except Exception as e:
            return ConnectorResult(ok=False, data={}, error=str(e))


# ── Android CUA (Computer Use Agent) ────────────────────────────────

class AndroidCuaConnector(BaseConnector):
    name = "android_cua"

    def __init__(self):
        self._cua = None

    def _mgr(self):
        if self._cua is None:
            from .android_cua import CuaManager
            self._cua = CuaManager()
        return self._cua

    def dump_ui(self) -> ConnectorResult:
        mgr = self._mgr()
        try:
            summary = mgr.ui_text_summary()
            raw = mgr.dump_ui_raw()
            return ConnectorResult(ok=True, data={"summary": summary, "raw_xml": raw})
        except Exception as e:
            return ConnectorResult(ok=False, data={}, error=str(e))

    def screenshot(self) -> ConnectorResult:
        mgr = self._mgr()
        try:
            path = mgr.screenshot()
            if not path:
                return ConnectorResult(ok=False, data={}, error="screenshot failed")
            return ConnectorResult(ok=True, data={"path": path})
        except Exception as e:
            return ConnectorResult(ok=False, data={}, error=str(e))

    def tap(self, x: int, y: int) -> ConnectorResult:
        mgr = self._mgr()
        try:
            ok = mgr.tap(x, y)
            return ConnectorResult(ok=ok, data={"x": x, "y": y})
        except Exception as e:
            return ConnectorResult(ok=False, data={}, error=str(e))

    def tap_text(self, text: str, exact: bool = True) -> ConnectorResult:
        mgr = self._mgr()
        try:
            ok = mgr.tap_by_text(text, exact)
            if ok:
                return ConnectorResult(ok=True, data={"text": text, "exact": exact})
            return ConnectorResult(ok=False, data={"text": text}, error=f"element '{text}' not found")
        except Exception as e:
            return ConnectorResult(ok=False, data={}, error=str(e))

    def type_text(self, text: str) -> ConnectorResult:
        mgr = self._mgr()
        try:
            ok = mgr.input_text(text)
            return ConnectorResult(ok=ok, data={"text": text})
        except Exception as e:
            return ConnectorResult(ok=False, data={}, error=str(e))

    def press_key(self, key: str) -> ConnectorResult:
        mgr = self._mgr()
        try:
            ok = mgr.press_key(key)
            return ConnectorResult(ok=ok, data={"key": key})
        except Exception as e:
            return ConnectorResult(ok=False, data={}, error=str(e))

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> ConnectorResult:
        mgr = self._mgr()
        try:
            ok = mgr.swipe(x1, y1, x2, y2, duration_ms)
            return ConnectorResult(ok=ok, data={"x1": x1, "y1": y1, "x2": x2, "y2": y2})
        except Exception as e:
            return ConnectorResult(ok=False, data={}, error=str(e))

    def open_app(self, package: str) -> ConnectorResult:
        mgr = self._mgr()
        try:
            ok = mgr.open_app(package)
            return ConnectorResult(ok=ok, data={"package": package})
        except Exception as e:
            return ConnectorResult(ok=False, data={}, error=str(e))

    def go_home(self) -> ConnectorResult:
        mgr = self._mgr()
        try:
            ok = mgr.go_home()
            return ConnectorResult(ok=ok, data={"action": "home"})
        except Exception as e:
            return ConnectorResult(ok=False, data={}, error=str(e))

    def go_back(self) -> ConnectorResult:
        mgr = self._mgr()
        try:
            ok = mgr.go_back()
            return ConnectorResult(ok=ok, data={"action": "back"})
        except Exception as e:
            return ConnectorResult(ok=False, data={}, error=str(e))

    def scroll_down(self) -> ConnectorResult:
        mgr = self._mgr()
        try:
            ok = mgr.scroll_down()
            return ConnectorResult(ok=ok, data={"action": "scroll_down"})
        except Exception as e:
            return ConnectorResult(ok=False, data={}, error=str(e))

    def scroll_up(self) -> ConnectorResult:
        mgr = self._mgr()
        try:
            ok = mgr.scroll_up()
            return ConnectorResult(ok=ok, data={"action": "scroll_up"})
        except Exception as e:
            return ConnectorResult(ok=False, data={}, error=str(e))

    def find(self, text: str = "", resource_id: str = "", class_name: str = "") -> ConnectorResult:
        mgr = self._mgr()
        try:
            results = mgr.find_elements(text, resource_id, class_name)
            return ConnectorResult(ok=True, data={
                "found": len(results),
                "elements": [
                    {"text": e.text, "resource_id": e.resource_id,
                     "class": e.class_name, "bounds": e.bounds,
                     "center": list(e.center)}
                    for e in results
                ]
            })
        except Exception as e:
            return ConnectorResult(ok=False, data={}, error=str(e))

    def get_screen_state(self) -> ConnectorResult:
        mgr = self._mgr()
        try:
            state = mgr.get_screen_state()
            return ConnectorResult(ok=True, data=state)
        except Exception as e:
            return ConnectorResult(ok=False, data={}, error=str(e))


# ── Kommo (formerly amoCRM) ──────────────────────────────────────────

class KommoConnector(BaseConnector):
    name = "kommo"

    def __init__(self, subdomain: str = "", access_token: str = ""):
        self.subdomain = subdomain or os.environ.get("CRM_KOMMO_SUBDOMAIN", "")
        self.access_token = access_token or os.environ.get("CRM_KOMMO_TOKEN", "")
        self._base = f"https://{self.subdomain}.kommo.com/api/v4"

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def create_lead(self, title: str, payload: Dict[str, Any]) -> ConnectorResult:
        if not self.access_token:
            return self.dry_run("create_lead", {"title": title, "payload": payload})
        try:
            contacts_data = payload.pop("contacts", [])
            top_level = payload
            lead = {"name": title, **top_level}

            # Create contacts first, then reference by ID
            if contacts_data:
                created = []
                for c in contacts_data:
                    name = c.pop("name", "Contact")
                    cfv = c.pop("custom_fields_values", [])
                    c_body = {"name": name}
                    if cfv:
                        c_body["custom_fields_values"] = cfv
                    resp = requests.post(f"{self._base}/contacts", headers=self._headers(), json=[c_body], timeout=30)
                    if resp.ok:
                        cid = resp.json()["_embedded"]["contacts"][0]["id"]
                        created.append({"id": cid})
                if created:
                    lead["_embedded"] = {"contacts": created}

            resp = requests.post(f"{self._base}/leads", headers=self._headers(), json=[lead], timeout=30)
            if resp.ok:
                data = resp.json()
                return ConnectorResult(ok=True, data={"lead_id": data["_embedded"]["leads"][0]["id"], "response": data})
            return ConnectorResult(ok=False, data={}, error=f"kommo error {resp.status_code}: {resp.text[:300]}")
        except Exception as e:
            return ConnectorResult(ok=False, data={}, error=str(e))

    def update_status(self, lead_id: str, status: str) -> ConnectorResult:
        if not self.access_token:
            return self.dry_run("update_status", {"lead_id": lead_id, "status": status})
        try:
            body = [{"id": int(lead_id), "status_id": int(status) if status.isdigit() else status}]
            resp = requests.patch(f"{self._base}/leads", headers=self._headers(), json=body, timeout=30)
            return ConnectorResult(ok=resp.ok, data={"lead_id": lead_id, "status": status, "response": resp.json() if resp.ok else resp.text[:300]})
        except Exception as e:
            return ConnectorResult(ok=False, data={}, error=str(e))

    def list_leads(self, limit: int = 20) -> ConnectorResult:
        if not self.access_token:
            return self.dry_run("list_leads", {"limit": limit})
        try:
            resp = requests.get(f"{self._base}/leads", headers=self._headers(), params={"limit": limit}, timeout=30)
            if resp.status_code == 204:
                return ConnectorResult(ok=True, data={"leads": []})
            if resp.ok:
                return ConnectorResult(ok=True, data=resp.json())
            return ConnectorResult(ok=False, data={}, error=f"kommo error {resp.status_code}: {resp.text[:300]}")
        except Exception as e:
            return ConnectorResult(ok=False, data={}, error=str(e))


# ── Notion ───────────────────────────────────────────────────────────

class NotionConnector(BaseConnector):
    name = "notion"

    def __init__(self, token: str = "", database_id: str = ""):
        self.token = token or os.environ.get("CRM_NOTION_TOKEN", "")
        self.database_id = database_id or os.environ.get("CRM_NOTION_DATABASE_ID", "")

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }

    def create_page(self, title: str, content: str, database: str = "") -> ConnectorResult:
        if not self.token:
            return self.dry_run("create_page", {"title": title, "content": content, "database": database})

        db_id = database or self.database_id
        if not db_id:
            return ConnectorResult(ok=False, data={}, error="no database_id configured")

        try:
            body = {
                "parent": {"database_id": db_id},
                "properties": {
                    "title": {"title": [{"type": "text", "text": {"content": title[:100]}}]}
                },
                "children": [
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {"rich_text": [{"type": "text", "text": {"content": content[:2000]}}]},
                    }
                ],
            }
            resp = requests.post("https://api.notion.com/v1/pages", headers=self._headers(), json=body, timeout=30)
            if resp.ok:
                data = resp.json()
                return ConnectorResult(ok=True, data={"page_id": data["id"], "url": data.get("url", "")})
            return ConnectorResult(ok=False, data={}, error=f"notion error {resp.status_code}: {resp.text[:300]}")
        except Exception as e:
            return ConnectorResult(ok=False, data={}, error=str(e))

    def query_database(self, filter_dict: Optional[Dict[str, Any]] = None) -> ConnectorResult:
        if not self.token:
            return self.dry_run("query_database", {"filter": filter_dict})
        db_id = self.database_id
        if not db_id:
            return ConnectorResult(ok=False, data={}, error="no database_id configured")
        try:
            body = {}
            if filter_dict:
                body["filter"] = filter_dict
            resp = requests.post(f"https://api.notion.com/v1/databases/{db_id}/query", headers=self._headers(), json=body, timeout=30)
            if resp.ok:
                return ConnectorResult(ok=True, data=resp.json())
            return ConnectorResult(ok=False, data={}, error=f"notion error {resp.status_code}: {resp.text[:300]}")
        except Exception as e:
            return ConnectorResult(ok=False, data={}, error=str(e))


# ── WhatsApp Cloud API ────────────────────────────────────────────────

class WhatsAppConnector(BaseConnector):
    name = "whatsapp"

    def __init__(self, token: str = "", phone_number_id: str = ""):
        self.token = token or os.environ.get("CRM_WHATSAPP_TOKEN", "")
        self.phone_number_id = phone_number_id or os.environ.get("CRM_WHATSAPP_PHONE_ID", "")

    def send_message(self, to: str, text: str) -> ConnectorResult:
        if not self.token:
            return self.dry_run("send_message", {"to": to, "text": text})
        try:
            url = f"https://graph.facebook.com/v22.0/{self.phone_number_id}/messages"
            body = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": text[:4096]},
            }
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }
            resp = requests.post(url, headers=headers, json=body, timeout=30)
            if resp.ok:
                return ConnectorResult(ok=True, data=resp.json())
            return ConnectorResult(ok=False, data={}, error=f"whatsapp error {resp.status_code}: {resp.text[:300]}")
        except Exception as e:
            return ConnectorResult(ok=False, data={}, error=str(e))

    def send_template(self, to: str, template_name: str, lang: str = "es", components: Optional[List[Dict]] = None) -> ConnectorResult:
        if not self.token:
            return self.dry_run("send_template", {"to": to, "template": template_name})
        try:
            url = f"https://graph.facebook.com/v22.0/{self.phone_number_id}/messages"
            body: Dict[str, Any] = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "template",
                "template": {"name": template_name, "language": {"code": lang}},
            }
            if components:
                body["template"]["components"] = components
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }
            resp = requests.post(url, headers=headers, json=body, timeout=30)
            if resp.ok:
                return ConnectorResult(ok=True, data=resp.json())
            return ConnectorResult(ok=False, data={}, error=f"whatsapp error {resp.status_code}: {resp.text[:300]}")
        except Exception as e:
            return ConnectorResult(ok=False, data={}, error=str(e))


# ── Instagram Graph API ──────────────────────────────────────────────

class InstagramConnector(BaseConnector):
    name = "instagram"

    def __init__(self, token: str = "", ig_user_id: str = ""):
        self.token = token or os.environ.get("CRM_INSTAGRAM_TOKEN", "")
        self.ig_user_id = ig_user_id or os.environ.get("CRM_INSTAGRAM_USER_ID", "")

    def _graph(self, endpoint: str, params: Dict[str, str], method: str = "GET") -> ConnectorResult:
        if not self.token:
            return self.dry_run(endpoint, params)
        try:
            params["access_token"] = self.token
            url = f"https://graph.facebook.com/v22.0/{endpoint}"
            if method == "GET":
                resp = requests.get(url, params=params, timeout=30)
            else:
                resp = requests.post(url, data=params, timeout=30)
            if resp.ok:
                return ConnectorResult(ok=True, data=resp.json())
            return ConnectorResult(ok=False, data={}, error=f"instagram error {resp.status_code}: {resp.text[:300]}")
        except Exception as e:
            return ConnectorResult(ok=False, data={}, error=str(e))

    def publish(self, media_path: str, caption: str) -> ConnectorResult:
        if not self.token or not self.ig_user_id:
            return self.dry_run("publish", {"media_path": media_path, "caption": caption})

        path = Path(media_path)
        if not path.exists():
            return ConnectorResult(ok=False, data={}, error=f"file not found: {media_path}")

        try:
            media_type = "IMAGE"
            mime = mimetypes.guess_type(path.name)[0] or ""
            if mime.startswith("video/"):
                media_type = "VIDEO"

            create = self._graph(
                f"{self.ig_user_id}/media",
                {"image_url" if media_type == "IMAGE" else "video_url": "", "caption": caption, "media_type": media_type},
                method="POST",
            )
            if not create.ok:
                return create

            creation_id = create.data.get("id")
            if not creation_id:
                return ConnectorResult(ok=False, data=create.data, error="no media id returned")

            time.sleep(3)
            publish = self._graph(
                f"{self.ig_user_id}/media_publish",
                {"creation_id": creation_id},
                method="POST",
            )
            return publish
        except Exception as e:
            return ConnectorResult(ok=False, data={}, error=str(e))

    def get_media(self, limit: int = 10) -> ConnectorResult:
        return self._graph(f"{self.ig_user_id}/media", {"fields": "id,caption,media_type,media_url,timestamp", "limit": str(limit)})
