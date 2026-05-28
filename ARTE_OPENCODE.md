# ARTE_OPENCODE.md — Mi Espacio de Trabajo

**Agente:** opencode
**Fecha del informe:** 27 de Mayo de 2026
**Proyecto:** hola-3 — CRM Automation para Rancho Raíz (Zira)

---

## 🏆 LOGRO: Mapeo Completo del Proyecto

Este archivo documenta la arquitectura completa del sistema CRM hola-3,
sus conectores, flujos de trabajo, y el plan de integración con el
proyecto `publicidad` (generación de reels).

---

## 📊 Resumen del Sistema

### ¿Qué es hola-3?

Un sistema de automatización CRM para la posada **Rancho Raíz** (Calingasta,
San Juan, Argentina). El sistema recibe leads desde múltiples canales
(Gmail, WhatsApp, Instagram, Telegram, Web), los califica, los persiste
en un store local JSON, y ejecuta acciones automáticas como:
- Crear eventos en Google Calendar
- Subir fotos a Google Drive
- Registrar leads en Kommo (CRM)
- Enviar mensajes por Telegram/WhatsApp
- Generar notificaciones en Android (termux-notification)

### Stack Tecnológico

| Tecnología | Uso | Estado |
|-----------|-----|--------|
| **Python 3.10+** | Lenguaje principal | ✅ Funcional |
| **Google APIs** | Gmail, Calendar, Drive, Sheets, Docs | ✅ OAuth configurado |
| **python-telegram-bot** | Bot de Telegram principal | ✅ Funcional |
| **Pillow** | Procesamiento de fotos (PhotoPipeline) | ✅ Con fallback |
| **FastAPI + Uvicorn** | Hybrid AI Server | ✅ Implementado |
| **Pydantic** | Modelos de datos (hybrid/) | ✅ Implementado |
| **Requests** | Clientes HTTP (Kommo, Notion, WhatsApp, Instagram) | ✅ Implementado |
| **Termux-API** | Notificaciones Android | ⚠️ Linker roto |
| **Shizuku + CUA** | Android Computer Use Agent | 🚧 Experimental |

---

## 🏗️ Arquitectura del Proyecto

```
hola-3/
├── AGENT.md                    ← Guía original del proyecto
├── ROADMAP.md                  ← Roadmap con ✅ y 🚧
├── CREDENCIALES.md             ← Referencia de credenciales
├── ARTE_OPENCODE.md            ← ← ESTE ARCHIVO
├── ARTE_OPENCLAW.md            ← Workspace para openclaw
├── ARTE_HERMES.md              ← Workspace para hermes
├── .env                        ← Variables de entorno (NO git)
│
├── crm/                        ← ★ Núcleo del CRM
│   ├── __init__.py
│   ├── connectors.py           ← 10 conectores unificados (813 líneas)
│   ├── orchestrator.py         ← CRMOrchestrator (flujos completos)
│   ├── models.py               ← Dataclasses: Lead, PhotoAsset, CRMEvent
│   ├── store.py                ← CRMStore (JSON persistente)
│   ├── photo_pipeline.py       ← PhotoPipeline (Pillow) 5 variantes
│   ├── autonomy.py             ← "Segundo Cerebro" (Google Docs)
│   ├── cli.py                  ← CLI argparse (--journey-demo, etc.)
│   ├── google_auth.py          ← OAuth2 para Google APIs
│   ├── oauth_capture.py        ← Captura de código OAuth
│   └── android_cua.py          ← Computer Use Agent (Shizuku)
│
├── asistente/                  ← ★ Asistentes de IA
│   ├── telegram/
│   │   ├── telegram_bot.py     ← Bot principal (358 líneas)
│   │   └── telegram.py         ← Cliente Telegram simple
│   ├── google/
│   │   ├── gmail.py            ← Conector Gmail (independiente)
│   │   ├── calendar.py         ← Conector Calendar
│   │   ├── drive.py            ← Conector Drive
│   │   └── sheets.py           ← Conector Sheets
│   ├── instagram/
│   │   └── instagram.py        ← Conector Instagram
│   ├── examples/               ← Ejemplos: generar_pdf, enviar_pdf
│   ├── utils/
│   │   └── notification.py     ← termux-notification wrapper
│   └── mail_utils.py           ← Utilidades de correo
│
├── hybrid/                     ← ★ Sistema Híbrido IA
│   ├── server.py               ← FastAPI server (webhook gateway)
│   ├── gateway_client.py       ← Cliente del Gateway OpenClaw
│   ├── models.py               ← Pydantic: GatewayEvent, Instruction, etc.
│   ├── parser.py               ← Parser con IA + regex fallback
│   ├── config.py               ← Configuración (host, puerto, modelo)
│   ├── store.py                ← Store para el servidor híbrido
│   ├── handlers/
│   │   └── crm_flows.py        ← Manejadores de eventos CRM
│   ├── simulacion_equipo.py    ← Simulación de team members
│   ├── instagram_sim.py        ← Simulador de Instagram
│   ├── demo_real.py            ← Demo real del sistema
│   └── test_hybrid.py          ← Tests del sistema híbrido
│
├── simulators/                 ← ★ Simuladores
│   ├── crm_simulator.py        ← Simulador general del CRM
│   ├── zira_bot.py             ← Bot Zira (simulado)
│   ├── zira_photo_pipeline.py  ← Pipeline de fotos Zira
│   ├── zira_telegram.py        ← Cliente Telegram Zira
│   ├── zira_voice.py           ← Voz Zira (TTS)
│   ├── send_zira_menu.py       ← Enviar menú Zira
│   └── voice_demo.py           ← Demo de voz
│
├── equipo.py                   ← Datos del equipo + huéspedes registrados
├── parser.py                   ← Parser NL independiente
├── idea_engine.py              ← Motor de ideas contextuales
├── project_monitor.py          ← Monitor con Gemini API + notificaciones
├── simular.py                  ← Script de simulación
├── telegram_listener.py        ← Listener de Telegram
├── demo_notifications.py       ← Demo de notificaciones
├── cua_test_full.py            ← Test de CUA
├── test_segundo_cerebro.py     ← Test del Segundo Cerebro
├── generar_pdf.py, enviar_pdf.py, informe_diario.py, reauth_google.py
└── crm_state/                  ← Estado persistente (gitignored)
```

