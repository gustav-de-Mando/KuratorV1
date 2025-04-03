import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Discord Bot Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Google Sheets Configuration
TRADE_SHEET_ID = os.getenv('TRADE_SHEET_ID')
GOOGLE_SERVICE_ACCOUNT = os.getenv('GOOGLE_SERVICE_ACCOUNT')

# Default command prefix
PREFIX = '!'

# Treaty limits per user (adjust as needed)
TREATY_LIMITS = {
    "Nichtangriffspakt": 5,      # Each user can have max 5 non-aggression pacts
    "Schutzbündnis": 3,         # Each user can have max 3 protection pacts
    "Allianzvertrag": 2,        # Each user can have max 2 alliance treaties
    "Hochzeitspakt": 1,         # Each user can have max 1 marriage pact
    "Großallianzvertrag": 1     # Each user can have max 1 grand alliance
}

# Resources for trading
TRADE_RESOURCES = [
    "Holz",
    "Stein", 
    "Eisen", 
    "Nahrung", 
    "Stoff", 
    "Dukaten"
]

# Development options
DEVELOPMENT_TYPES = [
    # Civilian developments
    {"name": "Infrastruktur", "levels": 7, "military": False},
    {"name": "Wirtschaft", "levels": 7, "military": False},
    {"name": "Landwirtschaft", "levels": 7, "military": False},
    {"name": "Bildung", "levels": 7, "military": False},
    {"name": "Kultur", "levels": 7, "military": False},
    # Military units - these have quantity
    {"name": "Infanterie", "levels": 7, "military": True},
    {"name": "Kavallerie", "levels": 7, "military": True},
    {"name": "Artillerie", "levels": 7, "military": True},
    {"name": "Korvette", "levels": 7, "military": True},
    {"name": "Fregatte", "levels": 7, "military": True},
    {"name": "Linienschiff", "levels": 7, "military": True},
]

# Roles that can use mod commands
MOD_ROLES = ["Admin", "Moderator", "Game Master"]