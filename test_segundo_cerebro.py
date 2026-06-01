import json, os
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import time
import re

print('=== DEMOSTRACIÓN: Flujo de trabajo con "Segundo Cerebro" (Google Docs) ===')
print('Basado en el documento: Ideas - Segundo Cerebro Rancho Raiz')
print('=' * 70)

def _token_path():
    return Path(os.environ.get('CRM_STATE_DIR', 'crm_state')) / '.google_token.json'

# Configurar credenciales
token_file = _token_path()
with open(token_file) as f:
    stored = json.load(f)

creds = Credentials.from_authorized_user_file(str(token_file), stored.get('scopes', []))
if creds.expired and creds.refresh_token:
    print('🔄 Refrescando token de acceso...')
    creds.refresh(Request())
    token_file.write_text(json.dumps(json.loads(creds.to_json())))
    print('✅ Token refrescado y guardado.')

# Construir servicios
docs_service = build('docs', 'v1', credentials=creds)
drive_service = build('drive', 'v3', credentials=creds)

print('')
print('📋 PASO 1: Leyendo el documento de "Ideas - Segundo Cerebro"...')
print('-' * 50)

# Buscar el documento específico
results = drive_service.files().list(
    q="name='Ideas - Segundo Cerebro Rancho Raiz' and mimeType='application/vnd.google-apps.document'",
    pageSize=1,
    fields="files(id, name, modifiedTime)"
).execute()

items = results.get('files', [])

if not items:
    print('❌ No se encontró el documento de Ideas')
