# ARTE_OPENCLAW.md — Espacio de Trabajo

**Agente:** openclaw
**Proyecto:** hola-3 — Gateway Execution y Automatización CRM
**Fecha:** 27 de Mayo de 2026

---

## 🎯 Rol

Ejecución de instrucciones del sistema híbrido (hybrid/server.py), procesamiento
batch de leads, sincronización con APIs externas, y automatización a bajo nivel
(mover archivos, ejecutar scripts, gateway de instrucciones).

---

## 📂 Archivos de Referencia

| Archivo | Propósito |
|---------|-----------|
| `ARTE_OPENCODE.md` | Análisis completo del proyecto |
| `ROADMAP.md` | Estado actual del desarrollo |
| `hybrid/gateway_client.py` | Cliente que te envía instrucciones |
| `hybrid/server.py` | FastAPI server que recibe webhooks |
| `hybrid/handlers/crm_flows.py` | Manejadores de eventos CRM |
| `crm/connectors.py` | Los 10 conectores que puedes invocar |
| `crm/orchestrator.py` | Flujos CRM completos |
| `crm/photo_pipeline.py` | Procesamiento de fotos |
| `crm/android_cua.py` | Android CUA (Computer Use Agent) |
| `equipo.py` | Datos del equipo Rancho Raíz |

---

## 🏗️ Infraestructura Disponible

- **Runtime:** Python 3.10+
- **Google APIs:** Gmail, Calendar, Drive, Sheets, Docs (OAuth2 configurado)
- **Telegram:** Bot API (token en .env)
- **Kommo:** CRM API v4
- **Notion:** API REST
- **WhatsApp:** Cloud API (token expirado — regenerar)
- **Instagram:** Graph API (token vivo)
- **Shizuku:** Android CUA (requiere foreground)
- **FastAPI + Uvicorn:** Hybrid Server en localhost
- **Pillow:** Procesamiento de imágenes

---

## 📐 Gateway de Instrucciones

El hybrid server recibe webhooks y te envía instrucciones a ejecutar.
Tú eres el ejecutor — el que realmente hace las llamadas a APIs.

### Formato de Instrucción

```python
class Instruction(BaseModel):
    action: str      # ej: "telegram.send_message", "kommo.create_lead"
    payload: Dict    # parámetros de la acción
```

### Formato de Evento Entrante

```python
class GatewayEvent(BaseModel):
    event_id: str
    type: str        # nueva_reserva, checkin, checkout, incidente, pago, telegram_msg, informe_diario
    timestamp: str
    source: str      # gmail, telegram, whatsapp, instagram, manual
    data: Dict
```

### Endpoints del Servidor

```bash
# Iniciar servidor
cd /data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3
python -m hybrid.server

# Probar envío de webhook
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "type": "nueva_reserva",
    "source": "telegram",
    "data": {
      "text": "Hola, quiero reservar para 4 personas del 15 al 18 de junio"
    }
  }'
```

---

## ⚡ Tareas Prioritarias

### 1. Procesar Instrucciones del Gateway
Cuando el hybrid server recibe un evento, debe:
1. Parsear el texto con IA (hybrid/parser.py)
2. Identificar la acción CRM necesaria
3. Enviarte la instrucción a ejecutar via `gateway_client.py`
4. Ejecutar la acción real (llamada API)
5. Reportar resultado al servidor

### 2. Sincronización Batch
- Ejecutar `crm/orchestrator.py --gmail-digest` periódicamente
- Sincronizar leads de Kommo → CRM local
- Backup automático de `crm_state/` a Google Drive

### 3. Pipeline de Fotos
Ejecutar PhotoPipeline para:
```bash
# Procesar foto individual
python -c "
from crm.photo_pipeline import PhotoPipeline
pp = PhotoPipeline('crm_state')
result = pp.process('ruta/foto.jpg', 'asset-001', caption='Mi foto')
print(result)
"
```

### 4. Android CUA Automation
Si Shizuku está activo:
```python
from crm.android_cua import CuaManager
cua = CuaManager()
cua.open_app("com.whatsapp")  # Abrir WhatsApp automáticamente
cua.tap_by_text("Rancho Raíz")  # Tocar contacto
cua.input_text("Hola, soy Zira. Te confirmo tu reserva.")
cua.press_key("ENTER")
```

