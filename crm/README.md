# CRM Core

This package is the working CRM nucleus for Rancho Raíz / Zira.

## What it covers

- Lead ingestion from Gmail, WhatsApp, Instagram, Telegram, and web.
- Journey stages from first contact to post-stay follow-up.
- Trial connectors for Kommo and Notion.
- Dry-run connectors for Drive, Calendar, Sheets, WhatsApp, Instagram, and Telegram.
- Photo asset workflow for edit variants, preview, review, and publish prep.
- Gmail digest mode that can qualify likely booking requests and push them into the CRM.

## Journey

1. First contact lands in Gmail, WhatsApp, Instagram, or Telegram.
2. The lead is profiled and scored.
3. The system offers hospitality context before the guest arrives.
4. Pre-arrival reminders and info are scheduled.
5. During the stay, the bot can answer and assist.
6. After checkout, the lead can be followed up for review or return.

## Philosophy

- The CRM should accompany the client from first contact to post-stay.
- It should transmit the posada experience before arrival.
- It should keep supporting the guest during the stay and after departure.
- Kommo and Notion are treated as trials until we decide whether they stay.

## Usage

```bash
python3 -m crm.cli --brief
python3 -m crm.cli --gmail-digest --limit 5
python3 -m crm.cli --lead-name "Cliente demo" --arrival-date 2026-06-01 --departure-date 2026-06-05 --guests 3 --brief
python3 -m crm.cli --photo /path/to/photo.jpg --photo-caption "Habitación con vista"
python3 -m crm.cli --lead-name "Cliente demo" --arrival-date 2026-06-01 --departure-date 2026-06-05 --guests 3 --photo /path/to/photo.jpg --brief
python3 -m crm.cli --photo /path/to/photo.jpg --photo-caption "Vista del valle" --photo-only
python3 -m crm.cli --journey-demo --lead-name "Cliente demo" --photo /path/to/photo.jpg
bash crm/run_journey_demo.sh
```

## Environment

Optional env vars:

- `CRM_GMAIL_USER` — Gmail account email
- `CRM_GMAIL_APP_PASSWORD` — Gmail app password (not regular password)
- `CRM_TG_TOKEN` — Telegram bot token
- `CRM_TG_CHAT_ID` — Telegram chat ID for notifications

### Google integrations (Drive, Calendar, Sheets)

Requires a Google Cloud OAuth 2.0 credential file:

1. Go to https://console.cloud.google.com/apis/credentials
2. Create an OAuth 2.0 Client ID (Desktop app type)
3. Download the JSON and save it
4. Set `CRM_GOOGLE_CREDS` to the path of that JSON file
5. On first use, the connector will open a browser for OAuth consent

OAuth tokens are cached in `CRM_STATE_DIR/.google_token.json`.

- `CRM_GOOGLE_CREDS` — path to the client_secret JSON file
- `CRM_STATE_DIR` — directory for OAuth token cache (default: `crm_state`)

### Kommo

- `CRM_KOMMO_SUBDOMAIN` — your Kommo subdomain (e.g. `misdatos`)
- `CRM_KOMMO_TOKEN` — access token for Kommo API v4

### Notion

- `CRM_NOTION_TOKEN` — Notion integration token (starts with `ntn_` or `secret_`)
- `CRM_NOTION_DATABASE_ID` — target database ID

### WhatsApp Cloud API

- `CRM_WHATSAPP_TOKEN` — permanent WhatsApp Cloud API token
- `CRM_WHATSAPP_PHONE_ID` — phone number ID from Meta Business

### Instagram Graph API

- `CRM_INSTAGRAM_TOKEN` — Instagram Graph API token
- `CRM_INSTAGRAM_USER_ID` — Instagram Business user ID

If a connector's credentials are missing, it falls back to **dry-run mode** (logs the action without calling the external API).

## Photo flow

When you pass `--photo`, the CRM now generates:

- `square` variant for social crops
- `feed` variant for Instagram-style publication
- `story` variant for vertical stories
- `preview` variant for review and Telegram handoff
- `ready` variant as the suggested publish candidate

Artifacts are stored under the CRM state root in `media/<asset_id>/`.
