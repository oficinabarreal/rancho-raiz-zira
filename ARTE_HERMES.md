# ARTE_HERMES.md — Mapa de Arquitectura y Estado del Proyecto

**Agente:** big-pickle (Hermes)
**Proyecto:** hola-3 — CRM Autónomo para Rancho Raíz
**Última actualización:** 30/05/2026 14:00

---

> Mapa vivo del ecosistema. Cada sección se revisa sistemáticamente,
> se marca su estado, y se actualiza al actuar sobre ella.
>
> **Leyenda:**
> - ✅ = Funcional / Probado / OK
> - ⚠️ = Incompleto / Sin probar / Dependencias faltantes
> - ❌ = Roto / No funciona
> - 🚧 = En desarrollo / Planificado
> - 💡 = Observación / Mejora sugerida

---

## VISTA GENERAL DE LA ARQUITECTURA

```
                    ┌──────────────────────┐
                    │   Telegram Bot       │ ← /factura, /emails, /status, /crm
                    │  asistente/telegram  │
                    └────────┬─────────────┘
                             │
                    ┌────────▼─────────────┐
                    │  Hybrid Server       │ ← FastAPI :8081
                    │  hybrid/             │    Parser IA + regex
                    │  + MCP Client        │    HTML → imagen (Chromium)
                    └────────┬─────────────┘
                             │
              ┌──────────────┼──────────────────┐
              │              │                  │
       ┌──────▼──────┐ ┌────▼──────┐ ┌─────────▼──────────┐
       │  CORE CRM   │ │ CENTRAL   │ │  PIPELINE ARTE     │
       │  crm/       │ │ FLOWS     │ │  pipeline.py       │
       │             │ │ flows/    │ │                    │
       │  models     │ │ central   │ │  → banner (MCP)    │
       │  store      │ │ _crm/     │ │  → GIF (ffmpeg)    │
       │  connectors │ │  engine   │ │  → reel (ffmpeg)   │
       │  google_auth│ │  state_   │ │  → Telegram        │
       │  orchestrat.│ │  machine  │ │    Aprobar/Rechazar│
       │  autonomy   │ │  parser   │ │  → Email           │
       │  photo_pipe │ │           │ │                    │
       │  android_cua│ │ mensajeria│ │                    │
       └──────┬──────┘ └────┬──────┘ └────────────────────┘
              │             │
       ┌──────▼─────────────▼──────────────────────────────┐
       │                   SIMULADORES                     │
       │  simulators/                                      │
       │  - crm_simulator.py (8 escenarios + Zira demo)    │
       │  - integrador_publicidad.py (captacion→posteo)    │
       │  - simulacion_pipeline_completo.py (CLI completa) │
       │  - integracion_publicidad/ (pipeline doc)         │
       └───────────────────────────────────────────────────┘
```

---

## 1. CORE CRM (`crm/`) — [REVISADO ✅]

> **Propósito:** Modelos de datos, persistencia, conectores externos,
> orquestación de flujos de lead, procesamiento de fotos, agente autónomo,
> y automatización Android CUA.
>
> **Valor en la Arquitectura:** ⭐⭐⭐⭐⭐ (CRÍTICO)
> Esta es la **capa base** del CRM. Sin conectores no hay comunicación con APIs reales.
> Sin el orquestador no hay pipeline de lead. Sin google_auth no hay Google Workspace.
> Todo el sistema se apoya en `crm/` como fundación. Si esta capa falla, no funciona nada.

---

### 1.1 models.py — [✅ CORRECTO — 88 líneas]

| Aspecto | Estado |
|---------|--------|
| **Enums** | JourneyStage (NEW→QUALIFIED→BOOKED→PRE_ARRIVAL→IN_STAY→POST_STAY→LOST), Channel (GMAIL, WHATSAPP, INSTAGRAM, TELEGRAM, PHONE, WEB) — correctos |
| **Dataclasses** | Lead, CustomerProfile, CustomerJourney, PhotoAsset, CRMEvent — bien diseñados |
| **to_dict()** | Lead con `.to_dict()` via `asdict()` — funcional |
| **touch()** | Actualiza `updated_at` y `last_touch` — correcto |
| **Tamaño** | 88 líneas, limpio, sin imports innecesarios |

**💡 Observaciones:**
- Faltan modelos: Pago, Propiedad, Tarea, Notificacion, EventoCalendar (mencionados conceptualmente pero no definidos)
- Los modelos existentes cubren el flujo lead→booking→stay. Los faltantes son para contabilidad y operaciones.

---

### 1.2 store.py — [✅ CORRECTO — 57 líneas]

| Aspecto | Estado |
|---------|--------|
| **Persistencia** | JSON en `crm_state/` — leads.json, events.json, assets.json |
| **CRUD** | upsert_lead, record_event, upsert_asset, list_leads, list_assets |
| **Manejo de errores** | Lee archivo corrupto sin crash (fallback a default) |
| **Tamaño** | 57 líneas, simple y efectivo |

**⚠️ Riesgos:**
- **Sin concurrencia**: dos writes simultáneos pierden datos (read→modify→write no atómico)
- **Sin índices**: búsqueda lineal en listas
- **Escalabilidad**: OK para <1000 leads, degrada después

**💡 Mejora sugerida:** Migrar a SQLite con `sqlite3` (built-in en Python 3.13) daría concurrencia básica + consultas

---

### 1.3 connectors.py — [✅✅ COMPLETO — 9 conectores, 813 líneas]

| Conector | Estado | Dependencias | Probado | Detalle |
|----------|--------|-------------|---------|---------|
| **GmailConnector** | ✅ | google-api (gmail scope) | ✅ email | Lista/envía mensajes, dry-run sin auth |
| **TelegramConnector** | ✅ | CRM_TG_TOKEN + CHAT_ID | ✅ pipeline | sendMessage + sendPhoto multipart, botones inline |
| **DriveConnector** | ✅ | google-api (drive scope) | ❌ No probado | Upload resumable, list files, create folder |
| **CalendarConnector** | ✅ | google-api (calendar scope) | ❌ No probado | create_event timezone ARG, list_upcoming |
| **SheetsConnector** | ✅ | google-api (sheets scope) | ❌ No probado | append_row, read, auto-create spreadsheet |
| **DocsConnector** | ✅ | google-api (docs scope) | ❌ No probado | read, create, append |
| **AndroidCuaConnector** | ⚠️ | Shizuku + android_cua.py | ❌ No probado | dump_ui, screenshot, tap, type, swipe, open_app, find, scroll |
| **KommoConnector** | ⚠️ | CRM_KOMMO_TOKEN + SUBDOMAIN | ❌ No config | create_lead, update_status, list_leads |
| **WhatsAppConnector** | ⚠️ | CRM_WHATSAPP_TOKEN + PHONE_ID | ❌ No config | send_message, send_template (Cloud API v22) |
| **InstagramConnector** | ⚠️ | CRM_INSTAGRAM_TOKEN + USER_ID | ❌ No config | publish (IMAGE/VIDEO), get_media |
| **NotionConnector** | ⚠️ | CRM_NOTION_TOKEN | ❌ No config | create_page, query_database |

**✅ Puntos fuertes:**
- Todos heredan de `BaseConnector` con `dry_run()` — comportamiento predecible sin auth
- `ConnectorResult(ok, data, error)` — interfaz unificada
- Manejo de errores con try/except en todos
- Timeouts de 30s en requests HTTP

**⚠️ Pendientes:**
- Instagram publish usa `image_url: ""` (no sube archivo, solo URL pública)
- Kommo `update_status` asume status_id como int — incompatible con pipelines string
- WhatsApp token no está en .env
- AndroidCua requiere Shizuku en foreground

---

### 1.4 google_auth.py — [✅ CORRECTO — 81 líneas]

| Aspecto | Estado |
|---------|--------|
| **OAuth2 flow** | Completo con refresh automático |
| **Scopes** | drive, calendar, sheets, gmail, gmail_settings, docs |
| **Token storage** | `crm_state/.google_token.json` — **YA AUTENTICADO** ✅ |
| **Refresh** | Refresca automáticamente si expired + tiene refresh_token |
| **Fallback** | Si no hay credenciales, retorna None (no crash) |

**💡 Nota:** Token actual expiró y se refrescó automáticamente. Mientras el refresh_token sea válido (no revocado), funciona sin intervención.

---

### 1.5 orchestrator.py — [✅ ROBUSTO — 347 líneas]

