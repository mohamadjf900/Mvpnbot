from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import database as db
from utils.helpers import back_button

router = Router()

async def show_proxy_list(message_or_callback):
    """نمایش لیست پروکسی‌ها با دکمه‌های کلیک‌پذیر"""
    proxies = await db.get_active_proxies(limit=50)
    
    if not proxies:
        text = "❌ در حال حاضر پروکسی فعالی موجود نیست.\nلطفاً بعداً مراجعه کنید."
        if isinstance(message_or_callback, Message):
            await message_or_callback.answer(text, reply_markup=back_button())
        else:
            await message_or_callback.message.edit_text(text, reply_markup=back_button())
        return

    builder = InlineKeyboardBuilder()
    added_count = 0
    
    for p in proxies:
        # ساخت لینک پروکسی
        if "url" in p and p["url"] and p["url"].startswith("https://t.me/proxy?"):
            # لینک مستقیم تلگرام
            link = p["url"]
            label = p["remarks"] if p["remarks"] else "پروکسی"
        else:
            # پروکسی معمولی → ساخت لینک tg://
            ip = p.get("ip")
            port = p.get("port")
            ptype = p.get("type", "HTTP").lower()
            if ip and port:
                link = f"tg://proxy?server={ip}&port={port}&type={ptype}"
                label = f"{ptype.upper()} {ip}:{port}"
            else:
                continue  # اطلاعات کافی نیست
        
        builder.add(InlineKeyboardButton(text=label, url=link))
        added_count += 1
    
    if added_count == 0:
        text = "❌ هیچ پروکسی معتبری یافت نشد."
        if isinstance(message_or_callback, Message):
            await message_or_callback.answer(text, reply_markup=back_button())
        else:
            await message_or_callback.message.edit_text(text, reply_markup=back_button())
        return
    
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data="menu_main"))
    
    if isinstance(message_or_callback, Message):
        await message_or_callback.answer(
            "🔹 **پروکسی‌های فعال:**\nروی هر دکمه کلیک کنید تا پروکسی فعال شود.",
            reply_markup=builder.as_markup()
        )
    else:
        await message_or_callback.message.edit_text(
            "🔹 **پروکسی‌های فعال:**\nروی هر دکمه کلیک کنید تا پروکسی فعال شود.",
            reply_markup=builder.as_markup()
        )
        await message_or_callback.answer()

# ========== هندلر دکمه Reply Keyboard ==========
@router.message(F.text == "🚀 پروکسی")
async def proxy_menu_message(message: Message):
    await db.update_activity(message.from_user.id)
    await db.log_usage(message.from_user.id, "proxy")
    await show_proxy_list(message)

# ========== هندلر دکمه Inline ==========
@router.callback_query(F.data == "menu_proxy")
async def proxy_menu_callback(callback: CallbackQuery):
    await db.update_activity(callback.from_user.id)
    await db.log_usage(callback.from_user.id, "proxy")
    await show_proxy_list(callback)
