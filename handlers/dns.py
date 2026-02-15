from aiogram import Router, F
from aiogram.types import CallbackQuery
import config
from utils.helpers import back_button
import database as db

router = Router()

@router.callback_query(F.data == "menu_dns")
async def dns_menu(callback: CallbackQuery):
    await db.update_activity(callback.from_user.id)
    await db.log_usage(callback.from_user.id, "dns")
    text = "🎮 DNSهای پیشنهادی برای گیمرها:\n\n"
    for dns in config.DNS_LIST:
        game_tag = "✅ مناسب بازی" if dns['for_gaming'] else ""
        text += f"🔹 {dns['name']}: {dns['primary']} و {dns['secondary']} {game_tag}\n"
    text += "\nبرای استفاده، DNS سیستم خود را تغییر دهید."
    await callback.message.edit_text(text, reply_markup=back_button())
    await callback.answer()