| Método | Líneas | Estado | Descripción |
|--------|--------|--------|-------------|
| `ingest_event()` | 40 | ✅ | Crea Lead desde payload, registra CRMEvent, persiste |
| `qualify_lead()` | 22 | ✅ | Scoring base 20 + email+10 + phone+10 + guests+10 + arrival+10. Stages: NEW<50 → QUALIFIED≥50 → BOOKED≥80 |
| `schedule_pre_arrival()` | 27 | ✅ | Crea Calendar event + Sheets row. Avanza a PRE_ARRIVAL |
| `handle_photo()` | 37 | ✅ | PhotoPipeline + Drive + Notion + Kommo + Telegram preview |
| `notify_guest()` | 11 | ✅ | Telegram + WhatsApp (o simulado local si no hay conectores) |
| `publish_lead_to_kommo()` | 24 | ✅ | Kommo lead + Notion page |
| `simulate_guest_journey()` | 22 | ✅ | Pipeline completo en un llamado: ingest→qualify→publish→pre_arrival→notify→photo |
| `ingest_gmail_digest()` | 38 | ✅ | Lee Gmail, detecta booking emails, crea leads, califica, agenda |
| `ingest_photo_asset()` | 7 | ✅ | Wrapper de handle_photo con ID por hash |

**💡 Observaciones:**
- InstagramConnector no se usa en ningún método del orquestador
- WhatsAppConnector solo en `notify_guest()`, no en flujo de lead
- `schedule_pre_arrival()` asume arrival_date string ISO sin validación
- No hay manejo de pagos en el orquestador

---

### 1.6 autonomy.py — [⚠️ INDEPENDIENTE — 182 líneas]

| Aspecto | Estado |
|---------|--------|
| **Propósito** | Lee "Segundo Cerebro" (Google Doc), extrae ideas bullet, clasifica y ejecuta |
| **Integración** | ❌ No integrado con orchestrator ni pipeline |
| **Clasificador** | Regex por keywords (gmail/drive/docs/sheets/cua/notify/crm/unknown) |
| **Ejecutor** | Solo implementa gmail y docs. Demás: "TIPO X NO IMPLEMENTADO" |
| **IDs hardcodeados** | SEGUNDO_CEREBRO_ID y PERFIL_VIRTUAL_ID |
| **Ejecución** | `python -m crm.autonomy` |

**⚠️ Limitaciones:**
- Solo ejecuta 2 de 7 tipos de ideas
- No tiene logging consistente (prints crudos)
- No reporta errores a Telegram

---

### 1.7 photo_pipeline.py — [✅ CORRECTO — 113 líneas]

| Variante | Resolución | Método | Estado |
|----------|-----------|--------|--------|
| square | 1080×1080 | fit (fill) | ✅ |
| feed | 1080×1350 | fit (fill) | ✅ |
| preview | 720×720 | contain (no fill) | ✅ |
| story | 1080×1920 | blur bg + fg centrado | ✅ |
| ready | feed o square | el ≥ | ✅ |
| **Fallback** | — | copia directa sin Pillow | ✅ |

**Assets:** `crm_state/media/{asset_id}/`

---

### 1.8 android_cua.py — [⚠️ NO PROBADO — 349 líneas]

| Comando | Implementación | Estado |
|---------|---------------|--------|
| UI dump | XML parsing con limpieza AnyClaw | ✅ |
| Screenshot | `screencap -p` | ✅ |
| Tap | `input tap x y` | ✅ |
| Type text | `input text ...` | ✅ |
| Press key | `input keyevent ...` | ✅ |
| Swipe | `input swipe x1 y1 x2 y2` | ✅ |
| Open app | `monkey -p package 1` | ✅ |
| Find elements | Búsqueda por text/resource-id/class | ✅ |
| **Probado** | — | ❌ Nunca ejecutado |

**⚠️ Riesgo:** Shizuku requiere permiso ADK. Si no está activo, falla silenciosamente.

---

### 1.9 crm_state/ — Persistencia actual

| Archivo | Contenido | Estado |
|---------|-----------|--------|
| `.google_token.json` | Token OAuth2 | ✅ Autenticado |
| `.tg_offset` | Último update_id procesado | ✅ |
| `leads.json` | 2 leads (34 líneas) | ✅ |
| `events.json` | ~40 eventos | ✅ |
| `reservas.json` | Reservas reales huéspedes | ✅ |
| `huespedes.json` | Perfiles huéspedes | ✅ |
| `pagos.json` | Pagos registrados | ✅ |
| `equipo.json` | Equipo | ✅ |
| `incidentes.json` | Incidentes | ✅ |
| `tickets.json` | Tickets soporte | ✅ |
| `config.json` | Config general | ✅ |
| `informes/` | Informes generados | ✅ |
| `media/` | Assets photo_pipeline | ✅ |
| `assets.json` | Assets foto procesados | ✅ |
| `parser_report.json` | Reporte parser NLP | ✅ |
| `reservas.csv / .json` | Backup + procesadas | ✅ |

---

## 2. CENTRAL FLOWS (`flows/`) — [REVISADO ✅]

> **Propósito:** Motor de pipeline de negocio (reservas, incidentes, pagos, informes),
> máquina de estados del CRM, parser NLP dual (IA + regex), generación de banners y reels,
> y conectores de mensajería con re-export desde crm.connectors.
>
> **Valor en la Arquitectura:** ⭐⭐⭐⭐ (ALTO)
> Esta es la **capa de lógica de negocio**. engine.py orquesta el ciclo de vida de
> cada reserva/incidente/pago. state_machine.py define el pipeline de 8 pasos del CRM.
> El parser dual (IA+regex) es el cerebro que entiende mensajes de huéspedes en texto libre.
> banner_flows y reel_pipeline habilitan generación de contenido automatizada.
> Sin `flows/`, el Hybrid Server sería solo un router vacío.

**Estructura:**
```
flows/
├── __init__.py          → Re-exporta: nueva_reserva, procesar_incidente, procesar_pago, generar_informe
├── central_crm/         → Core de flujos
│   ├── engine.py        → Funciones de negocio (nueva_reserva, procesar_incidente, etc.)
│   ├── models.py        → Pydantic models: GatewayResponse, Instruction, Reserva, Incidente, Pago, InformeDiario
│   ├── state_machine.py → PipelineFSM — 9 estados (8 pasos + HISTORIAL_ARCHIVADO)
│   ├── parser.py        → Parser dual: _llm_parse() → fallback _regex_parse()
│   └── store.py         → Persistencia JSON en hybrid/crm_state/
├── arte/                → Generación multimedia
│   ├── banner_flows.py  → generar_banner via MCP (HTML → imagen)
│   └── reel_pipeline.py → generar_reel via import dinámico de test-mcp-render
├── mensajeria/          → Re-export stubs
│   ├── telegram_connector.py    → stub: from crm.connectors import TelegramConnector
│   ├── whatsapp_connector.py     → stub: from crm.connectors import WhatsAppConnector
│   ├── instagram_connector.py    → stub: from crm.connectors import InstagramConnector
│   └── gateway.py                → mcp_html_a_imagen + enviar_instrucciones al Gateway
└── third_party/         → Integraciones externas
    ├── kommo_connector.py  → stub
    └── webhook_ingress.py  → Webhook receiver
```

---

### 2.1 engine.py — [✅ ROBUSTO — 221 líneas]

| Función | Estado | Descripción |
|---------|--------|-------------|
| `nueva_reserva()` | ✅ | Parsea texto → crea Reserva → persiste → genera Instructions (Telegram + Kommo + Calendar + Sheets) |
| `procesar_incidente()` | ✅ | Crea Incidente → persiste → notifica por Telegram |
| `procesar_pago()` | ✅ | Crea Pago → persiste → notifica por Telegram |
| `generar_informe()` | ✅ | Lee reservas/incidentes/pagos → genera texto → persiste + Telegram + Gmail |

**💡 Observaciones:**
- Las 4 funciones retornan `GatewayResponse` con `instructions: List[Instruction]` — diseño limpio
- `init_parser()` se llama al arranque para configurar IA desde hybrid.config
- `_build_reserva_instructions()` genera hasta 6 instrucciones automáticas por reserva
- `_to_iso()` convierte fechas DD/MM/YYYY a ISO — cubre separadores / - .
- El store guarda en `hybrid/crm_state/` (no en `crm_state/`) — ⚠️ **dos stores distintos en el proyecto**

---

### 2.2 models.py — [✅ CORRECTO — 76 líneas]

| Modelo | Tipo | Campos clave |
|--------|------|-------------|
| `GatewayEvent` | Pydantic BaseModel | event_id, type, timestamp, source, data |
| `Instruction` | Pydantic BaseModel | action (str), payload (Dict) |
| `GatewayResponse` | Pydantic BaseModel | event_id, status, message, instructions[], state_updates, parser_info |
| `Reserva` | Pydantic BaseModel | name, pax, check_in, check_out, amount, phone, email, source, nights, notes |
| `Incidente` | Pydantic BaseModel | guest, tipo, desc, severidad, reportado_por, fecha |
| `Pago` | Pydantic BaseModel | guest, monto, metodo, fecha, recibido_por, notas |
| `MiembroEquipo` | Pydantic BaseModel | nombre, rol, telegram_id, email, telefono, responsabilidades |
| `InformeDiario` | Pydantic BaseModel | fecha, eventos_hoy, reservas_proximas, publicaciones, inventario, estado_crm, estado_parser |

**✅ Bien:** Usa Pydantic en vez de dataclasses (validación nativa, serialización `.model_dump()`)

