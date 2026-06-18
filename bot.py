import os
import telebot
from telebot import types
import json
import sqlite3
from config import BOT_TOKEN, CHANNEL_ID
from database import *
from middlewares import *

# اتصال به ربات از طریق توکن ست شده در رندر
bot = telebot.TeleBot(os.getenv('BOT_TOKEN', BOT_TOKEN))

# تلاش برای ساخت و تنظیم دیتابیس
try:
    create_db()
except NameError:
    try:
        setup_db()
    except NameError:
        pass

# --- اتصال و فعال‌سازی مستقیم هندلرها بدون ارور کرش ---
import handlers.start
import handlers.proxy
import handlers.v2ray
import handlers.wireguard
import handlers.dns
import handlers.buy
import handlers.support
import handlers.admin
import handlers.ticket

if __name__ == "__main__":
    print("--- Robot Started Successfully on Render! ---")
    # زمان انتظار طولانی‌تر برای پایداری در اینترنت‌های ضعیف
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