else:
    doc_id = items[0]['id']
    doc_title = items[0]['name']
    modified_time = items[0]['modifiedTime']
    print(f'📄 Documento encontrado: "{doc_title}"')
    print(f'🕒 Última modificación: {modified_time}')
    print(f'🔗 ID: {doc_id}')
    
    # Obtener el contenido
    print('')
    print('📖 PASO 2: Extrayendo contenido del documento...')
    print('-' * 50)
    
    try:
        doc = docs_service.documents().get(documentId=doc_id).execute()
        
        # Función para extraer texto
        def extract_text_from_struct(struct):
            text = ''
            if 'paragraph' in struct:
                for elem in struct['paragraph'].get('elements', []):
                    if 'textRun' in elem:
                        text += elem['textRun'].get('content', '')
            elif 'table' in struct:
                for row in struct['table'].get('tableRows', []):
                    for cell in row.get('tableCells', []):
                        for content in cell.get('content', []):
                            text += extract_text_from_struct(content)
            elif 'tableOfContents' in struct:
                for content in struct['tableOfContents'].get('content', []):
                    text += extract_text_from_struct(content)
            return text
        
        full_text = ''
        for element in doc.get('body', {}).get('content', []):
            full_text += extract_text_from_struct(element)
        
        # Limpiar texto
        lines = [line.strip() for line in full_text.split('\n') if line.strip()]
        cleaned_text = '\n'.join(lines)
        
        print(f'📝 Caracteres totales: {len(cleaned_text)}')
        print(f'📄 Líneas totales: {len(lines)}')
        
        # Buscar secciones clave
        print('')
        print('🔍 PASO 3: Analizando contenido para encontrar ideas accionables...')
        print('-' * 50)
        
        # Buscar la sección de "ULTIMAS IDEAS"
        ideas_section_match = re.search(r'ULTIMAS IDEAS:(.*?)(?:\n\n|\n[A-Z]|$)', cleaned_text, re.DOTALL | re.IGNORECASE)
        if ideas_section_match:
            ideas_section = ideas_section_match.group(1).strip()
            print('💡 Sección "ULTIMAS IDEAS" encontrada:')
            preview = ideas_section[:200] + ("..." if len(ideas_section) > 200 else "")
            print(f'   "{preview}"')
            
            # Buscar ideas que comiencen con guion o número
            idea_lines = [line.strip() for line in ideas_section.split('\n') if line.strip()]
            actionable_ideas = []
            for line in idea_lines:
                if line.startswith('-') or line.startswith('•') or re.match(r'^\d+\.', line):
                    # Limpiar el marcador
                    idea = re.sub(r'^[-•\d.\s]+', '', line).strip()
                    if idea and idea.lower() not in ['(escribe aca tus ideas nuevas)', '']:
                        actionable_ideas.append(idea)
            
            if actionable_ideas:
                print('')
                print(f'✨ {len(actionable_ideas)} ideas accionables encontradas:')
                for i, idea in enumerate(actionable_ideas[:3], 1):  # Mostrar hasta 3
                    print(f'   {i}. {idea}')
            else:
                print('')
                print('📝 No se encontraron ideas accionables específicas (solo placeholders o instrucciones)')
                
        # Buscar la sección de "HISTORIAL" 
        history_match = re.search(r'Historial:(.*?)(?:\n\n|\n[A-Z]|$)', cleaned_text, re.DOTALL | re.IGNORECASE)
        if history_match:
            history_section = history_match.group(1).strip()
            print('')
            print(f'📜 Sección "HISTORIAL" encontrada ({len(history_section)} caracteres)')
            # Mostrar las últimas 2 líneas del historial
            history_lines = [line.strip() for line in history_section.split('\n') if line.strip() and not line.startswith('=')]
            if history_lines:
                print('   Últimas entradas del historial:')
                for line in history_lines[-2:]:
                    print(f'   • {line}')
        
        print('')
        print('🎯 PASO 4: Simulando ejecución de una idea (modo demostración)...')
        print('-' * 50)
        
        # En lugar de ejecutar realmente una idea (que podría requerir aprobación),
        # vamos a demostrar cómo sería el proceso de documentación de resultados
        
        demo_idea = "Probar conexión con la API de Google Sheets para verificar estado de reservas"
        print(f'💡 Idea de ejemplo a procesar: "{demo_idea}"')
        print('🤔 Evaluando si necesita aprobación...')
        
        # Según las reglas: Si requiere aprobación, preguntar por Telegram
        # Para esta demo, asumimos que es una operación segura de solo lectura
        needs_approval = False  # En realidad, esto dependería de la naturaleza de la idea
        
        if needs_approval:
            print('📱 [SIMULACIÓN] Enviando solicitud de aprobación por Telegram...')
            print('   Esperando respuesta... (en un caso real, el agente esperaría aquí)')
            print('   ✅ Aprobación recibida (simulado)')
        else:
            print('✅ Idea considerada segura para ejecutar sin aprobación previa')
        
        print('')
        print('⚙️  Ejecutando idea...')
        # Simular alguna acción (en este caso, verificamos Google Sheets de nuevo)
        try:
            sheets_service = build('sheets', 'v4', credentials=creds)
            # Usar una hoja de muestra para no afectar datos reales
            result = sheets_service.spreadsheets().get(
                spreadsheetId='1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'
            ).execute()
            sheet_title = result.get('properties', {}).get('title', 'Desconocido')
            print(f'✅ Acción completada con éxito: Verificó hoja de cálculo "{sheet_title}"')
            print('📊 Esto confirmaría que las APIs de Google están funcionando correctamente')
        except Exception as e:
            print(f'❌ Error al ejecutar la idea: {e}')
        
        print('')
        print('📝 PASO 5: Documentando el resultado en el mismo documento...')
        print('-' * 50)
        print('   [En un caso real, aquí se agregaría una entrada al documento]')
        print('   Ejemplo de qué se documentaría:')
        print('   21-May-2026:')
        print('   - Probó conexión con Google Sheets API')
        print('   - Resultado: Éxito - Hoja de cálculo accesible')
        print('   - Conclusión: Los conectores de Google están funcionando correctamente')
        
    except Exception as e:
        print(f'❌ Error al procesar el documento: {e}')
        import traceback
        traceback.print_exc()

print('')
print('=' * 70)
print('✨ DEMOSTRACIÓN COMPLETADA')
print('')
print('📌 RESUMEN DE LO QUE SE PUEDE HACER CON EL "SEGUNDO CEREBRO":')
print('   1. Leer periódicamente el documento de ideas')
print('   2. Extraer ideas accionables (las que comienzan con -, • o números)')
print('   3. Evaluar si cada idea requiere aprobación (según reglas definidas)')
print('   4. Ejecutar ideas seguras inmediatamente')
print('   5. Solicitar aprobación por Telegram para ideas que lo requieran')
print('   6. Documentar resultados y conclusiones en el mismo documento')
print('   7. Mantener un historial de lo que se ha hecho')
print('')
print('🔧 PRÓXIMOS PASOS PARA IMPLEMENTAR ESTE FLUJO AUTOMÁTICO:')
print('   - Crear un script que ejecute este ciclo cada N minutos/horas')
print('   - Integrar notificaciones de Telegram para solicitudes de aprobación')
print('   - Añadir lógica de aprendizaje para mejorar la evaluación de ideas')
print('   - Considerar usar el documento de "Perfil Virtual" para contexto adicional')
