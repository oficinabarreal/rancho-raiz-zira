#!/usr/bin/env python3
"""
buzon.py — Google Docs Buzón de Instrucciones para Automejora v2.

Crea/actualiza un documento en Google Docs con:
  1. Contexto del proyecto (estructura, última actividad, tests)
  2. Sección [BUZÓN_DE_INSTRUCCIONES] donde Gemini (o humano) escribe sugerencias
  3. Las sugerencias con formato [NUEVA_MEJORA] ... [FIN_MEJORA]

Modos de uso:
  python3 scripts/buzon.py create      — crea o actualiza el doc
  python3 scripts/buzon.py read        — lee sugerencias pendientes del buzón
  python3 scripts/buzon.py clear       — limpia sugerencias ya procesadas
  python3 scripts/buzon.py status      — muestra estado del proyecto y últimas runs
"""
import json
import os
import re
import subprocess
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path

# ─── Config ────────────────────────────────────────────────────────
DOC_TITLE = "CRM Automejora — Contexto + Buzón"
PROJECT_DIR = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_DIR / "crm_state"
TOKEN_FILE = STATE_DIR / ".google_token.json"
GH_REPO = "oficinabarreal/rancho-raiz-zira"
BUZON_MARKER_START = "[BUZÓN_DE_INSTRUCCIONES]"
BUZON_MARKER_END = "=== FIN DEL DOCUMENTO ==="


