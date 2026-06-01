# ROADMAP — Asistente Personal CRM Rancho Raíz

## 📌 Contexto
Esta carpeta `asistente/` encapsula un asistente personal para automatizar tareas del CRM Rancho Raíz, ofreciendo conectores genéricos para Gmail, Calendar, Drive, Sheets, Telegram e Instagram. Los flujos específicos (ej: factura) se construyen combinando estas habilidades.

## ✅ Logros (hoy)
- **Extracción de Gmail vía API**: Se recuperó un correo del 12/05/2026 dirigido a `alejandro.beltran@foraco.com` con etiqueta CRM.
- **Envío de correos con adjuntos**: Implementado en `mail_utils.py` mediante Gmail API (multipart).
- **Bot de Telegram**: `telegram_bot.py` escucha comandos (`/start`, `/emails`, `/status`) y utiliza los conectores.
- **Arquitectura por habilidades**: Conectores organizados en `google/`, `telegram/`, `instagram/` con `__init__.py` y re-exportaciones.
- **Ejemplo completo (factura)**: Workflow que genera factura PDF y la envía por email, disponible en `examples/`.
- **Portabilidad**: Los scripts usan rutas relativas y deben ejecutarse como módulos (`python -m`) desde la raíz.

## 📂 Estructura de archivos
```
asistente/
├── __init__.py
├── AGENT.md
├── ROADMAP.md
├── mail_utils.py
│
├── google/
│   ├── __init__.py
│   ├── gmail.py
│   ├── calendar.py
│   ├── sheets.py
│   └── drive.py
│
├── telegram/
│   ├── __init__.py
│   ├── telegram.py
│   └── telegram_bot.py
│
├── instagram/
│   ├── __init__.py
│   └── instagram.py
│
└── examples/
    ├── generar_pdf.py
    ├── enviar_pdf.py
    ├── factura_alejandro_beltran.txt
    └── factura_alejandro_beltran.pdf
```

## 🔮 Próximos pasos (futuro del asistente)
- **Ampliación de comandos del bot**: Añadir `/send`, `/drive upload`, `/calendar add`, etc., para cubrir más acciones genéricas.
- **Scheduler**: Automatizar tareas repetitivas (ej: resumen diario de correos no leídos).
- **CLI unificada**: Comando `asistente/run --task <habilidad> --args ...`.
- **Logs estructurados**: Archivo `asistente.log` con trazabilidad.
- **Rate limits y reintentos**: Manejo robusto de límites de API.
- **Gestión de .env**: Cargar automáticamente variables de entorno (CRM_TG_TOKEN, etc.).
- **Más integraciones**: WhatsApp, Facebook, etc.

## 📋 Cómo usar (rápido)
```bash
cd /data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3
python -m asistente.telegram.telegram_bot   # Inicia el bot
```
Comandos del bot: `/start`, `/emails [query]`, `/status`.

Para usar conectores en scripts:
```python
from asistente.google.gmail import GmailConnector
gmail = GmailConnector()
...
```

Ejemplos completos (factura) en `asistente/examples/`.

## ⚙️ Requisitos
Dependencias Python:
- google-api-python-client
- google-auth-oauthlib
- fpdf2 (solo para ejemplos)
- python-telegram-bot

Credenciales: `CREDENCIALES.md` y `crm_state/.google_token.json` en raíz. Token de Telegram en variable de entorno `TELEGRAM_BOT_TOKEN` o `CRM_TG_TOKEN` (también admitido en `.env`).

## 🧭 Dirección
El asistente busca ser una caja de herramientas modular para el día a día de Rancho Raíz, con conectores reutilizables y un bot de Telegram como capa de control. Cada nuevo requerimiento puede salvarse como un skill o como un ejemplo, y el bot puede extenderse para desencadenar cualquier acción a través de comandos simples.

**Para agentes:** La entrada principal está en AGENT.md.