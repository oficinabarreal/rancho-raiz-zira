#!/usr/bin/env python3
"""
Envía la factura de prueba de Alejandro Beltrán como adjunto PDF.
Usa mail_utils para abstraer el envío por Gmail API.
"""

from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent

# Importar send_gmail_mime de forma compatible tanto como módulo como script
try:
    from .mail_utils import send_gmail_mime
except ImportError:
    from mail_utils import send_gmail_mime

def make_body() -> str:
    return f"""Hola,

Este es un correo de prueba del sistema CRM de Rancho Raiz.

✅ FACTURA EN MODO PDF DEMO
Esta factura fue generada automaticamente desde el correo original
del cliente Alejandro Beltran (alejandro.beltran@foraco.com) del
dia 12 de mayo de 2026.

Se adjunta la factura en:
   · Formato PDF (convertida desde TXT)
   · MODO DEMO / TEST del CRM Rancho Raiz

Detalle del cliente:
   · Cliente: Sr. Alejandro Beltran
   · Email: alejandro.beltran@foraco.com
   · Estadia: 3 noches (22/05/2025 - 25/05/2025)
   · Total abonado: $100.000

Este correo es parte de las pruebas del sistema CRM.
No tiene validez fiscal.

---
Sistema CRM Ranchor Raiz · {datetime.now().strftime('%Y-%m-%d %H:%M')}
Modo: DEMO / TEST
"""

def main():
    print("=== ENVIANDO FACTURA PDF (modo test CRM Rancho Raiz - modo PDF) ===")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    pdf_path = BASE_DIR / "factura_alejandro_beltran.pdf"
    if not pdf_path.exists():
        print(f"❌ No existe el PDF: {pdf_path}")
        return

    subject = 'test modo demo CRM Rancho Raiz [modo PDF]'
    body = make_body()

    # 1. Enviar a ltelloraiz@gmail.com
    print("1. Enviando a ltelloraiz@gmail.com ...")
    try:
        resp = send_gmail_mime(
            to="ltelloraiz@gmail.com",
            subject=subject,
            body_text=body,
            attachments=[pdf_path]
        )
        print(f"   ✅ OK - ID: {resp['id']}, Thread: {resp.get('threadId', '')}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")

    # 2. Enviar a oficinabarreal@gmail.com
    print("\n2. Enviando a oficinabarreal@gmail.com ...")
    try:
        resp = send_gmail_mime(
            to="oficinabarreal@gmail.com",
            subject=subject,
            body_text=body,
            attachments=[pdf_path]
        )
        print(f"   ✅ OK - ID: {resp['id']}, Thread: {resp.get('threadId', '')}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")

    print("\n=== ENVIO COMPLETADO (modo PDF) ===")

if __name__ == "__main__":
    main()
