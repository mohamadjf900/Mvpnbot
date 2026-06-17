import asyncio
import logging
import traceback
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from config import BOT_TOKEN
from handlers import start, proxy, v2ray, wireguard, dns, buy, support, admin, ticket
from middlewares import CheckSubscriptionMiddleware
from database import init_db
import keep_alive

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    # حلقه بی‌نهایت برای راه‌اندازی مجدد خودکار
    while True:
        try:
            logger.info("🚀 Starting keep-alive server...")
            keep_alive.start_server()
            
            logger.info("📂 Initializing database...")
            await init_db()
            
            logger.info("🤖 Creating bot instance...")
            bot = Bot(token=BOT_TOKEN)
            dp = Dispatcher()

            # اضافه کردن Middleware
            dp.message.middleware(CheckSubscriptionMiddleware())
            dp.callback_query.middleware(CheckSubscriptionMiddleware())

            # اضافه کردن روت‌ها
            dp.include_router(start.router)
            dp.include_router(proxy.router)
            dp.include_router(v2ray.router)
            dp.include_router(wireguard.router)
            dp.include_router(dns.router)
            dp.include_router(buy.router)
            dp.include_router(support.router)
            dp.include_router(admin.router)
            dp.include_router(ticket.router)

            await set_commands(bot)
            
            logger.info("✅ Starting polling...")
            await dp.start_polling(bot)
            
        except Exception as e:
            logger.error(f"❌ Polling stopped with error: {e}\n{traceback.format_exc()}")
            logger.info("🔄 Restarting in 5 seconds...")
            await asyncio.sleep(5)
        finally:
            # در صورت خروج از try یا بروز خطا، دوباره تلاش کن
            logger.info("🔄 Restarting main loop...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
