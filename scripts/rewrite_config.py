"""Fix config tab - clear and rewrite with RAW mode to fix CSV export."""
import sys
sys.path.insert(0, '/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3')
from crm.google_auth import get_service

svc = get_service('sheets', 'v4', 'sheets')
sheet_id = '1dd2sVgDAHPITFcE83QGP00eTNs8qiv1pFT3PmJaNikI'

# First clear the entire tab
svc.spreadsheets().values().clear(
    spreadsheetId=sheet_id,
    range='config!A1:Z100'
).execute()

# Write all data in RAW mode
data = [
    ['clave', 'valor', 'descripcion'],
    ['password_admin', 'rancho', 'Contrasena del panel admin'],
    ['telefono', '0054 9 264 123 4567', 'Telefono de contacto'],
    ['whatsapp', '5492641234567', 'WhatsApp solo numeros'],
    ['email', 'info@ranchoraiz.com', 'Email de contacto'],
    ['direccion', 'Ruta 149, Barreal, San Juan', 'Direccion de la posada'],
    ['ig_usuario', 'ranchoraiz.barreal', 'Usuario de Instagram'],
]

svc.spreadsheets().values().update(
    spreadsheetId=sheet_id,
    range='config!A1:C7',
    valueInputOption='RAW',  # RAW not USER_ENTERED
    body={'values': data}
).execute()

print('Config tab rewritten with RAW mode')

# Verify CSV export
import urllib.request
url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=config'
resp = urllib.request.urlopen(url, timeout=15)
csv_content = resp.read().decode('utf-8')
print('CSV export:')
for line in csv_content.strip().split('\n'):
    print(line)
