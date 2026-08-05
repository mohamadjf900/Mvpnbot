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
    
    proxies = await db.get_active_proxies(limit=50)
    if not proxies:
        await callback.message.edit_text(
            "❌ در حال حاضر پروکسی فعالی موجود نیست.\n"
            "لطفاً بعداً مراجعه کنید یا با ادمین تماس بگیرید.",
            reply_markup=back_button()
        )
        await callback.answer()
        return
    
    # جدا کردن پروکسی‌های لینکی و معمولی
    link_proxies = [p for p in proxies if "url" in p and p["url"]]
    normal_proxies = [p for p in proxies if "url" not in p or not p["url"]]
    
    builder = InlineKeyboardBuilder()
    
    # نمایش لینک‌های مستقیم (اولویت)
    if link_proxies:
        builder.add(InlineKeyboardButton(text="🔗━━━ لینک‌ها ━━━", callback_data="dummy"))
        for p in link_proxies:
            button_text = p['remarks'] if p['remarks'] else "پروکسی"
            builder.add(InlineKeyboardButton(text=button_text, url=p['url']))
    
    # نمایش پروکسی‌های معمولی
    if normal_proxies:
        if link_proxies:
            builder.add(InlineKeyboardButton(text="📡━━━ معمولی ━━━", callback_data="dummy"))
        for p in normal_proxies:
            button_text = f"{p['type']} {p['ip']}:{p['port']}"
            # برای پروکسی‌های معمولی از لینک tg:// استفاده می‌کنیم
            proxy_link = f"tg://proxy?server={p['ip']}&port={p['port']}"
            builder.add(InlineKeyboardButton(text=button_text, url=proxy_link))
    
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data="menu_main"))
    
    await callback.message.edit_text(
        "🔹 **پروکسی‌های فعال:**\n"
        "• روی دکمه‌ها کلیک کنید تا پروکسی فعال شود.\n"
        "• لینک‌ها مستقیماً در تلگرام فعال می‌شوند.",
        reply_markup=builder.as_markup()
    )
    await callback.answer()
