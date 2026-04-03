import sqlite3
import requests
import os
import threading
import http.server
import socketserver
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, ConversationHandler
from telegram.request import HTTPXRequest

# --- 1. DUMMY SERVER (Hosting platforms ko active rakhne ke liye) ---
def run_dummy_server():
    PORT = int(os.environ.get("PORT", 8080))
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# --- 2. CONFIG (GitHub par token mat likhna, Environment Variables use karein) ---
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# States
LANG, PLATFORM = range(2)

# Mappings
LANGUAGES = {
    "Hindi 🇮🇳": "hi", 
    "English 🇺🇸": "en", 
    "Korean 🇰🇷": "ko", 
    "Tamil": "ta", 
    "Telugu": "te"
}
PROVIDERS = {
    "Netflix": 8, 
    "Prime Video": 9, 
    "Disney+ Hotstar": 122, 
    "SonyLIV": 237, 
    "Zee5": 309
}

# --- 3. DATABASE ---
def init_db():
    conn = sqlite3.connect('bot_data.db')
    conn.execute('CREATE TABLE IF NOT EXISTS watched (user_id INTEGER, show_id INTEGER)')
    conn.commit()
    conn.close()

# --- 4. BOT FUNCTIONS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(l, callback_data=l)] for l in LANGUAGES.keys()]
    await update.message.reply_text(
        "👋 Welcome! Main aapka Web Series Assistant hoon.\n\nKaunsi **Language** ki series dekhni hai?", 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return LANG

async def select_platform(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    context.user_data['lang'] = LANGUAGES[query.data]
    await query.answer()
    
    keyboard = [[InlineKeyboardButton(p, callback_data=p)] for p in PROVIDERS.keys()]
    await query.edit_message_text(
        "Great! Ab **Platform** select karein:", 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return PLATFORM

async def final_suggestion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    platform_name = query.data
    lang = context.user_data['lang']
    user_id = update.effective_user.id
    
    url = f"https://api.themoviedb.org/3/discover/tv?api_key={TMDB_API_KEY}&with_original_language={lang}&with_watch_providers={PROVIDERS[platform_name]}&watch_region=IN&sort_by=popularity.desc"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
    except Exception as e:
        await query.message.reply_text("Connection error! Please try again later.")
        return ConversationHandler.END

    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    found = False
    for show in data.get('results', []):
        cursor.execute("SELECT 1 FROM watched WHERE user_id = ? AND show_id = ?", (user_id, show['id']))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO watched VALUES (?, ?)", (user_id, show['id']))
            conn.commit()
            
            poster = f"https://image.tmdb.org/t/p/w500{show['poster_path']}" if show.get('poster_path') else None
            caption = f"🎬 *{show['name']}*\n\n⭐ Rating: {show['vote_average']}\n\n📝 {show['overview'][:300]}..."
            
            if poster:
                await query.message.reply_photo(photo=poster, caption=caption, parse_mode='Markdown')
            else:
                await query.message.reply_text(caption, parse_mode='Markdown')
            found = True
            break
    
    if not found:
        await query.message.reply_text("Sab series dekh li hain aapne! Kuch naya try karein.")
    
    conn.close()
    return ConversationHandler.END

# --- 5. MAIN ---
if __name__ == '__main__':
    init_db()
    
    # Network settings for stable connection
    proxy_request = HTTPXRequest(connect_timeout=30, read_timeout=30)
    
    app = ApplicationBuilder().token(BOT_TOKEN).request(proxy_request).get_updates_request(proxy_request).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LANG: [CallbackQueryHandler(select_platform)],
            PLATFORM: [CallbackQueryHandler(final_suggestion)],
        },
        fallbacks=[CommandHandler('start', start)]
    )
    
    app.add_handler(conv_handler)
    print("Bot is LIVE...")
    app.run_polling()

