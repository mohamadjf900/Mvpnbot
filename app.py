from flask import Flask
import threading
import os
import subprocess

app = Flask(__name__)

@app.route('/')
def home():
    return "Aiogram VPN Bot is running 24/7!"

@app.route('/ping')
def ping():
    return "OK"

def run_aiogram_bot():
    # اجرای فایل اصلی ربات با استفاده از سیستم‌عامل در یک ترد جداگانه
    subprocess.run(["python", "bot.py"])

if __name__ == "__main__":
    # استارت زدن ربات به صورت موازی با سرور وب
    threading.Thread(target=run_aiogram_bot, daemon=True).start()
    
    # ست کردن پورت رندر
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
