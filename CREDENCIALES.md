# Credenciales — Rancho Raiz CRM

## Google Cloud Platform
- Proyecto: `gen-lang-client-0847420405`
- Número: `104536822997`
- Cliente OAuth 2.0 Web: `104536822997-b2s9bit8b5ugujh9bp152aqu6mfkm5rv.apps.googleusercontent.com`
- Secret: `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`
- Redirect URI registrada: `http://localhost:8080`
- APIs habilitadas: Gmail, Calendar, Drive, Sheets, Maps

### Token (renovable)
- Archivo: `crm_state/.google_token.json`
- Scopes: gmail.modify, gmail.compose, drive.file, calendar, spreadsheets, mail.google.com (full)
- Se auto-refresca al expirar

### Cómo renovar si expira:
1. Ir a https://console.cloud.google.com/apis/credentials
2. Abrir cliente OAuth 2.0
3. Verificar redirect_uri: `http://localhost:8080`
4. Ejecutar: `python crm/oauth_capture.py`
5. Abrir link, autorizar, capturar código

## WhatsApp Cloud API
- Token: `CRM_WHATSAPP_TOKEN` en .env
- Phone ID: `1144484832072419`
- Número: +54 9 264 548-0313
- Estado: EXPIRED (necesita generar nuevo token en Meta Developers)

## Instagram Graph API
- Token: `CRM_INSTAGRAM_TOKEN` en .env
- User ID: `17841480371697646`
- Cuenta: @rancho.raiz.2026
- Estado: ✅ Vivo

## Kommo (CRM)
- Subdomain: `CRM_KOMMO_SUBDOMAIN` en .env
- Token: `CRM_KOMMO_TOKEN` en .env

## Telegram
- Token: `CRM_TG_TOKEN` en .env
- Chat ID: `CRM_TG_CHAT_ID` en .env

## Entorno
- `.env` en raíz del proyecto (NO subir a git)
- `crm_state/` contiene tokens y datos locales

## Agentes

### Hermes (`~/.hermes/config.yaml`)
- **YAML reparado**: indentación inconsistente en tts/stt/memory/delegation/x_search (causaba fallback a default config, ignorando todas las overrides)
- Modelo default: `nvidia/nemotron-3-super-120b-a12b` (NVIDIA API key funcionando)
- Fallback: `openai` → `https://opencode.ai/zen/v1` (key expirada, 403)
- `opencode/big-pickle` agregado al model_catalog local (200K context window)
- OpenRouter API key eliminada (401, expirada)

### OpenClaw (`~/.openclaw/`)
- Instalación global completa con gateway, plugins, Telegram, cron
- `openclaw.json`: provider `opencode` añadido + modelo `opencode/big-pickle`
- `.worktrees/openclaw/`:
  - `daemon.py`: ejecutor de tareas en segundo plano
  - `ia_client.py`: cliente compartido (CLI big-pickle + fallback Zen API)
  - `cron.sh`: script para crontab
- Rol: automatización programada, webhooks, tareas de fondo

### Uso
```bash
# OpenClaw: una ronda de tareas programadas
python3 .worktrees/openclaw/daemon.py --once

# OpenClaw: escuchar webhooks en puerto 8083
python3 .worktrees/openclaw/daemon.py --webhook 8083

# Agregar al crontab (se ejecuta a los :30 de cada hora)
echo '30 * * * * /ruta/a/.worktrees/openclaw/cron.sh >> /tmp/openclaw.log 2>&1' | crontab -
```

### Nota
`opencode/big-pickle` está disponible directamente en el CLI de OpenCode (como esta sesión).
Agentes tipo Hermes/OpenClaw se conectan a través del CLI. Para llamadas API directas (sin CLI),
usan modelos NVIDIA como fallback configurado en cada agente.
