import sys
from pathlib import Path
from datetime import datetime
import base64
import mimetypes

sys.path.insert(0, str(Path("/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3")))

from crm.connectors import GmailConnector

print("=== ENVIANDO FACTURA PDF (modo test CRM Rancho Raiz - modo PDF) ===")
print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

FACTURA_PATH = Path(__file__).resolve().parent / "factura_demo.pdf"
FACTURA_TXT = Path(__file__).resolve().parent / "factura_demo.txt"

# Leer el archivo PDF y el texto
pdf_bytes = FACTURA_PATH.read_bytes()
texto_factura = FACTURA_TXT.read_text()

# Usar el servicio directamente para enviar archivo adjunto
gmail = GmailConnector()
svc = gmail._svc()

if not svc:
    print("❌ No se pudo obtener el servicio de Gmail")
    sys.exit(1)

# Crear mensaje MIME con adjunto
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formatdate

def enviar_con_adjunto(to_email):
    msg = MIMEMultipart()
    msg['To'] = to_email
    msg['Subject'] = 'test modo demo CRM Rancho Raiz [modo PDF]'
    msg['Date'] = formatdate(localtime=True)
    
    # Cuerpo del mensaje
    cuerpo = f"""Hola,

Este es un correo de prueba del sistema CRM de Rancho Raiz.

✅ FACTURA EN MODO PDF DEMO
Esta factura fue generada automaticamente desde el correo original
del cliente demo (demo@cliente.com) del
dia 12 de mayo de 2026.

Se adjunta la factura en:
   · Formato PDF (convertida desde TXT)
   · MODO DEMO / TEST del CRM Rancho Raiz

Detalle del cliente:
   · Cliente: Sr. Alejandro Beltran
   · Email: demo@cliente.com
   · Estadia: 3 noches (22/05/2025 - 25/05/2025)
   · Total abonado: $100.000

Este correo es parte de las pruebas del sistema CRM.
No tiene validez fiscal.

---
Sistema CRM Rancho Raiz · {datetime.now().strftime('%Y-%m-%d %H:%M')}
Modo: DEMO / TEST
"""
    msg.attach(MIMEText(cuerpo, 'plain'))
    
    # Adjuntar PDF
    part = MIMEBase('application', 'pdf')
    part.set_payload(pdf_bytes)
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename="factura_demo.pdf"')
    msg.attach(part)
    
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    resp = svc.users().messages().send(userId='me', body={'raw': raw}).execute()
    return resp

# 1. Enviar a ltelloraiz@gmail.com
print("1. Enviando a ltelloraiz@gmail.com ...")
try:
    resp1 = enviar_con_adjunto("ltelloraiz@gmail.com")
    print(f"   ✅ OK - ID: {resp1['id']}, Thread: {resp1.get('threadId', '')}")
except Exception as e:
    print(f"   ❌ ERROR: {e}")
print()

# 2. Enviar a oficinabarreal@gmail.com
print("2. Enviando a oficinabarreal@gmail.com ...")
try:
    resp2 = enviar_con_adjunto("oficinabarreal@gmail.com")
    print(f"   ✅ OK - ID: {resp2['id']}, Thread: {resp2.get('threadId', '')}")
except Exception as e:
    print(f"   ❌ ERROR: {e}")
print()

print("=== ENVIO COMPLETADO (modo PDF) ===")
