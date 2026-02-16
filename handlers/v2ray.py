from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import database as db
from utils.helpers import back_button
import logging

router = Router()

@router.callback_query(F.data == "menu_v2ray")
async def v2ray_menu(callback: CallbackQuery):
    await db.update_activity(callback.from_user.id)
    await db.log_usage(callback.from_user.id, "v2ray")
    
    try:
        configs = await db.get_all_v2ray()
        logging.info(f"V2Ray configs fetched: {len(configs) if configs else 0}")
    except Exception as e:
        logging.error(f"Error fetching v2ray configs: {e}")
        await callback.message.edit_text(
            "❌ خطا در دریافت کانفیگ‌ها. لطفاً بعداً تلاش کنید.",
            reply_markup=back_button()
        )
        await callback.answer()
        return
    
    if not configs:
        await callback.message.edit_text(
            "📡 کانفیگ V2Ray رایگان در حال حاضر موجود نیست.",
            reply_markup=back_button()
        )
        await callback.answer()
        return

    # ساخت متن با فرمت مناسب برای کپی
    text = "📡 کانفیگ‌های V2Ray:\n\n"
    for idx, c in enumerate(configs, 1):
        text += f"{idx}. {c['remarks']}:\n`{c['link']}`\n\n"
    
    # دکمه بازگشت
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔙 بازگشت", callback_data="menu_main"))
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup()
    )
    await callback.answer()