**⚠️:** engine.py usa `hasattr(reserva, \"model_dump\")` para compatibilidad Python 3.12+ vs 3.11-

---

### 2.3 state_machine.py — [✅ CORRECTO — 58 líneas]

| Aspecto | Estado |
|---------|--------|
| **PipelineState Enum** | 9 estados: CAPTACION_TELEGRAM → CREACION_CONTENIDO → ESPERA_APROBACION → POSTEO_ACTIVO → INTERACCION_INSTAGRAM → CALENTAMIENTO_LEAD → DERIVACION_WHATSAPP → ACOMPANAMIENTO_VIAJE → HISTORIAL_ARCHIVADO |
| **PipelineFSM** | ✅ init(client_id), advance(), can_advance_to(), to_dict() |
| **Transiciones** | Estrictamente lineales — solo permite avanzar 1 paso a la vez |
| **Contexto** | Dict que acompaña al cliente durante todo el pipeline |

**💡:** No hay método para retroceder, saltar pasos, o manejar estados de error/rechazo.

---

### 2.4 parser.py — [✅ DUAL — 156 líneas]

| Modo | Estado | Detalle |
|------|--------|---------|
| **IA (LLM)** | ✅ | Envía texto a endpoint OpenAI-compatible. Extrae JSON. Timeout 30s. |
| **Regex fallback** | ✅ | 7 categorías: name (3 patrones), pax (2), check_in (2), check_out (2), amount (3), phone (2), nights (2). Confidence: 0.5 + 0.1/campo, max 0.9 |
| **Rate limit** | ✅ | Detecta HTTP 429, guarda Retry-After |

**✅:** Estrategia IA-first, regex-fallback. Buena cobertura de fechas en español.
**⚠️:** No hay validación cruzada (ej: check_out > check_in)

---

### 2.5 store.py (flows/central_crm) — [⚠️ DUPLICADO — 35 líneas]

| Aspecto | Estado |
|---------|--------|
| **Ruta** | Guarda en `hybrid/crm_state/` |
| **Funciones** | read, write, append, update |
| **vs crm/store.py** | `crm/store.py` guarda en `crm_state/` (raíz) |

**⚠️⚠️ Dos stores paralelos:**
- `crm/store.py` → `crm_state/` (orchestrator)
- `flows/central_crm/store.py` → `hybrid/crm_state/` (engine)

**Ambos guardan `reservas.json` pero en directorios diferentes.** Datos inconsistentes si ambos sistemas se ejecutan.

---

### 2.6 banner_flows.py — [✅ FUNCIONAL — 61 líneas]

| Aspecto | Estado |
|---------|--------|
| `generar_banner()` | ✅ Toma HTML, width, height → MCP → GatewayResponse |
| Telegram opcional | ✅ Si send_telegram=True, notifica |
| Validación | ✅ Rechaza HTML vacío |

---

### 2.7 reel_pipeline.py — [⚠️ DEPENDENCIA EXTERNA — 64 líneas]

| Aspecto | Estado |
|---------|--------|
| `generar_reel()` | ✅ Import dinámico de `04_frames_a_video.py` desde test-mcp-render |
| Dependencia | ⚠️ Requiere que test-mcp-render exista |
| Parámetros | foto, audio, tagline, title, subtitle, cta, duracion |

**⚠️:** Si test-mcp-render se mueve o elimina, reel_pipeline falla. Sin fallback.

---

### 2.8 mensajeria/ — [⚠️ STUBS — 3 re-exports]

| Archivo | Contenido |
|---------|-----------|
| `telegram_connector.py` | `from crm.connectors import TelegramConnector` |
| `whatsapp_connector.py` | `from crm.connectors import WhatsAppConnector` |
| `instagram_connector.py` | `from crm.connectors import InstagramConnector` |
| `gateway.py` | `mcp_html_a_imagen()` wrapper + `enviar_instrucciones()` HTTP |

---

### 2.9 third_party/ — [⚠️ PARCIAL]

| Archivo | Estado |
|---------|--------|
| `kommo_connector.py` | stub |
| `webhook_ingress.py` | ⚠️ No leído aún |

---

### 💡 Resumen Central Flows

| Componente | Estado | Prioridad |
|-----------|--------|-----------|
| engine (reservas/incidentes/pagos/informes) | ✅ | — |
| models (Pydantic) | ✅ | — |
| state_machine (FSM 9 estados) | ✅ | — |
| parser (IA + regex) | ✅ | — |
| banner_flows (MCP) | ✅ | — |
| gateway.py | ✅ | — |
| stubs mensajeria (3 re-export) | ⚠️ | Baja |
| reel_pipeline (dep externa) | ⚠️ | Media |
| **Dual store paths** (crm_state/ vs hybrid/crm_state/) | ⚠️⚠️ | **ALTA** |
| third_party/webhook | ⚠️ | Baja |

---

## 3. HYBRID AI (`hybrid/`) — [REVISADO ✅]

> **Propósito:** Servidor híbrido FastAPI (:8081) que recibe eventos del Gateway,
> los procesa con IA (parser NLP + motor de flujos), y devuelve instrucciones concretas
> para que el Gateway las ejecute contra APIs reales (Telegram, Gmail, Kommo, Calendar,
> Sheets, WhatsApp, Android CUA). También incluye el propio Gateway server (:8082)
> y el cliente MCP para generación de banners/reels via Chromium.
>
> **Valor en la Arquitectura:** ⭐⭐⭐⭐⭐ (CRÍTICO)
> Esta es la **capa de integración y ejecución** del CRM. Es el punto de entrada de
> todos los eventos externos, el que decide qué hacer y el que ejecuta las acciones
> contra APIs reales. Sin `hybrid/`, el CRM es solo un montón de conectores y modelos
> sin coordinación. Los 3 procesos que deben correr (server.py + gateway_server.py +
> test-mcp-render) son el corazón operativo del sistema.

**Estructura:**
```
hybrid/
├── .env                          # Tokens y configuración sensible
├── HYBRID_SUMMARY.md             # Documentación resumen
├── WHATSAPP_AR_NUMBERS.md        # Números WhatsApp Argentina
├── requirements.txt              # fastapi, uvicorn, pydantic, requests
├── config.py                     # 65 líneas — Settings con carga desde .env
├── server.py                     # 157 líneas — FastAPI: 12 endpoints
├── gateway_client.py             # 36 líneas — POSTea instrucciones al Gateway
├── gateway_server.py             # 328 líneas — Gateway HTTP server (:8082)
├── mcp_client.py                 # 168 líneas — Cliente MCP (HTML→imagen)
├── models.py                     # 81 líneas — Pydantic models unificados
├── parser.py                     # 219 líneas — Parser NLP dual con rotación
├── store.py                      # 35 líneas — Persistencia JSON en crm_state/
├── demo_real.py                  # Demo funcional verificada 20/20
├── test_hybrid.py                # Tests unitarios
├── test_stress_mcp.py            # Test de estrés MCP
├── instagram_sim.py              # Simulador de interacciones Instagram
├── simulacion_equipo.py          # Simulador de equipo
├── handlers/
│   └── crm_flows.py              # 10 líneas — puente de compatibilidad
└── crm_state/
    └── media/                    # Output de imágenes generadas
```

---

### 3.1 config.py — [✅ CORRECTO — 65 líneas]

| Aspecto | Detalle |
|---------|---------|
| **Clase `Settings`** | host=127.0.0.1, port=8081 |
| **Gateway URL** | `http://127.0.0.1:8082` (configurable vía `CRM_GATEWAY_URL`) |
| **Carga `.env`** | Manual con `setdefault()` — solo define si no existe |
| **IA Parser** | Lee `CRM_IA_ENDPOINT`, `CRM_IA_API_KEY`, `CRM_IA_MODEL` |
| **`ia_available`** | `True` solo si endpoint + key + model están todos seteados |
| **Telegram** | Solo `chat_id` y `bot_username` — no hace llamadas directas |
| **Kommo** | Solo `pipeline_id: 13768223` |
| **Google Sheets** | Solo `sheet_id` — sin auth |
| **Equipo path** | `STATE_DIR / "equipo.json"` |

**💡 Observación:** Usa `setdefault()` (no override), a diferencia de `gateway_server.py` que sí hace override. Consistencia: config.py es pasivo (no debería pisar vars del entorno), gateway_server.py necesita pisar porque carga `.env` después de los imports de conectores.

---

### 3.2 server.py — [✅ FUNCIONAL — 157 líneas]

