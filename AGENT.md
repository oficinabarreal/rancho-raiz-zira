# hola-3: CRM Automation for Rancho Raíz

## Overview
This project automates CRM workflows for Rancho Raíz, focusing on integrating Google Workspace (Gmail, Calendar, Sheets, Drive) with Telegram-based interactions and AI-assisted task execution. The system enables voice/text commands via Telegram to trigger actions like invoice generation, email sending, and data retrieval.

## Directory Structure
- `asistente/` - Main AI assistant components (Telegram bot, Gmail connectors, AI parser)
- `crm/` - Core CRM connectors (Gmail, Calendar, Sheets, Drive) with standardized interfaces
- `hybrid/` - Experimental hybrid AI approaches (local + cloud model routing)
- `simulators/` - Test scripts and workflow simulators (invoice generation, daily reports)
- `crm_state/` - Persistent state (Google OAuth tokens, temporary data)
- `CREDENCIALES.md` - Reference for credential variables (not actual secrets)
- `.env` - Environment variables (API keys, tokens - **not committed**)

## Key Features
- **Telegram Bot**: Commands like `/emails`, `/send`, `/status` for Gmail interactions
- **AI-Powered Natural Language**: Interpret Spanish phrases like "dame el último no leido" into Gmail queries
- **Modular Connectors**: Standard `ConnectorResult` interface across Google services
- **Local-First Fallback**: Heuristic parsers ensure offline functionality when LLMs are unavailable
- **Simulation Suite**: Scripts to test workflows without touching real data

## Getting Started
1. Ensure `crm_state/.google_token.json` exists (valid Google OAuth token)
2. Set `CRM_TG_TOKEN` in `.env` (Telegram bot token)
3. Install dependencies: `pip install -r requirements.txt` (if applicable)
4. Run the Telegram bot: `python -m asistente.telegram.telegram_bot`
5. Test commands in Telegram: `/emails dame el ultimo no leido`

## Conventions
- All scripts executed via `python -m <module>` from project root to avoid path conflicts
- Credentials never hardcoded; use `.env` or `CREDENCIALES.md` as reference
- Connectors return `ConnectorResult` with `.ok` (bool) and `.data` (dict)
- Telegram bot interprets natural language with LLM fallback to heuristic parser

## Safety
- Never commit `.env` with real tokens
- Google token stored in `crm_state/` (gitignored)
- External actions (email sends) require explicit confirmation in production flows