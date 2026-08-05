import os
from dotenv import load_dotenv

load_dotenv()

# ========== تنظیمات اصلی ==========
BOT_TOKEN = os.getenv("BOT_TOKEN", "8389885213:AAG4WUqbtwOZOG8lYO-hf95WcX2nt0h_BPk")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "765318133").split(',')))
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-1003730654738"))  # اصلاح شد (دو - حذف شد)
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/mvpni7")  # اصلاح شد (تکراری حذف شد)

# ========== اطلاعات برند و پشتیبانی ==========
BRAND_NAME = os.getenv("BRAND_NAME", "Mvpn")
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "Mj054")  # بدون @

# ========== تنظیمات دیتابیس ==========
DB_PATH = os.getenv("DB_PATH", "bot.db")

# ========== تنظیمات رفرال ==========
REFERRAL_REQUIRED_COUNT = int(os.getenv("REFERRAL_REQUIRED_COUNT", "3"))
REFERRAL_REWARD_VOLUME = int(os.getenv("REFERRAL_REWARD_VOLUME", "50"))

# ========== پلن‌های پیش‌فرض ==========
DEFAULT_GAMING_PLANS = [
    (10, 70000),   # (حجم به گیگ, قیمت به تومان)
    (20, 140000),
    (30, 210000),
    (40, 280000),
    (50, 350000),
]

DEFAULT_MULTI_PLANS = [
    ("تک کاربره نامحدود یکماهه", 150000),
    ("دو کاربره نامحدود یکماهه", 250000),
    ("تک کاربره نامحدود دوماهه", 250000),
    ("دو کاربره نامحدود دوماهه", 450000),
]

# ========== تنظیمات DNS ==========
DNS_LIST = [
    {"name": "Google", "primary": "8.8.8.8", "secondary": "8.8.4.4", "for_gaming": False},
    {"name": "Cloudflare", "primary": "1.1.1.1", "secondary": "1.0.0.1", "for_gaming": True},
    {"name": "OpenDNS", "primary": "208.67.222.222", "secondary": "208.67.220.220", "for_gaming": False},
    {"name": "Quad9", "primary": "9.9.9.9", "secondary": "149.112.112.112", "for_gaming": False},
]
