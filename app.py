from flask import Flask
import threading
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7!"

@app.route('/ping')
def ping():
    return "OK"

def run_bot():
    # اجرای فایل اصلی ربات
    os.system("python bot.py")

if __name__ == "__main__":
    # اجرای ربات در یک Thread جداگانه
    threading.Thread(target=run_bot, daemon=True).start()
    
    # اجرای سرور وب روی پورتی که رندر مشخص می‌کند
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