| Endpoint | Método | Descripción | Estado |
|----------|--------|-------------|--------|
| `/health` | GET | Health check + estado parser + gateway | ✅ |
| `/webhook/reserva` | POST | Nueva reserva → engine + enviar instrucciones | ✅ |
| `/webhook/reserva/raw` | POST | Reserva desde texto plano | ✅ |
| `/webhook/incidente` | POST | Reporte de incidente | ✅ |
| `/webhook/pago` | POST | Registro de pago | ✅ |
| `/webhook/informe` | POST | Informe diario (event default si no se envía) | ✅ |
| `/webhook/banner` | POST | Genera banner HTML→imagen (async) | ✅ |
| `/webhook/banner/raw` | POST | Banner desde JSON plano | ✅ |
| `/webhook/reel` | POST | Genera reel video (async) | ✅ |
| `/webhook/reel/raw` | POST | Reel desde JSON plano | ✅ |
| `/gateway/response` | POST | Recibe confirmación del Gateway | ✅ |
| `/state/{collection}` | GET | Lee colección de estado | ✅ |

**Startup:** llama a `init_parser()` que configura el parser IA — si no hay `.env` o vars, opera solo modo regex.

**✅ Corregido en esta revisión:**
- `import uuid` movido al tope del archivo (estaba duplicado dentro de 3 endpoints)
- Todos los webhooks ahora guardan `instrucciones_enviadas` en `state_updates` consistentemente (antes incidente/pago/informe no lo hacían)
- `webhook_informe` ya no usa mutable default (`GatewayEvent(type="informe_diario", data={})` era instancia mutable compartida)

---

### 3.3 gateway_client.py — [✅ SIMPLE — 36 líneas]

- POSTea `{action, payload}` a `{gateway_url}/execute`
- Timeout 15s por instrucción
- Devuelve lista con resultados individuales (status, ok, response truncada)

---

### 3.4 gateway_server.py — [✅ PIEZA CLAVE — 328 líneas]

Gateway HTTP server raw (sin framework, `http.server`). **Ejecutor real de todas las acciones contra APIs.**

**ACTION_MAP:**

| Categoría | Acciones | Estado |
|-----------|----------|--------|
| **Mensajería** | telegram.send_message, whatsapp.send_message | ✅ |
| **CRM** | kommo.create_lead | ✅ |
| **Google** | calendar.create_event, sheets.append_row, gmail.send_message, gmail.send_html | ✅ |
| **Render** | render.html_to_image, render.banner, render.generate_reel | ✅ |
| **Android CUA (14)** | dump_ui, screenshot, tap, tap_text, type_text, press_key, swipe, open_app, home, back, scroll_down, scroll_up, find, state | ✅ |

**💡 Observaciones:**
- `send_telegram` extrae `chat_id` del payload pero **no lo usa** — el connector lee el chat_id desde la env `CRM_TG_CHAT_ID`. El payload se ignora.
- `render.html_to_image` y `render.generate_reel` usan `asyncio.run()` dentro de handler síncrono — puede conflictuar si el event loop ya está corriendo
- Carga `.env` con **override** (a diferencia de config.py que usa `setdefault`) — intencional porque necesita pisar vars para los conectores
- Las 14 acciones CUA dependen de Shizuku + AndroidCuaConnector — si Shizuku no está activo, responden con error sin crash

---

### 3.5 mcp_client.py — [✅ FUNCIONAL PERO FRÁGIL — 168 líneas]

| Aspecto | Detalle |
|---------|---------|
| **Protocolo** | JSON-RPC 2.0 sobre subprocess stdin/stdout (MCP handshake manual) |
| **Servidor** | `test-mcp-render/server.py` (default en `~/Documents/proyectos/`) |
| **Chromium** | `/data/data/com.termux/files/usr/bin/chromium-browser` |
| **Output** | `hybrid/crm_state/media/` |
| **Expone** | `html_a_imagen()` y `html_a_imagen_bytes()` |

**⚠️ Riesgos:**
- Sin pool de conexiones — cada llamada lanza un subprocess nuevo
- Buffer de lectura frágil — acumula chunks hasta encontrar JSON match
- Timeout duro de 30s — puede quedarse corto para HTMLs complejos
- Chromium en Termux puede fallar por sandbox (problema común en Android)

---

### 3.6 parser.py — [✅ DUAL CON ROTACIÓN — 219 líneas]

| Modo | Detalle | Confidence |
|------|---------|-----------|
| **IA** | POST a endpoint OpenAI-compatible. Prompt en español rioplatense. | 0.9 |
| **Rotación** | 4 modelos fallback: nemotron-3-super-free → minimax-m2.5-free → deepseek-v4-flash-free → big-pickle | — |
| **Regex** | 7 categorías: nombre, pax, check_in/out, monto, teléfono, email, source, noches | Score 1/6 por campo |
| **Rate limit** | Detecta HTTP 429, pasa al siguiente modelo | — |

**⚠️ Observación:** Este parser en `hybrid/parser.py` es **independiente** del de `flows/central_crm/parser.py`. El híbrido tiene rotación de modelos; el de flows es más simple. `server.py` importa el de flows (`flows.central_crm.parser`), no el de hybrid.

---

### 3.7 models.py — [✅ CORRECTO — 81 líneas]

Modelos Pydantic v2: `GatewayEvent`, `Instruction`, `GatewayResponse`, `Reserva`, `Incidente`, `Pago`, `MiembroEquipo`, `InformeDiario`.

**⚠️:** `flows/central_crm/models.py` tiene los mismos modelos duplicados con estructura casi idéntica.

---

### 3.8 store.py — [⚠️ DUPLICADO — 35 líneas]

| Aspecto | Estado |
|---------|--------|
| **Ruta** | Guarda en `hybrid/crm_state/` |
| **Funciones** | read, write, append, update |
| **vs crm/store.py** | `crm/store.py` guarda en `crm_state/` (raíz del proyecto) |

**⚠️⚠️ Dual persistence paths:** `hybrid/store.py` es el tercer store del proyecto (después de `crm/store.py` y `flows/central_crm/store.py`). Todos escriben JSON pero en directorios distintos.

---

### 3.9 handlers/crm_flows.py — [✅ PUENTE — 10 líneas]

Re-exporta todo desde `flows.central_crm.engine` y `flows.arte.*`. La doc interna dice: "nuevo código debe importar directamente desde flows".

---

### 💡 Resumen HYBRID AI

| Componente | Estado | Prioridad |
|-----------|--------|-----------|
| config.py (Settings) | ✅ | — |
| server.py (FastAPI 12 endpoints) | ✅ | — |
| gateway_client.py | ✅ | — |
| gateway_server.py (24 acciones, 328 líneas) | ✅ | **ALTA** |
| mcp_client.py (HTML→imagen) | ✅ (frágil) | Media |
| parser.py (dual con rotación) | ✅ | — |
| models.py (Pydantic) | ✅ | — |
| handlers/crm_flows.py (bridge) | ✅ | — |
| store.py (persistencia) | ⚠️ | **ALTA** (unificar con crm/store.py) |
| **Dual models** (hybrid/models vs flows/models) | ⚠️ | Baja |
| **Dual parser** (hybrid/parser vs flows/parser) | ⚠️ | Baja |

---

### 🧠 FLUJO HÍBRIDO COMPLETO

```
OpenClaw Gateway (externo)
       │
       ▼  POST /webhook/{tipo}
┌──────────────────┐
│  hybrid/server.py │──→ Parser IA/regex → Engine (reglas de negocio)
│  (FastAPI :8081)  │──→ Genera List[Instruction]
└──────┬───────────┘
       │
       │  POST /execute
       ▼
┌──────────────────┐
│ gateway_server.py │──→ ACTION_MAP → Conector real
│  (:8082, raw HTTP)│     → Telegram / Gmail / Kommo / Calendar
│  24 acciones      │     → Sheets / WhatsApp / Android CUA
└──────────────────┘     → Render (MCP → Chromium)

Los 3 procesos activos necesarios:
  1. hybrid/server.py       → :8081
  2. hybrid/gateway_server.py → :8082
  3. test-mcp-render/server.py → (subprocess, lanzado por mcp_client.py)
```

---

## 4. PIPELINE ARTE (`pipeline.py`) — [REVISADO ✅]

> **Propósito:** Pipeline autónomo de generación y aprobación de contenido visual
> (banner, GIF, reel) con modo cache-first y envío a Telegram para aprobación humana
> con botones Aprobar/Rechazar.
>
> **Valor en la Arquitectura:** ⭐⭐⭐ (MEDIO-ALTO)
> Esta es la **capa de contenido** del CRM. Maneja el ciclo creativo: captación de idea
> → generación (MCP/Chromium) → aprobación humana → posteo → notificación.
> Opera de forma semi-autónoma (requiere aprobación humana, salvo --auto).
> Su valor es medio-alto porque no es crítica para el core del CRM (reservas/pagos),
> pero es esencial para la estrategia de contenido de Rancho Raíz en redes.

El sistema TIENE DOS versiones del pipeline que comparten ~80% de código:
- **`pipeline.py`** (548 líneas) — Versión base. Modo cache o full. 4 pasos.
- **`simulacion_pipeline_completo.py`** (765 líneas) — Versión fortalecida con PipelineMetrics, cache TTL, timeouts, 8 pasos (incluye simulación lead journey).

