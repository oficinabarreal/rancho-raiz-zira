# Pipeline Completo: Integración Publicidad → CRM

## Visión General

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      PIPELINE INTEGRADO v1.1                             │
│    Reels existentes o generación nueva + Aprobación CRM + Posteo        │
└──────────────────────────────────────────────────────────────────────────┘

  ┌─ REELS EXISTENTES ─┐
  │ ~/ranchoraiz_reels/ │──┐
  │ (9 reels previos)   │  │
  └─────────────────────┘  │
                           ├──→ ELEGIR ──→ TELEGRAM ──→ ¿APROBAR? ──→ SÍ ──→ EMAIL ──→ SIMULAR IG
  ┌─ GENERAR NUEVO ────┐  │                 (video +       (a/r/s)       (Gmail a    ("Posteo
  │ FFmpeg (lab.js)    │──┘                  botones)                     oficinaba-   realizado"
  │ 22 fotos, Ken Burns│                                                                  vía TG)
  │ texto, audio       │
  └─────────────────────┘
```

---

## Fase 1: Origen del Video

### Opción A: Usar reel existente

El simulador lista los 9 reels ya generados en `~/ranchoraiz_reels/`:

```bash
python simulators/integrador_publicidad.py --reels
# Muestra menú interactivo para elegir

python simulators/integrador_publicidad.py --usar-reel=pileta_reel.mp4
# Usa un reel específico por nombre
```

### Opción B: Generar nuevo

Si se quiere generar un reel nuevo desde las 22 fotos del banco de imágenes:

```bash
python simulators/integrador_publicidad.py --tema=pileta --kenburns=pan_left_to_right
python simulators/integrador_publicidad.py --auto
```

---

## Fase 2: Aprobación por Telegram

```
VIDEO ──→ Enviar a Telegram ──→ Esperar decisión
              │                       │
              │               ┌───────┴───────┐
              │               │               │
              ▼               ▼               ▼
         ✅ APROBAR       ❌ RECHAZAR      ⏭️ SALTAR
              │               │               │
              ▼               ▼               ▼
        Fase 3 + 4     Descartar + log    Salir sin
                                              publicar
```

El video se envía con caption informativo al chat de Telegram.
Se puede responder en la terminal: `a` (aprobar), `r` (rechazar), `s` (saltar).

---

## Fase 3: Email de Notificación

```
APROBACIÓN
    │
    ▼
Enviar email a oficinabarreal@gmail.com
    │
    ├─ Asunto: "🎬 Nuevo reel aprobado para publicar — {nombre}"
    ├─ Cuerpo: detalles del video (nombre, tamaño, tema, caption, fecha)
    │
    ▼
Si email OK → continuar a Fase 4
Si email falla → warning pero sigue igual
```

Usa `GmailConnector` de hola-3 (vía Gmail API / OAuth) y la cuenta
de Google configurada en `crm_state/.google_token.json`.

---

## Fase 4: "Posteo realizado" (Instagram simulado)

```
EMAIL ENVIADO
    │
    ▼
Registrar en log (logs/publicaciones.json)
    │
    ├─ timestamp, video, caption, tema, tamaño
    │
    ▼
Mostrar resumen en terminal
    │
    ▼
Enviar mensaje a Telegram:
  "📱 Posteo realizado en Instagram ✅
   🎬 pileta_reel.mp4
   🏷️  REFRESCA TUS SENTIDOS
   
   ⏳ Próximo paso: implementar publicación real
      vía Instagram Graph API"
```

---

## Pipeline Completo (cuando se aprueba)

```
1. ✅ Video aprobado en Telegram
2. ✅ Email a oficinabarreal@gmail.com
3. ✅ Log guardado en logs/publicaciones.json
4. ✅ Mensaje "Posteo realizado" en Telegram
5. ⏳ Publicación real en Instagram (futuro)
```

---

## Modos de Uso

```bash
# 1. Elegir reel existente interactivamente
python simulators/integrador_publicidad.py --reels

# 2. Usar reel específico
python simulators/integrador_publicidad.py \
  --usar-reel=pileta_reel.mp4 \
  --caption="REFRESCA TUS SENTIDOS - Rancho Raíz"

# 3. Generar nuevo reel
python simulators/integrador_publicidad.py --tema=pileta

# 4. Generar automático
python simulators/integrador_publicidad.py --auto

# 5. Batch (sin aprobación)
python simulators/integrador_publicidad.py --batch=5

# 6. Ver opciones disponibles
python simulators/integrador_publicidad.py --listar
```

---

## Diagrama de Secuencia (Caso Aprobado)

```
Usuario              Integrador              Telegram           Gmail          Instagram(sim)
  │                      │                      │                 │                 │
  │  --usar-reel=FILE    │                      │                 │                 │
  │─────────────────────►│                      │                 │                 │
  │                      │  sendVideo()         │                 │                 │
  │                      │─────────────────────►│                 │                 │
  │                      │  Video con botones   │                 │                 │
  │                      │◄─────────────────────│                 │                 │
  │  "a" (aprobar)       │                      │                 │                 │
  │─────────────────────►│                      │                 │                 │
  │                      │  send_email()        │                 │                 │
  │                      │──────────────────────────────────────►│                 │
  │                      │  ✅ Email enviado    │                 │                 │
  │                      │◄──────────────────────────────────────│                 │
  │                      │                      │                 │                 │
  │                      │  Log publicación     │                 │                 │
  │                      │─────────────────────────────────────────────────────────►│
  │                      │                      │                 │                 │
  │                      │  "Posteo realizado"  │                 │                 │
  │                      │─────────────────────►│                 │                 │
  │                      │                      │                 │                 │
  │◄─────────────────────│                      │                 │                 │
  │  ✅ Pipeline completo │                      │                 │                 │
```

---

## Reels Existentes (9)

| # | Reel | Tamaño | Tema |
|---|------|--------|------|
| 1 | `pileta_con_audio.mp4` | 1.2 MB | pileta |
| 2 | `montanas_reel.mp4` | 1.1 MB | montanas |
| 3 | `atardecer_reel.mp4` | 891 KB | atardecer |
| 4 | `brand_reel.mp4` | 605 KB | — |
| 5 | `noche_reel.mp4` | 1.7 MB | noche |
| 6 | `pileta_reel.mp4` | 1.0 MB | pileta |
| 7 | `ranchoraiz_storytelling.mp4` | 1.0 MB | — |
| 8 | `top-left-slide-up-cine_*.mp4` | 1.0 MB | — |
| 9 | `duracion-3s-rapido_*.mp4` | 1.2 MB | — |

---

## Estructura del Simulador

```
simulators/
├── integrador_publicidad.py         ← Script principal (v1.1, ~300 líneas)
├── integracion_publicidad/
│   ├── db.json                      ← 22 fotos con metadata
│   ├── fotos/*.jpg                  ← 22 imágenes (5 MB)
│   ├── audio/*.mp3                  ← 9 tracks de música (41 MB)
│   ├── output/                      ← Reels generados (FFmpeg)
│   ├── logs/
│   │   └── publicaciones.json       ← Historial de publicaciones
│   └── PIPELINE_INTEGRACION.md      ← Este documento
├── zira_bot.py, zira_telegram.py    ← Simuladores existentes
└── crm_simulator.py                 ← Simulador CRM existente
```

---

## Criterios de Éxito

- [x] Cargar db.json con metadata de 22 fotos
- [x] Listar reels existentes y elegir interactivamente
- [x] Usar reel específico por nombre (`--usar-reel=`)
- [x] Generar reel nuevo con FFmpeg (lab.js)
- [x] Enviar video a Telegram con botones inline
- [x] Aprobar → enviar email a oficinabarreal@gmail.com
- [x] Aprobar → simular posteo en Instagram
- [x] Aprobar → mensaje "Posteo realizado" en Telegram
- [x] Rechazar → descartar con log
- [x] Saltar → salir sin publicar
- [x] Batch mode: generar N reels sin intervención
- [ ] Publicación real en Instagram vía Graph API (futuro)

---

## Estándar de Automatización CRM — Rancho Raíz

### Logros del Pipeline Integrado

| # | Logro | Estado |
|---|-------|--------|
| 1 | Selección de reels existentes (9 previos) sin regenerar | ✅ |
| 2 | Aprobación por Telegram con video previo | ✅ |
| 3 | Email automático vía Gmail API con OAuth renovable | ✅ |
| 4 | Firma unificada "Zira" en todas las notificaciones | ✅ |
| 5 | Multi-destinatario preparado (Leo Tello, Ramon Tello, oficinabarreal) | ✅ |
| 6 | Simulación de posteo Instagram con log persistente | ✅ |
| 7 | Notificación "Posteo realizado" de vuelta a Telegram | ✅ |
| 8 | OAuth auto-refresh sin intervención manual | ✅ |
| 9 | Publicación a 3 destinatarios simultáneos (cuando se active) | ✅ |
| 10 | Pipeline ejecutable desde CLI single-command | ✅ |

### Firma estándar del sistema

```
--
Zira 🤖
Rancho Raíz — CRM Autónomo
*(Zira = anagrama de Raíz)*
```

### Próximas Automatizaciones

- `InstagramConnector.publish()` real vía Graph API (media container + publish)
- `send_video()` nativo en `TelegramConnector`
- Webhook `/generar_reel` en `hybrid/server.py` para API externa
- Pipeline `generate_and_publish()` como método de `CRMOrchestrator`
- Programación semanal de reels (cron/celery) con cola de aprobación
