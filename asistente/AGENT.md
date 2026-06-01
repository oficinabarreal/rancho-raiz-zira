# Asistente Personal - CRM Rancho Raíz

## Descripción
Este asistente implementa capacidades de automatización para el ecosistema Google (Gmail, Calendar, Sheets, Drive) y otras plataformas (Telegram, Instagram). Su foco es ofrecer **habilidades genéricas** que puedan combinarse para resolver múltiples tareas, como búsqueda de correos, gestión de calendarios, manipulación de hojas de cálculo, subida de archivos a Drive, y comunicación por Telegram.

## Funcionalidades principales
- **Gmail**: Listar mensajes, obtener contenido (texto/adjuntos), enviar correos (con/sin adjuntos), modificar etiquetas.
- **Calendar**: Listar eventos, crear citas, actualizar y eliminar eventos.
- **Sheets**: Leer rangos, escribir datos, añadir filas.
- **Drive**: Listar archivos y carpetas, subir/descargar, mover, actualizar metadatos.
- **Telegram**: Enviar mensajes y documentos, bot con comandos generales (`/start`, `/emails`, `/status`).
- **Instagram**: (conector base) para publicar y leer contenido.
- **Utilidades de envío de correo**: Capa de alto nivel `send_gmail_mime` para emails multipart (texto + adjuntos).
- **Ejemplos de flujos específicos**: La carpeta `examples/` contiene un caso de uso de factura (generación PDF y envío) como referencia.

## Arquitectura de habilidades (estructura por ecosistema)

```
asistente/
├── __init__.py
├── AGENT.md
├── ROADMAP.md
├── mail_utils.py
│
├── google/
│   ├── __init__.py
│   ├── gmail.py          # GmailConnector
│   ├── calendar.py       # CalendarConnector
│   ├── sheets.py         # SheetsConnector
│   └── drive.py          # DriveConnector
│
├── telegram/
│   ├── __init__.py
│   ├── telegram.py       # TelegramConnector
│   └── telegram_bot.py   # Bot polling con comandos generales
│
├── instagram/
│   ├── __init__.py
│   └── instagram.py      # InstagramConnector
│
└── examples/             # Flujos de ejemplo (no habilidades)
    ├── generar_pdf.py    # Genera factura PDF desde TXT (ejemplo)
    ├── enviar_pdf.py     # Envía PDF por Gmail (ejemplo)
    ├── factura_alejandro_beltran.txt
    └── factura_alejandro_beltran.pdf
```

### Cómo importar habilidades (Agent Quick Reference)

| Habilidad         | Ruta de importación                         | Uso típico |
|-------------------|---------------------------------------------|-------------|
| Gmail API         | `from asistente.google.gmail import GmailConnector` | Buscar, leer, enviar correos |
| Calendar          | `from asistente.google.calendar import CalendarConnector` | Gestionar eventos |
| Sheets            | `from asistente.google.sheets import SheetsConnector` | Leer/escribir hojas |
| Drive             | `from asistente.google.drive import DriveConnector` | Gestionar archivos |
| Telegram API      | `from asistente.telegram.telegram import TelegramConnector` | Enviar mensajes |
| Instagram         | `from asistente.instagram.instagram import InstagramConnector` | Publicar contenido |
| Utilidad mail     | `from asistente.mail_utils import send_gmail_mime, GmailSender` | Envío de correos con adjuntos |

> **Nota:** Cada módulo `*_connector` re-exporta la clase correspondiente de `crm.connectors`. Puedes usar directamente `crm.connectors` si prefieres no pasar por el paquete `asistente`.

### Ejemplo: bot de Telegram (comandos)

Una vez iniciado el bot (`python -m asistente.telegram.telegram_bot`), los comandos disponibles son:

- `/start` – Mensaje de bienvenida.
- `/emails [consulta]` – Interpreta peticiones en lenguaje natural (ej: "dame el último no leído", "de Alejandro"). Acepta también queries crudos de Gmail. Si el modelo LLM (OpenCode Zen) no está disponible, recae a un parser heurístico.
- `/status` – Muestra estado del sistema (token Gmail, ejemplos, etc.).

### Ejemplo: uso programático de Gmail

