from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime
from typing import Any

from crm.google_auth import get_service

SEGUNDO_CEREBRO_ID = "1p5kLFu6hcIuoM0QlRFepJJ-asiKTdR-1yaokVY75CFU"
PERFIL_VIRTUAL_ID = "1ifNxjZQcZ-4hhvH_9atPBces4ChiN7Z23DWD8sEBuEk"

def read_doc(doc_id: str) -> str:
    svc = get_service("docs", "v1", "docs")
    if not svc:
        return ""
    doc = svc.documents().get(documentId=doc_id).execute()
    text_parts = []
    for el in doc.get("body", {}).get("content", []):
        p = el.get("paragraph", {})
        for seg in p.get("elements", []):
            tr = seg.get("textRun", {})
            txt = tr.get("content", "")
            if txt:
                text_parts.append(txt)
    return "".join(text_parts)


def append_to_doc(doc_id: str, text: str):
    svc = get_service("docs", "v1", "docs")
    if not svc:
        return False
    doc = svc.documents().get(documentId=doc_id).execute()
    body = doc.get("body", {})
    content = body.get("content", [])
    if not content:
        return False
    end_index = content[-1].get("endIndex", 1)
    requests_body = [
        {
            "insertText": {
                "location": {"index": end_index - 1},
                "text": text,
            }
        }
    ]
    svc.documents().batchUpdate(documentId=doc_id, body={"requests": requests_body}).execute()
    return True


import re

SKIP_PHRASES = [
    "leer este doc periodicamente",
    "si hay una idea nueva",
    "si requiere aprobacion",
    "documentar el resultado",
    "(escribe aca tus ideas nuevas)",
]

def should_skip(content: str) -> bool:
    c = content.lower()
    for phrase in SKIP_PHRASES:
        if phrase in c:
            return True
    if re.match(r"^\d{2}-[A-Za-z]{3}-\d{4}", content):
        return True
    return False

def extract_new_ideas(full_text: str) -> list[str]:
    lines = full_text.split("\n")
    ideas = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- ") or stripped.startswith("* "):
            content = stripped[2:].strip()
            if content and not should_skip(content):
                ideas.append(content)
    return ideas


def classify_idea(idea: str) -> dict:
    idea_lower = idea.lower()
    if any(w in idea_lower for w in ["gmail", "label", "filtro", "correo", "inbox"]):
        return {"type": "gmail", "description": idea}
    if any(w in idea_lower for w in ["drive", "archivo", "file", "carpeta"]):
        return {"type": "drive", "description": idea}
    if any(w in idea_lower for w in ["doc", "docs", "documento", "nota", "escribir"]):
        return {"type": "docs", "description": idea}
    if any(w in idea_lower for w in ["sheet", "spreadsheet", "tabla", "excel", "calculo"]):
        return {"type": "sheets", "description": idea}
    if any(w in idea_lower for w in ["cua", "android", "shizuku", "app", "telefono", "bloc", "notas"]):
        return {"type": "cua", "description": idea}
    if any(w in idea_lower for w in ["telegram", "notificar", "reportar", "mensaje"]):
        return {"type": "notify", "description": idea}
    if any(w in idea_lower for w in ["reserva", "huesped", "hotel", "rancho", "raíz", "crm"]):
        return {"type": "crm", "description": idea}
    return {"type": "unknown", "description": idea}


def execute_idea(idea: str) -> str:
    classified = classify_idea(idea)
    action_type = classified["type"]
    description = classified["description"]

    if action_type == "gmail":
        return execute_gmail_action(description)
    elif action_type == "docs":
        return execute_docs_action(description)
    elif action_type == "unknown":
        return f"NO SE RECONOCE: {description}"
    else:
        return f"TIPO {action_type} NO IMPLEMENTADO: {description}"


def execute_gmail_action(idea: str) -> str:
    svc = get_service("gmail", "v1", "gmail")
    if not svc:
        return "Gmail no disponible (scope faltante)"

    idea_lower = idea.lower()
    results = []

    if "label" in idea_lower:
        name_match = re.search(r'["\']([^"\']+)["\']', idea)
        if name_match:
            label_name = name_match.group(1)
            try:
                label_data = {"name": label_name, "labelListVisibility": "labelShow", "messageListVisibility": "show"}
                result = svc.users().labels().create(userId="me", body=label_data).execute()
                results.append(f"Label '{label_name}' creada (id={result['id']})")
            except Exception as e:
                results.append(f"Error creando label '{label_name}': {e}")

    if "clean" in idea_lower or "limpiar" in idea_lower or "inbox" in idea_lower:
        results.append("INBOX: ~201 msgs. Usar labels CRM/Rancho Raíz/Social para archivar.")

    return "\n".join(results) if results else f"Gmail: no se ejecutó nada con: {idea}"


def execute_docs_action(idea: str) -> str:
    idea_lower = idea.lower()

    if "perfil" in idea_lower:
        return f"Doc Perfil Virtual ya existe: {PERFIL_VIRTUAL_ID}"
    if "segundo" in idea_lower or "cerebro" in idea_lower:
        return f"Doc Segundo Cerebro ya existe: {SEGUNDO_CEREBRO_ID}"

    return f"Docs: acción no reconocida: {idea}"


def run_cycle():
    text = read_doc(SEGUNDO_CEREBRO_ID)
    if not text:
        print("No se pudo leer el Segundo Cerebro")
        return

    ideas = extract_new_ideas(text)
    if not ideas:
        print("No hay ideas nuevas")
        return

    results = []
    for idea in ideas:
        print(f"Procesando idea: {idea}")
        result = execute_idea(idea)
        results.append(f"- {idea}\n  → {result}")

    # Also warn about CUA notes migration
    results.append("- Pendiente: migrar notas del Transsion Notebook (requires Shizuku foreground)")

    timestamp = datetime.now().strftime("%d-%b-%Y %H:%M")
    report = f"\n{timestamp}:\n" + "\n".join(results) + "\n"
    append_to_doc(SEGUNDO_CEREBRO_ID, report)
    print(f"Reporte añadido al doc:\n{report}")


if __name__ == "__main__":
    run_cycle()
