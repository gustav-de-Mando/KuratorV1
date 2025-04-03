import os
import logging
from threading import Thread
from flask import Flask, render_template

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('discord_bot')

# Create Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/health')
def health():
    return "Bot is alive!"

def run_flask():
    """Run the Flask application on a specific port"""
    app.run(host='0.0.0.0', port=5000)

def start_bot_process():
    """Start the Discord bot in a separate process"""
    from bot import run_bot
    run_bot()

# This is the main function that will be called by Gunicorn
if __name__ == "__main__":
    # Start the Discord bot in a separate thread
    bot_thread = Thread(target=start_bot_process)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Run the Flask web server in the main thread
    run_flask()