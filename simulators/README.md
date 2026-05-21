# CRM Simulator

This directory contains a deterministic replay tool for CRM demo flows.

## What it does

- Replays common CRM situations without touching live apps.
- Produces human-readable traces, Telegram-ready text, voice-ready lines, and JSON bundles.
- Lets you demo the pipeline before wiring Gmail, WhatsApp, Calendar, Sheets, or Telegram.

## Included scenarios

- `gmail_starlink_payment_issue`
- `whatsapp_booking_lead`
- `email_followup_reminder`

## Usage

```bash
python3 simulators/crm_simulator.py --list
python3 simulators/crm_simulator.py --scenario gmail_starlink_payment_issue
python3 simulators/crm_simulator.py --scenario whatsapp_booking_lead --format telegram
python3 simulators/crm_simulator.py --scenario email_followup_reminder --format json --export /tmp/demo.json
python3 simulators/crm_simulator.py --session client_demo --output /tmp/client_demo.md --export /tmp/client_demo.json
python3 simulators/crm_simulator.py --session puente_email_digest,puente_client_demo_bridge --with-external
python3 simulators/crm_simulator.py --session zira_demo --output /tmp/zira_demo.md
python3 simulators/send_zira_menu.py
python3 simulators/zira_bot.py --menu
python3 simulators/zira_bot.py
bash simulators/run_zira_service.sh
```

## Next steps

- Add more scenarios from real CRM files.
- Wire Telegram output to the actual bot.
- Add voice generation when the presentation script is ready.
- Turn the session output into a small HTML or mobile-friendly demo page.
- Keep extending Zira with more intents and photo post-processing steps.
- Run Zira as a service when you want continuous testing with Telegram updates.