---

## 🔌 Los 10 Conectores (crm/connectors.py)

Cada conector extiende `BaseConnector` y retorna `ConnectorResult(ok, data, error)`.

| Conector | API | Auth | Estado |
|----------|-----|------|--------|
| `GmailConnector` | Gmail API v1 | OAuth2 | ✅ Real |
| `TelegramConnector` | Telegram Bot API v6 | Token | ✅ Real |
| `DriveConnector` | Google Drive v3 | OAuth2 | ✅ Real |
| `CalendarConnector` | Google Calendar v3 | OAuth2 | ✅ Real |
| `SheetsConnector` | Google Sheets v4 | OAuth2 | ✅ Real |
| `DocsConnector` | Google Docs v1 | OAuth2 | ✅ Real |
| `AndroidCuaConnector` | Shizuku/ADB | Shizuku | 🚧 Exp. |
| `KommoConnector` | Kommo API v4 | Token | ✅ Config. |
| `NotionConnector` | Notion API | Token | ✅ Config. |
| `WhatsAppConnector` | WhatsApp Cloud API | Token | ⏳ Token exp. |
| `InstagramConnector` | Instagram Graph API | Token | ✅ Vivo |

### Dry-Run Mode

Todos los conectores tienen modo `dry_run`. Si no hay credenciales,
devuelven `ConnectorResult(ok=True, data={"dry_run": True, ...})`.
Esto permite probar flujos sin conexión real.

---

## 🔄 CRMOrchestrator (crm/orchestrator.py)

El orquestador central coordina:

```
EVENTO ENTRANTE (Gmail/Web/Telegram)
  │
  ├─ ingest_event() → crea Lead con CustomerProfile + CustomerJourney
  ├─ qualify_lead() → score 0-100, asigna stage (NEW/QUALIFIED/BOOKED/...)
  ├─ publish_lead_to_kommo() → Kommo + Notion
  ├─ schedule_pre_arrival() → Calendar + Sheets
  ├─ notify_guest() → Telegram + WhatsApp
  │
  └─ Flujo completo: simulate_guest_journey()
```

### Modelos de Datos (crm/models.py)

```
JourneyStage: NEW → QUALIFIED → BOOKED → PRE_ARRIVAL → IN_STAY → POST_STAY → LOST
Channel: GMAIL | WHATSAPP | INSTAGRAM | TELEGRAM | PHONE | WEB

Lead {
    lead_id, profile(CustomerProfile), journey(CustomerJourney),
    score(0-100), status, source, context, interactions[]
}

PhotoAsset {
    asset_id, path, caption, status, metadata
}
```

### PhotoPipeline (crm/photo_pipeline.py)

Procesa fotos con Pillow en 5 variantes:
- `square` (1080×1080)
- `feed` (1080×1350)
- `preview` (720×720)
- `story` (1080×1920 con blur background)
- `ready` (la que convenga)

Sin Pillow, hace fallback a copy.

---

## 🤖 Telegram Bot (asistente/telegram/telegram_bot.py)

Bot principal con comandos:
- `/emails [query NL]` — Lista/busca emails (con parser NL)
- `/send <to> <subject> <body>` — Envía email
- `/status` — Estado del sistema
- Parser NL en español con fallback entre 4 proveedores IA:
  1. OpenCode Zen (local, prioritario)
  2. NVIDIA NIM
  3. OpenRouter
  4. Google Gemini (último recurso)
- Si todos fallan: parser heurístico por regex

---

## 🧪 Hybrid AI System (hybrid/)

Sistema cliente-servidor para procesar eventos CRM:
- **Hybrid Server** (FastAPI): Recibe webhooks, parsea con IA, genera instrucciones
- **Parser**: Intenta IA → fallback a regex (fechas, montos, personas)
- **Gateway Client**: Envía instrucciones ejecutables al OpenClaw Gateway
- **Modelos**: Pydantic para GatewayEvent, Instruction, GatewayResponse

