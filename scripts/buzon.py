#!/usr/bin/env python3
"""Buzón de ideas Zira — escanea Drive, detecta ideas y feedback visual."""

import json, sys, re
from pathlib import Path
from datetime import datetime, timezone
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

PROJECT_DIR = Path("/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3")
TOKEN_FILE = PROJECT_DIR / "crm_state" / ".google_token.json"
STATE_FILE = PROJECT_DIR / "crm_state" / "buzon_state.json"

# Keywords que Zira entiende — expandido para incluir feedback visual
KEYWORDS = [
    # Ideas y sugerencias
    "idea", "sugerencia", "mejora", "propuesta", "feature",
    # Feedback visual de Zira
    "zira", "look", "aspecto", "ropa", "accesorio", "color",
    "montaña", "avatar", "dibujo", "diseño", "estilo",
    # CRM
    "crm", "rancho", "raíz", "posada", "lead", "cliente",
    # Facturas/pagos
    "factura", "pago", "starlink", "naturgy", "boleta",
    # Ideas generales
    "nota", "notis", "web", "dashboard", "inventario",
    "gasto", "compra", "inversion", "proveedor", "recepcion",
]

def get_drive_service():
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), ["https://www.googleapis.com/auth/drive.readonly", "https://www.googleapis.com/auth/drive.metadata.readonly"])
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build("drive", "v3", credentials=creds)

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"processed_docs": [], "ideas": [], "feedback_zira": []}

def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))

def classify_doc(title, content=""):
    """Clasifica el doc: idea general o feedback visual de Zira."""
    t = title.lower() + " " + content.lower()[:500]
    visual_keywords = ["look", "aspecto", "ropa", "accesorio", "avatar", "dibujo",
                       "diseño", "estilo zira", "quiero que zira", "zira se vea",
                       "zira look", "vestir", "color"]
    if any(kw in t for kw in visual_keywords):
        return "feedback_zira"
    return "idea"

def scan_new_docs(service, state):
    """Busca docs nuevos con keywords en el título."""
    query = "(" + " or ".join(f"title contains '{kw}'" for kw in KEYWORDS) + ")"
    query += " and trashed = false and createdTime > '2026-05-01T00:00:00Z'"
    
    results = service.files().list(
        q=query,
        fields="files(id, name, createdTime, webViewLink)",
        orderBy="createdTime desc"
    ).execute()
    
    new_docs = []
    for doc in results.get("files", []):
        if doc["id"] not in state["processed_docs"]:
            # Leer contenido
            try:
                content = service.files().export(fileId=doc["id"], mimeType="text/plain").execute()
                if isinstance(content, bytes):
                    content = content.decode("utf-8", errors="replace")
            except:
                content = ""
            
            doc_type = classify_doc(doc["name"], content)
            
            entry = {
                "id": doc["id"],
                "title": doc["name"],
                "created": doc["createdTime"],
                "url": doc["webViewLink"],
                "type": doc_type,
                "content_preview": content[:300],
            }
            new_docs.append(entry)
            state["processed_docs"].append(doc["id"])
            
            if doc_type == "feedback_zira":
                state["feedback_zira"].append(entry)
            else:
                state["ideas"].append(entry)
    
    return new_docs

def main():
    service = get_drive_service()
    state = load_state()
    
    print(f"🤖 Zira escaneando Drive...")
    print(f"   Keywords activas: {len(KEYWORDS)}")
    print(f"   Docs procesados hasta hoy: {len(state['processed_docs'])}")
    
    new_docs = scan_new_docs(service, state)
    
    if new_docs:
        print(f"\n📄 {len(new_docs)} documento(s) nuevo(s):")
        for doc in new_docs:
            icon = "💡" if doc["type"] == "idea" else "🎨"
            print(f"\n  {icon} [{doc['type'].upper()}] {doc['title']}")
            print(f"     {doc['url']}")
    else:
        print("\n✅ Sin novedades en el buzón")
    
    # Feedback de Zira
    fb = state.get("feedback_zira", [])
    if fb:
        print(f"\n🎨 Feedback visual recibido: {len(fb)}")
        for f in fb[-3:]:
            print(f"   • {f['title']} ({f['created'][:10]})")
    
    save_state(state)
    print(f"\n📦 Total: {len(state['ideas'])} ideas + {len(state.get('feedback_zira',[]))} feedback visual")

if __name__ == "__main__":
    main()
