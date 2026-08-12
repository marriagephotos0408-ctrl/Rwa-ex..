# keep_alive.py
import logging
from flask import Flask
from threading import Thread

app = Flask('')

# Suppress default flask logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/')
def home():
    return "Bot is alive!", 200

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
