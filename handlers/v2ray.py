from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import database as db
from utils.helpers import back_button

router = Router()

@router.callback_query(F.data == "menu_v2ray")
async def v2ray_menu(callback: CallbackQuery):
    await db.update_activity(callback.from_user.id)
    await db.log_usage(callback.from_user.id, "v2ray")
    
    configs = await db.get_all_v2ray()
    if not configs:
        await callback.message.edit_text(
            "کانفیگ V2Ray رایگان در حال حاضر موجود نیست.",
            reply_markup=back_button()
        )
        await callback.answer()
        return

    text = "📡 کانفیگ‌های V2Ray:\n\n"
    for c in configs:
        text += f"🔸 {c['remarks']}:\n`{c['link']}`\n\n"
    
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔙 بازگشت", callback_data="menu_main"))
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup()
    )
    await callback.answer()
