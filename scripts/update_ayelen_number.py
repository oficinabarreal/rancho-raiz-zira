#!/usr/bin/env python3
"""Update phone number to Ayelén's real number from WhatsApp export."""
import sys
sys.path.insert(0, '/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3')
from crm.google_auth import get_service

SHEET_ID = '1dd2sVgDAHPITFcE83QGP00eTNs8qiv1pFT3PmJaNikI'

svc = get_service('sheets', 'v4', 'sheets')
if not svc:
    print('ERROR: no sheets service')
    sys.exit(1)

# Update config: telefono and whatsapp to Ayelén's number
svc.spreadsheets().values().update(
    spreadsheetId=SHEET_ID, range='config!B2:C3',
    valueInputOption='RAW',
    body={'values': [
        ['+54 9 11 5959-5869', 'Teléfono de contacto (Ayelén)'],
        ['5491159595869', 'WhatsApp (solo números, para botón de reserva)'],
    ]}
).execute()
print('✅ Teléfono actualizado al número de Ayelén: +54 9 11 5959-5869')
