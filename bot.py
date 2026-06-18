import asyncio
import logging
import traceback
import signal
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
stop_flag = False

def signal_handler(sig, frame):
    global stop_flag
    logger.warning(f"Received signal {sig}, stopping gracefully...")
    stop_flag = True
    raise KeyboardInterrupt()

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

# ========== حلقه اصلی ==========
async def main_loop():
    global stop_flag
    
    # راه‌اندازی Health Check در پس‌زمینه
    asyncio.create_task(start_health_server())
    
    while not stop_flag:
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
            
            logger.info("✅ Starting polling...")
            await dp.start_polling(bot, handle_signals=False)
            
        except KeyboardInterrupt:
            logger.info("🔄 Polling stopped by signal. Restarting...")
            # فلگ را ریست می‌کنیم تا دوباره اجرا شود
            stop_flag = False
            continue
        except Exception as e:
            logger.error(f"❌ Polling stopped with error: {e}\n{traceback.format_exc()}")
            logger.info("🔄 Restarting in 5 seconds due to error...")
            await asyncio.sleep(5)
        finally:
            if not stop_flag:
                logger.info("🔄 Restarting main loop...")
                await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main_loop())