### 5. Notificaciones Android
```bash
python -c "
from asistente.utils.notification import send_notification
send_notification(title='CRM', message='Nueva reserva recibida')
"
```

---

## 🔄 Flujo Típico de Ejecución

```
1. Llega webhook → hybrid/server.py
2. Server parsea con IA + regex fallback
3. Server deduce acción → crea Instruction[]
4. gateway_client.py te envía las instrucciones
5. TÚ las ejecutas (llamadas HTTP reales)
6. Reportas resultado al server
7. Server persiste en hybrid/store.py
```

---

## 🧪 Comandos Útiles

```bash
# Verificar estado de conectores
python -m crm.cli --check-connectors

# Ejecutar demo de journey completo
python -m crm.cli --journey-demo --lead-name="Cliente Test" --guests=2

# Ver estado del store CRM
cat crm_state/leads.json | python -m json.tool

# Probar envío Telegram
python -c "
from crm.connectors import TelegramConnector
import os
tg = TelegramConnector(os.environ['CRM_TG_TOKEN'], int(os.environ['CRM_TG_CHAT_ID']))
print(tg.send_message('Hola desde OpenClaw'))
"

# Listar comandos del bot Telegram
python asistente/telegram/telegram_bot.py --help

# Probar parser de reservas
python -c "
from hybrid.parser import parse_reserva
result = parse_reserva('Hola, quiero reservar para el finde, 2 adultos')
print(result)
"

# Generar PDF de ejemplo
python generar_pdf.py

# Monitorear procesos
ps aux | grep python
```

---

## ⚠️ Restricciones y Bugs

- **WhatsApp token expirado** — Necesita regenerar en Meta Developers
- **termux-api** — Linker roto (`libnativeloader.so`). Usar comandos directos.
- **Android scoped storage** — No guardar en `/sdcard/`. Usar `~/` o `crm_state/`.
- **Instagram video publish** — No implementado. Solo imágenes.
- **CUA requiere Shizuku** en foreground — No funciona en background.
- **Google OAuth** — Se auto-refresca, pero si expira, ejecutar `python reauth_google.py`

---

## 📁 Output y Logs

Los resultados de ejecución se guardan en:
```
crm_state/              ← Estado CRM (leads, assets, events)
hybrid/store.py         ← Eventos del servidor híbrido
notification_log.txt    ← Historial de notificaciones
```

Para logs en tiempo real:
```bash
journalctl -f  # si systemd
# o simplemente
python hybrid/server.py 2>&1 | tee hybrid.log
```

---

## 🎯 Segunda Mision: Pruebas de Pipeline ARTE (desde 29-May-2026)

### Bitacora de configuracion

| Fecha | Cambio | Resultado |
|-------|--------|-----------|
| 28-May | big-pickle como primario | 401 no soportado ❌ |
| 28-May | Nemotron como primario | Token limit gratis, inestable ⚠️ |
| 29-May | Gemini 2.5 Flash como primario | Funciona con reasoning: false ✅ |

### Estado actual del modelo
- **Primario:** `gemini-2.5-flash` via OpenAI-compatible endpoint
- **Fallback:** `nvidia/nemotron-3-super-120b-a12b`
- **Auth:** Gemini API key configurada en auth-profiles.json
- **Proveedor:** `gemini` con baseUrl `https://generativelanguage.googleapis.com/v1beta/openai`
- **Observacion:** El modelo con `reasoning: true` devuelve contenido vacio en el endpoint OpenAI-compatible. Con `reasoning: false` funciona correctamente.

### Proxima prueba: Persistencia real 24/7 (simulada 1 hora)

En lugar del runner bash (sin LLM), el agente OpenClaw debe ejecutar el pipeline directamente cada 10 min durante 1 hora. Esto prueba:
- Persistencia del agente en sesion larga
- Consumo de tokens de Gemini gratis
- Estabilidad del gateway con llamadas recurrentes
- Capacidad del agente de autogestionar su loop

