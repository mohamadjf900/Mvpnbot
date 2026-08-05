from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
import config
from utils.helpers import back_button
import database as db

router = Router()

async def show_dns_list(message_or_callback):
    text = "🎮 **DNSهای پیشنهادی:**\n\n"
    for dns in config.DNS_LIST:
        game_tag = "✅ مناسب بازی" if dns['for_gaming'] else ""
        text += f"🔹 {dns['name']}: {dns['primary']} و {dns['secondary']} {game_tag}\n"
    text += "\nبرای استفاده، DNS سیستم خود را تغییر دهید."
    
    if isinstance(message_or_callback, Message):
        await message_or_callback.answer(text, reply_markup=back_button())
    else:
        await message_or_callback.message.edit_text(text, reply_markup=back_button())

@router.message(F.text == "🎮 DNS")
async def dns_menu_message(message: Message):
    await db.update_activity(message.from_user.id)
    await db.log_usage(message.from_user.id, "dns")
    await show_dns_list(message)

@router.callback_query(F.data == "menu_dns")
async def dns_menu_callback(callback: CallbackQuery):
    await db.update_activity(callback.from_user.id)
    await db.log_usage(callback.from_user.id, "dns")
    await show_dns_list(callback)
    await callback.answer()
