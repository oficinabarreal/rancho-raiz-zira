"""Fix the config sheet phone number."""
import sys
sys.path.insert(0, '/data/data/com/termux/files/home/Documents/Codex/2026-05-18/hola-3')
from crm.google_auth import get_service
import urllib.request

svc = get_service('sheets', 'v4', 'sheets')
svc.spreadsheets().values().update(
    spreadsheetId='1dd2sVgDAHPITFcE83QGP00eTNs8qiv1pFT3PmJaNikI',
    range='config!B3',
    valueInputOption='RAW',
    body={'values': [['0054 9 264 123 4567']]}
).execute()
print('Phone updated')

# Test CSV export
url = 'https://docs.google.com/spreadsheets/d/1dd2sVgDAHPITFcE83QGP00eTNs8qiv1pFT3PmJaNikI/gviz/tq?tqx=out:csv&sheet=config'
data = urllib.request.urlopen(url, timeout=15).read().decode('utf-8')
print('CSV output:')
for line in data.strip().split('\n'):
    print(line)
