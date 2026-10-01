import os
import threading
from flask import Flask
from bot import main_loop

app = Flask(__name__)

# Endpoint health check untuk mencegah Deplexo mematikan bot
@app.route('/')
def home():
    return "JKT48 Bot Monitoring is Active and Running!", 200

def run_flask():
    # Mengambil PORT yang diberikan oleh environment Deplexo (default: 8000)
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # 1. Jalankan bot monitoring di background thread (tidak akan blocking web server)
    bot_thread = threading.Thread(target=main_loop, daemon=True)
    bot_thread.start()
    
    # 2. Jalankan web server Flask di thread utama
    run_flask()