import os
import requests
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes

app = Flask(__name__)

# Config
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)

# Vercel Serverless Function
@app.route('/', methods=['POST'])
async def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        
        # Yahan aap apna bot logic daal sakte hain
        if update.message and update.message.text == "/start":
            await bot.send_message(chat_id=update.message.chat_id, text="Vercel par aapka swagat hai! 🚀")
            
        return "ok", 200
    return "error", 400

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    # Ye URL aapko Vercel se milega deploy hone ke baad
    webhook_url = "https://aapka-app-name.vercel.app/"
    s = requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}")
    if s.status_code == 200:
        return "Webhook Set Success!", 200
    return "Webhook Set Failed!", 400
