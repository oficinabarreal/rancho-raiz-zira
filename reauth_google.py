#!/usr/bin/env python3
"""OAuth on port 8080 (common test port per Google docs)."""

import json
import os, re, subprocess, sys
from pathlib import Path
from wsgiref.simple_server import make_server

os.environ.setdefault("CRM_STATE_DIR", "crm_state")
os.environ.setdefault("CRM_GOOGLE_CREDS", "/root/.google-workspace-creds.json")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from crm.google_auth import _all_scopes, _creds_path, _token_path

client_file = _creds_path()
if not client_file: print("No credentials file"); sys.exit(1)
from google_auth_oauthlib.flow import InstalledAppFlow

PORT = 8080
flow = InstalledAppFlow.from_client_secrets_file(str(client_file), _all_scopes(), redirect_uri=f"http://localhost:{PORT}/")
auth_url, _ = flow.authorization_url(access_type="offline", include_granted_scopes="true")
print(auth_url, flush=True)

socat = subprocess.Popen(["socat", f"TCP-LISTEN:{PORT},reuseaddr,fork", f"TCP:127.0.0.1:{PORT+1}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

codes = []
def wsgi_app(environ, start_response):
    qs = environ.get("QUERY_STRING", "")
    m = re.search(r"code=([^&]+)", qs)
    if m: codes.append(m.group(1))
    start_response("200 OK", [("Content-Type", "text/html")])
    return [b"<html><body><h1>OK</h1></body></html>"]

server = make_server("127.0.0.1", PORT+1, wsgi_app)
print(f"Waiting on 127.0.0.1:{PORT+1} (socat forwarding {PORT}->{PORT+1})", flush=True)
while not codes: server.handle_request()
socat.terminate(); socat.wait()

flow.fetch_token(code=codes[0])
_path = _token_path(); _path.parent.mkdir(parents=True, exist_ok=True)
_path.write_text(json.dumps(json.loads(flow.credentials.to_json())))
print("Token guardado!")