**Estructura:**
```
pipeline.py (base)
  ├── sección 1: OBTENER ASSETS (cache check)
  ├── sección 2: ENVIAR A TELEGRAM (banner, gif, reel)
  ├── sección 3: APROBACION (poll, auto, o CLI input)
  ├── sección 4: POSTEO EXITOSO + notificacion
  └── sección 5: NOTIFICACION EMAIL

simulacion_pipeline_completo.py (fortalecida)
  ├── PipelineMetrics (clase métricas + summary + JSON export)
  ├── paso 1: CAPTACION_TELEGRAM (simulación de captación)
  ├── paso 2: CREACION_CONTENIDO (banner, gif, reel con cache TTL)
  ├── paso 3: ESPERA_APROBACION (envío a Telegram)
  ├── paso 4: POSTEO_ACTIVO (+ notificación email)
  ├── paso 5: INTERACCION_INSTAGRAM (simulación)
  ├── paso 6: CALENTAMIENTO_LEAD (simulación)
  ├── paso 7: DERIVACION_WHATSAPP (simulación)
  └── paso 8: ACOMPAÑAMIENTO_VIAJE (simulación)
```

---

### 4.1 pipeline.py — [✅ FUNCIONAL — 548 líneas]

| Característica | Detalle | Estado |
|---------------|---------|--------|
| **Modo cache** | Busca en `simulaciones_output/` banners, GIFs, reels pre-generados | ✅ |
| **Modo full** | Genera assets con MCP (Chromium → banner), FFmpeg (GIF), test-mcp-render (reel) | ✅ |
| **Envío Telegram** | sendPhoto, sendAnimation, sendVideo con multipart manual | ✅ |
| **Aprobación** | 3 modos: Telegram buttons (--poll), CLI input, --auto | ✅ |
| **Email** | GmailConnector → oficinabarreal@gmail.com | ✅ |
| **Tema** | `--tema` argument (antes hardcoded "montanas") | ✅ Corregido |
| **skip-telegram** | Flag para omitir envíos a Telegram | ✅ Corregido |
| **skip-email** | Flag para omitir email | ✅ Corregido |
| **--solo-banner/gif/reel** | Filtros para generar/enviar solo cierto tipo de asset | ✅ |

**📦 Assets en cache (simulaciones_output/):**
- 7 banners PNG (527-558 KB cada uno)
- 6 GIFs animados (36-65 KB cada uno)
- 2 reels MP4 (4.5 MB cada uno)

---

### 4.2 simulacion_pipeline_completo.py — [✅ FORTALECIDA — 765 líneas]

| Característica | Detalle | Estado |
|---------------|---------|--------|
| **PipelineMetrics** | Clase con record(), summary(), to_json() | ✅ |
| **Cache con TTL** | 1 hora de validez antes de regenerar | ✅ |
| **Timeouts** | MCP 60s, FFmpeg 30s, frame 30s | ✅ |
| **Steps 5-8** | Simulación de Instagram, lead nurturing, WhatsApp, viaje | ✅ (simulación) |
| **Flag --lead** | Activa el journey completo de lead (pasos 5-8) | ✅ |
| **Flag --reel** | Activa generación de reel | ✅ |
| **Reporte JSON** | Exporta resultados + métricas a `simulaciones_output/` | ✅ |
| **HTML templates** | Banner y GIF con diseño gradient oscuro + dorado (C5A059) | ✅ |

---

### 💡 Resumen PIPELINE ARTE

| Componente | Estado | Prioridad |
|-----------|--------|-----------|
| pipeline.py (base) | ✅ | — |
| simulacion_pipeline_completo.py (fortalecida) | ✅ | — |
| Telegram helpers (multipart manual) | ⚠️ | Media |
| Email notification (GmailConnector) | ✅ | — |
| Cache system (simulaciones_output/) | ✅ | — |
| **Duplicación masiva entre pipeline.py y simulacion** | ⚠️⚠️ | **ALTA** |
| **No hay verificación FFmpeg disponible** | ⚠️ | Media |
| **3 implementaciones de Telegram helper** (pipeline, simulacion, crm.connectors) | ⚠️ | Baja |

---

### 🧠 FLUJO PIPELINE ARTE

```
CLI: python pipeline.py --mode full --tema pileta --poll
 │
 ├─ 1. buscar_cache("pileta") → si hay y no --force, usa cache
 │     si no hay o --force → genera:
 │       • banner: MCP (Chromium) → simulaciones_output/banner_pileta_*.png
 │       • gif: MCP (4 frames) → FFmpeg palettegen → anim_pileta_*.gif
 │       • reel: test-mcp-render → reel_pileta_*.mp4
 │
 ├─ 2. Envía a Telegram (sendPhoto, sendAnimation, sendVideo)
 │     + botones inline: [Aprobar] [Rechazar]
 │
 ├─ 3. Espera decisión:
 │     • --poll: polling Telegram API por callback_query (timeout 120s)
 │     • --auto: aprueba automáticamente
 │     • default: input() por CLI
 │
 ├─ 4. Si aprobado → mensaje "Posteo exitoso" a Telegram + email
 │
 └─ Si rechazado → mensaje "Sin publicación" + pipeline detenido
```

---

## 5. SIMULADORES (`simulators/`) — [✅ REVISADO]

> **Valor en la Arquitectura:** ⭐⭐⭐⭐ (ALTO)
> Los simuladores son el **banco de pruebas y vitrina comercial** del CRM.
> Sin ellos, probar el pipeline requiere APIs reales (Meta, Telegram, Gmail).
> Con ellos, cualquier escenario se puede demostrar en segundos, en cualquier
> dispositivo, sin riesgo de enviar mensajes reales a clientes.
>
> También son el **registro evolutivo** del proyecto — PLAN.md (389 líneas)
> documenta la visión de 8 fases que dio origen a la arquitectura actual,
> aunque en formato conversacional no ejecutable.

La carpeta `simulators/` contiene **tres subsistemas independientes** que
comparten la carpeta pero no se llaman entre sí:

```python
simulators/
├── crm_simulator.py           (725 lines)  # Deterministic replay tool
├── zira_bot.py                (361 lines)  # Bot Telegram real (Zira)
├── zira_telegram.py           (244 lines)  # Helpers compartidos del bot
├── zira_photo_pipeline.py     (191 lines)  # Pipeline de edición de fotos (PIL)
├── zira_voice.py              (14 lines)   # Síntesis de voz
├── send_zira_menu.py          (48 lines)   # Enviar menú inline a Telegram
├── integrador_publicidad.py   (733 lines)  # Pipeline publicidad → CRM
├── integracion_publicidad/    (dir)        # Assets de publicidad
│   ├── db.json                (2755 lines) # Asset DB con metadatos detallados
│   ├── PIPELINE_INTEGRACION.md(268 lines)  # Documentación del pipeline
│   ├── ROADMAP.md             (389 lines)  # Plan director histórico
│   ├── fotos/                 (22 JPGs)    # Banco de imágenes categorizadas
│   ├── audio/                 (7 MP3s)     # Pistas musicales por tema
│   ├── logs/publicaciones.json             # Historial de posteos simulados
│   └── output/                (logs)       # Logs de generación FFmpeg
├── client_demo.json           (15 KB)      # Bundle demo clientes
├── client_demo.md             (147 lines)  # Demo narrativa (5 escenarios)
├── client_demo_es.mp3         (188 KB)     # Voice demo (español)
├── zira_demo.json                         # Bundle demo Zira
├── zira_demo.md               (26 lines)   # Demo narrativa Zira
├── zira_demo_es.mp3           (312 KB)     # Voice demo Zira
├── zira_state.json            (5.4 KB)     # Estado persistente del bot
├── zira_leads.json            (1.3 KB)     # Leads capturados
├── zira_media/                (dir)        # Fotos procesadas (originals, edited, previews, ready, meta)
├── puente_flow_pack.json      (6.8 KB)     # Bridge flow definitions
├── crm_demo_scenarios.json    (484 B)      # Índice de escenarios
├── voice_demo.py              (4.6 KB)     # Demo de síntesis de voz
├── PLAN.md                    (389 lines)  # Plan director multi-agente (histórico)
├── README.md                  (40 lines)   # Docs de uso rápido
└── scripts .sh                (varios)     # run_zira_service, run_client_demo, etc.
```

---

### 5.1 CRM Simulator (`crm_simulator.py`) — [✅ FUNCIONAL — 725 líneas]

**Propósito:** Herramienta de *deterministic replay* para demostraciones comerciales
del CRM sin tocar APIs reales. Produce traces legibles, texto para Telegram,
líneas de voz (EN/ES), bundles JSON y diagramas Mermaid.

| Característica | Detalle | Estado |
|---------------|---------|--------|
| **8 escenarios** | billing, lead, follow-up, digest, Instagram scoring, WhatsApp autoresponse, bridge routing, video marketing | ✅ |
| **Sesiones multi-evento** | client_demo (5 escenarios concatenados con Mermaid), zira_demo | ✅ |
| **Formatos de salida** | texto, telegram, voice (EN), voice_es, JSON, Mermaid | ✅ |
| **Dataclasses** | Scenario (frozen), ScenarioStep, DialogueTurn | ✅ |
| **No toca APIs externas** | 100% determinístico, datos embebidos en SCENARIOS[] | ✅ |
| **Escenarios en vivo** | Simulan Gmail, WhatsApp, Instagram, Bridge, Video | ✅ |

