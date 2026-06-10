"""
Pool de escenarios para simulación de conversaciones diarias.
Cada escenario es una conversación completa con emojis, timestamps relativos,
y metadatos de plataforma.

Formato:
    ESCENARIOS: list[dict]
        id: str                — identificador único
        plataforma: str        — "instagram" | "whatsapp" | "whatsapp_grupo"
        titulo: str            — título visible de la conversación
        descripcion: str       — contexto breve
        participantes: dict    — {nombre: {tipo, inicial, color}}
        inicia: str            — hora de inicio "HH:MM"
        duracion_min: int      — duración total de la conversación en minutos
        mensajes: list[dict]   — {de, texto, hora_offset_min}
"""

ESCENARIOS = [
    # ═══════════════════════════════════════════════
    # DÍA 1 — ESCENARIOS PRINCIPALES
    # ═══════════════════════════════════════════════

    # ── 1. Instagram: Lead cálido ──
    {
        "id": "insta_lead_calido",
        "agente": "Sira",
        "plataforma": "instagram",
        "titulo": "💬 Lead cálido desde Instagram",
        "descripcion": "Martina descubre la cabaña en Instagram, Sira la atiende con calidez y deriva a WhatsApp.",
        "participantes": {
            "Sira": {"tipo": "bot", "inicial": "S", "color": "#e0115f"},
            "Martina": {"tipo": "lead", "inicial": "M", "color": "#5856d6"},
        },
        "inicia": "10:30",
        "duracion_min": 8,
        "mensajes": [
            {"de": "Martina", "texto": "Hola! Vi las fotos de la cabaña en IG, es una locura 😍"},
            {"de": "Sira",   "texto": "Hola Martina! Sí, la Cabaña del Cerro es un sueño 🏔️ Gracias por escribir!"},
            {"de": "Martina","texto": "Estamos viendo con mi novio para ir en enero. Tiene pileta?"},
            {"de": "Sira",   "texto": "Sí! Tiene pileta climatizada con vista a la cordillera 🤩 Te paso más fotos por WhatsApp si querés"},
            {"de": "Martina","texto": "Dale, pasame!"},
            {"de": "Sira",   "texto": "Acá te dejo el link de Ayelén que te pasa todos los detalles con fotos y precios → wa.link/ranchoraiz"},
            {"de": "Martina","texto": "Gracias! Ahí le escribo 🙌"},
            {"de": "Sira",   "texto": "Perfecto! Cualquier cosa acá estoy 🫶"},
        ],
    },

    # ── 2. WhatsApp: Consulta disponibilidad ──
    {
        "id": "wsp_disponibilidad",
        "agente": "Sira",
        "plataforma": "whatsapp",
        "titulo": "📱 Consulta de disponibilidad",
        "descripcion": "Carlos consulta por enero, Sira responde con info y precios.",
        "participantes": {
            "Sira": {"tipo": "bot", "inicial": "S", "color": "#005c4b"},
            "Carlos": {"tipo": "lead", "inicial": "C", "color": "#5e5ce6"},
        },
        "inicia": "11:00",
        "duracion_min": 12,
        "mensajes": [
            {"de": "Carlos","texto": "Hola, quería consultar disponibilidad para la primera quincena de enero"},
            {"de": "Sira",   "texto": "Hola Carlos! 👋 Tenemos disponibilidad la semana del 4 al 11 de enero. Te interesa?"},
            {"de": "Carlos","texto": "Sí, para 2 adultos. Cuál es el precio por noche?"},
            {"de": "Sira",   "texto": "Genial! Para 2 personas está $95.000 por noche con desayuno incluido 🥐"},
            {"de": "Sira",   "texto": "La Cabaña del Cerro tiene capacidad hasta 5 personas. Si vienen más, consultame precios!"},
            {"de": "Carlos","texto": "Me parece bien. Cómo hago para reservar?"},
            {"de": "Sira",   "texto": "Te paso con Ayelén que gestiona las reservas. Un toque y te conecto! 🤝"},
        ],
    },

    # ── 3. WhatsApp: Ayelén toma la reserva ──
    {
        "id": "wsp_ayelen_reserva",
        "agente": "Ayelén",
        "plataforma": "whatsapp",
        "titulo": "📋 Ayelén confirma la reserva",
        "descripcion": "Ayelén toma el caso, confirma detalles y gestiona el pago de la seña.",
        "participantes": {
            "Ayelén": {"tipo": "admin", "inicial": "A", "color": "#25d366"},
            "Carlos": {"tipo": "lead", "inicial": "C", "color": "#5e5ce6"},
        },
        "inicia": "11:30",
        "duracion_min": 15,
        "mensajes": [
            {"de": "Ayelén","texto": "Hola Carlos! Soy Ayelén, encargada de reservas. Sira me pasó tu consulta 😊"},
            {"de": "Carlos","texto": "Hola! Sí, quería reservar la semana del 4 al 11 de enero"},
            {"de": "Ayelén","texto": "Perfecto! Déjame confirmar:\n🏡 Cabaña del Cerro\n📅 4 al 11 de enero\n👥 2 adultos\n\nEs correcto?"},
            {"de": "Carlos","texto": "Sí, exacto"},
            {"de": "Ayelén","texto": "Perfecto! El proceso es así:\n💰 Seña del 30% por transferencia\n💵 Resto en efectivo al llegar\n\nTe paso los datos de la cuenta?"},
            {"de": "Carlos","texto": "Sí, dale"},
            {"de": "Ayelén","texto": "✅ Alias: rancho.raiz\n💳 MP: +54 9 11 5959-5869"},
            {"de": "Ayelén","texto": "Me avisás cuando hagas la transferencia y te confirmo todo! 🙌"},
            {"de": "Carlos","texto": "Ahí va, ya la hice. Te paso el comprobante"},
            {"de": "Ayelén","texto": "Recibido ✅ Te mando la confirmación en seguida!"},
        ],
    },

    # ── 4. WhatsApp Grupo: Aviso al equipo ──
    {
        "id": "wsp_grupo_aviso",
        "agente": "",
        "plataforma": "whatsapp_grupo",
        "titulo": "👥 Grupo Rancho — Nueva reserva",
        "descripcion": "Ayelén avisa al equipo que llega una reserva. Coordinación de limpieza y recepción.",
        "participantes": {
            "Ayelén": {"tipo": "admin", "inicial": "A", "color": "#25d366"},
            "Leo":    {"tipo": "owner", "inicial": "L", "color": "#f7c948"},
            "Diego":  {"tipo": "ops", "inicial": "D", "color": "#5ac8fa"},
            "Chiqui": {"tipo": "staff", "inicial": "C", "color": "#ff6482"},
        },
        "inicia": "12:00",
        "duracion_min": 10,
        "mensajes": [
            {"de": "Ayelén","texto": "📋 *NUEVA RESERVA CONFIRMADA*\nCarlos — Cabaña del Cerro\n4 al 11 de enero — 2 adultos\nSeña recibida ✅"},
            {"de": "Chiqui","texto": "Anotado! Dejo la cabaña impecable el 3 a la tarde 🙌"},
            {"de": "Ayelén","texto": "Gracias Chiqui! Sí, el 3 que quede lista"},
            {"de": "Leo",   "texto": "👍 Bien. Diego, te encargás de recibirlos el 4?"},
            {"de": "Diego", "texto": "Dale. Les doy la bienvenida y entrego llaves. Check-in desde las 14?"},
            {"de": "Ayelén","texto": "Exacto! Check-in desde las 14. Les pasé mi contacto por si necesitan algo"},
            {"de": "Leo",   "texto": "Perfecto. Cualquier cosa me avisan"},
        ],
    },

    # ── 5. WhatsApp: Leo a Diego ──
    {
        "id": "wsp_leo_diego_preparacion",
        "agente": "Leo",
        "plataforma": "whatsapp",
        "titulo": "🔧 Leo asigna preparación a Diego",
        "descripcion": "Leo confirma con Diego los preparativos para la llegada de los huéspedes.",
        "participantes": {
            "Leo":   {"tipo": "owner", "inicial": "L", "color": "#f7c948"},
            "Diego": {"tipo": "ops", "inicial": "D", "color": "#5ac8fa"},
        },
        "inicia": "12:15",
        "duracion_min": 7,
        "mensajes": [
            {"de": "Leo",   "texto": "Diego, la Cabaña del Cerro para el 4. Dejá todo listo"},
            {"de": "Leo",   "texto": "Revisá pileta, calefacción, y que esté todo funcionando"},
            {"de": "Diego", "texto": "Dale, mañana voy a hacer el recorrido completo"},
            {"de": "Diego", "texto": "Faltan las llaves nuevas?"},
            {"de": "Leo",   "texto": "Sí, mandé a hacer duplicado. El miércoles las tenés"},
            {"de": "Diego", "texto": "Perfecto, entonces el 4 los recibo yo. Les paso el contacto de Ayelén por cualquier cosa"},
            {"de": "Leo",   "texto": "Bien ahí. Cualquier problema me avisás"},
        ],
    },

    # ── 6. WhatsApp: Bienvenida al huésped ──
    {
        "id": "wsp_bienvenida_guest",
        "agente": "Sira",
        "plataforma": "whatsapp",
        "titulo": "🏡 Sira da la bienvenida al huésped",
        "descripcion": "Sira envía el mensaje automático de bienvenida con toda la información de la estadía.",
        "participantes": {
            "Sira":   {"tipo": "bot", "inicial": "S", "color": "#005c4b"},
            "Carlos": {"tipo": "lead", "inicial": "C", "color": "#5e5ce6"},
        },
        "inicia": "14:00",
        "duracion_min": 5,
        "mensajes": [
            {"de": "Sira", "texto": "Hola Carlos! Te damos la bienvenida a Rancho Raíz 🏔️🫶"},
            {"de": "Sira", "texto": "Te compartimos info útil para tu estadía:"},
            {"de": "Sira", "texto": "📍 *Check-in:* desde las 14hs\n📍 *Check-out:* 10hs\n🔑 Te recibe Diego en la entrada\n🅿️ Estacionamiento cubierto\n🥐 Desayuno de 8 a 10:30 en el quincho"},
            {"de": "Sira", "texto": "Cualquier cosa durante tu estadía, escribime acá o llamá a Ayelén al +54 9 11 5959-5869"},
            {"de": "Carlos","texto": "Perfecto, gracias! 🎉"},
            {"de": "Sira", "texto": "Que disfrutes la experiencia! 🙌🌄"},
        ],
    },

    # ═══════════════════════════════════════════════
    # DÍA 2 — ESCENARIOS FRÍOS / ALTERNATIVOS
    # ═══════════════════════════════════════════════

    # ── 7. Instagram: Lead frío ──
    {
        "id": "insta_lead_frio",
        "agente": "Sira",
        "plataforma": "instagram",
        "titulo": "❄️ Lead frío desde Instagram",
        "descripcion": "Florencia respone con poco interés, Sira mantiene la calidez y deja el link de WhatsApp.",
        "participantes": {
            "Sira":      {"tipo": "bot", "inicial": "S", "color": "#e0115f"},
            "Florencia": {"tipo": "lead", "inicial": "F", "color": "#ff9500"},
        },
        "inicia": "15:00",
        "duracion_min": 6,
        "mensajes": [
            {"de": "Sira",      "texto": "Hola! Vi que te gustó la foto de la Cabaña del Cerro 🏔️ Tenés ganas de conocerla?"},
            {"de": "Florencia", "texto": "Holi, sí lindo lugar"},
            {"de": "Sira",      "texto": "Es un paraíso! Estamos con precios especiales para enero ⭐"},
            {"de": "Florencia", "texto": "Ah mira, puede ser"},
            {"de": "Sira",      "texto": "Si querés te paso más info por WhatsApp sin compromiso! Link directo de Ayelén → wa.link/ranchoraiz"},
            {"de": "Florencia", "texto": "Dale, lo veo"},
            {"de": "Sira",      "texto": "Por supuesto! Cualquier consulta estoy acá 🫶"},
        ],
    },

    # ── 8. WhatsApp: Follow-up post-consulta ──
    {
        "id": "wsp_followup_silencio",
        "agente": "Sira",
        "plataforma": "whatsapp",
        "titulo": "🔄 Follow-up a lead silencioso",
        "descripcion": "Pablo pidió precios y quedó en silencio. Sira hace un follow-up amable al día siguiente.",
        "participantes": {
            "Sira":  {"tipo": "bot", "inicial": "S", "color": "#005c4b"},
            "Pablo": {"tipo": "lead", "inicial": "P", "color": "#af52de"},
        },
        "inicia": "09:30",
        "duracion_min": 5,
        "mensajes": [
            {"de": "Pablo","texto": "Hola, me pasan precio para febrero?"},
            {"de": "Sira",  "texto": "Hola Pablo! 😊 Para febrero tenemos disponible toda la primera quincena. La Cabaña del Cerro está $95k por noche para 2 personas."},
            {"de": "Pablo","texto": "Gracias, lo veo y te confirmo"},
            # Siguiente día, follow-up
            {"de": "Sira",  "texto": "Hola Pablo! 👋 Quería saber si te quedó alguna duda sobre los precios o fechas. Estoy acá para ayudarte!"},
            {"de": "Pablo","texto": "Gracias! Estamos viendo fechas con mi pareja, en estos días te confirmo"},
            {"de": "Sira",  "texto": "Perfecto! Cuando quieras me escribís. Acá está Ayelén también para ayudarte con la reserva 🤝"},
        ],
    },

    # ── 9. Instagram: Lead pregunta actividades ──
    {
        "id": "insta_actividades",
        "agente": "Sira",
        "plataforma": "instagram",
        "titulo": "🏔️ Lead pregunta sobre actividades",
        "descripcion": "Un lead consulta sobre qué hacer cerca de la posada. Sira recomienda actividades.",
        "participantes": {
            "Sira":    {"tipo": "bot", "inicial": "S", "color": "#e0115f"},
            "Lucía":   {"tipo": "lead", "inicial": "L", "color": "#34c759"},
        },
        "inicia": "17:30",
        "duracion_min": 8,
        "mensajes": [
            {"de": "Lucía", "texto": "Hola! Está buena esa cabaña. Hay algo para hacer cerca?"},
            {"de": "Sira", "texto": "Hola Lucía! Sí, Barreal tiene un montón de actividades 🎯 Cabalgatas, trekking, avistaje de estrellas, y el famoso Cerro Mercedario"},
            {"de": "Lucía", "texto": "Uh genial! Y para comer?"},
            {"de": "Sira", "texto": "Hay varias opciones ricas en el pueblo 🍝 Te paso recomendaciones por WhatsApp si querés!"},
            {"de": "Sira", "texto": "Acá el link de Ayelén que te cuenta todo → wa.link/ranchoraiz"},
            {"de": "Lucía", "texto": "Dale, gracias!"},
        ],
    },

    # ── 10. WhatsApp: Consulta de último momento ──
    {
        "id": "wsp_ultimo_momento",
        "agente": "Sira",
        "plataforma": "whatsapp",
        "titulo": "⚡ Consulta de último momento",
        "descripcion": "Un lead pregunta para el finde actual. Sira y Ayelén coordinan rápido.",
        "participantes": {
            "Sira":   {"tipo": "bot", "inicial": "S", "color": "#005c4b"},
            "Ayelén": {"tipo": "admin", "inicial": "A", "color": "#25d366"},
            "Jorge":  {"tipo": "lead", "inicial": "J", "color": "#ff2d55"},
        },
        "inicia": "19:00",
        "duracion_min": 10,
        "mensajes": [
            {"de": "Jorge","texto": "Hola! Para este finde tienen algo?"},
            {"de": "Sira",  "texto": "Hola Jorge! Déjame consultar disponibilidad y te confirmo ya mismo ⏳"},
            {"de": "Sira",  "texto": "Tenés la Cabaña del Cerro libre justo para este finde! Check-in viernes, check-out domingo. 2 noches."},
            {"de": "Jorge","texto": "Genial! Cuanto sale?"},
            {"de": "Sira",  "texto": "$190.000 las 2 noches para 2 personas. Te paso con Ayelén para coordinar la reserva!"},
            {"de": "Ayelén","texto": "Hola Jorge! Te confirmo la Cabaña del Cerro para este finde. Te parece?"},
            {"de": "Jorge","texto": "Dale, reservado!"},
            {"de": "Ayelén","texto": "✅ Te mando los datos de pago de la seña al toque"},
        ],
    },

    # ── 11. WhatsApp Grupo: Cambio de reserva ──
    {
        "id": "wsp_grupo_cambio",
        "agente": "",
        "plataforma": "whatsapp_grupo",
        "titulo": "🔄 Cambio en reserva confirmada",
        "descripcion": "Ayelén avisa que cambió la fecha de una reserva. El equipo se reacomoda.",
        "participantes": {
            "Ayelén": {"tipo": "admin", "inicial": "A", "color": "#25d366"},
            "Leo":    {"tipo": "owner", "inicial": "L", "color": "#f7c948"},
            "Diego":  {"tipo": "ops", "inicial": "D", "color": "#5ac8fa"},
        },
        "inicia": "08:00",
        "duracion_min": 8,
        "mensajes": [
            {"de": "Ayelén","texto": "⚠️ *ACTUALIZACIÓN*\nLa reserva de Martina pasó del 15/01 al 22/01. Misma cabaña, mismos huéspedes."},
            {"de": "Leo",   "texto": "OK, gracias por avisar. Diego, ajustá el cronograma?"},
            {"de": "Diego", "texto": "Dale, sin problema. La semana del 15 queda libre entonces."},
            {"de": "Ayelén","texto": "Exacto! Así que si llega otra consulta para esa semana, está disponible"},
            {"de": "Leo",   "texto": "Bien. Me sirve porque justo preguntaron por esas fechas"},
        ],
    },

    # ── 12. WhatsApp: Post-estadía agradecimiento ──
    {
        "id": "wsp_post_estadia",
        "agente": "Sira",
        "plataforma": "whatsapp",
        "titulo": "✨ Seguimiento post-estadía",
        "descripcion": "Sira escribe al día siguiente del check-out para agradecer y pedir feedback.",
        "participantes": {
            "Sira":   {"tipo": "bot", "inicial": "S", "color": "#005c4b"},
            "Carlos": {"tipo": "lead", "inicial": "C", "color": "#5e5ce6"},
        },
        "inicia": "10:00",
        "duracion_min": 5,
        "mensajes": [
            {"de": "Sira",  "texto": "Hola Carlos! Espero que hayan descansado 🏔️ Queríamos saber cómo estuvo todo en la cabaña"},
            {"de": "Carlos","texto": "Todo perfecto! La cabaña es hermosa, volvemos seguro 🙌"},
            {"de": "Sira",  "texto": "Qué alegría! 🫶 Nos ayuda un montón si nos dejan una reseña en Google Maps o IG"},
            {"de": "Sira",  "texto": "Los esperamos de nuevo cuando quieran! 🏡✨"},
            {"de": "Carlos","texto": "Dale, ahora dejamos reseña! Gracias por todo"},
        ],
    },
]


