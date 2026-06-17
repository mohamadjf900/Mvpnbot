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
import keep_alive

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flag برای کنترل خروج از حلقه
should_stop = False

def signal_handler(sig, frame):
    global should_stop
    logger.warning(f"Received signal {sig}, stopping polling gracefully...")
    should_stop = True
    # با این کار حلقه asyncio را مجبور به توقف می‌کنیم
    raise KeyboardInterrupt()

# ثبت handler برای سیگنال‌ها
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="شروع مجدد"),
        BotCommand(command="stats", description="آمار (فقط ادمین)"),
        BotCommand(command="broadcast", description="ارسال همگانی (ادمین)"),
        BotCommand(command="ticket", description="سیستم پشتیبانی"),
        BotCommand(command="mytickets", description="تیکت‌های من"),
    ]
    await bot.set_my_commands(commands)

async def main_loop():
    global should_stop
    while not should_stop:
        try:
            logger.info("🚀 Starting keep-alive server...")
            keep_alive.start_server()
            
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
            # این استثنا توسط signal_handler پرتاب می‌شود
            logger.info("🔄 Polling stopped by signal. Restarting...")
            # فلگ should_stop را ریست می‌کنیم تا حلقه دوباره اجرا شود
            should_stop = False
            continue
        except Exception as e:
            logger.error(f"❌ Polling stopped with error: {e}\n{traceback.format_exc()}")
            logger.info("🔄 Restarting in 5 seconds due to error...")
            await asyncio.sleep(5)
        finally:
            # اگر به دلیل خطا یا سیگنال حلقه متوقف شد، ۵ ثانیه صبر کن و دوباره تلاش کن
            if not should_stop:
                logger.info("🔄 Restarting main loop...")
                await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main_loop())