**Escenarios disponibles:**
| ID | Canal | Prioridad | Intención |
|----|-------|-----------|-----------|
| gmail_starlink_payment_issue | Gmail | high | payment_failed |
| whatsapp_booking_lead | WhatsApp | medium | booking_request |
| email_followup_reminder | Gmail | low | check_status |
| email_digest_starlink | Gmail (digest) | high | billing |
| instagram_lead_scoring | Instagram | medium | lead_capture |
| whatsapp_business_autoresponse | WhatsApp Business | high | reservation |
| bridge_task_routing | Bridge | system | routing |
| video_marketing_pipeline | Video | medium | publish |

**Uso:**
```bash
python simulators/crm_simulator.py --list
python simulators/crm_simulator.py --scenario gmail_starlink_payment_issue
python simulators/crm_simulator.py --scenario instagram_lead_scoring --format telegram
python simulators/crm_simulator.py --session client_demo --output /tmp/demo.md
```

> 💡 **Observación:** Los escenarios son data classes estáticas, NO ejecutan
> el engine real (flows/central_crm/engine.py). Sirven para demos, pero cuando
> se quieran migrar a pruebas reales del sistema, habrá que reconectarlos.

---

### 5.2 Zira Bot (`zira_bot.py` + helpers) — [✅ FUNCIONAL — 361+244+191+14 líneas]

**Propósito:** Bot Telegram real para la posada (Rancho Raíz) con capacidades
de atención al cliente, procesamiento de fotos y síntesis de voz.

**Zira = anagrama de Raíz** — identidad del asistente virtual.

| Componente | Archivo | Función | Estado |
|-----------|---------|---------|--------|
| **Bot principal** | zira_bot.py (361) | Polling de updates, routing de mensajes y callbacks | ✅ |
| **Helpers de Telegram** | zira_telegram.py (244) | Textos (welcome, prices, FAQ, availability, reserve), menú inline keyboard, persistencia JSON | ✅ |
| **Pipeline de fotos** | zira_photo_pipeline.py (191) | PIL: original → square/feed/story crops → preview → ready + metadatos | ✅ |
| **Síntesis de voz** | zira_voice.py (14) | TTS sincrónico para respuestas de audio | ✅ |
| **Envío de menú** | send_zira_menu.py (48) | Utilidad one-shot para enviar el menú interactivo | ✅ |

**Flujo del bot:**
```
Usuario → Telegram → Polling (zira_bot.py)
 ├─ /start, /menu → welcome_text() + inline keyboard
 ├─ texto libre → classify_text() → FAQ / prices / availability / reserve
 ├─ foto → download → process_photo (PIL) → preview + ready + meta
 └─ callback_query → respuesta inline + audio opcional
```

**Menú inline (zira_telegram.py):**
```
┌─────────────────────┬──────────────────┐
│ Info posada         │ Ubicación        │
├─────────────────────┼──────────────────┤
│ Qué incluye         │ Precios          │
├─────────────────────┼──────────────────┼──────────┐
│ Disponibilidad      │ Reservar         │ Subir foto │
├─────────────────────┼──────────────────┤
│ Escuchar            │ Más preguntas    │
└─────────────────────┴──────────────────┘
```

**Pipeline de fotos (zira_photo_pipeline.py):**
```
Foto raw (Telegram)
  → guardar original en zira_media/originals/
  → generar crops: square (1:1), feed (4:5), story (9:16)
  → generar preview (contact sheet)
  → generar ready (versión para publicar, feed 4:5)
  → guardar metadata (job_id, suggested_caption, hashtags)
  → notificar en Telegram con preview + ready
```

**Configuración:** `~/.codex/telegram-bridge.json` (token y chat_id)
→ 💡 **INCONSISTENCIA:** El CRM principal usa `.env` (CRM_TG_TOKEN).
  Zira usa un archivo JSON separado en `~/.codex/`. Dos fuentes de token distintas.

**Tarifario embebido (2026):**
| Personas | Precio/noche |
|----------|-------------|
| 1 | $80.000 |
| 2 | $95.000 |
| 3 | $105.000 |
| 4 | $115.000 |
| 5 | $120.000 |

> 💡 **Observación:** Los precios están hardcodeados en zira_telegram.py.
> Si cambian, hay que editar el código. Sería mejor tenerlos en una fuente de datos.

---

### 5.3 Integrador Publicidad (`integrador_publicidad.py`) — [✅ FUNCIONAL — 733 líneas]

**Propósito:** Pipeline completo de generación → aprobación → publicación de
contenido publicitario para Instagram Reels.

**Tres subsistemas en uno:**

#### 5.3.1 Generación de Reels (vía Node.js/FFmpeg)
```
lab.js (ranchocut)
  ├── 22 fotos categorizadas en 5 temas
  ├── 7 pistas de audio MP3
  ├── 12 tipos de Ken Burns (center, pan_left_to_right, zoom_out...)
  ├── 4 estilos de texto (fade, slide_up, slide_left, pulse)
  └── output: MP4 en integracion_publicidad/output/ o ~/ranchoraiz_reels/
```

**Temas y Assets:**
| Tema | Fotos | Audio | Texto |
|------|-------|-------|-------|
| pileta | 6,7,8,9,10,11,19,20,21,22 | RiverMeditation.mp3 | REFRESCA TUS SENTIDOS |
| noche | 1,2,6,7 | PaperWings.mp3 | BAJO LAS ESTRELLAS |
| atardecer | 3,5,11,22 | AutumnSunset.mp3 | ATARDECER DORADO |
| montanas | 2,3,4,5,8,9,13,17,19,20 | GreenLeaves.mp3 | VISTAS QUE ENAMORAN |
| logo | 16,17,18 | AcousticGuitar1.mp3 | RANCHO RAÍZ |

#### 5.3.2 Aprobación por Telegram
```
Video → sendVideo a Telegram (chat_id del CRM)
       → botones inline: [✅ Aprobar] [❌ Rechazar]
       → fallback a terminal si Telegram falla (a/r/s)
       → 3 reintentos de decisión
```

#### 5.3.3 Pipeline de Publicación
```
APROBADO → 1. Email (GmailConnector) a oficinabarreal@gmail.com
         → 2. Simular publicación en Instagram (log + display)
         → 3. Notificar "Posteo realizado" en Telegram
```

**Modos de ejecución:**
```bash
# Listar temas y opciones
python simulators/integrador_publicidad.py --listar

# Usar reel existente (interactivo)
python simulators/integrador_publicidad.py --reels

# Usar reel específico
python simulators/integrador_publicidad.py --usar-reel=pileta_reel.mp4

# Generar nuevo reel automático
python simulators/integrador_publicidad.py --auto

# Generar con tema específico
python simulators/integrador_publicidad.py --tema=pileta --kenburns=pan_left_to_right

# Batch mode (sin aprobación)
python simulators/integrador_publicidad.py --batch=5 --caption="Mi caption"

# Manual (fotos específicas)
python simulators/integrador_publicidad.py --manual=6,11,19,8 --audio=RiverMeditation.mp3
```

> 💡 **Observación:** EMAIL_TO está hardcodeado solo a oficinabarreal@gmail.com
> con comentario "Agregar ltelloraiz, Ramonleandrotello cuando indique" (línea 46).

---

### 5.4 Documentación y Planificación

| Archivo | Líneas | Propósito | Estado |
|---------|--------|-----------|--------|
| integracion_publicidad/PIPELINE_INTEGRACION.md | 268 | Documentación visual del pipeline publicidad → CRM | ✅ |
| integracion_publicidad/ROADMAP.md | 389 | Plan director histórico (conversacional, generado por IA) | ⚠️ Narrativo |
| integracion_publicidad/db.json | 2755 | Asset DB con metadatos (tags, descripciones, clima, momentos) | ✅ |
| PLAN.md | 389 | Plan multi-agente (8 fases, FSM, webhooks universales) | ⚠️ Histórico |
| README.md | 40 | Docs de uso rápido | ✅ |
| client_demo.md | 147 | Demo narrativa (5 escenarios con Mermaid) | ✅ |
| zira_demo.md | 26 | Demo narrativa del bot Zira | ✅ |

**PLAN.md** (389 líneas): Documento fascinante — es en realidad una **conversación
completa con un agente de IA** donde se planificaron las 8 fases del proyecto.
Contiene conceptos muy valiosos: máquina de estados FSM, webhooks universales,
outbound syncer para Kommo/HubSpot, arquitectura de capas. Pero está en formato
narrativo/dialógico, no como plan ejecutable actualizado. → 💡 **Convendría
extraer las decisiones firmes a un plan estructurado.**

---

### 💡 Resumen SIMULADORES

