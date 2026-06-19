from flask import Flask
import threading
import os
import subprocess
import time
import requests

app = Flask(__name__)

# آدرس اختصاصی رندر شما برای پینگ داخلی
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "https://mvpnbot-3.onrender.com")

@app.route('/')
def home():
    return "Bot is running 24/7 with Ticket and Self-Ping Systems!"

@app.route('/ping')
def ping():
    return "OK"

# بیدارباش داخلی هوشمند
def self_ping_loop():
    time.sleep(60) # ۱ دقیقه صبر برای لایو شدن کانتینر داکر
    print("--- Internal Self-Ping Active ---")
    while True:
        try:
            url = f"{RENDER_URL}/ping"
            response = requests.get(url, timeout=10)
            print(f"Self-ping successful. Status: {response.status_code}")
        except Exception as e:
            print(f"Self-ping warning: {e}")
        
        time.sleep(300) # هر ۵ دقیقه یک‌بار پینگ بفرست

def run_bot_process():
    subprocess.run(["python", "bot.py"])

if __name__ == "__main__":
    # ۱. اجرای سیستم بیدارباش در پس‌زمینه
    threading.Thread(target=self_ping_loop, daemon=True).start()

    # ۲. اجرای ربات آیوگرام در پس‌زمینه
    threading.Thread(target=run_bot_process, daemon=True).start()
    
    # ۳. روشن شدن وب‌سرور فِلسک روی پورت رندر
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
