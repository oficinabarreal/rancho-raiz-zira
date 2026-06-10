#!/usr/bin/env python3
"""
Zira Chat Responder — lee mensajes nuevos de la Google Sheet y los devuelve
para que Hermes/Zira genere respuestas.

Uso: python3 scripts/zira_responder.py check
  → Muestra los mensajes nuevos (remitente=guest, respondido=NO) en JSON

Uso: python3 scripts/zira_responder.py respond <session_id> <texto>
  → Escribe una respuesta de Zira en la sheet y marca los originales como respondidos
"""

import sys, json
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
TOKEN_FILE = PROJECT_DIR / "crm_state" / ".google_token.json"
SHEET_ID = "1MK76i7CTM44yCJu32SIq1fdOU5uVMBG5HXWWpoKfklg"


def get_sheets():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    creds = Credentials.from_authorized_user_file(
        str(TOKEN_FILE), ["https://www.googleapis.com/auth/spreadsheets"]
    )
    if not creds.valid:
        creds.refresh(Request())
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    from googleapiclient.discovery import build
    return build("sheets", "v4", credentials=creds)


def check_new():
    """Devuelve los mensajes nuevos no respondidos."""
    svc = get_sheets()
    data = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range="'mensajes'!A:G"
    ).execute()
    rows = data.get("values", [])
    
    nuevos = []
    for i, row in enumerate(rows):
        if i == 0:
            continue  # header
        if len(row) >= 5 and row[3] == "guest" and (len(row) < 6 or row[5] != "SI"):
            nuevos.append({
                "fila": i + 1,
                "id": row[0],
                "session_id": row[1],
                "timestamp": row[2],
                "remitente": row[3],
                "mensaje": row[4],
            })
    return nuevos


def write_response(session_id, texto):
    """Escribe la respuesta de Zira en la sheet."""
    svc = get_sheets()
    
    # Obtener último ID
    data = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range="'mensajes'!A:A"
    ).execute()
    ids = [r for r in data.get("values", []) if r]
    next_id = len(ids)  # 0-indexed, but we use it as display ID
    
    # Leer todas las filas para encontrar las del session_id
    all_data = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range="'mensajes'!A:G"
    ).execute()
    rows = all_data.get("values", [])
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Marcar mensajes originales como respondidos
    updates = []
    for i, row in enumerate(rows):
        if i == 0:
            continue
        if len(row) > 1 and row[1] == session_id:
            row_respondido = row[5] if len(row) > 5 else "NO"
            if row_respondido != "SI":
                updates.append(i + 1)
    
    for fila in updates:
        svc.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range=f"'mensajes'!F{fila}",
            valueInputOption="USER_ENTERED",
            body={"values": [["SI"]]}
        ).execute()
        # También poner timestamp de respuesta
        if len(rows[fila - 1]) >= 7:
            svc.spreadsheets().values().update(
                spreadsheetId=SHEET_ID,
                range=f"'mensajes'!G{fila}",
                valueInputOption="USER_ENTERED",
                body={"values": [[now]]}
            ).execute()
    
    # Agregar nueva fila con la respuesta de Zira
    svc.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range="'mensajes'!A:G",
        valueInputOption="USER_ENTERED",
        body={"values": [[next_id, session_id, now, "zira", texto, "NO", now]]}
    ).execute()
    
    print(f"✅ Respuesta escrita para sesión {session_id}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 zira_responder.py check")
        print("     python3 zira_responder.py respond <session_id> <texto>")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "check":
        nuevos = check_new()
        print(json.dumps(nuevos, ensure_ascii=False, indent=2))
    
    elif action == "respond":
        if len(sys.argv) < 4:
            print("❌ Faltan parámetros: respond <session_id> <texto>")
            sys.exit(1)
        session_id = sys.argv[2]
        texto = sys.argv[3]
        write_response(session_id, texto)
    
    else:
        print(f"❌ Acción desconocida: {action}")
        sys.exit(1)
