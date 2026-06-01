"""
mensajeria — Módulo de mensajería modular y multicanal

Basado en el Zira bot (simulators/zira_bot.py) pero generalizado para
soportar múltiples canales (Telegram, consola, webhook, etc.) con
handlers intercambiables y modos de operación.

═══ Arquitectura ═══

    Channel (Telegram/Console/...)
        │  recibe mensaje entrante
        ▼
    Bot._resolve_user_mode()
        │  determina modo: leads / team / guests
        ▼
    Core Router (mode-aware)
        │  clasifica intent filtrando por modo activo
        ▼
    Handler (tagged by mode)
        │  procesa y genera respuesta(s)
        ▼
    Channel
        envía respuesta(s) al usuario

═══ Modos de operación ═══

    🎯 leads  → Prospectos. Handlers: welcome, faq, prices,
                 availability, reserve, photo, listen, fallback.
    👥 team   → Equipo interno. Handlers: welcome, tasks,
                 schedule, fallback.
    🏡 guests → Huéspedes. Handlers: welcome, assist, reserve,
                 faq, photo, fallback.

    Cada handler declara su set de modos via `modes`.
    Handlers sin modes (set vacío) aplican a todos.

═══ Archivos ═══

    core/
        message.py          — IncomingMessage, OutgoingMessage, IntentResult
        router.py           — IntentRouter (mode-aware classifier)
        handler.py          — BaseHandler abstracto
        state.py            — ConversationState (turns, leads, user modes)
    channels/
        base.py             — BaseChannel abstracto
        telegram.py         — Telegram Bot API
        console.py          — stdin/stdout (testing)
    handlers/
        info.py             — Welcome / menú principal
        faq.py              — Info posada, ubicación, amenities
        pricing.py          — Precios, disponibilidad, reservas
        photos.py           — Subida/procesamiento de fotos
        voice.py            — TTS (edge-tts)
        fallback.py         — Respuesta por defecto
    modes/
        __init__.py         — Package
        registry.py         — MODE_INFO, CHANNEL_MODE, resolve_mode()
    data/
        leads/              — Datos particionados para prospectos
        team/               — Datos particionados para equipo
        guests/             — Datos particionados para huéspedes
    state/                  — Persistencia (turns, leads, users)
    bot.py                  — Orquestador Bot
    main.py                 — CLI entry point
"""
