import os
import json
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
import logging
from utils.logger import setup_logger

logger = setup_logger()

def get_sheets_service():
    # Load credentials from environment
    creds_json = os.getenv('GOOGLE_SERVICE_ACCOUNT')
    if not creds_json:
        logger.error("Google service account credentials not found")
        return None
    
    try:
        # Clean and validate the JSON string
        if not creds_json:
            logger.error("Empty credentials provided")
            return None
            
        # Remove any surrounding whitespace and quotes
        creds_json = creds_json.strip().strip('"\'')
        
        # Handle line endings consistently
        creds_json = creds_json.replace('\r\n', '\n').replace('\r', '\n')
        
        try:
            creds_dict = json.loads(creds_json)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format in credentials: {str(e)}")
            return None
            
        # Validate required fields
        required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if field not in creds_dict]
        if missing_fields:
            logger.error(f"Missing required fields in credentials: {', '.join(missing_fields)}")
            return None
            
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        return build('sheets', 'v4', credentials=credentials)
    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Sheets-Service: {str(e)}")
        return None

def log_trade_to_sheet(spreadsheet_id, initiator_country, partner_country, 
                      offer_resource, offer_amount, request_resource, request_amount):
    service = get_sheets_service()
    if not service:
        logger.error("Konnte keine Verbindung zur Google Sheets API herstellen")
        return
    
    # Prepare all possible resources
    resources = ["Stein", "Eisen", "Holz", "Nahrung", "Stoff", "Dukaten"]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create two entries for the transaction - one from each perspective
    
    # Entry 1: Initiator als Exporteur, Partner als Importeur
    values1 = [[
        timestamp,
        initiator_country,  # Exporteur
        partner_country,    # Importeur
    ]]
    
    # Für jede Ressource prüfen, ob es die angebotene Ressource ist
    for resource in resources:
        if resource == offer_resource:
            values1[0].append(offer_amount)  # Die Menge eintragen
        else:
            values1[0].append(0)  # 0 für alle anderen Ressourcen
    
    # Entry 2: Partner als Exporteur, Initiator als Importeur
    values2 = [[
        timestamp,
        partner_country,    # Exporteur
        initiator_country,  # Importeur
    ]]
    
    # Für jede Ressource prüfen, ob es die angeforderte Ressource ist
    for resource in resources:
        if resource == request_resource:
            values2[0].append(request_amount)  # Die Menge eintragen
        else:
            values2[0].append(0)  # 0 für alle anderen Ressourcen
    
    # Log both entries to the spreadsheet
    body1 = {'values': values1}
    body2 = {'values': values2}
    
    try:
        # First entry
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range='Handelsbuch!A:I',
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body1
        ).execute()
        
        # Second entry
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range='Handelsbuch!A:I',
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body2
        ).execute()
        
        logger.info(f"Handel erfolgreich in Tabelle eingetragen: {initiator_country} <-> {partner_country}")
    except Exception as e:
        logger.error(f"Fehler beim Eintragen des Handels in die Tabelle: {str(e)}")

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
    # Verwende die spezifische Tabellen-ID, die vom Benutzer angegeben wurde
    spreadsheet_id = "1quKEnSHhzW_z4MCJkoQhYuorB9S5OdmMEntAPdFT1a8"
    service = get_sheets_service()
    if not service:
        logger.error("Konnte keine Verbindung zur Google Sheets API herstellen")
        return
    
    # Aktuelles Datum im Format DD.MM.YYYY
    heute = datetime.now().strftime("%d.%m.%Y")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Kosten als Einzelwerte
    holz = kosten.get("holz", 0)
    stein = kosten.get("stein", 0)
    eisen = kosten.get("eisen", 0)
    stoff = kosten.get("stoff", 0)
    nahrung = kosten.get("nahrung", 0)
    gold = kosten.get("gold", 0)
    
    # Liste der militärischen Einheiten
    militaerische_einheiten = [
        "Infanterie", "Kavallerie", "Artillerie", "Korvette", "Fregatte", "Linienschiff"
    ]
    
    # Formatiere für militärische Einheiten
    is_military = ausbau_art in militaerische_einheiten
    # Bei militärischen Einheiten wird die Anzahl in der Ausbauart angezeigt
    ausbau_str = f"{ausbau_art} (x{anzahl})" if is_military else ausbau_art
    
    # Bereite die Daten für das Sheet vor
    values = [[
        heute,                  # Datum
        land,                   # Land
        ausbau_str,             # Ausbauart
        f"Stufe {level}",       # Level
        gebiet,                 # Gebiet
        holz,                   # Holz
        stein,                  # Stein
        eisen,                  # Eisen
        stoff,                  # Stoff
        nahrung,                # Nahrung
        gold                    # Gold
    ]]
    
    # Trage die Daten in das Sheet ein
    body = {'values': values}
    
    ausbau_success = False
    
    try:
        # Das Blatt existiert bereits in der angegebenen Tabelle gemäß Link
        # Der gid-Wert im Link deutet auf ein Blatt mit ID 1687206609 hin
        
        # Direktes Einfügen einer neuen Zeile in das bestehende Blatt
        try:
            service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range='Ausbau!A:K',  # Direkt an das Blatt "Ausbau" anhängen
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logger.info(f"Daten wurden direkt in die Tabelle 'Ausbau' eingetragen")
            ausbau_success = True
        except Exception as e:
            logger.error(f"Fehler beim Eintragen in die Tabelle 'Ausbau': {str(e)}")
            # Wenn ein Fehler auftritt, versuche einen Fallback
            try:
                # Fallback: Rufe die Daten ab und füge sie an die nächste freie Zeile an
                result = service.spreadsheets().values().get(
                    spreadsheetId=spreadsheet_id,
                    range='Ausbau!A:A'
                ).execute()
                
                rows = result.get('values', [])
                next_row = len(rows) + 1
                
                service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=f'Ausbau!A{next_row}:K{next_row}',
                    valueInputOption='USER_ENTERED',
                    body=body
                ).execute()
                
                logger.info(f"Fallback-Methode: Ausbaudaten erfolgreich in Zeile {next_row} eingetragen")
                ausbau_success = True
            except Exception as fallback_error:
                logger.error(f"Auch Fallback-Methode fehlgeschlagen: {str(fallback_error)}")
                ausbau_success = False
        
        # Wenn der Ausbau erfolgreich in die Tabelle eingetragen wurde,
        # trage ihn zusätzlich ins Handelsbuch ein
        if ausbau_success:
            try:
                # Formatiere die Ausbauart als Kommentar für das Handelsbuch
                ausbau_info = f"{ausbau_str}, Stufe {level}, Gebiet {gebiet}"
                
                # Erstelle den Handels-Eintrag mit separaten Spalten für Ausbau-Details
                handelsbuch_values = [[
                    timestamp,              # Datum
                    land,                   # Exporteur (das Land, das den Ausbau durchführt)
                    "Ausbau",               # Importeur (fest als "Ausbau")
                    stein,                  # Stein
                    eisen,                  # Eisen
                    holz,                   # Holz
                    nahrung,                # Nahrung
                    stoff,                  # Stoff
                    gold,                   # Gold/Dukaten
                    ausbau_art,             # Art des Ausbaus
                    f"Stufe {level}",       # Ausbaustufe
                    str(gebiet)             # Gebietsnummer
                ]]
                
                # Trage in das Handelsbuch ein
                handelsbuch_body = {'values': handelsbuch_values}
                
                service.spreadsheets().values().append(
                    spreadsheetId=spreadsheet_id,
                    range='Handelsbuch!A:J',  # Jetzt mit einer zusätzlichen Spalte für Kommentare
                    valueInputOption='RAW',
                    insertDataOption='INSERT_ROWS',
                    body=handelsbuch_body
                ).execute()
                
                logger.info(f"Ausbau wurde zusätzlich als Eintrag im Handelsbuch eingetragen")
            except Exception as handelsbuch_error:
                logger.error(f"Fehler beim Eintragen des Ausbaus ins Handelsbuch: {str(handelsbuch_error)}")
                # Kein Abbruch, da der Eintrag in der Ausbau-Tabelle bereits erfolgt ist
        
        logger.info(f"Ausbau erfolgreich in die Tabelle eingetragen: {ausbau_art} (Stufe {level}) für {land}")
        return True
    except Exception as e:
        logger.error(f"Fehler beim Eintragen des Ausbaus in die Tabelle: {str(e)}")
        return False
