from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import database as db
from utils.helpers import back_button

router = Router()

@router.callback_query(F.data == "menu_proxy")
async def proxy_menu(callback: CallbackQuery):
    await db.update_activity(callback.from_user.id)
    await db.log_usage(callback.from_user.id, "proxy")
    
    proxies = await db.get_active_proxies(limit=30)
    if not proxies:
        await callback.message.edit_text(
            "در حال حاضر پروکسی فعالی موجود نیست.\nلطفاً بعداً مراجعه کنید.",
            reply_markup=back_button()
        )
        await callback.answer()
        return
    
    builder = InlineKeyboardBuilder()
    for p in proxies:
        if "url" in p and p["url"]:
            # لینک مستقیم
            button_text = p['remarks'] if p['remarks'] else "پروکسی"
            builder.add(InlineKeyboardButton(text=button_text, url=p['url']))
        else:
            # پروکسی معمولی
            button_text = f"{p['type']} {p['ip']}:{p['port']}"
            builder.add(InlineKeyboardButton(text=button_text, callback_data="proxy_info"))
    
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data="menu_main"))
    
    await callback.message.edit_text(
        "🔹 **پروکسی‌های فعال:**\nروی هر دکمه کلیک کنید تا پروکسی فعال شود.",
        reply_markup=builder.as_markup()
    )
    await callback.answer()
