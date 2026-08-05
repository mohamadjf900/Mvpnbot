from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import database as db
from utils.helpers import back_button

router = Router()

async def show_proxy_list(message_or_callback):
    """نمایش لیست پروکسی‌ها (هم برای Message و هم CallbackQuery)"""
    proxies = await db.get_active_proxies(limit=50)
    if not proxies:
        text = "❌ در حال حاضر پروکسی فعالی موجود نیست.\nلطفاً بعداً مراجعه کنید."
        if isinstance(message_or_callback, Message):
            await message_or_callback.answer(text, reply_markup=back_button())
        else:
            await message_or_callback.message.edit_text(text, reply_markup=back_button())
        return
    
    text = "🔹 **لیست پروکسی‌های فعال:**\n\n"
    for p in proxies:
        if "url" in p and p["url"]:
            text += f"🔗 {p['remarks']}: {p['url'][:50]}...\n"
        else:
            text += f"🔸 {p['type']} {p['ip']}:{p['port']}\n"
    
    if isinstance(message_or_callback, Message):
        await message_or_callback.answer(text, reply_markup=back_button())
    else:
        await message_or_callback.message.edit_text(text, reply_markup=back_button())

@router.message(F.text == "🚀 پروکسی")
async def proxy_menu_message(message: Message):
    await db.update_activity(message.from_user.id)
    await db.log_usage(message.from_user.id, "proxy")
    await show_proxy_list(message)

@router.callback_query(F.data == "menu_proxy")
async def proxy_menu_callback(callback: CallbackQuery):
    await db.update_activity(callback.from_user.id)
    await db.log_usage(callback.from_user.id, "proxy")
    await show_proxy_list(callback)
    await callback.answer()
