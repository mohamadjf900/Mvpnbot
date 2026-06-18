from flask import Flask
import threading
import os
import telebot
from config import BOT_TOKEN, CHANNEL_ID
from database import *
from middlewares import *

app = Flask(__name__)

# تعریف اصلی ربات در فایل مادر
bot = telebot.TeleBot(os.getenv('BOT_TOKEN', BOT_TOKEN))

@app.route('/')
def home():
    return "Bot is running 24/7!"

@app.route('/ping')
def ping():
    return "OK"

def start_bot():
    print("--- Registering Handlers ---")
    
    # ایمپورت مستقیم هندلرها بعد از ساخته شدن شیء bot
    import handlers.start
    import handlers.proxy
    import handlers.v2ray
    import handlers.wireguard
    import handlers.dns
    import handlers.buy
    import handlers.support
    import handlers.admin
    import handlers.ticket
    
    print("--- Robot Started Successfully on Render! ---")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)

if __name__ == "__main__":
    # تلاش برای راه اندازی دیتابیس
    try:
        create_db()
    except NameError:
        try:
            setup_db()
        except NameError:
            pass

    # اجرای ربات روی یک Thread جداگانه
    threading.Thread(target=start_bot, daemon=True).start()
    
    # اجرای سرور وب روی پورتی که رندر به داکر می‌دهد
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
