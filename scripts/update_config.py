#!/usr/bin/env python3
"""Update the Google Sheet config with new address and phone."""
import sys
import json
import os

sys.path.insert(0, '/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3')

try:
    from crm.google_auth import get_service
except ImportError as e:
    print(f"ERROR: Could not import google_auth: {e}")
    sys.exit(1)

SHEET_ID = "1dd2sVgDAHPITFcE83QGP00eTNs8qiv1pFT3PmJaNikI"

def main():
    print("Getting Google Sheets service...")
    svc = get_service('sheets', 'v4', 'sheets')
    if not svc:
        print("ERROR: Failed to get sheets service")
        return False

    print("Reading current config from sheet...")
    try:
        # Read the config tab
        result = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range="config!A:B"
        ).execute()
        
        rows = result.get('values', [])
        if not rows:
            print("ERROR: No data found in config tab")
            return False
            
        # Convert to dictionary
        config = {}
        for row in rows:
            if len(row) >= 2:
                config[row[0]] = row[1]
        
        print("Current configuration:")
        for key, value in config.items():
            print(f"  {key}: {value}")
        
        # Update the required fields
        print("\nUpdating configuration...")
        config["direccion"] = "Rancho Raiz, Evaristo Gomez 3511, J5411 Barreal, San Juan"
        config["telefono"] = "+54 9 264 585-3266"  # Ayelen's contact number
        
        print("New configuration:")
        for key, value in config.items():
            print(f"  {key}: {value}")
        
        # Convert back to rows for updating
        values = [[key, value] for key, value in config.items()]
        
        # Update the sheet
        print("\nUpdating Google Sheet...")
        body = {
            'values': values
        }
        
        update_result = svc.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range="config!A:B",
            valueInputOption='RAW',
            body=body
        ).execute()
        
        updated_cells = update_result.get('updatedCells', 0)
        print(f"SUCCESS: Updated {updated_cells} cells in the config tab")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)