# ═══════════════════════════════════════════════════════════
# JORNADA COMPLETA — Una historia conectada de principio a fin
# ═══════════════════════════════════════════════════════════
# Lucía descubre Rancho Raíz en Instagram → WhatsApp → Reserva
# → Coordinación del equipo → Bienvenida con alerta climática
# → Seguimiento durante estadía → Post-estadía

JORNADA_COMPLETA = [
    # ── Capítulo 1: Instagram — Captura ──
    {
        "capitulo": 1,
        "id": "j_captura_instagram",
        "plataforma": "instagram",
        "titulo": "🎯 Captura — Sira detecta un lead en Instagram",
        "contexto": "Lucía dio like a una foto de la Cabaña del Cerro. Sira activa la captura de leads.",
        "etapa": "Captura",
        "icono": "🎯",
        "fecha": None,  # mismo día
        "agente": "Sira",
        "participantes": {
            "Sira": {"tipo": "bot", "inicial": "S", "color": "#e0115f"},
            "Lucía": {"tipo": "lead", "inicial": "L", "color": "#34c759"},
        },
        "inicia": "10:30",
        "duracion_min": 5,
        "mensajes": [
            {"de": "Sira",  "texto": "Hola Lucía! Vi que te gustó la foto de la Cabaña del Cerro 🏔️ Tenés ganas de conocerla?"},
            {"de": "Lucía", "texto": "Hola! Sí, está hermosa. Tenés disponibilidad para febrero?"},
            {"de": "Sira",  "texto": "Gracias! Sí, tenemos disponible la primera semana de febrero. Es un paraíso 🤩"},
            {"de": "Sira",  "texto": "Te cuento más por WhatsApp que acá en IG no puedo pasar tanta info! Este es el link directo → wa.link/ranchoraiz"},
            {"de": "Lucía", "texto": "Dale, ahora escribo! Gracias 🙌"},
        ],
    },

    # ── Capítulo 2: WhatsApp — Contacto ──
    {
        "capitulo": 2,
        "id": "j_contacto_whatsapp",
        "plataforma": "whatsapp",
        "titulo": "💬 Contacto — Lucía llega por WhatsApp",
        "contexto": "Lucía usa el link que Sira le pasó por Instagram. Sira la recibe con la información.",
        "etapa": "Contacto",
        "icono": "💬",
        "fecha": None,
        "agente": "Sira",
        "participantes": {
            "Sira": {"tipo": "bot", "inicial": "S", "color": "#005c4b"},
            "Lucía": {"tipo": "lead", "inicial": "L", "color": "#34c759"},
        },
        "inicia": "11:00",
        "duracion_min": 10,
        "mensajes": [
            {"de": "Lucía", "texto": "Holi! Soy Lucía, me habló Sira por Instagram 😊"},
            {"de": "Sira",  "texto": "Hola Lucía! Bienvenida 🤗 Te confirmo: la Cabaña del Cerro está disponible del 1 al 8 de febrero. Son 2 personas?"},
            {"de": "Lucía", "texto": "Sí, con mi pareja!"},
            {"de": "Sira",  "texto": "Perfecto! Para 2 personas está $95.000 por noche con desayuno incluido 🥐 La cabaña tiene capacidad hasta 5 si en otro momento vienen más."},
            {"de": "Lucía", "texto": "Genial, nos re sirve. Cómo hacemos para reservar?"},
            {"de": "Sira",  "texto": "Te paso con Ayelén que gestiona las reservas. Ella te va a tomar los datos y coordinar el pago de la seña. Un toque!"},
        ],
    },

    # ── Capítulo 3: WhatsApp Ayelén — Reserva ──
    {
        "capitulo": 3,
        "id": "j_reserva_ayelen",
        "plataforma": "whatsapp",
        "titulo": "📋 Reserva — Ayelén confirma con Lucía",
        "contexto": "Ayelén toma el caso. Confirma fechas, huéspedes y gestiona la seña.",
        "etapa": "Reserva",
        "icono": "📋",
        "fecha": None,
        "agente": "Ayelén",
        "participantes": {
            "Ayelén": {"tipo": "admin", "inicial": "A", "color": "#25d366"},
            "Lucía":  {"tipo": "lead", "inicial": "L", "color": "#34c759"},
        },
        "inicia": "11:30",
        "duracion_min": 15,
        "mensajes": [
            {"de": "Ayelén","texto": "Hola Lucía! Soy Ayelén, encargada de reservas. Sira me pasó tu consulta 😊"},
            {"de": "Lucía", "texto": "Hola! Sí, queremos reservar la Cabaña del Cerro del 1 al 8 de febrero para 2 personas"},
            {"de": "Ayelén","texto": "Perfecto! Te confirmo:\n🏡 Cabaña del Cerro\n📅 1 al 8 de febrero\n👥 2 adultos\nTodo ok?"},
            {"de": "Lucía", "texto": "Sí, perfecto!"},
            {"de": "Ayelén","texto": "Genial! El proceso es:\n💰 Seña del 30% por transferencia\n💵 Resto en efectivo al llegar\n\nTe paso los datos?"},
            {"de": "Lucía", "texto": "Dale!"},
            {"de": "Ayelén","texto": "✅ Alias: rancho.raiz\n💳 MP: +54 9 11 5959-5869\n\nMe avisás cuando hagas la transferencia?"},
            {"de": "Lucía", "texto": "Ahí va, ya la hice! Te paso comprobante"},
            {"de": "Ayelén","texto": "Recibido y verificado ✅ Reserva confirmada! Te vamos a mandar info antes de la llegada 🙌"},
        ],
    },

    # ── Capítulo 4: WhatsApp Grupo — Coordinación ──
    {
        "capitulo": 4,
        "id": "j_coordinacion_grupo",
        "plataforma": "whatsapp_grupo",
        "titulo": "👥 Coordinación — El equipo se prepara",
        "contexto": "Ayelén avisa al equipo. Chiqui prepara la cabaña, Diego coordina la recepción.",
        "etapa": "Coordinación",
        "icono": "👥",
        "fecha": None,
        "agente": "",
        "participantes": {
            "Ayelén": {"tipo": "admin", "inicial": "A", "color": "#25d366"},
            "Leo":    {"tipo": "owner", "inicial": "L", "color": "#f7c948"},
            "Diego":  {"tipo": "ops", "inicial": "D", "color": "#5ac8fa"},
            "Chiqui": {"tipo": "staff", "inicial": "C", "color": "#ff6482"},
        },
        "inicia": "12:00",
        "duracion_min": 10,
        "mensajes": [
            {"de": "Ayelén","texto": "📋 *NUEVA RESERVA CONFIRMADA*\nLucía — Cabaña del Cerro\n1 al 8 de febrero — 2 adultas\nSeña recibida ✅"},
            {"de": "Chiqui","texto": "Anotado! Dejo la cabaña impecable el 31 de enero 🧹✨"},
            {"de": "Ayelén","texto": "Gracias Chiqui! El 31 a la tarde que quede lista 🙌"},
            {"de": "Leo",   "texto": "👍 Bien. Diego, recibilas el 1 a la tarde?"},
            {"de": "Diego", "texto": "Sí, dale. Check-in a las 14hs. Les doy la bienvenida y les entrego las llaves."},
            {"de": "Ayelén","texto": "Perfecto! Les pasé mi contacto por cualquier cosa. Ya les vamos a mandar la info de bienvenida!"},
        ],
    },

    # ── Capítulo 5: WhatsApp — Bienvenida + Alerta climática ──
    {
        "capitulo": 5,
        "id": "j_bienvenida_clima",
        "plataforma": "whatsapp",
        "titulo": "🏡 Bienvenida con alerta del clima",
        "contexto": "Sira envía la bienvenida con recomendaciones. El pronóstico indica lluvias para el finde de llegada, así que Sira agrega recomendaciones de abrigo y actividades bajo techo.",
        "etapa": "Bienvenida",
        "icono": "🏡",
        "fecha": None,
        "agente": "Sira",
        "participantes": {
            "Sira":  {"tipo": "bot", "inicial": "S", "color": "#005c4b"},
            "Lucía": {"tipo": "lead", "inicial": "L", "color": "#34c759"},
        },
        "inicia": "14:00",
        "duracion_min": 5,
        "mensajes": [
            {"de": "Sira", "texto": "Hola Lucía! Falta poquito para tu llegada a Rancho Raíz 🏔️🎉 Te compartimos info útil:"},
            {"de": "Sira", "texto": "📍 *Check-in:* 14hs | *Check-out:* 10hs\n🔑 Te recibe Diego en la entrada\n🅿️ Estacionamiento cubierto\n🥐 Desayuno de 8 a 10:30 en el quincho"},
            {"de": "Sira", "texto": "⚠️ *ALERTA DEL CLIMA:* Se esperan lluvias para el finde de tu llegada 🌧️ No te preocupes! La cabaña tiene estufa, piletón climatizado y galería cubierta para que disfruten igual."},
            {"de": "Sira", "texto": "🧥 *Recomendación:* Traer ropa de abrigo y calzado impermeable si quieren salir a caminar por Barreal. Los atardeceres post-lluvia son mágicos 🏔️🌅"},
            {"de": "Lucía","texto": "Gracias por avisar! Llevamos algo para cocinar también?"},
            {"de": "Sira", "texto": "La cabaña tiene cocina completa con todo! Si querés, el almacén del pueblo tiene cosas ricas para comprar allá 🥟🛒"},
            {"de": "Sira", "texto": "Cualquier cosa durante tu estadía, acá estoy! Buen viaje 🙌"},
        ],
    },

    # ── Capítulo 6: WhatsApp — Seguimiento durante estadía ──
    {
        "capitulo": 6,
        "id": "j_seguimiento_estadia",
        "plataforma": "whatsapp",
        "titulo": "📱 Seguimiento — Día 3 de la estadía",
        "contexto": "Lucía ya está alojada. Sira hace seguimiento para ver cómo va todo. El clima mejoró.",
        "etapa": "Seguimiento",
        "icono": "📱",
        "fecha": "2026-02-03",  # durante la estadía
        "agente": "Sira",
        "participantes": {
            "Sira":  {"tipo": "bot", "inicial": "S", "color": "#005c4b"},
            "Lucía": {"tipo": "guest", "inicial": "L", "color": "#34c759"},
        },
        "inicia": "10:00",
        "duracion_min": 5,
        "mensajes": [
            {"de": "Sira", "texto": "Hola Lucía! Cómo va todo por la Cabaña del Cerro? 🏔️"},
            {"de": "Lucía","texto": "Increíble! La cabaña es hermosa. Ayer llovió pero igual salimos a conocer Barreal"},
            {"de": "Sira", "texto": "Qué bueno! Sí, ayer pasó un frente. Hoy mejora según el pronóstico, sale el sol ☀️"},
            {"de": "Sira", "texto": "Si el día está lindo, les recomiendo ir a las Dunas de Barreal, está espectacular! También pueden cabalgar en el Valle 🐴"},
            {"de": "Lucía","texto": "Gracias! Justo estábamos viendo qué hacer hoy! Vamos a las dunas 😊"},
            {"de": "Sira", "texto": "Perfecto! Cualquier cosa me escriben. Que lo disfruten 🙌🌄"},
        ],
    },

    # ── Capítulo 7: WhatsApp — Post-estadía ──
    {
        "capitulo": 7,
        "id": "j_post_estadia",
        "plataforma": "whatsapp",
        "titulo": "✨ Post-estadía — Agradecimiento y reseña",
        "contexto": "Lucía ya se fue. Sira agradece y pide reseña. Lucía deja 5 estrellas.",
        "etapa": "Post-estadía",
        "icono": "✨",
        "fecha": "2026-02-09",  # post check-out
        "agente": "Sira",
        "participantes": {
            "Sira":  {"tipo": "bot", "inicial": "S", "color": "#005c4b"},
            "Lucía": {"tipo": "guest", "inicial": "L", "color": "#34c759"},
        },
        "inicia": "10:00",
        "duracion_min": 4,
        "mensajes": [
            {"de": "Sira", "texto": "Hola Lucía! Esperamos que hayan disfrutado la experiencia en Rancho Raíz 🏔️🫶"},
            {"de": "Sira", "texto": "Nos ayuda un montón si nos dejan una reseña en Google Maps o Instagram. Así otros viajeros conocen el lugar!"},
            {"de": "Lucía","texto": "Ya la dejamos en Google! 5 ⭐⭐⭐⭐⭐ Volvemos seguro, nos encantó todo!"},
            {"de": "Sira", "texto": "Gracias Lucía! Nos alegra mucho 🥹 Los esperamos de nuevo cuando quieran. Un abrazo grande! 🏡✨"},
        ],
    },
]


