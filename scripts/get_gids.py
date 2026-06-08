"""Get sheet GIDs."""
import sys
sys.path.insert(0, '/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3')
from crm.google_auth import get_service

svc = get_service('sheets', 'v4', 'sheets')
result = svc.spreadsheets().get(
    spreadsheetId='1dd2sVgDAHPITFcE83QGP00eTNs8qiv1pFT3PmJaNikI',
    fields='sheets.properties'
).execute()
for s in result.get('sheets', []):
    p = s.get('properties', {})
    title = p.get('title', '?')
    gid = p.get('sheetId', '?')
    print(f'{title}: gid={gid}')
