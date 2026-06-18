import os
import telebot
from config import BOT_TOKEN

# این فایل فقط متغیر ربات را برای هندلرها آماده نگه می‌دارد تا چرخه ایمپورت شکسته شود
bot = telebot.TeleBot(os.getenv('BOT_TOKEN', BOT_TOKEN))
