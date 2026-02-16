from flask import Flask
import threading
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/ping')
def ping():
    return "OK"

def run_bot():
    # اینجا فایل اصلی بات رو اجرا کن
    os.system("python bot.py")

if __name__ == "__main__":
    # بات رو در یک thread جدا اجرا کن
    threading.Thread(target=run_bot, daemon=True).start()
    # وب سرور رو راه بنداز
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
