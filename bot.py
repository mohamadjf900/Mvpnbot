import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from config import BOT_TOKEN
# اضافه کردن ticket به ایمپورت هندلرها
from handlers import start, proxy, v2ray, wireguard, dns, buy, support, admin, ticket
from middlewares import CheckSubscriptionMiddleware
from database import init_db
from utils.proxy_updater import update_proxies_periodically

logging.basicConfig(level=logging.INFO)

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="شروع مجدد"),
        BotCommand(command="stats", description="آمار (فقط ادمین)"),
        BotCommand(command="broadcast", description="ارسال همگانی (ادمین)"),
        BotCommand(command="ticket", description="سیستم پشتیبانی"),
        BotCommand(command="mytickets", description="تیکت‌های من"),
    ]
    await bot.set_my_commands(commands)

async def main():
    # راه‌اندازی دیتابیس ربات
    await init_db()
    
    # خواندن توکن از رندر یا کانفیگ
    token = os.getenv("BOT_TOKEN", BOT_TOKEN)
    bot = Bot(token=token)
    dp = Dispatcher()

    # فعال‌سازی میدلور جوین اجباری
    dp.message.middleware(CheckSubscriptionMiddleware())
    dp.callback_query.middleware(CheckSubscriptionMiddleware())

    # اتصال تمام روترها به دیسپچر اصلی (شامل روتر تیکت)
    dp.include_router(start.router)
    dp.include_router(proxy.router)
    dp.include_router(v2ray.router)
    dp.include_router(wireguard.router)
    dp.include_router(dns.router)
    dp.include_router(buy.router)
    dp.include_router(support.router)
    dp.include_router(admin.router)
    dp.include_router(ticket.router)  # 👈 این خط جا افتاده بود که اضافه شد!

    await set_commands(bot)

    # اجرای آپدیتر پروکسی‌ها در پس‌زمینه
    asyncio.create_task(update_proxies_periodically())

    print("--- Aiogram Bot with Ticket System is Polling Now! ---")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
