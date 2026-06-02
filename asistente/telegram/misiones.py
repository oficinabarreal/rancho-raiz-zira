"""
Misiones de capacitación Zira — Telegram Inline Keyboard

Agrega al telegram_bot.py existente para mostrar botones de misiones.

Uso: el usuario escribe /misiones y Zira muestra los botones.
Al tocar un botón, Zira explica la misión paso a paso.
"""

MISIONES = {
    "mision1": {
        "nombre": "🛏️ Llegada del huésped",
        "emoji": "🛏️",
        "historia": "Un cliente escribe desde WhatsApp preguntando por una habitación para el fin de semana largo.",
        "tarea": "Escribime 'soy un cliente' y preguntame disponibilidad para el 20 de julio, 2 personas, 3 noches.",
        "aprendes": "Cómo entra la información al CRM sin que nadie tipee nada. Zira detecta el lead, lo clasifica y lo registra automáticamente.",
        "evaluacion": [
            "¿Zira entendió bien lo que pediste?",
            "¿El resultado te sirve o necesitás algo distinto?",
            "¿Cómo explicarías esto a Leo o Ayelén?"
        ]
    },
    "mision2": {
        "nombre": "📅 Se acerca la factura",
        "emoji": "📅",
        "historia": "Estás en la posada y olvidaste que la luz vence la semana que viene.",
        "tarea": "No hagas nada. Esperá el recordatorio automático de mañana a las 10am por email y Telegram.",
        "aprendes": "Zira no espera que te acordés. Él se acuerda por vos y te avisa sin que le pidas nada.",
        "evaluacion": [
            "¿Te llegó el recordatorio?",
            "¿La información era clara?",
            "¿Preferís otro canal o formato?"
        ]
    },
    "mision3": {
        "nombre": "💡 Buzón de ideas",
        "emoji": "💡",
        "historia": "Se te ocurre algo que mejorarías de la posada o del CRM.",
        "tarea": "Creá un documento nuevo en Google Drive con 'idea', 'sugerencia' o 'propuesta' en el título y escribí tu idea.",
        "aprendes": "Cómo sugerir cambios al CRM sin tener que pedirle a nadie. Zira lo detecta solo desde tu Drive.",
        "evaluacion": [
            "¿Zira detectó tu documento?",
            "¿Qué tan rápido apareció en el buzón?",
            "¿Usarías esto seguido o preferís otro método?"
        ]
    },
    "mision4": {
        "nombre": "📊 Informe semanal",
        "emoji": "📊",
        "historia": "Terminó la semana y querés ver qué pasó.",
        "tarea": "Abrí el dashboard: https://oficinabarreal.github.io/rancho-raiz-zira/",
        "aprendes": "No necesitás preguntarle a nadie cómo viene la cosa. Abrís el link y ves todo: facturas, sistema, simulaciones.",
        "evaluacion": [
            "¿Pudiste abrir el dashboard?",
            "¿Entendés lo que muestra cada sección?",
            "¿Agregarías algo que no está?"
        ]
    }
}


def teclado_misiones():
    """Genera el inline keyboard de Telegram para mostrar las misiones."""
    return {
        "inline_keyboard": [
            [
                {"text": MISIONES["mision1"]["emoji"] + " " + MISIONES["mision1"]["nombre"], "callback_data": "mision:1"},
                {"text": MISIONES["mision2"]["emoji"] + " " + MISIONES["mision2"]["nombre"], "callback_data": "mision:2"},
            ],
            [
                {"text": MISIONES["mision3"]["emoji"] + " " + MISIONES["mision3"]["nombre"], "callback_data": "mision:3"},
                {"text": MISIONES["mision4"]["emoji"] + " " + MISIONES["mision4"]["nombre"], "callback_data": "mision:4"},
            ],
            [
                {"text": "❓ ¿Cómo funciona esto?", "callback_data": "mision:ayuda"},
            ]
        ]
    }


def texto_mision(mision_id):
    """Devuelve el texto formateado de una misión."""
    m = MISIONES.get(f"mision{mision_id}")
    if not m:
        return "Misón no encontrada."
    
    partes = [
        f"*{m['nombre']}*",
        "",
        f"📖 *Historia:* {m['historia']}",
        "",
        f"🎯 *Tu tarea:* {m['tarea']}",
        "",
        f"💡 *Qué aprendés:* {m['aprendes']}",
        "",
        "📝 *Después respóndeme:*",
    ]
    for i, p in enumerate(m["evaluacion"], 1):
        partes.append(f"  {i}. {p}")
    partes.extend([
        "",
        "🤖 *Listo para empezar?* Decime 'arranco'",
    ])
    return "\n".join(partes)


TEXTO_AYUDA = """
*🤖 Zira — Capacitación Guiada*

Esto es un juego con misiones. Cada misión te enseña una parte del CRM.
No hay errores, solo aprendizaje mutuo: vos entendés cómo funciona Zira,
Zira entiende cómo trabajás vos.

*Cómo funciona:*
1. Elegí una misión tocando un botón
2. Leé la historia y hacé la tarea
3. Respondé 3 preguntas simples después
4. Pasamos a la siguiente

Al completar las 4 misiones, Zira se ajusta a tu forma de trabajar.
"""