| Componente | Estado | Prioridad |
|-----------|--------|-----------|
| crm_simulator.py (8 escenarios) | ✅ | — |
| zira_bot.py (bot real Telegram) | ✅ | — |
| zira_photo_pipeline.py (PIL) | ✅ | — |
| integrador_publicidad.py (publicidad→CRM) | ✅ | — |
| integracion_publicidad/assets (22 fotos, 7 audios) | ✅ | — |
| **Telegram helper fragmentation** (3 formas distintas) | ⚠️ | Media |
| **crm_simulator standalone** (no ejecuta engine real) | ⚠️ | Baja |
| **EMAIL_TO hardcodeado** (solo oficinabarreal@gmail.com) | ⚠️ | Baja |
| **Dos fuentes de token Telegram** (.env vs ~/.codex/) | ⚠️ | Baja |
| **PLAN.md en formato conversacional** (no ejecutable) | ⚠️ | Media |
| **zira_telegram.py precios hardcodeados** | ⚠️ | Baja |
| **Pillow no listado en requirements** (zira_photo_pipeline.py) | ⚠️ | Baja |
| **zira_demo_es.mp3 y client_demo_es.mp3** (archivos grandes, ~500KB) | ✅ | — |

---

### 🧠 FLUJO COMPLETO: Integrador Publicidad → CRM

```bash
CLI: python simulators/integrador_publicidad.py --auto
   o: python simulators/integrador_publicidad.py --reels
   o: python simulators/integrador_publicidad.py --tema=pileta

 │
 ├─ 1. REEL: elegir existente o generar nuevo (Node.js / lab.js)
 │     • 22 fotos categorizadas en 5 temas
 │     • 12 tipos de Ken Burns, 4 estilos de texto
 │     • 7 pistas de audio MP3
 │     • Output: MP4 en ~/ranchoraiz_reels/ o integracion_publicidad/output/
 │
 ├─ 2. APROBACIÓN: enviar video a Telegram con botones inline
 │     • Si Telegram falla → fallback a terminal
 │     • 3 reintentos de decisión
 │     • Opciones: Aprobar / Rechazar / Saltar
 │
 ├─ 3. SI APROBADO:
 │     ├─ Email (GmailConnector) a oficinabarreal@gmail.com
 │     │   Asunto: "🎬 Nuevo reel aprobado para publicar — {nombre}"
 │     │
 │     ├─ Simular publicación en Instagram (log en publicaciones.json)
 │     │   Display visual con marco ASCII
 │     │
 │     └─ Notificar "Posteo realizado" en Telegram
 │
 └─ SI RECHAZADO: descartar + log
```

---

### 🔗 Conexiones con otras secciones

| Sección | Conexión |
|---------|----------|
| **CORE CRM** (crm/connectors) | integrador_publicidad.py usa GmailConnector para enviar emails |
| **CORE CRM** (crm/connectors) | Zira bot usa Telegram directamente (no vía crm.connectors) |
| **PIPELINE ARTE** (pipeline.py) | Comparte ~80% lógica con simulacion_pipeline_completo.py (que está *dentro* del pipeline, no en simulators/) |
| **PIPELINE ARTE** | 3ra implementación de Telegram helper (junto a pipeline.py e integrador_publicidad.py) |
| **HYBRID AI** | crm_simulator.py podría consumir los endpoints del Hybrid Server en el futuro |
| **INFRAESTRUCTURA** | PLAN.md contiene el roadmap original de 8 fases que guió la evolución |

---

## 6. INFRAESTRUCTURA Y DOCUMENTACIÓN — [✅ REVISADO]

> **Valor en la Arquitectura:** ⭐⭐⭐⭐ (ALTO)
> Es la **capa de conocimiento y gobierno** del proyecto. Sin estos archivos,
> ningún agente (Hermes, OpenCode, OpenClaw) podría entender la arquitectura,
> los conectores, las credenciales o el roadmap. Son la memoria institucional
> del sistema. CONTEXTO_CONFIG.md es particularmente crítico porque documenta
> horas de pruebas de integración de modelos que de otro modo se perderían.

La raíz del proyecto contiene **12+ archivos** de documentación, planificación
y herramientas auxiliares. Varios están duplicados en subdirectorios.

```python
raíz del proyecto/
├── PLAN.md                 (389 lines)  # Plan multi-agente histórico
├── ROADMAP.md              (46 lines)   # Roadmap ejecutivo (Q2 2026 → 2027)
├── AGENT.md                (37 lines)   # Overview rápido del proyecto
├── CREDENCIALES.md         (80 lines)   # Referencia de tokens y API keys
├── CONTEXTO_CONFIG.md      (394 lines)  # Trazabilidad de configs + historial de pruebas
├── ARTE_OPENCODE.md        (1110 lines) # Documentación exhaustiva (perspectiva OpenCode)
├── ARTE_HERMES.md          ← ESTE ARCHIVO
├── equipo.py               (167 lines)  # Datos del equipo + huéspedes registrados
├── project_monitor.py      (210 lines)  # Monitor con Gemini API + notificaciones Android
├── idea_engine.py          (154 lines)  # Motor de sugerencias contextuales
│
├── asistente/
│   ├── ROADMAP.md          (81 lines)   # Roadmap del asistente
│   └── AGENT.md            (159 lines)  # Guía del asistente personal
│
├── crm/
│   └── AGENT.md            (45 lines)   # Guía de conectores CRM
│
└── simulators/
    ├── PLAN.md             (389 lines)  # DUPLICADO de raíz/PLAN.md
    └── integracion_publicidad/
        └── ROADMAP.md      (389 lines)  # Plan director publicidad (histórico)
```

---

### 6.1 Documentos de Planificación

| Archivo | Líneas | Propósito | Estado | Duplicado? |
|---------|--------|-----------|--------|------------|
| **PLAN.md** (raíz) | 389 | Plan multi-agente 8 fases (FSM, webhooks universales, outbound syncer) | ⚠️ Histórico conversacional | Sí, idéntico en simulators/PLAN.md |
| **ROADMAP.md** (raíz) | 46 | Roadmap ejecutivo: ✅ completado, 🚧 en progreso, 🎯 futuro, timeline Q2-Q4 2026, maintenance | ✅ Actualizado | Sí (asistente/ + integracion_publicidad/) |
| **AGENT.md** (raíz) | 37 | Overview: estructura, features, setup, conventions, safety | ✅ | Sí (asistente/ + crm/) |
| **asistente/ROADMAP.md** | 81 | Roadmap específico del asistente: logros, estructura, próximos pasos | ✅ | — |
| **asistente/AGENT.md** | 159 | Guía detallada del asistente: conectores, ejemplos, flujo típico | ✅ | — |
| **crm/AGENT.md** | 45 | Guía de conectores CRM: interfaz estandarizada ConnectorResult | ✅ | — |

**PLAN.md** (389 líneas): Como se mencionó en Sección 5, es una conversación completa
con un agente de IA donde se definieron las 8 fases del proyecto. La tabla FSM de
8 pasos (CAPTACION_TELEGRAM → ACOMPAÑAMIENTO_VIAJE) es el concepto más valioso,
y coincide exactamente con la implementación en `flows/central_crm/state_machine.py`.
También contiene el diseño de webhooks universales y outbound syncer.

**ROADMAP.md** (46 líneas): Es el documento de planificación **realmente mantenido**.
Muestra el progreso real del proyecto con checkboxes. El timeline Q2-Q4 2026 + 2027
es realista y bien estructurado.

> 💡 **Observación:** La duplicación de PLAN.md (raíz y simulators/) y ROADMAP.md
> (raíz, asistente/, integracion_publicidad/) es confusa. Cada subdirectorio debería
> tener solo información específica de su ámbito, no copias literales.

---

### 6.2 Documentos de Configuración y Credenciales

| Archivo | Líneas | Propósito | Estado |
|---------|--------|-----------|--------|
| **CREDENCIALES.md** | 80 | Referencia de tokens: Google OAuth, WhatsApp, Instagram, Kommo, Telegram, Hermes, OpenClaw | ✅ |
| **CONTEXTO_CONFIG.md** | 394 | Trazabilidad de configuraciones: 8 iteraciones de modelos, historial de pruebas, cadenas de modelos activas, A2UI, metodología de laboratorio | ✅ ⚠️ (contiene secrets) |

**CREDENCIALES.md** — Referencia central de credenciales:
| Servicio | Token/ID | Estado |
|----------|----------|--------|
| Google OAuth | Proyecto `gen-lang-client-0847420405`, Client ID y Secret documentados | ✅ |
| WhatsApp Cloud API | Token en .env, Phone ID `1144484832072419` | ⚠️ EXPIRED |
| Instagram Graph API | Token en .env, User ID `17841480371697646` | ✅ Vivo |
| Kommo (CRM) | Subdomain + Token en .env | ✅ Configurado |
| Telegram | CRM_TG_TOKEN en .env, Chat ID `8272684219` | ✅ |
| Hermes config | `~/.hermes/config.yaml` | ✅ |
| OpenClaw config | `~/.openclaw/` completo (gateway, modelos, auth) | ✅ |
| OpenCode Zen | API key `sk-Acd...Ow3p` | ✅ |

