from flask import Flask
import threading
import os
import subprocess
import time
import requests

app = Flask(__name__)

# آدرس رندر شما برای سیستم بیدارباش خودکار
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "https://mvpnbot-3.onrender.com")

@app.route('/')
def home():
    return "Aiogram VPN Bot with Ticket System is running 24/7!"

@app.route('/ping')
def ping():
    return "OK"

# سیستم خودکفا برای بیدار نگه داشتن سرور توسط خودش
def self_ping():
    time.sleep(60) # ۱ دقیقه صبر برای لایو شدن کامل سرور
    print("--- Self-Ping System Activated ---")
    while True:
        try:
            url = f"{RENDER_URL}/ping"
            response = requests.get(url, timeout=10)
            print(f"Self-ping sent. Response: {response.status_code}")
        except Exception as e:
            print(f"Self-ping failed: {e}")
        
        time.sleep(300) # هر ۵ دقیقه یک‌بار

def run_aiogram_bot():
    subprocess.run(["python", "bot.py"])

if __name__ == "__main__":
    # ۱. اجرای سیستم بیدارباش داخلی در پس‌زمینه
    threading.Thread(target=self_ping, daemon=True).start()

    # ۲. اجرای ربات اصلی آیوگرام در پس‌زمینه
    threading.Thread(target=run_aiogram_bot, daemon=True).start()
    
    # ۳. روشن کردن سرور وب Flask
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