```python
from asistente.google.gmail import GmailConnector

gmail = GmailConnector()
# Buscar correos no leídos
mensajes = gmail.list_messages(query='is:unread', max_results=5)
for m in mensajes:
    meta = gmail.get_message(m['id'], content_type='metadata')
    # procesar headers...
```

---

## Cómo usar (rápido)
1. **Instalar dependencias**:
   ```bash
   pip install google-api-python-client google-auth-oauthlib fpdf2 python-telegram-bot
   ```
2. **Preparar credenciales**: Asegurar `CREDENCIALES.md` y token `crm_state/.google_token.json` en la raíz del proyecto. Para el bot, definir `TELEGRAM_BOT_TOKEN` (variable de entorno) o `CRM_TG_TOKEN` (en `.env`).
3. **Ejecutar** desde la raíz `hola-3` con `python -m`:
   - Iniciar bot de Telegram:
     ```bash
     python -m asistente.telegram.telegram_bot
     ```
   - Usar comandos en Telegram: `/start`, `/emails`, `/status`.
4. **Probar ejemplos**: Los scripts de factura están en `asistente/examples/` (no son habilidades principales). Se ejecutan con:
   ```bash
   python -m asistente.examples.generar_pdf
   python -m asistente.examples.enviar_pdf
   ```

---

## Notas importantes
- Todos los módulos usan rutas relativas e inyectan `PROJECT_ROOT` en `sys.path` para que `crm.connectors` sea importable.
- El bot de Telegram puede extenderse con nuevos comandos que utilicen cualquier conector del asistente.
- Los ejemplos de `examples/` son demostrativos y no forman parte del conjunto de habilidades reutilizables.

## Extensión
Para añadir una nueva **habilidad** (conector):
1. Crea una subcarpeta en `asistente/` (ej: `whatsapp/`).
2. Dentro, un archivo `<servicio>.py` que re-exporte el conector desde `crm.connectors` o implemente uno nuevo.
3. Documenta la importación en este AGENT.md.
4. Si requiere credenciales, agrégalas a `CREDENCIALES.md` y/o `.env`.

Para añadir un **comando al bot**:
1. Edita `asistente/telegram/telegram_bot.py`.
2. Añade una función `async def nuevo_comando(update, context): ...`
3. Regístrala con `application.add_handler(CommandHandler("nuevo", nuevo_comando))`
4. Usa los conectores existentes dentro de la función.

---

## Estado de las integraciones (probado)
- ✅ Gmail (lectura, envío)
- ✅ Calendar
- ✅ Sheets
- ✅ Drive
- ✅ Telegram (envío de mensajes y bot)
- ✅ Instagram (lectura de media)

## Roadmap
Ver `ROADMAP.md` para el plan de mejoras: scheduler, CLI unificada, logs, rate limiting, etc.

---

## Para agentes de IA
- **Punto de entrada**: Explora los conectores en `google/`, `telegram/`, `instagram/`. El bot de Telegram es `telegram_bot.py`.
- **Credenciales**: Busca `CREDENCIALES.md` y `crm_state/.google_token.json` en la raíz. El token de Telegram puede estar en la variable de entorno `TELEGRAM_BOT_TOKEN` o `CRM_TG_TOKEN`, o en `.env`.
- **Ejecución**: Usa `python -m asistente.<modulo>` o `python -m asistente.telegram.telegram_bot`.
- **Evita conflictos de path**: No ejecutes scripts directamente desde `asistente/` (ej: `python asistente/generar_pdf.py`), porque el directorio `asistente/` en `sys.path` puede enmascarar el paquete `google`. Usa siempre `-m` desde la raíz.

### Flujo típico de agente (ejemplo)
```python
# 1. Listar correos no leídos
from asistente.google.gmail import GmailConnector
gmail = GmailConnector()
unread = gmail.list_messages(query='is:unread', max_results=5)

# 2. Subir archivo a Drive
from asistente.google.drive import DriveConnector
drive = DriveConnector()
drive.upload_file('/ruta/local/file.txt', mime_type='text/plain', folder_id='ID_CARPETA')

# 3. Enviar notificación por Telegram
from asistente.telegram.telegram import TelegramConnector
tg = TelegramConnector(chat_id=CHAT_ID)
tg.send_message(f"Se subieron {len(unread)} correos no leídos y el archivo file.txt a Drive.")
```