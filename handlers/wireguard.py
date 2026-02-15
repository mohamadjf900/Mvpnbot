from aiogram import Router, F
from aiogram.types import CallbackQuery
import database as db
from utils.helpers import back_button

router = Router()

@router.callback_query(F.data == "menu_wireguard")
async def wireguard_menu(callback: CallbackQuery):
    await db.update_activity(callback.from_user.id)
    await db.log_usage(callback.from_user.id, "wireguard")
    configs = await db.get_all_wireguard()
    if not configs:
        text = "کانفیگ WireGuard رایگان در حال حاضر موجود نیست."
    else:
        text = "🔒 کانفیگ‌های WireGuard:\n\n"
        for c in configs:
            text += f"🔸 {c['remarks']}:\n`{c['config']}`\n\n"
    await callback.message.edit_text(text, reply_markup=back_button())
    await callback.answer()
