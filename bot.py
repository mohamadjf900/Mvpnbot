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

# --- تعریف یک استثنا برای خروج از حلقه Polling ---
class PollingStop(Exception):
    pass

# --- Handler جدید برای سیگنال SIGTERM ---
def signal_handler(sig, frame):
    logger.warning(f"Received signal {sig}, stopping polling gracefully...")
    # با پرتاب این استثنا، حلقه while آن را گرفته و دوباره شروع می‌کند
    raise PollingStop("SIGTERM received")

# ثبت handler برای سیگنال SIGTERM
signal.signal(signal.SIGTERM, signal_handler)

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
    while True:
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
            # غیرفعال کردن مدیریت سیگنال توسط aiogram
            await dp.start_polling(bot, handle_signals=False)
            
        except PollingStop:
            logger.info("🔄 Polling stopped by signal. Restarting...")
            # در اینجا نیازی به sleep نیست، چون حلقه while دوباره اجرا می‌شود
            continue
        except Exception as e:
            logger.error(f"❌ Polling stopped with error: {e}\n{traceback.format_exc()}")
            logger.info("🔄 Restarting in 5 seconds due to error...")
            await asyncio.sleep(5)
        finally:
            # اگر به هر دلیل حلقه شکست، ۵ ثانیه صبر کن و دوباره تلاش کن
            if not isinstance(e, PollingStop):
                logger.info("🔄 Restarting main loop...")
                await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main_loop())
