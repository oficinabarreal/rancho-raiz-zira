#!/usr/bin/env python3
"""Add promo columns to habitaciones + create promociones tab."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crm.google_auth import get_service

SHEET_ID = "1dd2sVgDAHPITFcE83QGP00eTNs8qiv1pFT3PmJaNikI"

svc = get_service("sheets", "v4", "sheets")
if not svc:
    print("ERROR: no sheets service")
    sys.exit(1)

# 1. Check existing habitaciones headers
headers = svc.spreadsheets().values().get(
    spreadsheetId=SHEET_ID, range="habitaciones!A1:Z1"
).execute()
existing = headers.get("values", [[]])[0]
print(f"Habitaciones headers actuales ({len(existing)}): {existing}")

cols_to_add = []
if "precio_promocion" not in existing:
    cols_to_add.append("precio_promocion")
if "promo_label" not in existing:
    cols_to_add.append("promo_label")

if cols_to_add:
    start_col = chr(65 + len(existing))  # e.g. G
    end_col = chr(65 + len(existing) + len(cols_to_add) - 1)
    col_range = f"habitaciones!{start_col}1:{end_col}1"
    svc.spreadsheets().values().update(
        spreadsheetId=SHEET_ID, range=col_range,
        valueInputOption="RAW",
        body={"values": [cols_to_add]}
    ).execute()
    print(f"✅ Columnas agregadas: {cols_to_add}")
else:
    print("ℹ️ Columnas de promo ya existen")

# 2. Check if promociones tab exists
try:
    sheets_meta = svc.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    tab_names = [s["properties"]["title"] for s in sheets_meta.get("sheets", [])]
    print(f"Tabs: {tab_names}")
except:
    tab_names = []

if "promociones" not in tab_names:
    body = {"requests": [{"addSheet": {"properties": {"title": "promociones"}}}]}
    svc.spreadsheets().batchUpdate(spreadsheetId=SHEET_ID, body=body).execute()
    print("✅ Pestaña 'promociones' creada")

    # Seed data
    svc.spreadsheets().values().update(
        spreadsheetId=SHEET_ID, range="promociones!A1:G3",
        valueInputOption="RAW",
        body={"values": [
            ["nombre", "descripcion", "precio_regular", "precio_promo", "imagen_url", "activo", "orden"],
            ["Escapada de Invierno", "3 noches en Matrimonial con desayuno + cabalgata", "105000", "85000", "", "SI", "1"],
            ["Finde Largo Cabaña", "2 noches en Cabaña Completa con traslado incluido", "130000", "99000", "", "SI", "2"],
        ]}
    ).execute()
    print("✅ Datos seed en promociones")
else:
    print("ℹ️ Pestaña 'promociones' ya existe")

print("\n🎉 Listo")
print(f"URL: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")
