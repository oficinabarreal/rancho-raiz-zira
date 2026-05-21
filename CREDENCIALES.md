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
