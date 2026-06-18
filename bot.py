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
restart_event = asyncio.Event()

def signal_handler(sig, frame):
    global stop_polling
    logger.warning(f"Received signal {sig}, stopping polling gracefully...")
    stop_polling = True
    restart_event.set()

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

# ========== ساخت یک‌باره دیسپچر ==========
async def build_dispatcher():
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
    
    return dp

# ========== اجرای ربات ==========
async def main():
    global stop_polling
    
    await start_health_server()
    await init_db()
    
    bot = Bot(token=BOT_TOKEN)
    dp = await build_dispatcher()
    await set_commands(bot)
    logger.info("✅ Bot and dispatcher initialized.")
    
    while True:
        try:
            logger.info("✅ Starting polling...")
            polling_task = asyncio.create_task(dp.start_polling(bot, handle_signals=False))
            
            # منتظر سیگنال یا Event
            await restart_event.wait()
            
            # توقف polling
            logger.info("🛑 Stopping polling...")
            polling_task.cancel()
            try:
                await polling_task
            except asyncio.CancelledError:
                pass
            
            # بستن کامل session بات
            await bot.session.close()
            logger.info("✅ Bot session closed.")
            
            # ایجاد session جدید
            bot = Bot(token=BOT_TOKEN)
            logger.info("✅ New bot session created.")
            
            # ریست فلگ و Event
            stop_polling = False
            restart_event.clear()
            
            # تأخیر ۵ ثانیه برای اطمینان از بسته شدن کامل اتصال قبلی
            logger.info("🔄 Waiting 5 seconds before restart...")
            await asyncio.sleep(5)
            
        except Exception as e:
            logger.error(f"❌ Critical error: {e}\n{traceback.format_exc()}")
            logger.info("🔄 Restarting in 5 seconds due to error...")
            await asyncio.sleep(5)
            # ریست Event و فلگ
            stop_polling = False
            restart_event.clear()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
