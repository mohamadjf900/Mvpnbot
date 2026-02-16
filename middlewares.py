from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Callable, Dict, Any, Awaitable
import config

class CheckSubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        if hasattr(event, "text") and event.text:
            if event.text.startswith("/start") or user.id in config.ADMIN_IDS:
                return await handler(event, data)

        bot = data["bot"]
        try:
            member = await bot.get_chat_member(chat_id=config.CHANNEL_ID, user_id=user.id)
            if member.status in ["left", "kicked"]:
                raise Exception("not member")
        except:
            keyboard = InlineKeyboardBuilder()
            keyboard.add(InlineKeyboardButton(text="📢 عضویت در کانال", url=config.CHANNEL_LINK))
            keyboard.add(InlineKeyboardButton(text="✅ عضو شدم", callback_data="check_join"))
            keyboard.adjust(1)
            await event.answer(
                "🔒 برای استفاده از ربات باید در کانال ما عضو شوید.\nپس از عضویت، دکمه «عضو شدم» را بزنید.",
                reply_markup=keyboard.as_markup()
            )
            return
        return await handler(event, data)
