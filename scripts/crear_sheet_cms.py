"""Create the Google Sheet CMS for Rancho Raíz web admin."""
import sys
sys.path.insert(0, '/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3')
from crm.google_auth import get_service

svc = get_service('sheets', 'v4', 'sheets')
if not svc:
    print('ERROR: No sheets service')
    sys.exit(1)

# Create the spreadsheet
sheet = svc.spreadsheets().create(body={
    'properties': {'title': 'Rancho Raíz - Web CMS'},
    'sheets': [
        {'properties': {'title': 'config'}},
        {'properties': {'title': 'habitaciones'}},
        {'properties': {'title': 'servicios'}},
        {'properties': {'title': 'galeria'}},
        {'properties': {'title': 'promociones'}},
    ]
}).execute()

sheet_id = sheet['spreadsheetId']
sheet_url = sheet['spreadsheetUrl']
print(f'✅ Sheet created!')
print(f'ID: {sheet_id}')
print(f'URL: {sheet_url}')

# config
svc.spreadsheets().values().update(
    spreadsheetId=sheet_id, range='config!A1:C7',
    valueInputOption='RAW',
    body={'values': [
        ['clave', 'valor', 'descripcion'],
        ['password_admin', 'rancho', 'Contraseña del panel admin'],
        ['telefono', '0054 9 264 123 4567', 'Teléfono de contacto'],
        ['whatsapp', '5492641234567', 'WhatsApp (solo números)'],
        ['email', 'info@ranchoraiz.com', 'Email de contacto'],
        ['direccion', 'Ruta 149, Barreal, San Juan', 'Dirección de la posada'],
        ['ig_usuario', 'ranchoraiz.barreal', 'Usuario de Instagram'],
    ]}
).execute()

# habitaciones (con columnas de promo)
svc.spreadsheets().values().update(
    spreadsheetId=sheet_id, range='habitaciones!A1:H6',
    valueInputOption='RAW',
    body={'values': [
        ['nombre', 'precio', 'descripcion', 'imagen_url', 'activo', 'orden', 'precio_promocion', 'promo_label'],
        ['Habitación Matrimonial', '35000', 'Amplia habitación con cama queen, vista a la cordillera. Baño privado, calefacción, ropa blanca incluida, WiFi.', '', 'SI', '1', '', ''],
        ['Habitación Doble', '28000', 'Dos camas individuales. Ideal para amigos o compañeros. Baño compartido, calefacción, ropa blanca incluida.', '', 'SI', '2', '', ''],
        ['Habitación Familiar', '45000', 'Capacidad para 4 personas. Dos ambientes, baño privado, cocina equipada, calefacción, Smart TV.', '', 'SI', '3', '', ''],
        ['Cabaña Completa', '65000', 'Cabaña independiente con cochera, parrilla, cocina completa y vistas 360° de la Cordillera de los Andes.', '', 'SI', '4', '55000', '15% OFF'],
        ['Camping', '5000', 'Espacio para carpa con acceso a baños y duchas calientes. Fogón compartido, zona de mate.', '', 'SI', '5', '', ''],
    ]}
).execute()

# servicios
svc.spreadsheets().values().update(
    spreadsheetId=sheet_id, range='servicios!A1:D5',
    valueInputOption='RAW',
    body={'values': [
        ['nombre', 'descripcion', 'icono', 'activo'],
        ['WiFi Starlink', 'Conexión satelital de alta velocidad en todo el predio', 'wifi', 'SI'],
        ['Desayuno Casero', 'Pan amasado, dulces regionales, frutas de estación, mate y café de montaña', 'cafe', 'SI'],
        ['Cabalgatas', 'Excursiones a caballo por la precordillera con guías locales', 'caballo', 'SI'],
        ['Traslado', 'Te buscamos y llevamos desde la terminal de Barreal o San Juan', 'auto', 'SI'],
    ]}
).execute()

# galeria
svc.spreadsheets().values().update(
    spreadsheetId=sheet_id, range='galeria!A1:D2',
    valueInputOption='RAW',
    body={'values': [
        ['imagen_url', 'descripcion', 'orden', 'activo'],
        ['', 'Vista de la Cordillera desde el patio', '1', 'SI'],
    ]}
).execute()

# promociones
svc.spreadsheets().values().update(
    spreadsheetId=sheet_id, range='promociones!A1:G3',
    valueInputOption='RAW',
    body={'values': [
        ['nombre', 'descripcion', 'precio_regular', 'precio_promo', 'imagen_url', 'activo', 'orden'],
        ['Escapada de Invierno', '3 noches en Matrimonial con desayuno + cabalgata', '105000', '85000', '', 'SI', '1'],
        ['Finde Largo Cabaña', '2 noches en Cabaña Completa con traslado incluido', '130000', '99000', '', 'SI', '2'],
    ]}
).execute()

# Make readable by anyone with link (for GH Actions)
try:
    drive_svc = get_service('drive', 'v3', 'drive')
    if drive_svc:
        drive_svc.permissions().create(
            fileId=sheet_id,
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()
        print('✅ Sheet is public (anyone with link can read)')
except Exception as e:
    print(f'⚠️ Could not set public: {e}')

print()
print('=' * 60)
print('✅ LISTO! Compartí este link con Leo y Ayelén:')
print(f'{sheet_url}')
print()
print(f'Admin dashboard: https://oficinabarreal.github.io/rancho-raiz-zira/admin/')
print(f'Contraseña admin: rancho')
print('=' * 60)
