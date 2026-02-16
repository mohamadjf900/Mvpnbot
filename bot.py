import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from config import BOT_TOKEN
from handlers import start, proxy, v2ray, wireguard, dns, buy, support, admin
from middlewares import CheckSubscriptionMiddleware
from database import init_db
import keep_alive  # <-- این خط جدید است

logging.basicConfig(level=logging.INFO)

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="شروع مجدد"),
        BotCommand(command="stats", description="آمار (فقط ادمین)"),
        BotCommand(command="broadcast", description="ارسال همگانی (ادمین)"),
    ]
    await bot.set_my_commands(commands)

async def main():
    keep_alive.start_server()  # <-- این خط جدید است
    await init_db()
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

    await set_commands(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
