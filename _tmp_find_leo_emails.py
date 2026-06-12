#!/usr/bin/env python3
import sys, json, base64
from pathlib import Path
sys.path.insert(0, "/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3")

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

creds = Credentials.from_authorized_user_info(
    json.loads(Path("crm_state/.google_token.json").read_text())
)
if creds.expired and creds.refresh_token:
    creds.refresh(Request())

gmail = build("gmail", "v1", credentials=creds)

# Search for recent sent emails to possible Leo addresses
results = gmail.users().messages().list(
    userId="me",
    q="to:(ltelloraiz OR ramonleandro OR tello) in:sent",
    maxResults=15
).execute()

print(f"Found {len(results.get('messages', []))} messages")
for msg in results.get("messages", []):
    full = gmail.users().messages().get(
        userId="me", id=msg["id"], format="metadata",
        metadataHeaders=["To", "Cc", "Subject", "From"]
    ).execute()
    headers = {h["name"]: h["value"] for h in full["payload"]["headers"]}
    print(f"\nTo: {headers.get('To','?')}")
    print(f"Subject: {headers.get('Subject','?')}")
    print(f"Cc: {headers.get('Cc','-')}")
    print(f"From: {headers.get('From','?')}")