def obtener_jornada_completa():
    """Devuelve la jornada completa ordenada por capítulo."""
    return list(JORNADA_COMPLETA)


def obtener_escenarios_del_dia(fecha=None, cantidad=6):
    """
    Selecciona `cantidad` escenarios del pool de forma determinista
    basada en la fecha. Garantiza al menos 1 Instagram y 1 WhatsApp (no grupo)
    si hay disponibles, para dar variedad visual cada día.
    """
    import hashlib
    from datetime import date, datetime

    if fecha is None:
        fecha = date.today()
    elif isinstance(fecha, str):
        fecha = datetime.strptime(fecha, "%Y-%m-%d").date()

    # Seed determinista basado en la fecha (ordinal)
    seed = fecha.toordinal()
    hashed = hashlib.sha256(str(seed).encode()).hexdigest()

    def mezclar(lista, hash_seed):
        """Fisher-Yates determinista."""
        items = list(lista)
        for i in range(len(items) - 1, 0, -1):
            byte_val = int(hash_seed[(i * 2) % len(hash_seed) : (i * 2 + 2) % len(hash_seed)], 16)
            j = byte_val % (i + 1)
            items[i], items[j] = items[j], items[i]
        return items

    # Separar por plataforma
    igs = [e for e in ESCENARIOS if e["plataforma"] == "instagram"]
    wsps = [e for e in ESCENARIOS if e["plataforma"] == "whatsapp"]
    grupos = [e for e in ESCENARIOS if e["plataforma"] == "whatsapp_grupo"]

    seleccionados = []

    # Garantizar 1 Instagram (si hay)
    if igs:
        ig_ordenados = mezclar(igs, hashed + "ig")
        seleccionados.append(ig_ordenados[0])

    # Garantizar 1 WhatsApp (si hay)
    if wsps:
        wsp_ordenados = mezclar(wsps, hashed + "wsp")
        seleccionados.append(wsp_ordenados[0])

    # Completar con el resto
    restantes = [e for e in ESCENARIOS if e not in seleccionados]
    restantes_mezclados = mezclar(restantes, hashed + "rest")
    faltan = cantidad - len(seleccionados)
    seleccionados.extend(restantes_mezclados[:faltan])

    # Ordenar por hora de inicio
    seleccionados.sort(key=lambda e: e["inicia"])
    return seleccionados
