import json, urllib.parse
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/documents',
]

CLIENT_CONFIG = {
    'web': {
        'client_id': '104536822997-b2s9bit8b5ugujh9bp152aqu6mfkm5rv.apps.googleusercontent.com',
        'project_id': 'gen-lang-client-0847420405',
        'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'client_secret': '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',
        'redirect_uris': ['http://localhost:8080']
    }
}

flow = InstalledAppFlow.from_client_config(CLIENT_CONFIG, scopes=SCOPES)
auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline', include_granted_scopes='true')

print("=== ABRÍ este link en tu navegador ===")
print(auth_url)
print()
print("Autorizá y te redirigirá a localhost:8080")
print("(La página dirá que no conecta, pero el código ya se capturó)")
print()

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(q)
        code = params.get('code', [None])[0]
        if code:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><body><h1>OK</h1><p>Codigo capturado. Cerra esta pestana.</p></body></html>")
            with open('/tmp/oauth_code.txt', 'w') as f:
                f.write(code)
        else:
            self.send_response(400)
            self.end_headers()

server = HTTPServer(('0.0.0.0', 8080), Handler)
server.timeout = 120

while server.timeout > 0:
    server.handle_request()
    if Path('/tmp/oauth_code.txt').exists():
        break

with open('/tmp/oauth_code.txt') as f:
    code = f.read().strip()

flow.fetch_token(code=code)
creds = flow.credentials
tok_path = '/root/Documents/Codex/2026-05-18/hola-3/crm_state/.google_token.json'
with open(tok_path, 'w') as f:
    json.dump(json.loads(creds.to_json()), f)
print(f"✅ Token guardado con scopes: {creds.scopes}")