### Plan de prueba (1 hora, ~6 ciclos)

| Ciclo | Comando | Que prueba |
|-------|---------|------------|
| 1 | `pipeline.py --solo-banner --auto` | Banner desde cache |
| 2 | `pipeline.py --solo-gif --auto` | GIF desde cache |
| 3 | `pipeline.py --solo-reel --auto` | Reel desde cache |
| 4 | `pipeline.py --mode cache --auto` | Banner + GIF + reel completo |
| 5 | `pipeline.py --solo-banner --poll` | Banner con aprobacion Telegram |
| 6 | `pipeline.py --mode cache --auto` | Cierre completo |

### Log de persistencia

| # | Hora | Ciclo | Resultado | Obs |
|---|------|-------|-----------|-----|
| 1 | 06:08 | `--solo-banner --auto` | COMPLETADO ✅ | Banner desde caché, enviado a Telegram y email notificado |
| 2 | 06:17 | `--solo-gif --auto` | 429 RATE LIMIT ❌ | Gemini free tier: cuota diaria/minuto agotada |
| 3 | 06:33 | `--solo-reel --auto` | TIMEOUT ❌ | El pipeline se quedó atascado, probablemente por el agotamiento de tokens en la cadena de modelos. El proceso fue terminado. |
| 4 | 12:34 | `--mode cache --auto` | TIMEOUT ❌ | El pipeline se quedó atascado, incluso después del posible reinicio de la cuota de Gemini. El proceso fue terminado. |

### Gemini Free Tier — Limites reales (investigado web)

| Modelo | RPM | TPM | RPD | Contexto |
|--------|-----|-----|-----|----------|
| **Gemini 2.5 Flash** | 10 | 250K | 250 | 1M tokens |
| **Gemini 2.5 Flash Lite** | 30 | 1M | 1,000 | 1M tokens |

- Los limites son **por proyecto**, no por API key
- RPD se resetea a **medianoche Pacific Time** (07:00 UTC)
- Esta API key venia siendo usada en AI Studio, por eso se agoto rapido
- Manana deberia renovarse el contador diario

### Cadena de modelos configurada (29-May)

| Prioridad | Modelo | Donde esta |
|-----------|--------|------------|
| 1° | `gemini-2.5-flash` | openclaw.json + models.json |
| 2° | `gemini-2.5-flash-lite` | openclaw.json + models.json |
| 3° | `nvidia/nemotron-3-super-120b-a12b` | openclaw.json + models.json |

OpenClaw hace fallback automatico entre los modelos listados.

### Opciones para produccion 24/7

| Opcion | Ventaja | Desventaja |
|--------|---------|------------|
| 1. Usar Flash-Lite (30 RPM, 1000 RPD) | Mayor cuota gratis | Modelo mas simple |
| 2. Agregar billing (Tier 1) | 150-300 RPM, sin RPD | Cuesta $ |
| 3. Rotar entre Gemini + Nemotron | Distribuye carga | Nemotron tambien tiene limites |
| 4. Usar OpenRouter con Gemini | Unica API, multiple providers | Costo por token |

| # | Hora | Comando | Resultado | Obs |
|---|------|---------|-----------|-----|
<!-- runner-insert -->
| 1 | 00:29 | `--mode cache --auto` | COMPLETADO ✅ | Banner, GIF y reel desde cache, enviados a Telegram y email notificado |
| 2 | 00:39 | `--solo-banner --auto` | TIMEOUT ❌ | El proceso se detuvo tras 10 minutos sin salida, se canceló |

*(runner.sh inserta nuevas filas automaticamente)*

### Runner automatizado (`runner.sh`)
```bash
# Iniciar:
cd /data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3
bash runner.sh

# El runner:
# - Cicla entre 4 modos (full, banner, gif, reel)
# - Limpia spool de Telegram antes de cada ciclo
# - Timeout de 5 min por pipeline
# - Logea cada ciclo en esta tabla
# - Registra heartbeat
# - Maneja SIGINT/SIGTERM para cierre limpio
```

### Registro de latidos
```bash
python /data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3/.worktrees/openclaw/heartbeat.py --beat openclaw "runner ciclo N"
```
