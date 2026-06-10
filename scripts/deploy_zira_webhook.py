#!/usr/bin/env python3
"""
Despliega el webhook de Google Apps Script para Zira Chat.

Intenta crear y deployar via API. Si no tiene permisos,
imprime instrucciones para deploy manual (2 min).
"""

import sys, json, time
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

TOKEN_FILE = PROJECT_DIR / "crm_state" / ".google_token.json"
GS_FILE = PROJECT_DIR / "simulaciones" / "chats" / "gs_zira_chat.gs"

# Intentar API primero
def try_api_deploy():
    """Intenta deployar via Apps Script API."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    import urllib.request, urllib.error

    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), [
        "https://www.googleapis.com/auth/script.projects",
        "https://www.googleapis.com/auth/script.deployments",
    ])
    if not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            return None
    
    # Leer el código
    code = GS_FILE.read_text()
    
    # Crear proyecto
    import googleapiclient.discovery as discovery
    svc = discovery.build('script', 'v1', credentials=creds)
    
    try:
        project = svc.projects().create(body={
            'title': 'Zira Chat Webhook',
            'parentId': '1MK76i7CTM44yCJu32SIq1fdOU5uVMBG5HXWWpoKfklg'
        }).execute()
        project_id = project['scriptId']
        print(f"✅ Proyecto creado: {project_id}")
        
        # Subir código
        svc.projects().updateContent(
            scriptId=project_id,
            body={
                'files': [{
                    'name': 'Codigo',
                    'type': 'SERVER_JS',
                    'source': code
                }, {
                    'name': 'appsscript',
                    'type': 'JSON',
                    'source': json.dumps({
                        'timeZone': 'America/Argentina/San_Juan',
                        'dependencies': {},
                        'exceptionLogging': 'STACKDRIVER',
                        'runtimeVersion': 'V8'
                    })
                }]
            }
        ).execute()
        print("✅ Código subido")
        
        # Crear deployment como web app
        deployment = svc.projects().deployments().create(
            scriptId=project_id,
            body={
                'versionNumber': 1,
                'manifestFileName': 'appsscript',
                'description': 'Webhook Zira Chat v1'
            }
        ).execute()
        
        # Extraer URL del deployment
        deployment_id = deployment.get('deploymentId', '')
        print(f"✅ Deployment creado: {deployment_id}")
        
        # La URL de web app se construye así
        webapp_url = f"https://script.google.com/macros/s/{deployment_id}/exec"
        print(f"✅ Web App URL: {webapp_url}")
        
        return webapp_url
        
    except Exception as e:
        print(f"⚠️  API falló: {e}")
        return None


def print_manual_instructions():
    """Imprime instrucciones para deploy manual."""
    gs_path = str(GS_FILE)
    print()
    print("=" * 60)
    print("  DEPLOY MANUAL (2 minutos)")
    print("=" * 60)
    print()
    print("  1. Abrí este link en tu navegador:")
    print("     https://script.google.com/create")
    print()
    print(f"  2. Copiá TODO el contenido de:")
    print(f"     {gs_path}")
    print()
    print("  3. Pegalo en el editor (reemplaza todo)")
    print()
    print("  4. Guardá: Ctrl+S → Nombre: 'Zira Chat'")
    print()
    print("  5. Deploy → 'Implementar como aplicación web'")
    print("     • Ejecutar como: 'Yo' (tu cuenta)")
    print("     • Quién tiene acceso: 'Cualquier usuario'")
    print()
    print("  6. Copiá la URL del webhook")
    print()
    print("  7. Pegala en zira-huespedes.html donde dice:")
    print("     WEBAPP_URL = 'ACA_VA_LA_URL'")
    print()
    print("  8. Hacé commit y push del HTML")
    print()
    print("=" * 60)


def main():
    print("🔧 Desplegando Zira Chat Webhook...\n")
    
    url = try_api_deploy()
    
    if url:
        print(f"\n✅ Webhook listo: {url}")
        # Guardar URL en un archivo de referencia
        ref_file = PROJECT_DIR / "simulaciones" / "chats" / ".webhook_url"
        ref_file.write_text(url)
        print(f"   URL guardada en {ref_file}")
    else:
        print_manual_instructions()


if __name__ == '__main__':
    main()
