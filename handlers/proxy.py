from aiogram import Router, F
from aiogram.types import CallbackQuery
import database as db
from utils.helpers import back_button

router = Router()

@router.callback_query(F.data == "menu_proxy")
async def proxy_menu(callback: CallbackQuery):
    await db.update_activity(callback.from_user.id)
    await db.log_usage(callback.from_user.id, "proxy")
    proxies = await db.get_active_proxies(limit=15)
    if not proxies:
        text = "در حال حاضر پروکسی فعالی موجود نیست.\nلطفاً بعداً مراجعه کنید."
    else:
        text = "🔹 لیست پروکسی‌های فعال:\n\n"
        for p in proxies:
            text += f"{p['type']}  {p['ip']}:{p['port']}\n"
        text += "\n⚠️ ممکن است برخی غیرفعال شوند."
    await callback.message.edit_text(text, reply_markup=back_button())
    await callback.answer()