# ─── Google Docs API ───────────────────────────────────────────────
def get_docs_service():
    """Obtiene service de Google Docs usando el token existente."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    if not TOKEN_FILE.exists():
        print("❌ No hay token OAuth en", TOKEN_FILE)
        return None

    with open(TOKEN_FILE) as f:
        stored = json.load(f)

    # Normalizar: from_authorized_user_file necesita campo "token"
    if "access_token" in stored and "token" not in stored:
        stored["token"] = stored["access_token"]
    # Asegurar scopes
    scopes = stored.get("scopes", [])
    if "https://www.googleapis.com/auth/documents" not in scopes:
        print("❌ El token no tiene scope de documentos")
        return None

    creds = Credentials.from_authorized_user_info(stored, scopes)

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # Guardar token refrescado
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(creds.to_json())

    if not creds or not creds.valid:
        print("❌ Credenciales no válidas. Reautenticación necesaria.")
        return None

    return build("docs", "v1", credentials=creds)


def find_or_create_doc(service):
    """Busca el doc por título o lo crea. Retorna (doc_id, created)."""
    # Buscar usando Drive API (Docs API no busca por título)
    from googleapiclient.discovery import build
    import google.auth
    
    # Obtener credenciales del service de Docs
    creds = None
    if TOKEN_FILE.exists():
        from google.oauth2.credentials import Credentials
        with open(TOKEN_FILE) as f:
            stored = json.load(f)
        scopes = stored.get("scopes", [])
        if "token" in stored and "access_token" not in stored:
            stored["access_token"] = stored.pop("token")
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), scopes)

    if not creds:
        print("❌ No hay credenciales válidas")
        return None, False

    drive = build("drive", "v3", credentials=creds)
    
    # Buscar
    results = drive.files().list(
        q=f"name='{DOC_TITLE}' and mimeType='application/vnd.google-apps.document' and trashed=false",
        spaces="drive",
        fields="files(id, name, modifiedTime)"
    ).execute()
    
    files = results.get("files", [])
    if files:
        doc_id = files[0]["id"]
        print(f"📄 Doc encontrado: '{DOC_TITLE}' (modificado: {files[0]['modifiedTime']})")
        return doc_id, False
    
    # Crear
    doc = drive.files().create(
        body={
            "name": DOC_TITLE,
            "mimeType": "application/vnd.google-apps.document"
        },
        fields="id"
    ).execute()
    doc_id = doc.get("id")
    print(f"📄 Doc creado: '{DOC_TITLE}' (ID: {doc_id})")
    return doc_id, True


def get_project_context():
    """Genera el contexto actual del proyecto como texto plano."""
    lines = []
    lines.append(f"Última actualización: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("")

    # Git info
    try:
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, cwd=PROJECT_DIR, timeout=10
        ).stdout.strip()
        last_commit = subprocess.run(
            ["git", "log", "-1", "--format=%h %s (%ar)"],
            capture_output=True, text=True, cwd=PROJECT_DIR, timeout=10
        ).stdout.strip()
        lines.append(f"Rama: {branch}")
        lines.append(f"Último commit: {last_commit}")
        lines.append("")
    except:
        pass

    # Estructura del proyecto
    lines.append("── Estructura del Proyecto ──")
    for pattern, label in [
        ("crm/*.py", "CRM Core"),
        ("simulators/crm_simulator.py", "Simulador"),
        ("tests/*.py", "Tests"),
        ("mensajeria/**/*.py", "Mensajería"),
        ("scripts/*.sh", "Scripts"),
        (".github/workflows/*.yml", "Workflows CI"),
    ]:
        files = sorted(PROJECT_DIR.glob(pattern))
        lines.append(f"  {label}: {len(files)} archivo(s)")

    # Tests
    lines.append("")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
            capture_output=True, text=True, cwd=PROJECT_DIR, timeout=30
        )
        test_out = result.stdout.strip().split("\n")[-1] if result.stdout else "?"
        test_err = result.stderr.strip().split("\n")[-1] if result.stderr else ""
        lines.append(f"Tests: {test_out} {test_err}")
    except:
        lines.append("Tests: no disponible")

    # GH Actions último run
    lines.append("")
    token = _get_gh_token()
    if token:
        import urllib.request
        try:
            req = urllib.request.Request(
                f"https://api.github.com/repos/{GH_REPO}/actions/runs?per_page=3&branch=main",
                headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                lines.append("── Últimos runs en main ──")
                for run in data.get("workflow_runs", []):
                    icon = "✅" if run.get("conclusion") == "success" else "❌"
                    lines.append(f"  {icon} #{run['run_number']} {run['name']}: {run.get('conclusion', '?')}")
                lines.append("")
        except:
            pass

    return "\n".join(lines)


def _get_gh_token():
    """Obtiene GitHub token de credential store o variable de entorno."""
    tok = os.environ.get("GITHUB_TOKEN", "")
    if tok:
        return tok
    try:
        result = subprocess.run(
            ["git", "credential-store", "get"],
            input="protocol=https\nhost=github.com\n",
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.split("\n"):
            if line.startswith("password="):
                return line.split("=", 1)[1]
    except:
        pass
    # Fallback: leer .git-credentials
    cred_file = Path.home() / ".git-credentials"
    if cred_file.exists():
        import re
        m = re.search(r'https://[^:]+:([^@]+)@', cred_file.read_text())
        if m:
            return m.group(1)
    return ""


def get_processed_docs():
    """Lee IDs de docs ya procesados."""
    state_file = STATE_DIR / "buzon_state.json"
    if state_file.exists():
        return set(json.loads(state_file.read_text()).get("processed_docs", []))
    return set()


def save_processed_doc(doc_id: str):
    """Marca un doc como procesado."""
    state_file = STATE_DIR / "buzon_state.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    processed = get_processed_docs()
    processed.add(doc_id)
    state_file.write_text(json.dumps({"processed_docs": list(processed)}, indent=2))


def scan_new_docs(drive):
    """Busca documentos creados por el usuario en las últimas 24h que
    parezcan ideas/sugerencias para el CRM."""
    from datetime import timedelta
    
    since = (datetime.now(timezone.utc) - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
    results = drive.files().list(
        q=f"mimeType='application/vnd.google-apps.document' and createdTime > '{since}' and trashed=false",
        fields="files(id, name, createdTime)",
        orderBy="createdTime desc"
    ).execute()
    
    keywords = ["sumar", "crm", "idea", "sugerencia", "mejora", "feature", "propuesta", 
                 "nota", "notis", "web", "dashboard", "github", "zira", "rancho",
                 "posada", "automatizar", "proyecto", "bot", "lead", "factura"]
    found = []
    
    for f in results.get("files", []):
        name = f["name"].lower()
        if any(k in name for k in keywords) and "buzón" not in name and "contexto + buzón" not in name:
            found.append(f)
    return found


def append_to_buzon(service, doc_id, text):
    """Agrega texto al inicio del buzón (después del sectionBreak)."""
    requests = [{
        "insertText": {
            "location": {"index": 1},
            "text": text + "\n\n"
        }
    }]
    service.documents().batchUpdate(
        documentId=doc_id, body={"requests": requests}
    ).execute()
    return True


def get_drive_service():
    """Obtiene service de Google Drive."""
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    
    if not TOKEN_FILE.exists():
        return None
    with open(TOKEN_FILE) as f:
        stored = json.load(f)
    if "access_token" in stored and "token" not in stored:
        stored["token"] = stored["access_token"]
    scopes = stored.get("scopes", [])
    creds = Credentials.from_authorized_user_info(stored, scopes)
    if creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
    return build("drive", "v3", credentials=creds)


def update_doc_content(service, doc_id, context_text):
    """Reemplaza TODO el contenido del doc con contexto + buzón."""
    docs = service.documents()
    
    # Obtener doc actual para conocer estructura
    document = docs.get(documentId=doc_id).execute()
    content_list = document.get("body", {}).get("content", [])
    end_index = content_list[-1].get("endIndex", 1) if content_list else 1
    
    # Si el doc está vacío o solo tiene sectionBreak (endIndex=1) o un párrafo vacío (endIndex=2)
    # eliminamos desde 1 hasta end_index-1, pero solo si hay contenido real
    requests = []
    if end_index > 2:
        # Borrar desde el primer carácter hasta el último (excluyendo sectionBreak)
        requests.append({
            "deleteContentRange": {
                "range": {
                    "startIndex": 1,
                    "endIndex": end_index - 1
                }
            }
        })
    
    # 2. Insertar nuevo contenido
    buzón_template = f"""


