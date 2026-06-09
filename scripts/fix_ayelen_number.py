#!/usr/bin/env python3
"""Fix sheet rows: restore password_admin, update telefono and whatsapp."""
import sys
sys.path.insert(0, '/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3')
from crm.google_auth import get_service

SHEET_ID = '1dd2sVgDAHPITFcE83QGP00eTNs8qiv1pFT3PmJaNikI'

svc = get_service('sheets', 'v4', 'sheets')
if not svc:
    print('ERROR: no sheets service')
    sys.exit(1)

# Read current state
result = svc.spreadsheets().values().get(
    spreadsheetId=SHEET_ID, range='config!A:C'
).execute()
rows = result.get('values', [])
print("Current config:")
for r in rows:
    print(f"  {r}")

# Fix rows:
# Row 2: password_admin -> restore to 'rancho'
# Row 3: telefono -> update to Ayelen's number
# Row 4: whatsapp -> update to Ayelen's number (format for wa.me links)
# Update all at once: range B2:C7
svc.spreadsheets().values().update(
    spreadsheetId=SHEET_ID, range='config!B2:C7',
    valueInputOption='RAW',
    body={'values': [
        ['rancho', 'Contraseña del panel admin'],
        ['+54 9 11 5959-5869', 'Teléfono de contacto (Ayelén)'],
        ['5491159595869', 'WhatsApp (solo números, para botón de reserva)'],
        ['ranchoraiz.barreal@gmail.com', 'Email de contacto'],
        ['Rancho Raiz, Evaristo Gomez 3511, J5411 Barreal, San Juan', 'Dirección de la posada'],
        ['ranchoraiz.barreal', 'Instagram oficial'],
    ]}
).execute()
print('✅ Sheet corregida: password_admin restaurado, teléfono actualizado a Ayelén')
