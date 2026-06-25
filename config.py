import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "8389885213:AAG4WUqbtwOZOG8lYO-hf95WcX2nt0h_BPk")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "765318133").split(',')))

# 📢 لیست کانال‌های عضویت اجباری (میتوانی بعداً کانال‌های تبلیغاتی را هم اینجا اضافه کنی)
REQUIRED_CHANNELS = [
    {"id": -1003730654738, "link": "https://https://t.me/mvpni7", "name": "📢 کانال اصلی ما"},
   ]

DNS_LIST = [
    {"name": "Google", "primary": "8.8.8.8", "secondary": "8.8.4.4", "for_gaming": False},
    {"name": "Cloudflare", "primary": "1.1.1.1", "secondary": "1.0.0.1", "for_gaming": True},
    {"name": "OpenDNS", "primary": "208.67.222.222", "secondary": "208.67.220.220", "for_gaming": False},
    {"name": "Quad9", "primary": "9.9.9.9", "secondary": "149.112.112.112", "for_gaming": False},
]