### Handlers de CRM Flows:
- `nueva_reserva()` — Extrae datos de reserva de texto libre
- `procesar_incidente()` — Clasifica y reporta incidentes
- `procesar_pago()` — Registra pagos
- `generar_informe()` — Genera informe diario

---

## 🧠 Segundo Cerebro (crm/autonomy.py)

Sistema autónomo que lee un Google Doc ("Segundo Cerebro"), extrae ideas
nuevas (líneas que empiezan con `- ` o `* `), las clasifica por tipo
(gmail, drive, docs, sheets, cua, notify, crm), y ejecuta acciones.

```
ID del doc: 1p5kLFu6hcIuoM0QlRFepJJ-asiKTdR-1yaokVY75CFU
ID Perfil Virtual: 1ifNxjZQcZ-4hhvH_9atPBces4ChiN7Z23DWD8sEBuEk
```

---

## 👥 Equipo (equipo.py)

Datos del equipo Rancho Raíz con roles y responsabilidades:
- **Leo Tello** — Dueño / Finanzas
- **Ayelen Juricevic** — Booking / Ventas
- **Diego** — Operaciones
- **Chiqui** — Limpieza

+ 8 huéspedes registrados con datos reales.

---

## 📡 Project Monitor (project_monitor.py)

Monitor que cada 30 minutos:
1. Obtiene contexto del proyecto (git status, archivos clave, notificaciones recientes, procesos activos)
2. Llama a Gemini 2.5 Flash API para generar notificación inteligente
3. Envía notificación Android vía termux-notification

---

## 💡 Idea Engine (idea_engine.py)

Motor que genera sugerencias contextuales basadas en el estado actual del
proyecto (qué features están implementados vs pendientes según ROADMAP.md).
Puede correr en modo continuo (cada 30 min) o `--once`.

---

## 🤖 Android CUA (crm/android_cua.py)

Computer Use Agent para Android vía Shizuku/ADB:
- dump_ui, screenshot, tap, tap_by_text, type_text, press_key
- swipe, open_app, go_home, go_back, scroll
- find_elements, get_screen_state
- Integrado como `AndroidCuaConnector` en connectors.py

---

## 🚀 Plan de Integración publicidad ↔ hola-3

