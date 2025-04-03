import os
import asyncio
import logging
from dotenv import load_dotenv
import discord
from discord.ext import commands
from keep_alive import keep_alive

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('discord_bot')

def run_bot():
    """Run the Discord bot."""
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    
    bot = commands.Bot(command_prefix='!', intents=intents)
    
    @bot.event
    async def on_ready():
        """Called when the bot has connected to Discord."""
        logger.info(f'Bot connected as {bot.user.name}')
        
    async def load_extensions():
        """Load all cogs from the cogs directory."""
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and not filename.startswith('_'):
                try:
                    await bot.load_extension(f'cogs.{filename[:-3]}')
                    logger.info(f'Loaded extension: cogs.{filename[:-3]}')
                except Exception as e:
                    logger.error(f'Failed to load extension {filename}: {e}')
    
    @bot.event
    async def setup_hook():
        """Called when the bot is starting up."""
        await load_extensions()
    
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error('No token provided. Please set the DISCORD_TOKEN environment variable.')
        return
    
    # Start the webserver to keep the bot alive
    keep_alive()
    
    # Run the bot
    try:
        bot.run(token)
    except discord.errors.LoginFailure:
        logger.error('Invalid token. Please check your DISCORD_TOKEN environment variable.')
    except Exception as e:
        logger.error(f'An error occurred while running the bot: {e}')

if __name__ == "__main__":
    run_bot()