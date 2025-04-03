import os
import json
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

def get_sheets_service():
    """Create and return a Google Sheets service object"""
    try:
        # Check if we have a JSON file or a direct service account info in env var
        if os.path.exists('empire-service-account.json'):
            credentials = service_account.Credentials.from_service_account_file(
                'empire-service-account.json', 
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
        elif os.environ.get('GOOGLE_SERVICE_ACCOUNT'):
            service_account_info = json.loads(os.environ.get('GOOGLE_SERVICE_ACCOUNT'))
            credentials = service_account.Credentials.from_service_account_info(
                service_account_info,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
        else:
            print("No Google service account credentials found")
            return None
            
        return build('sheets', 'v4', credentials=credentials)
    except Exception as e:
        print(f"Error setting up Google Sheets service: {e}")
        return None

def log_trade_to_sheet(spreadsheet_id, initiator_country, partner_country, 
                      offer_resource, offer_amount, request_resource, request_amount):
    """Log a trade agreement to the spreadsheet"""
    try:
        # Always use the actual trade sheet ID from environment variable
        spreadsheet_id = os.environ.get('TRADE_SHEET_ID', spreadsheet_id)
        
        service = get_sheets_service()
        if not service:
            return False
            
        # Format date
        date = datetime.now().strftime('%d.%m.%Y')
        
        # Prepare row data
        row_data = [
            date,
            initiator_country,
            partner_country,
            f"{offer_resource} ({offer_amount})",
            f"{request_resource} ({request_amount})"
        ]
        
        # Append row to spreadsheet
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range='Handelsverträge!A:E',
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body={'values': [row_data]}
        ).execute()
        
        return True
    except Exception as e:
        print(f"Error logging trade to sheet: {e}")
        return False

def log_ausbau_to_sheet(spreadsheet_id, land, ausbau_art, level, kosten, gebiet, anzahl=1):
    """
    Trägt einen Ausbau in die Google Tabelle ein.
    
    Parameters:
    -----------
    spreadsheet_id: Die ID des Google Sheets (wird überschrieben mit der festen ID)
    land: Das Land, das den Ausbau durchführt
    ausbau_art: Die Art des Ausbaus
    level: Die Ausbaustufe
    kosten: Dictionary mit den Kosten (holz, stein, eisen, etc.)
    gebiet: Die Gebietsnummer
    anzahl: Die Anzahl der Einheiten (nur bei militärischen Einheiten relevant)
    """
    try:
        # Always use the actual trade sheet ID from environment variable
        spreadsheet_id = os.environ.get('TRADE_SHEET_ID', spreadsheet_id)
        
        service = get_sheets_service()
        if not service:
            return False
            
        # Format date
        date = datetime.now().strftime('%d.%m.%Y')
        
        # Format costs
        kosten_str = ", ".join([f"{k.capitalize()}: {v}" for k, v in kosten.items() if v > 0])
        
        # Prepare row data
        row_data = [
            date,
            land,
            f"{ausbau_art} (Stufe {level})",
            kosten_str,
            f"Gebiet {gebiet}",
            anzahl if anzahl > 1 else ""
        ]
        
        # Append row to spreadsheet
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range='Ausbau!A:F',
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body={'values': [row_data]}
        ).execute()
        
        return True
    except Exception as e:
        print(f"Error logging development to sheet: {e}")
        return False