**⚠️ CONTEXTO_CONFIG.md contiene API keys en texto plano** (líneas 122, 371-374).
El propio archivo dice "NO hacer commit ni compartir" pero es un riesgo latente.

**CONTEXTO_CONFIG.md** — Joya de documentación técnica. Registro de 8 iteraciones
de configuración de modelos con resultados, causas raíz, lecciones aprendidas.
Incluye:
- Iteración 1-8 con resultados detallados (✅, ❌, ⚠️)
- Solución para big-pickle en OpenClaw: proxy LiteLLM
- A2UI replicado desde el entorno (Python http.server + Chromium headless)
- Matriz de 10 combinaciones probadas
- Metodología de laboratorio: "No asumir fracaso — probar todas las combinaciones"
- Referencias cruzadas a todos los archivos de configuración

---

### 6.3 Documentación Exhaustiva (ARTE_*.md)

| Archivo | Líneas | Propósito | Estado |
|---------|--------|-----------|--------|
| **ARTE_OPENCODE.md** | 1110 | Documentación completa desde perspectiva OpenCode: arquitectura, conectores, orchestrator, Hybrid AI, Zira, plan de integración publicidad, MCP html_a_imagen, experimentos multimedia | ✅ Exhaustivo |
| **ARTE_HERMES.md** | ~1125 | ← ESTE ARCHIVO. Mapa de arquitectura y estado del proyecto | ✅ En evolución |

**ARTE_OPENCODE.md** (1110 líneas) — El documento más grande del proyecto.
Documenta:
- Stack tecnológico completo (Python 3.10+, Google APIs, Pillow, FastAPI, Pydantic, etc.)
- Los 10 conectores (con estados: ✅ Real, 🚧 Exp., ⏳ Token exp.)
- CRMOrchestrator con flujo completo ingest→qualify→publish→schedule→notify
- Modelos de datos: Lead, PhotoAsset, JourneyStage, Channel
- Telegram Bot con 4 proveedores IA fallback
- Hybrid AI System (FastAPI + MCP Client)
- Segundo Cerebro (Google Docs autónomo)
- Android CUA (Shizuku/ADB)
- Plan de integración publicidad ↔ hola-3 (5 puntos detallados)
- 14 notas para futuros agentes
- MCP html_a_imagen: render a costo $0 con Chromium headless
- Experimentos multimedia: overlays transparentes, plantillas JSON, stop-motion GIF

---

### 6.4 Herramientas Auxiliares

| Archivo | Líneas | Propósito | Estado |
|---------|--------|-----------|--------|
| **equipo.py** | 167 | Datos del equipo (Leo, Ayelen, Diego, Chiqui) + 8 huéspedes registrados con datos reales | ✅ |
| **project_monitor.py** | 210 | Monitor automático: git status → Gemini API → termux-notification cada 30 min | ⚠️ Sin uso activo |
| **idea_engine.py** | 154 | Motor de sugerencias contextuales basado en ROADMAP.md → notificación | ⚠️ Sin uso activo |

**equipo.py** — Datos del equipo Rancho Raíz:
| Persona | Rol | Email | Teléfono |
|---------|-----|-------|----------|
| Leo Tello | Dueño / Finanzas | ltelloraiz@gmail.com | +54 9 264 548-0313 |
| Ayelen Juricevic | Booking / Ventas | ayelenjuricevic@gmail.com | +54 9 11 5959-5869 |
| Diego (vos) | Operaciones | oficinabarreal@gmail.com | — |
| Chiqui | Limpieza | — | — |

+ 8 huéspedes registrados con datos reales (nombres, fechas, montos, notas).
Función `guardar()` exporta a `crm_state/equipo.json` y `crm_state/huespedes.json`.

**project_monitor.py** — Usa Gemini 2.5 Flash API para generar notificaciones
inteligentes sobre el estado del proyecto. Verifica git status, archivos clave,
historial de notificaciones y procesos activos. Envía vía termux-notification.

> ⚠️ **Observación:** project_monitor.py línea 33 tiene API key hardcodeada
> como fallback (`AIzaSy...8qRw`). Si .env no tiene GOOGLE_API_KEY, usa
> la key en texto plano. También usa gemini-2.5-flash (mismos rate limits que
> el CRM, podría competir por cuota).

**idea_engine.py** — Genera sugerencias genéricas basadas en archivos existentes
("Consider testing Gmail connector", "Enhance Telegram bot", etc.). Corre en
modo continuo (cada 30 min) o `--once`. No ejecuta acciones reales.

> 💡 **Observación:** idea_engine.py no tiene integración real con el sistema.
> Sus sugerencias son estáticas (basadas en `Path.exists()`) y no reflejan el
> estado real del proyecto. project_monitor.py al menos usa la API de Gemini.

---

### 💡 Resumen INFRAESTRUCTURA Y DOCUMENTACIÓN

| Componente | Estado | Prioridad |
|-----------|--------|-----------|
| ROADMAP.md (raíz, ejecutivo) | ✅ | — |
| AGENT.md (raíz + asistente + crm) | ✅ | — |
| CREDENCIALES.md | ✅ | — |
| CONTEXTO_CONFIG.md | ✅ Joya técnica | — |
| ARTE_OPENCODE.md | ✅ Exhaustivo | — |
| equipo.py | ✅ | — |
| **PLAN.md formato conversacional** (no ejecutable) | ⚠️ | Media |
| **Duplicación de PLAN.md** (raíz y simulators/) | ⚠️ | Baja |
| **Duplicación de ROADMAP.md** (raíz, asistente/, integracion_publicidad/) | ⚠️ | Baja |
| **Duplicación de AGENT.md** (raíz, asistente/, crm/) | ⚠️ | Baja |
| **API keys en texto plano** (CONTEXTO_CONFIG.md, project_monitor.py) | ⚠️⚠️ | **ALTA** |
| **project_monitor.py sin uso activo** | ⚠️ | Baja |
| **idea_engine.py sin integración real** | ⚠️ | Baja |
| **project_monitor.py compite por rate-limit de Gemini** | ⚠️ | Media |

---

### 🔗 Conexiones con otras secciones

| Sección | Conexión |
|---------|----------|
| **CORE CRM** | AGENT.md documenta los conectores; CREDENCIALES.md lista tokens; equipo.py contiene datos del equipo |
| **CENTRAL FLOWS** | PLAN.md contiene la tabla FSM original que coincide con flows/central_crm/state_machine.py |
| **HYBRID AI** | CONTEXTO_CONFIG.md documenta toda la cadena de modelos y el historial de pruebas; CREDENCIALES.md lista tokens de API |
| **PIPELINE ARTE** | ARTE_OPENCODE.md documenta el pipeline en detalle; CREDENCIALES.md tiene tokens necesarios |
| **SIMULADORES** | PLAN.md duplicado en simulators/; equipo.py define los roles humanos que los simuladores ejercitan |

---

## EQUIPO HUMANO

| Persona | Rol | Contacto |
|---------|-----|----------|
| **Leo Tello** | Dueño / Finanzas | ltelloraiz@gmail.com |
| **Ayelen Juricevic** | Booking / Ventas | ayelenjuricevic@gmail.com |
| **Diego** (vos) | Operaciones / Dev | oficinabarreal@gmail.com |
| **Chiqui** | Limpieza | — |

---

## CADENA DE MODELOS

| Orden | Modelo | Provider | Estado |
|-------|--------|----------|--------|
| 1° | big-pickle (deepseek-v4-flash) | OpenCode Zen | ✅ (reasoning_effort: low) |
| 2° | gemini-2.5-flash | — | ✅ (reasoning: false, 10 RPM) |
| 3° | gemini-2.5-flash-lite | — | ✅ (30 RPM, no probado aún) |
| 4° | nvidia/nemotron-3-super | — | ✅ Fallback |

**Nota:** big-pickle NO funciona via OpenClaw (routing bug 401). SI funciona via Hermes.

---

## PUERTOS Y SERVICIOS

| Servicio | Puerto | Estado |
|----------|--------|--------|
| Hybrid Server | :8081 | ✅ Documentado | FastAPI con 12 endpoints webhook |
| Gateway Server | :8082 | ✅ Documentado | 24 acciones (Telegram, Gmail, Kommo, Calendar, Sheets, WhatsApp, CUA, Render) |
| OpenClaw Gateway | :18789 | ⏳ No verificado | Gateway externo original |
| MCP Render | subproceso | ✅ Chromium disponible | Lanzado por mcp_client.py desde test-mcp-render |

---

## ESTADO DEL REPOSITORIO

- **HEAD:** `368a91f` — v2.3 Monitoreo y heartbeat de agentes
- **Modificados:** .gitignore, ARTE_OPENCODE.md, ROADMAP.md, crm_state/.google_token.json, .tg_offset
- **Eliminados del índice:** __pycache__/ (todos los .pyc)
