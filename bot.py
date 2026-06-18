import os
import telebot
from telebot import types
import json
import sqlite3
from threading import Thread
from flask import Flask
from config import BOT_TOKEN, CHANNEL_ID
from database import *
from middlewares import *

# اتصال به توکن ربات از طریق متغیرهای محیطی رندر
bot = telebot.TeleBot(os.getenv('BOT_TOKEN', BOT_TOKEN))

# --- بخش فیک سرور وب برای زنده نگه داشتن رندر ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running 24/7!"

def run_web_server():
    # رندر خودش پورت را تعیین می‌کند، اگر نبود روی پورت 10000 می‌رود
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web_server)
    t.start()
# ----------------------------------------

# تلاش برای ساخت دیتابیس
try:
    create_db()
except NameError:
    try:
        setup_db()
    except NameError:
        pass

# لود کردن خودکار هندلرها
try:
    from handlers import start, proxy, v2ray, wireguard, dns, buy, support, admin, ticket
    for handler in [start, proxy, v2ray, wireguard, dns, buy, support, admin, ticket]:
        if hasattr(handler, 'register_handlers'):
            handler.register_handlers(bot)
except Exception as e:
    print(f"Note on handlers: {e}")

if __name__ == "__main__":
    print("--- Starting Web Server for Render ---")
    keep_alive() # روشن کردن سرور وب در پس‌زمینه
    
    print("--- Robot Started Successfully on Render! ---")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
