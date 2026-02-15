from aiogram import Router, F
from aiogram.types import CallbackQuery
from utils.helpers import back_button
import database as db

router = Router()

@router.callback_query(F.data == "menu_buy")
async def buy_menu(callback: CallbackQuery):
    await db.update_activity(callback.from_user.id)
    await db.log_usage(callback.from_user.id, "buy")
    text = (
        "💼 برای خرید کانفیگ اختصاصی یا VPN با کیفیت، با ادمین در ارتباط باشید:\n\n"
        f"🆔 @Mj054 (یوزرنیم ادمین را اینجا قرار دهید)\n\n"
        "یا از طریق ربات پشتیبانی اقدام کنید."
    )
    await callback.message.edit_text(text, reply_markup=back_button())
    await callback.answer()
