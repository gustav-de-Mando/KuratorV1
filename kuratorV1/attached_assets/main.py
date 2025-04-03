import os
import discord
from discord.ext import commands
import logging
import threading
import asyncio
from utils.logger import setup_logger
from utils.config import PREFIX
from flask import Flask
from keep_alive import keep_alive

keep_alive()








# Setup Flask app for gunicorn
app = Flask(__name__)

# Setup logging
logger = setup_logger()

# Global variable to track bot thread
bot_thread = None
bot_running = False

# Mutex für synchronisierten Zugriff auf Bot-Status
bot_lock = threading.Lock()

# Initialize bot with command prefix and intents
intents = discord.Intents.default()
intents.message_content = True  # For reading message content
intents.members = True          # For member-related events
intents.guilds = True           # For server-related events
intents.presences = True        # For presence updates

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# Load cogs
initial_cogs = [
    'cogs.moderation',
    'cogs.general',
    'cogs.trade',
    'cogs.treaties',
    'cogs.ausbau'
]

@bot.event
async def on_ready():
    logger.info(f'Bot is ready! Logged in as {bot.user.name} ({bot.user.id})')
    # Sync slash commands with Discord
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} command(s)")
        for cmd in synced:
            logger.info(f"Synced command: {cmd.name}")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")

async def load_extensions():
    for extension in initial_cogs:
        try:
            await bot.load_extension(extension)
            logger.info(f'Loaded extension {extension}')
        except Exception as e:
            logger.error(f'Failed to load extension {extension}: {str(e)}')

async def start_bot_async():
    """Asynchronous function to start the bot"""
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("Discord token not found in environment variables")
        return

    try:
        await load_extensions()
        await bot.start(token)
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}")

def run_bot_thread():
    """Function to run the bot in a separate thread"""
    global bot_running
    
    # Verwende den Lock, um Wettlaufsituationen zu vermeiden
    with bot_lock:
        if bot_running:
            logger.info("Bot is already running")
            return
        
        logger.info("Starting Discord bot in a separate thread")
        bot_running = True
    
    # Create a new event loop for the bot
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Run the bot in the new event loop
    try:
        loop.run_until_complete(start_bot_async())
    except Exception as e:
        logger.error(f"Error in bot thread: {str(e)}")
    finally:
        # Setze den Bot-Status zurück, wenn der Thread endet
        with bot_lock:
            bot_running = False
            logger.info("Bot thread stopped")

def start_bot():
    """Start the bot in a separate thread if it's not already running"""
    global bot_thread, bot_running
    
    # Verwende den Lock für Thread-Sicherheit
    with bot_lock:
        if bot_running and bot_thread and bot_thread.is_alive():
            logger.info("Bot is already running in a separate thread")
            return
        
        # Create and start the bot thread nur wenn noch nicht gestartet
        if not bot_running or not bot_thread or not bot_thread.is_alive():
            bot_thread = threading.Thread(target=run_bot_thread, daemon=True)
            bot_thread.start()
            logger.info("Bot thread started")
        else:
            logger.info("Bot is already running, no need to start a new thread")

# Flask routes
@app.route('/')
def index():
    global bot_thread, bot_running
    
    # Verwende Lock für Thread-Sicherheit
    with bot_lock:
        # Check if the bot is running, start it if not
        if not bot_running or not bot_thread or not bot_thread.is_alive():
            # Bot außerhalb des Locks starten, um Deadlocks zu vermeiden
            bot_lock.release()
            try:
                start_bot()
                status = "Bot was not running and has been started"
            finally:
                bot_lock.acquire()
        else:
            status = "Bot is running"
    
    return f"""
    <html>
        <head>
            <title>Discord Bot Status</title>
            <style>
                body {{ 
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #2c2f33;
                    color: #ffffff;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    background-color: #23272a;
                    padding: 20px;
                    border-radius: 5px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                }}
                h1 {{ color: #7289da; }}
                p {{ line-height: 1.6; }}
                .status {{ 
                    padding: 10px;
                    border-radius: 5px;
                    margin: 20px 0;
                    background-color: #32363b;
                }}
                .online {{ color: #43b581; }}
                .heartbeat {{ 
                    animation: pulse 2s infinite;
                    display: inline-block;
                    width: 10px;
                    height: 10px;
                    background-color: #43b581;
                    border-radius: 50%;
                    margin-right: 10px;
                }}
                @keyframes pulse {{
                    0% {{ transform: scale(0.95); opacity: 0.7; }}
                    50% {{ transform: scale(1); opacity: 1; }}
                    100% {{ transform: scale(0.95); opacity: 0.7; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Diplomatischer Bot - Status</h1>
                <div class="status">
                    <p><span class="heartbeat"></span> <span class="online">ONLINE</span> - {status}</p>
                </div>
                <p>
                    Dieser Discord-Bot unterstützt folgende Funktionen:
                </p>
                <ul>
                    <li>Moderation: kick, ban, clear</li>
                    <li>Informationen: ping, serverinfo, userinfo</li>
                    <li>Diplomatische Funktionen: Verträge, Handelsabkommen</li>
                    <li>Ausbauten: Wirtschaft, Bevölkerung, Militär, Infrastruktur</li>
                </ul>
                <p>
                    Der Bot läuft 24/7 und steht jederzeit für diplomatische Verhandlungen zur Verfügung.
                </p>
                
                <div class="mt-4">
                    <h4>Neue Funktionalität: Ausbausystem</h4>
                    <p>
                        Mit dem neuen <code>/ausbau</code>-Befehl können Länder ihre Territorien
                        entwickeln. Folgende Ausbauten stehen zur Verfügung:
                    </p>
                    <ul>
                        <li><strong>Infrastruktur:</strong> Wirtschaft, Bevölkerung, Bergbau, Agrabau</li>
                        <li><strong>Siedlungen:</strong> Nebenstadt, Handelsposten, Hauptstadt, Handelszentrum, Festung</li>
                        <li><strong>Militär:</strong> Infanterie, Kavallerie, Artillerie, Korvette, Fregatte, Linienschiff</li>
                    </ul>
                    <p>Alle Ausbauaktivitäten werden automatisch in der zentralen Tabelle festgehalten.</p>
                </div>
            </div>
        </body>
    </html>
    """

# Start the bot when the script is imported (for gunicorn)
start_bot()

# If running directly (for local development)
if __name__ == "__main__":
    # When running locally, we can use the Flask development server with the bot
    app.run(host="0.0.0.0", port=8080, debug=True)