# Roadmap: hola-3 CRM Automation

## ✅ Completed
- [x] Gmail connector with `list_messages` and `send_message` via `ConnectorResult`
- [x] Telegram bot with `/emails`, `/send`, `/status` commands
- [x] Natural language parsing for Spanish phrases (heuristic + LLM fallback)
- [x] Credential management via `.env` and `CREDENCIALES.md`
- [x] Google OAuth token persistence in `crm_state/.google_token.json`
- [x] Modular structure: `asistente/google/`, `asistente/telegram/`, `crm/connectors/`
- [x] Simulation scripts: `generar_pdf.py`, `enviar_pdf.py`, `informe_diario.py`
- [x] AGENT.md and ROADMAP.md in root and `asistente/` for agent context
- [x] Android notification system via termux-notification for task reminders, API alerts, and process status
- [x] Demo script showcasing notification capabilities

## 🚧 In Progress
- [ ] Hybrid AI routing: local model (OpenCode Zen) → cloud fallback (OpenRouter/NVIDIA)
- [ ] Enhanced NLP: better handling of dates, ranges, and complex queries
- [ ] Web navigation via agent-browser (CUA) for Shizuku-enabled Android
- [ ] Instagram/WhatsApp integration for multi-channel CRM
- [ ] Scheduled jobs (cron) for daily reports and backup workflows
- [ ] Voice input/output via TTS/STX for hands-free operation

## 🎯 Future Goals
- [ ] Full CRM sync: bidirectional Google Sheets ↔ Kommo/Instagram
- [ ] AI-assisted invoice generation from email templates
- [ ] Multi-agent workflow: delegate email triage to specialized subagents
- [ ] Dashboard: real-time metrics via Hermes dashboard
- [ ] Offline-first mode: local queue for actions when network unavailable

## 📅 Timeline
- **Q2 2026**: Core Gmail/Telegram/NLP/Android notifications complete (current)
- **Q3 2026**: Hybrid AI, CUA/web navigation, Instagram integration
- **Q4 2026**: Scheduled jobs, voice I/O, multi-agent workflows
- **2027**: Full CRM sync, invoice AI, dashboard

## 🔧 Maintenance
- Update `.env` with valid API keys when rotating credentials
- Renew Google token via `crm/oauth_capture.py` if expired (checks auto-refresh)
- Monitor Telegram bot logs via `hermes logs -f` or `process(action='log')`
- Test notification system periodically with `python demo_notifications.py`

## ✅ Definition of Done
A feature is complete when:
- Implemented in modular style (connectors in `crm/`, assistants in `asistente/`)
- Covered by simulation or test script
- Documented in AGENT.md/ROADMAP.md
- Safe to run: no hard credentials, clear error handling