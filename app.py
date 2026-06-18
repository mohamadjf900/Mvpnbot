from flask import Flask
import threading
import os
import subprocess
import time
import requests

app = Flask(__name__)

# آدرس رندر شما (اگر در بخش Environment ست نشده باشد، از این آدرس استفاده می‌کند)
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "https://mvpnbot-3.onrender.com")

@app.route('/')
def home():
    return "Aiogram VPN Bot is running 24/7!"

@app.route('/ping')
def ping():
    return "OK"

# --- هک هوشمند برای بیدار نگه داشتن سرور توسط خودش ---
def self_ping():
    # ۱ دقیقه صبر می‌کنیم تا ابتدا سرور کاملاً لایو و مستقر شود
    time.sleep(60)
    print("--- Self-Ping System Activated ---")
    while True:
        try:
            # ارسال درخواست به خودِ سرور (صفحه اصلی یا پینگ)
            url = f"{RENDER_URL}/ping"
            response = requests.get(url, timeout=10)
            print(self_ping)
            print(f"Self-ping sent to {url}. Response: {response.status_code}")
        except Exception as e:
            print(f"Self-ping failed: {e}")
        
        # هر ۵ دقیقه (۳۰۰ ثانیه) یک‌بار این کار را تکرار کن
        time.sleep(300)

def run_aiogram_bot():
    subprocess.run(["python", "bot.py"])

if __name__ == "__main__":
    # ۱. اجرای سیستم سلف-پینگ (بیدارباش داخلی) در پس‌زمینه
    threading.Thread(target=self_ping, daemon=True).start()

    # ۲. اجرای ربات اصلی آیوگرام در پس‌زمینه
    threading.Thread(target=run_aiogram_bot, daemon=True).start()
    
    # ۳. روشن کردن سرور وب Flask
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
