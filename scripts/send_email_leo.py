#!/usr/bin/env python3
"""Send email to both of Leo's emails."""
import sys
sys.path.insert(0, '/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3')
from crm.connectors import GmailConnector

def main():
    gmail = GmailConnector()
    
    subject = "🚀 Sitio web de Rancho Raíz — ya está online"
    
    body = """Hola Leo,

El sitio web de Rancho Raíz ya está funcionando. Te cuento rápido lo que tenemos:

🌐 WEB PÚBLICA
https://oficinabarreal.github.io/rancho-raiz-zira/

Ahí están todas las habitaciones con sus precios, servicios, galería y contacto.
Cuando alguien toca "Reservar" o "Consultar" el mensaje llega directo al WhatsApp de Ayelén (+54 9 11 5959-5869).

🔧 PANEL ADMIN
https://oficinabarreal.github.io/rancho-raiz-zira/admin/
Contraseña: rancho

Desde el admin pueden ver toda la info cargada: precios, servicios, promociones, configuración. Es un panel de lectura para que chequeen que todo esté bien.

📝 CÓMO SE ACTUALIZA
No hay que tocar código. Todo se maneja desde una planilla de Google Sheets:
https://docs.google.com/spreadsheets/d/1dd2sVgDAHPITFcE83QGP00eTNs8qiv1pFT3PmJaNikI/edit

Cada 30 minutos el sitio se actualiza solo con lo que carguen ahí.
Si quieren actualizar al toque, me avisan y lo disparo manualmente.

✅ COSAS PARA REVISAR
- Los precios de las cabañas los saqué del chat de WhatsApp del grupo, pero revisalos en el admin o en la web a ver si están en un rango correcto. Si hay que ajustar algo, se cambia en la planilla.
- Faltan subir fotos reales del lugar — cuando tengan algunas lindas las agregamos al toque.
- Después vamos afinando detalles de a poco.

Cualquier cosa me dicen y la vamos puliendo.

Saludos,
Diego"""

    for to in ["ramonleandrotello@gmail.com", "oficinabarreal@gmail.com"]:
        print(f"Sending to {to}...", end=" ")
        result = gmail.send_message(to=to, subject=subject, body_text=body)
        if result.ok:
            print(f"✅ OK (id: {result.data.get('message_id', '?')})")
        else:
            print(f"❌ {result.error}")

if __name__ == "__main__":
    main()
