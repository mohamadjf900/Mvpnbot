import asyncio
import logging
import traceback
import signal
import sys
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from config import BOT_TOKEN
from handlers import start, proxy, v2ray, wireguard, dns, buy, support, admin, ticket
from middlewares import CheckSubscriptionMiddleware
from database import init_db
from aiohttp import web

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== Health Check ==========
async def health_check(request):
    return web.Response(text="OK")

async def start_health_server():
    app = web.Application()
    app.router.add_get('/health', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()
    logger.info("✅ Health check server running on port 10000")

# ========== مدیریت سیگنال ==========
stop_polling = False

def signal_handler(sig, frame):
    global stop_polling
    logger.warning(f"Received signal {sig}, stopping polling gracefully...")
    stop_polling = True

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# ========== دستورات ربات ==========
async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="شروع مجدد"),
        BotCommand(command="stats", description="آمار (فقط ادمین)"),
        BotCommand(command="broadcast", description="ارسال همگانی (ادمین)"),
        BotCommand(command="ticket", description="سیستم پشتیبانی"),
        BotCommand(command="mytickets", description="تیکت‌های من"),
    ]
    await bot.set_my_commands(commands)

# ========== اجرای ربات ==========
async def run_bot():
    global stop_polling
    
    while True:
        try:
            logger.info("📂 Initializing database...")
            await init_db()
            
            logger.info("🤖 Creating bot instance...")
            bot = Bot(token=BOT_TOKEN)
            dp = Dispatcher()

            dp.message.middleware(CheckSubscriptionMiddleware())
            dp.callback_query.middleware(CheckSubscriptionMiddleware())

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
            
            # راه‌اندازی Health Check
            asyncio.create_task(start_health_server())
            
            logger.info("✅ Starting polling...")
            # شروع Polling بدون مدیریت سیگنال
            polling_task = asyncio.create_task(dp.start_polling(bot, handle_signals=False))
            
            # منتظر می‌مانیم تا سیگنال یا خطا رخ دهد
            while not stop_polling:
                await asyncio.sleep(1)
            
            # دریافت SIGTERM: متوقف کردن Polling
            logger.info("🛑 Stopping polling due to signal...")
            polling_task.cancel()
            try:
                await polling_task
            except asyncio.CancelledError:
                pass
            
            # ریست کردن فلگ برای دفعه بعد
            stop_polling = False
            
            # بستن اتصال بات
            await bot.session.close()
            
            logger.info("🔄 Restarting in 2 seconds...")
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"❌ Critical error: {e}\n{traceback.format_exc()}")
            logger.info("🔄 Restarting in 5 seconds due to error...")
            await asyncio.sleep(5)

# ========== نقطه ورود ==========
if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
