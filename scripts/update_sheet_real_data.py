#!/usr/bin/env python3
"""Update the Sheet with real data from WhatsApp exports."""
import sys
sys.path.insert(0, '/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3')
from crm.google_auth import get_service

SHEET_ID = '1dd2sVgDAHPITFcE83QGP00eTNs8qiv1pFT3PmJaNikI'

svc = get_service('sheets', 'v4', 'sheets')
if not svc:
    print('ERROR: no sheets service')
    sys.exit(1)

# 1. CONFIG - real data
svc.spreadsheets().values().update(
    spreadsheetId=SHEET_ID, range='config!A1:C7',
    valueInputOption='RAW',
    body={'values': [
        ['clave', 'valor', 'descripcion'],
        ['password_admin', 'rancho', 'Contraseña del panel admin'],
        ['telefono', '+54 9 264 585-3266', 'Teléfono de contacto (Ayelén)'],
        ['whatsapp', '5492645853266', 'WhatsApp (solo números, para botón de reserva)'],
        ['email', 'ranchoraiz.barreal@gmail.com', 'Email de contacto'],
        ['direccion', 'Ruta 149, Barreal, San Juan, Argentina', 'Dirección de la posada'],
        ['ig_usuario', 'ranchoraiz.barreal', 'Instagram oficial'],
    ]}
).execute()
print('✅ Config actualizada')

# 2. HABITACIONES - real pricing structure
svc.spreadsheets().values().update(
    spreadsheetId=SHEET_ID, range='habitaciones!A1:H8',
    valueInputOption='RAW',
    body={'values': [
        ['nombre', 'precio', 'descripcion', 'imagen_url', 'activo', 'orden', 'precio_promocion', 'promo_label'],
        ['Cabaña Completa (1 pers.)', '80000',
         'Alquiler completo de la cabaña para 1 persona. Cabaña independiente con cochera, parrilla, cocina equipada, WiFi Starlink, patio con pileta y vistas a la Cordillera de los Andes.',
         '', 'SI', '1', '', ''],
        ['Cabaña Completa (2 pers.)', '95000',
         'Alquiler completo de la cabaña para 2 personas. Ideal para parejas. Cabaña independiente con cochera, parrilla, cocina equipada, WiFi Starlink, patio con pileta y vistas a la Cordillera.',
         '', 'SI', '2', '', ''],
        ['Cabaña Completa (3 pers.)', '105000',
         'Alquiler completo de la cabaña para 3 personas. Cabaña independiente con cochera, parrilla, cocina equipada, WiFi Starlink, patio con pileta.',
         '', 'SI', '3', '', ''],
        ['Cabaña Completa (4 pers.)', '115000',
         'Alquiler completo de la cabaña para 4 personas. Dos ambientes, baño privado, cocina equipada, calefacción, Smart TV, WiFi Starlink, parrilla y pileta.',
         '', 'SI', '4', '', ''],
        ['Cabaña Completa (5 pers.)', '120000',
         'Alquiler completo de la cabaña para 5 personas. Capacidad máxima. Todas las comodidades: cochera, parrilla, cocina completa, WiFi Starlink, patio con pileta y vistas 360°.',
         '', 'SI', '5', '', ''],
        ['Camping (por persona)', '5000',
         'Espacio para carpa en el predio con acceso a baño, ducha caliente, fogón compartido y zona de mate. WiFi Starlink incluido.',
         '', 'SI', '6', '', ''],
        ['Noche sola (tarifa única)', '120000',
         'Tarifa especial para reserva de una sola noche en la cabaña completa, sin importar la cantidad de personas.',
         '', 'SI', '7', '', ''],
    ]}
).execute()
print('✅ Habitaciones actualizadas')

# 3. SERVICIOS - real services
svc.spreadsheets().values().update(
    spreadsheetId=SHEET_ID, range='servicios!A1:D6',
    valueInputOption='RAW',
    body={'values': [
        ['nombre', 'descripcion', 'icono', 'activo'],
        ['WiFi Starlink', 'Internet satelital de alta velocidad en todo el predio y la cabaña', 'wifi', 'SI'],
        ['Patio con Pileta', 'Amplio patio con pileta de temporada, ideal para disfrutar del clima de Barreal', 'montaña', 'SI'],
        ['Parrilla & Fogón', 'Asador completo con leña incluida y fogón compartido para noches al aire libre', 'montaña', 'SI'],
        ['Cochera Privada', 'Estacionamiento cubierto dentro del predio', 'auto', 'SI'],
        ['Vistas a la Cordillera', 'Vistas panorámicas a la Cordillera de los Andes desde toda la propiedad', 'montaña', 'SI'],
    ]}
).execute()
print('✅ Servicios actualizados')

# 4. PROMOCIONES - updated offers
svc.spreadsheets().values().update(
    spreadsheetId=SHEET_ID, range='promociones!A1:G4',
    valueInputOption='RAW',
    body={'values': [
        ['nombre', 'descripcion', 'precio_regular', 'precio_promo', 'imagen_url', 'activo', 'orden'],
        ['Escapada de Invierno', '3 noches en Cabaña (2 pers.) con leña y wifi incluidos', '285000', '250000', '', 'SI', '1'],
        ['Finde Largo', '2 noches en Cabaña Completa (hasta 4 pers.) con traslado desde San Juan', '230000', '200000', '', 'SI', '2'],
        ['Semana en la Montaña', '7 noches en Cabaña (2 pers.) con 10% de descuento', '665000', '598500', '', 'SI', '3'],
    ]}
).execute()
print('✅ Promociones actualizadas')

print('\n🎉 Sheet actualizada con datos reales!')
