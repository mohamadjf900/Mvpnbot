import asyncio
import logging
from aiogram import Bot, Dispatcher, F, BaseMiddleware
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery
from time import monotonic
import config
import database as db
from handlers import start, proxy, v2ray, wireguard, dns, buy, support, admin, ticket, referral, shop

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== آنتی‌اسپم ==========
class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = 0.6):
        self.rate_limit = rate_limit
        self.last_call: dict[int, float] = {}
    
    async def __call__(self, handler, event, data):
        user = data.get("event_from_user")
        if user is not None:
            now = monotonic()
            last = self.last_call.get(user.id)
            if last is not None and (now - last) < self.rate_limit:
                if isinstance(event, CallbackQuery):
                    await event.answer("⏳ لطفاً کمی آرومتر بزنید!", show_alert=False)
                return
            self.last_call[user.id] = now
        return await handler(event, data)

# ========== راه‌اندازی ==========
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# اضافه کردن Middleware آنتی‌اسپم
dp.message.outer_middleware(ThrottlingMiddleware(rate_limit=0.7))
dp.callback_query.outer_middleware(ThrottlingMiddleware(rate_limit=0.4))

# ========== ثبت روت‌ها ==========
dp.include_router(start.router)
dp.include_router(proxy.router)
dp.include_router(v2ray.router)
dp.include_router(wireguard.router)
dp.include_router(dns.router)
dp.include_router(buy.router)
dp.include_router(support.router)
dp.include_router(admin.router)
dp.include_router(ticket.router)
dp.include_router(referral.router)
dp.include_router(shop.router)  # سیستم فروشگاهی

# ========== اجرا ==========
async def main():
    await db.init_db()
    await bot.set_my_commands([
        ("start", "شروع مجدد"),
        ("coupon", "استفاده از کد تخفیف"),
    ])
    logger.info("✅ Bot started!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
