import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Config
TOKEN = os.getenv("BOT_TOKEN")

@app.route('/')
def home():
    return "Bot is Running!"

@app.route('/set_webhook')
def set_webhook():
    # Aapka Vercel URL yahan automatic detect hoga
    domain = request.host_url.replace('http://', 'https://')
    url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={domain}"
    r = requests.get(url)
    return r.json()

@app.route('/', methods=['POST'])
def telegram_update():
    if request.method == "POST":
        update = request.get_json()
        
        # Simple Reply Logic (Sirf test ke liye)
        if "message" in update:
            chat_id = update["message"]["chat"]["id"]
            text = update["message"].get("text", "")
            
            if text == "/start":
                msg = "Vercel par aapka swagat hai! 🚀 Ab hum series logic add karenge."
                requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={msg}")
        
        return jsonify({"status": "ok"}), 200

# Vercel ko ye line chahiye hoti hai
app_handle = app
