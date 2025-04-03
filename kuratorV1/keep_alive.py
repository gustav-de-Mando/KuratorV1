from main import app, run_flask
from threading import Thread

def keep_alive():
    """Start a Flask web server in a separate thread"""
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    return t