### Situación Actual
- **publicidad/**: Pipeline FFmpeg para generar reels 9:16 con Ken Burns,
  texto animado, audio contextual, y envío a Telegram
- **hola-3/**: CRM con conectores a Gmail, Calendar, Drive, Kommo, Telegram,
  más PhotoPipeline con Pillow para procesar imágenes

### Puntos de Integración

1. **PhotoPipeline (hola-3) → publicidad (ranchocut/lab.js)**
   - Que el PhotoPipeline de hola-3 llame a lab.js para generar reels
   - Pasar las fotos procesadas como input al pipeline FFmpeg

2. **InstagramConnector (hola-3) → Reels generados (publicidad)**
   - Usar InstagramConnector para publicar los reels generados
   - El connector ya tiene método `publish(media_path, caption)`

3. **TelegramConnector (hola-3) → Envío de reels**
   - Ya existe `telegram.send_photo()` — extender para video
   - O usar `ranchocut/telegram.js` (Node.js) desde hola-3

4. **CRMOrchestrator (hola-3) → Programación de contenido**
   - Usar `schedule_pre_arrival()` para programar publicación de reels
   - Calendar + Sheets como agenda editorial

5. **Hybrid Server (hola-3) → Orquestación de generación**
   - Webhook `generar_reel` que invoque lab.js
   - Instrucciones OpenClaw para ejecutar batch de generación

### Cómo Llamar a publicidad desde hola-3

```python
import subprocess
import json

def generar_reel_publicidad(fotos: list[int], kenburns: str, estilo: str,
                            audio: str = "", telegram: bool = False) -> dict:
    cmd = [
        "node", "/data/data/com.termux/files/home/publicidad/ranchocut/lab.js",
        f"--manual={','.join(str(f) for f in fotos)}",
        f"--kenburns={kenburns}",
        f"--estilo={estilo}",
        "--overlay=cinematic",
        "--duracion=4"
    ]
    if audio:
        cmd.append(f"--audio={audio}")
    if telegram:
        cmd.append("--telegram")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    return {"ok": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr}
```

---

## ⚠️ Limitaciones Conocidas

1. **termux-api linker roto** — `libnativeloader.so` no funciona.
   `termux-notification` funciona directo, pero `termux-setup-storage` no.
2. **Android scoped storage** — No se puede escribir a `/sdcard/`.
3. **WhatsApp token expirado** — Necesita regenerar en Meta Developers.
4. **Sin puppeteer/Chromium** — No hay navegador headless.
5. **Google OAuth** — Token en `crm_state/.google_token.json`, se auto-refresca.
6. **Instagram publish** — Solo soporta IMAGE, no VIDEO (falta subida a FB).

---

## 📦 Backup del Proyecto

```
~/backup-hola-3-v1.tar.gz      ← Backup v1 (27-Mayo-2026)
```

Creado el 27-Mayo-2026. Contiene TODO el proyecto excepto node_modules,
.venv, __pycache__ y .worktrees.

Para restaurar:
```bash
tar -xzf ~/backup-hola-3-v1.tar.gz -C /data/data/com.termux/files/home/Documents/Codex/2026-05-18/
```

---

## 📝 Notas para Futuros Agentes

1. **Siempre leer AGENT.md** para entender el propósito del proyecto
2. **Siempre leer ROADMAP.md** para saber qué está ✅ y qué está 🚧
3. **Siempre leer CREDENCIALES.md** para saber qué tokens usar (nunca hardcodear)
4. **Usar `python -m modulo`** desde la raíz para evitar path conflicts
5. **Todos los conectores soportan dry_run** — probar sin credenciales reales
6. **El CRMOrchestrator tiene `dry_run=True`** por defecto
7. **No hay base de datos SQL** — todo es JSON en `crm_state/`
8. **InstagramConnector no soporta video** — solo imágenes
9. **Telegram es el canal más confiable** — funciona siempre
10. **Priorizar hybrid/parser con IA** — el regex fallback es limitado
11. **CUA requiere Shizuku** — no funciona sin permisos ADB
12. **publicidad/ está en ~/publicidad** — no en Documents/Codex
13. **Para publicar reels**: usar Telegram como canal principal
14. **El equipo real** está en `equipo.py` con datos de contacto

---

## 🏆 LOGRO: Servidor MCP html_a_imagen — Render a costo $0

### Fecha
28 de Mayo de 2026

### Objetivo
Dotar al sistema CRM de capacidad nativa para convertir HTML/CSS dinámico en imágenes
estáticas PNG/JPEG de alta calidad, a **costo $0**, usando exclusivamente recursos
locales y Open Source. Orientado a banners publicitarios, historias Instagram,
cupones y plantillas de email generados por agentes autónomos.

### Stack del Proyecto Aislado

| Componente | Tecnología |
|-----------|-----------|
| **MCP Server** | Python + `mcp` SDK 1.27.1 (stdio) |
| **Render Engine** | `chromium-browser` headless vía CLI |
| **Formato** | PNG/JPEG, resolución configurable |
| **Costo** | $0 (todo local — Chromium del sistema) |
| **Ubicación** | `~/Documents/proyectos/test-mcp-render/` |

### Herramientas MCP Expuestas

1. **`html_a_imagen`** — Recibe HTML + width/height/formato, renderiza con Chromium
   headless, guarda PNG/JPEG en disco, devuelve `{path, size, width, height, format}`.
2. **`html_a_imagen_bytes`** — Ídem pero devuelve la imagen codificada en base64
   para consumo directo del agente vía `ImageContent`.

### Pruebas Exitosas

| Prueba | Dimensión | Tamaño | Estado |
|--------|-----------|--------|--------|
| Banner cuadrado | 1080×1080 | ~574 KB PNG | ✅ |
| Historia Instagram | 1080×1920 | ~790 KB PNG | ✅ |
| Protocolo MCP stdio | init → list → call | 574 KB | ✅ |
| Integración vía subprocess | hybrid/server.py → MCP | 574 KB | ✅ |

### Pipeline de Integración al CRM

```
Agente (Hermes/OpenClaw)
    │
    ├── POST /webhook/banner → hybrid/server.py
    │
    ▼
MCP Client Bridge (hybrid/mcp_client.py)
    │
    ├── Lanza servidor MCP como subproceso hijo
    ├── Envía jsonrpc via stdio (initialize → tools/call)
    ├── Chromium headless: --screenshot → PNG/JPEG
    │
    ▼
    Imagen lista en crm_state/media/
    │
    ├── → Telegram: envía para aprobación
    ├── → PhotoPipeline: procesa variantes
    └── → Instagram: publica (futuro)
```

### Factores Clave de Éxito

| Factor | Detalle |
|--------|---------|
| **$0** | Sin APIs de pago — chromium-browser del sistema |
| **Aislamiento** | Proyecto aparte del CRM hasta validación |
| **Velocidad** | ~3-5 segundos por render 1080×1080 |
| **Limpieza** | Tempfiles se eliminan post-render |
| **MCP nativo** | Sigue el estándar mcpstack.pro, replicado local |
| **Limpieza de tempfiles** | HTML temporal se elimina en `finally` bloque |
| **Sin dependencias pesadas** | Solo `mcp` (PyPI) + Chromium del sistema |

---

## 🏆 LOGRO: Integración Multimedia — Overlays, Plantillas y Animación

### Fecha
28 de Mayo de 2026

### Contexto
Análisis de la tecnología MCP html_a_imagen vs IA generativa tradicional:
- **NO es** Midjourney/DALL-E (no inventa pixeles desde cero)
- **SÍ es** un motor de composición gráfica ultrapreciso que posiciona elementos reales (fotos, texto, emojis) exactamente donde la IA ordena
- La salida es **estática** (PNG/JPEG), pero se integra con FFmpeg y Three.js para crear contenido animado

### Experimentos Realizados

| # | Experimento | Tecnologías | Resultado |
|---|------------|-------------|-----------|
| 1 | **Overlay transparente** | Chromium RGBA + FFmpeg composición | ✅ 47 KB overlay PNG, 143 KB composite JPG |
| 2 | **Generador de plantillas** | JSON schema → HTML template → MCP render | ✅ 80 KB banner instagram_feed |
| 3 | **Stop-motion animado** | 5 frames HTML variantes + FFmpeg GIF | ✅ 5 frames @2fps, 296 KB GIF |

### Experimentos en detalle

#### Exp 1: Overlay Transparente + FFmpeg
Se genera un PNG con fondo transparente (solo texto + formas) usando Chromium
con flag `--default-background-color=00000000`. Luego FFmpeg compone el overlay
sobre una foto real de la posada.

```
chromium-browser --headless --screenshot=overlay.png \
  --default-background-color=00000000

ffmpeg -i foto.jpg -i overlay.png \
  -filter_complex "[0]scale=1080:1080,crop=1080:1080[bg];[bg][1]overlay=0:0" \
  composicion.jpg
```

**Aplicación directa**: Superponer textos/emojis sobre videos Ken Burns para
Reels de Instagram (efecto CapCut automatizado).

#### Exp 2: Sistema de Plantillas JSON
Se definió un schema JSON formal que Hermes/OpenClaw pueden usar para generar
banners:

```json
{
  "plantilla": "instagram_feed",
  "variables": {
    "url_foto_posada": "file:///path/to/foto.jpg",
    "etiqueta_superior": "🏕️ NUEVA TEMPORADA",
    "titulo_principal": "Escapate a los Andes",
    "descuento_o_gancho": "20% OFF",
    "emoticono_clave": "🏔️",
    "cta_texto": "Reservá tu lugar"
  }
}
```

El sistema carga la plantilla HTML, reemplaza variables con `string.Template`,
y envía el HTML resultante al servidor MCP para renderizar la imagen.

#### Exp 3: Animación Stop-Motion
5 frames HTML con variaciones programáticas (posición Y de emoji, opacidad
del título) generados individualmente y unidos por FFmpeg en un GIF animado.

```python
# Cada frame tiene bounce_y y opacity variables
generar_html_frame(frame_idx, total)
  → bounce_y = sin(angle × 2) × 30
  → opacity  = 0.6 + 0.4 × sin(angle × 3)

ffmpeg -framerate 2 -i frame_%03d.png animacion.gif
```

**Aplicación**: Crear anuncios animados cortos, secuencias de antes/después,
o transiciones para stories desde HTML puro.

### Stack de Integración Multimedia

```
MCP Server (html_a_imagen)
    │
    ├── PNG transparente (RGBA)
    │     └── FFmpeg → overlay sobre video Ken Burns
    │
    ├── PNG opaco (foto + texto)
    │     ├── Telegram → aprobación humana
    │     ├── Instagram → publicación directa
    │     └── Three.js → textura para plano 3D
    │
    └── Secuencia de PNGs (N frames)
          └── FFmpeg → GIF animado / video corto
```

### Lecciones Aprendidas

1. **Chromium con `--default-background-color=00000000`** genera PNGs con
   canal alfa real — ideal para overlays transparentes.
2. **FFmpeg + overlay PNG transparente** reemplaza a CapCut/Editores visuales
   para superposición de texto en videos.
3. **Plantillas JSON + string.Template** permiten que agentes autónomos
   generen banners sin saber HTML.
4. **Stop-motion desde Chromium** es viable para animaciones cortas (3-5 fps)
   pero el overhead de lanzar Chromium por frame (~3-5s) limita la fluidez.
   Para animaciones largas, conviene generar el HTML con CSS animations
   y capturar un video directamente con `--display-capture` o similar.

### Próximos pasos sugeridos

- [ ] Integrar el generador de plantillas con Hermes para campañas automáticas
- [ ] Usar Three.js para mapear banners como texturas 3D en la guía interactiva
- [ ] Secuenciar frames con `--virtual-time-budget` para animaciones CSS nativas

---

## 🏆 LOGRO: Pipeline Modular y Plan de Maduración

### Fecha
28 de Mayo de 2026

### Problemas Detectados en la Simulación Anterior (`simulacion_pipeline_completo.py`)

| Problema | Causa | Solución |
|----------|-------|----------|
| Email llegó antes que aprobación TG | Auto-approve 3s + GIF 40s → timing desync | **Aprobación manual**, sin auto-timer |
| Múltiples mensajes duplicados en TG | Cada ejecución enviaba 3 msjs × varias pruebas | Una corrida limpia por vez |
| Sin "posteo exitoso" | Crash de Google Auth en paso 5 impedía llegar al paso 6 | Posteo exitoso **siempre se envía**, email no bloquea |
| GIF no visible en TG | Se usaba `sendPhoto` (no soporta GIF) | Ahora `sendAnimation` |
| Generación lenta (8 frames × 5s = 40s) retrasaba todo | Cache no priorizado | **Cache primero**, generación bajo demanda |

### Pipeline Resultante (`pipeline.py`)

```
python3 pipeline.py                  # modo cache (default) — instantáneo
python3 pipeline.py --mode full      # genera si no hay cache
python3 pipeline.py --mode full --force  # regenera siempre
```

Flujo actual:
1. **OBTENER ASSETS** — cache o genera (banner PNG + GIF animation)
2. **ENVIAR A TELEGRAM** — texto con botones + banner (photo) + GIF (animation)
3. **APROBACION MANUAL** — input por terminal (s/n)
4. **NOTIFICACION EMAIL** — opcional, no bloquea (pendiente OAuth Google)
5. **POSTEO EXITOSO** — siempre se envía a Telegram

Todo sin Chromium en modo cache (~1s total). Generación + pipeline en modo full (~20-40s).

---

## 🗺️ Plan de Maduración — Hacia un Pipeline Sólido, Fluido y Profesional

Fases progresivas, cada una se prueba y estabiliza antes de avanzar.

### Fase 1: Telegram Solo — Sin Email (actual)
- [x] Pipeline básico: banner + GIF → Telegram → aprobación manual → posteo exitoso
- [x] Cache de assets priorizado (`pipeline.py --mode cache`)
- [x] Generación bajo demanda (`--mode full --force`)
- [x] GIF como animación (sendAnimation)
- [x] Eliminado auto-approve (input manual)
- [ ] Desacoplar completamente el email del flujo principal

### Fase 2: Pipeline Solo Foto (banner)
- [ ] Probar pipeline completo solo con banner (sin GIF)
- [ ] Verificar que banner → Telegram → aprobación → posteo funciona limpio
- [ ] Medir tiempos: cache (~1s) vs generación (~5-10s)
- [ ] Asegurar un solo mensaje de posteo exitoso

### Fase 3: Agregar GIF al Pipeline
- [x] Probar banner + GIF juntos
- [x] Verificar que ambos medios se visualizan correctamente en TG
- [x] Cache separado para cada asset
- [x] Si un asset falla, el otro continúa

### Fase 4: Agregar Reel al Pipeline
- [x] Integrar `generar_reel` como asset del pipeline
- [x] Cache de reels existentes en `~/ranchoraiz_reels/`
- [x] Enviar reel a TG como video (sendVideo)
- [x] Reel solo: aprobar y rechazar con polling
- [x] Banner + GIF + Reel completo: aprobar y rechazar
- [ ] Generación bajo demanda con `--mode full --force`

### Fase 5: Integrar Informes vía Email
- [x] Configurar Google OAuth token (token existente en `crm_state/.google_token.json`)
- [x] Arreglar normalización `token` → `access_token` en `crm/google_auth.py`
- [x] Email post-aprobación con resumen de assets
- [x] Email no bloquea el flujo principal
- [ ] Enviar email con adjuntos (banner, GIF)

### Fase 6: Posteos Reales
- [ ] Publicar banner en Instagram (vía InstagramConnector)
- [ ] Publicar reel en Instagram (requiere subida a Facebook Graph)
- [ ] Publicar en canal de Telegram
- [ ] Tracking de publicación (fecha, canal, respuesta)

### Fase 7: Interacción Humana en el Flujo
- [x] Callback real de botones de Telegram (polling getUpdates)
- [x] Aprobación/rechazo desde Telegram sin intervención en terminal
- [ ] Feedback loop: aprobado → publica, rechazado → pide cambios
- [ ] Múltiples revisores humanos con roles

### Fase 8: Producción Profesional y Escalable
- [ ] Todos los assets en base de datos (JSON Store → SQLite/GSheets)
- [ ] Pipeline ejecutándose como servicio (systemd/termux services)
- [ ] Logging estructurado con rotación
- [ ] Dashboard de estado del pipeline
- [ ] Pruebas automatizadas (pytest)
- [ ] Documentación completa

---

## 📦 Estado Actual (Checkpoint 28-May-2026)

### Assets Generados en Cache
| Asset | Ruta | Tamaño | Última modificación |
|-------|------|--------|-------------------|
| Banner montañas | `simulaciones_output/banner_montanas_*.png` | ~540-565 KB | Recién generado |
| GIF anim montañas | `simulaciones_output/anim_montanas_*.gif` | ~37-66 KB | Recién generado |
| Reels varios | `~/ranchoraiz_reels/*.mp4` | 600 KB - 1.8 MB | 27-May |

### Comandos de Prueba
```bash
# Pipeline banner + GIF completo (botones en Telegram)
python3 pipeline.py --mode cache --poll

# Solo banner
python3 pipeline.py --mode cache --solo-banner --poll

# Solo GIF
python3 pipeline.py --mode cache --solo-gif --poll

# Con regeneración forzada de assets
python3 pipeline.py --mode full --force --poll
```

### Archivos Clave
| Archivo | Propósito |
|---------|-----------|
| `pipeline.py` | Pipeline CRM+ARTE principal (cache + generación + TG + email) |
| `simulacion_pipeline_completo.py` | Versión anterior (deprecated, mantener como referencia) |
| `simulaciones_output/` | Output de banners y GIFs generados |
| `flows/arte/banner_flows.py` | Handlers generar_banner integrados en CRM |
| `flows/arte/reel_pipeline.py` | Handlers generar_reel integrados en CRM |
| `experimentos/04_frames_a_video.py` | Pipeline Reel (Ken Burns + keyframes + audio) |

---

## 🧪 Resultados de Pruebas — Fases 1 a 3 (28-May-2026)

### Resumen
Se probaron los 6 caminos del pipeline de aprobación/rechazo con assets en
cache (sin Chromium), todos con resultado exitoso.

### Resultados

| # | Assets | Botón | Lo que ve el usuario en Telegram | Estado |
|---|--------|-------|----------------------------------|--------|
| 1 | Banner solo | Aprobar | 📸 Banner → ❓ Botones → ✅ "Publicación exitosa" | ✅ |
| 2 | Banner solo | Rechazar | 📸 Banner → ❓ Botones → "Sin publicación — MONTANAS" | ✅ |
| 3 | GIF solo | Aprobar | 🎬 GIF → ❓ Botones → ✅ "Publicación exitosa" | ✅ |
| 4 | GIF solo | Rechazar | 🎬 GIF → ❓ Botones → "Sin publicación — MONTANAS" | ✅ |
| 5 | Banner + GIF | Aprobar | 📸 Banner → 🎬 GIF → ❓ Botones → ✅ "Publicación exitosa" | ✅ |
| 6 | Banner + GIF | Rechazar | 📸 Banner → 🎬 GIF → ❓ Botones → "Sin publicación — MONTANAS" | ✅ |
| 7 | Reel solo | Aprobar | 🎬 Reel → ❓ Botones → ✅ "Publicación exitosa" | ✅ |
| 8 | Reel solo | Rechazar | 🎬 Reel → ❓ Botones → "Sin publicación — MONTANAS" | ✅ |
| 9 | Banner + GIF + Reel | Aprobar | 📸 Banner → 🎬 GIF → 🎬 Reel → ❓ Botones → ✅ "Pub. exitosa" | ✅ |
| 10 | Banner + GIF + Reel | Rechazar | 📸 Banner → 🎬 GIF → 🎬 Reel → ❓ Botones → "Sin publicación" | ✅ |

### Tiempos
- **Modo cache**: ~1-2 segundos (sin Chromium)
- **Modo full --force**: Banner ~11s + GIF ~20s (4 frames) = ~31s total
- **Reel**: desde ~60-90s (Ken Burns + keyframes + audio)
- **Polling**: detecta botón en ~1-2s
- **Email**: ~1-2s (conexión Gmail API)

Documentación de la arquitectura de aprobación implementada, sus decisiones,
casos borde y proyección a futuro. Esto constituye la base sobre la que se
construirán todas las interacciones humanas del pipeline.

### Arquitectura

```
Pipeline (pipeline.py)
  │
  ├── 1. Obtener assets (cache o genera)
  ├── 2. Enviar assets a Telegram (foto, animación, video)
  │     └── Cada asset en su propio mensaje, SIN botones aún
  ├── 3. Enviar mensaje aparte con inline_keyboard (Aprobar/Rechazar)
  │     └── Botones aparecen DEBAJO de todos los assets
  ├── 4. Polling: getUpdates cada 0.5s con offset persistente
  │     └── Detectar callback_query → answerCallbackQuery → retornar decisión
  ├── 5. Email (no bloqueante, falla graceful)
  └── 6. Mensaje de devolución (Publicación exitosa / Sin publicación)
```

### Decisión Técnica: Polling vs Webhook

| Aspecto | Polling (elegido) | Webhook |
|---------|------------------|---------|
| **Infraestructura** | Solo necesita HTTP(S) saliente | Requiere IP pública + SSL/tunel |
| **Termux** | Funciona sin config adicional | Necesita ngrok/cloudflared |
| **Estado** | Stateless (offset en memoria) | Stateful (FastAPI + DB) |
| **Latencia** | ~1-2s (poll cada 0.5s) | ~0.1s (push) |
| **Robustez** | Reconecta automáticamente | Pierde eventos si cae el server |
| **Complejidad** | Baja (~50 líneas) | Alta (server + tunnel + HTTPS) |

**Veredicto**: Polling es la opción correcta para Termux/Android. Webhook se
evaluará en Fase 8 cuando el pipeline corra como servicio 24/7.

### Mecanismo de Polling (`tg_poll_decision`)

```
1. Limpiar updates pendientes viejos (offset = último + 1)
2. Loop: getUpdates(offset, timeout=10)
3. Por cada update con callback_query:
   a. Verificar data en ("aprobar", "rechazar")
   b. answerCallbackQuery → quita relojito de carga
   c. Retornar decisión
4. Si timeout (120s) → retornar "rechazar" por defecto
```

### Flujo de Mensajes en Telegram

**Orden de mensajes:**
```
 1. 📸 [foto banner]
    Rancho Raiz: MONTANAS

 2. 🎬 [animación GIF]
    GIF - MONTANAS

 3. ✅/❌ ¿Aprobás este contenido?
    [Aprobar] [Rechazar]

 4. (si aprobado) "Publicación exitosa"
    Tema: MONTANAS
    Banner: banner_...png
    GIF: anim_...gif

    (si rechazado) "Sin publicación — MONTANAS"
```

### Reglas del Juego (Edge Cases y Mitigaciones)

#### 1. Botones siempre al final, después de todos los assets
- Los assets se envían primero (cada uno en su mensaje, sin botones).
- Luego se envía un mensaje aparte con `inline_keyboard`.
- Esto asegura que el usuario vea TODO el contenido antes de decidir.
- Si se incrustaran los botones en el primer asset, el usuario podría
  aprobar sin ver el GIF o el reel.

#### 2. Los botones expiran
- `callback_query_id` expira ~1 hora.
- `answerCallbackQuery` con ID expirado → 400 → se ignora.
- Mitigación: limpiar updates viejos al inicio con `offset=-1`.

#### 3. Timeout por defecto = Rechazar
- Si no responde en 120s → se asume rechazo.
- Se envía "Sin publicación" igual.
- Evita pipelines trabados para siempre.

#### 4. El banner se envía una vez
- No se regenera entre envío y decisión.
- Si se rechaza, el mismo banner puede re-enviarse con cambios.

#### 5. Decisión binaria (por ahora)
- Solo Aprobar / Rechazar.
- Sin "modificar", "reprogramar" ni "comentar".
- Se expandirá en fases siguientes.

#### 6. Sin estado persistente
- La decisión no se guarda en JSON store.
- El offset se lleva en memoria; se pierde al reiniciar.
- Para Fase 8: persistir offset + decisiones.

#### 7. Email no interfiere
- Va DESPUÉS de la devolución a Telegram.
- Si falla (Google OAuth), no afecta el mensaje de "Publicación exitosa".

#### 8. Múltiples corridas = mensajes duplicados
- Cada `pipeline.py` envía un banner nuevo.
- Mitigación: polling procesa el primer callback que llega.
- Banners viejos quedan huérfanos pero no causan errores.

### Proyección: Cómo Escala Esta Base

| Asset | Mensajes | Botones | Devolución |
|-------|----------|---------|------------|
| Banner solo | 1 foto | Mensaje aparte después | "Pub. exitosa" / "Sin pub." |
| GIF solo | 1 animación | Mensaje aparte después | Idem |
| Banner + GIF | 1 foto + 1 animación | Mensaje aparte después | Idem (Fase 3 ✅) |
| Banner + GIF + Reel | 1 foto + 1 animación + 1 video | Mensaje aparte después | Idem (Fase 4 ✅) |
| Feedback loop | Edit msg markup | Aprobar/Modificar/Rechazar | "Modificando..." |

### Comandos Estandarizados

```bash
# Solo banner (Fase 2)
python3 pipeline.py --mode cache --solo-banner --poll

# Solo GIF (Fase 3)
python3 pipeline.py --mode cache --solo-gif --poll

# Solo reel (Fase 4)
python3 pipeline.py --mode cache --solo-reel --poll

# Banner + GIF (Fase 3 completo)
python3 pipeline.py --mode cache --poll

# Con regeneración forzada de assets
python3 pipeline.py --mode full --force --poll

# Depuración sin Telegram (input por terminal)
python3 pipeline.py --mode cache --solo-banner
```

### Checklist para Agregar un Nuevo Asset

- [ ] 1. Agregar a `buscar_cache()` 
- [ ] 2. Enviar con método TG correcto (`sendPhoto/Animation/Video`)
- [ ] 3. Botones en mensaje APARTE después de todos los assets
- [ ] 4. Devolución menciona todos los assets enviados
- [ ] 5. Resumen en terminal refleja nuevo asset
- [ ] 6. Test: aprobar y rechazar con `--poll`
- [ ] 7. Test: `--mode full --force` sin cache

---

## Próximas Fases — Posteo y Campañas

### Fase 6: Posteo Directo (sin aprobación)
- [ ] Pipeline sin `--poll` → postea directo sin preguntar
- [ ] `--auto` flag que omite aprobación y va directo a POSTEO
- [ ] Útil para contenido recurrente/confiable, o testing

### Fase 7: Posteo con Aprobación (completo)
- [ ] `--poll` es el default
- [ ] Botón "Aprobar" → postea + email
- [ ] Botón "Rechazar" → descarta + avisa

### Fase 8: Diferenciar tipos de posteo
- [ ] `--tipo posteo` → contenido a Instagram/Facebook (directo a red social)
- [ ] `--tipo campania` → mailing + informes + reportes a Gmail
- [ ] `--tipo ambos` → posteo en redes + email campaign report
- [ ] Los informes/reportes por Gmail llevan adjuntos (PDF con métricas)
- [ ] Las campañas publicitarias usan el mismo pipeline pero destino distinto

### Fase 9: Posteo Real a Redes Sociales
- [ ] Conectar Instagram Graph API (o ManyChat como puente)
- [ ] Conectar Facebook Pages API
- [ ] `--publicar` flag que envía a redes en vez de solo Telegram
- [ ] Diferenciar: contenido orgánico vs. campaña paga

### Fase 10: Feedback Loop (modificar/rechazar con cambios)
- [ ] Botón triple: Aprobar / Modificar / Rechazar
- [ ] "Modificar" → solicita cambios + re-genera
- [ ] Ciclo de revisión sin reiniciar el pipeline desde cero