================================================================
{BUZON_MARKER_START}
================================================================
Instrucciones para Gemini:
1. Analiza el contexto del proyecto y el código fuente (disponible en GitHub).
2. Si tenés una propuesta de mejora autónoma, escribila abajo usando este formato:

[NUEVA_MEJORA]
OBJETIVO: [Breve descripción]
COMPONENTE: [ruta del archivo a modificar]
CÓDIGO_NUEVO:
```python
# Código nuevo o corregido
```
[FIN_MEJORA]

3. Podés dejar múltiples mejoras, una tras otra.
4. Zira procesará y limpiará el buzón automáticamente.

Instrucciones para Zira:
1. Lee periódicamente esta sección.
2. Si detectás [NUEVA_MEJORA], procesala con el pipeline automejora.
3. Borrá el tag procesado y escribí el resultado al final.

{BUZON_MARKER_END}"""

    full_text = context_text + buzón_template
    
    requests.append({
        "insertText": {
            "location": {"index": 1},
            "text": full_text
        }
    })
    
    # Ejecutar
    result = docs.batchUpdate(documentId=doc_id, body={"requests": requests}).execute()
    print(f"✅ Documento actualizado: {len(full_text)} caracteres")
    return True


def read_suggestions(service, doc_id):
    """Lee el contenido del doc y extrae sugerencias [NUEVA_MEJORA]."""
    document = service.documents().get(documentId=doc_id).execute()
    content = document.get("body", {}).get("content", [])
    
    # Reconstruir texto plano
    full_text = ""
    for elem in content:
        if "paragraph" in elem:
            for run in elem["paragraph"].get("elements", []):
                if "textRun" in run:
                    full_text += run["textRun"].get("content", "")
    
    # Extraer sugerencias
    suggestions = []
    pattern = re.compile(
        r'\[NUEVA_MEJORA\](.*?)\[FIN_MEJORA\]',
        re.DOTALL
    )
    
    for match in pattern.finditer(full_text):
        raw = match.group(1).strip()
        suggestion = {"raw": raw}
        
        # Extraer campos
        obj = re.search(r'OBJETIVO:\s*(.+)', raw)
        if obj: suggestion["objetivo"] = obj.group(1).strip()
        
        comp = re.search(r'COMPONENTE:\s*(.+)', raw)
        if comp: suggestion["componente"] = comp.group(1).strip()
        
        code = re.search(r'CÓDIGO_NUEVO:\s*```python\s*(.*?)```', raw, re.DOTALL)
        if code: suggestion["codigo"] = code.group(1).strip()
        
        suggestions.append(suggestion)
    
    return suggestions, full_text


def clear_processed(service, doc_id, suggestion_indices=None):
    """Marca como procesadas las sugerencias (las elimina del texto)."""
    suggestions, full_text = read_suggestions(service, doc_id)
    
    if not suggestions:
        print("📭 No hay sugerencias para limpiar")
        return
    
    # Reconstruir texto sin las sugerencias procesadas
    if suggestion_indices is None:
        suggestion_indices = list(range(len(suggestions)))
    
    new_text = full_text
    for idx in reversed(sorted(suggestion_indices)):
        if idx < len(suggestions):
            s = suggestions[idx]
            # Buscar el bloque [NUEVA_MEJORA]...[FIN_MEJORA] en el texto original
            pattern = re.escape(s["raw"])
            # Encerrar en el tag
            block = f"[NUEVA_MEJORA]\n{s['raw']}\n[FIN_MEJORA]"
            new_text = new_text.replace(block, "[PROCESADO ✓]", 1)
    
    # Actualizar el doc
    document = service.documents().get(documentId=doc_id).execute()
    end_index = document.get("body", {}).get("content", [{}])[-1].get("endIndex", 1)
    
    requests = [
        {"deleteContentRange": {"range": {"startIndex": 1, "endIndex": end_index - 1}}},
        {"insertText": {"location": {"index": 1}, "text": new_text}}
    ]
    service.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()
    print(f"✅ {len(suggestion_indices)} sugerencia(s) marcadas como procesadas")


# ─── CLI ───────────────────────────────────────────────────────────
def cmd_create():
    """Crea o actualiza el documento con contexto actual."""
    service = get_docs_service()
    if not service:
        return 1
    doc_id, created = find_or_create_doc(service)
    if not doc_id:
        return 1
    
    context = get_project_context()
    update_doc_content(service, doc_id, context)
    print(f"\n🔗 https://docs.google.com/document/d/{doc_id}/edit")
    return 0


def cmd_read():
    """Lee sugerencias pendientes."""
    service = get_docs_service()
    if not service:
        return 1
    doc_id, _ = find_or_create_doc(service)
    if not doc_id:
        return 1
    
    suggestions, _ = read_suggestions(service, doc_id)
    if not suggestions:
        print("📭 No hay sugerencias pendientes en el buzón")
        return 0
    
    print(f"📬 {len(suggestions)} sugerencia(s) encontrada(s):\n")
    for i, s in enumerate(suggestions):
        print(f"── Sugerencia #{i+1} ──")
        print(f"  Objetivo:   {s.get('objetivo', 'N/A')}")
        print(f"  Componente: {s.get('componente', 'N/A')}")
        if s.get('codigo'):
            print(f"  Código: {len(s['codigo'])} caracteres")
        print()
    return 0


def cmd_clear():
    """Limpia todas las sugerencias."""
    service = get_docs_service()
    if not service:
        return 1
    doc_id, _ = find_or_create_doc(service)
    if not doc_id:
        return 1
    clear_processed(service, doc_id)
    return 0


def cmd_scan():
    """Escanea docs nuevos del usuario y los agrega al buzón."""
    service = get_docs_service()
    if not service:
        return 1
    doc_id, _ = find_or_create_doc(service)
    if not doc_id:
        return 1

    drive = get_drive_service()
    if not drive:
        print("❌ No se pudo conectar a Drive")
        return 1

    new_docs = scan_new_docs(drive)
    if not new_docs:
        print("📭 No se encontraron documentos nuevos con ideas")
        return 0

    # Filtrar docs ya procesados
    processed = get_processed_docs()
    pending = [d for d in new_docs if d["id"] not in processed]
    
    if not pending:
        print("📭 No hay documentos nuevos sin procesar")
        return 0

    print(f"📄 {len(pending)} documento(s) nuevo(s) sin procesar:")
    for d in pending:
        print(f"  • {d['name']} — https://docs.google.com/document/d/{d['id']}/edit")

    # Agregarlos al buzón
    for d in new_docs:
        # Intentar leer el contenido
        try:
            doc = service.documents().get(documentId=d["id"]).execute()
            content = ""
            for el in doc.get("body", {}).get("content", []):
                if "paragraph" in el:
                    for tr in el["paragraph"].get("elements", []):
                        if "textRun" in tr:
                            content += tr["textRun"].get("content", "")
            text = f"[NUEVA_MEJORA]\nOBJETIVO: {d['name']} (documento nuevo)\nCOMPONENTE: Documento de Google Docs\nURL: https://docs.google.com/document/d/{d['id']}/edit\nContenido: {content.strip()[:500]}\n[FIN_MEJORA]"
            append_to_buzon(service, doc_id, text)
            save_processed_doc(d["id"])
            print(f"  ✅ Agregado al buzón: {d['name']}")
        except Exception as e:
            print(f"  ⚠ Error al leer {d['name']}: {e}")

    return 0


def cmd_status():
    """Muestra estado del proyecto en terminal."""
    print("📊 Estado del Proyecto CRM\n")
    print(get_project_context())
    return 0


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 scripts/buzon.py <create|read|clear|status>")
        return 1
    
    cmd = sys.argv[1]
    commands = {
        "create": cmd_create,
        "read": cmd_read,
        "clear": cmd_clear,
        "scan": cmd_scan,
        "status": cmd_status,
    }
    
    fn = commands.get(cmd)
    if not fn:
        print(f"Comando desconocido: {cmd}")
        print("Usá: create, read, scan, clear, status")
        return 1
    
    return fn()


if __name__ == "__main__":
    sys.exit(main())
