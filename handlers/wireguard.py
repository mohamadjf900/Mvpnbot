from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, FSInputFile, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import database as db
from utils.helpers import back_button
import tempfile
import os

router = Router()

async def show_wireguard_list(message_or_callback):
    configs = await db.get_all_wireguard()
    if not configs:
        text = "🔒 کانفیگ WireGuard رایگان در حال حاضر موجود نیست."
        if isinstance(message_or_callback, Message):
            await message_or_callback.answer(text, reply_markup=back_button())
        else:
            await message_or_callback.message.edit_text(text, reply_markup=back_button())
        return
    
    # اگر پیام از نوع Message باشد
    if isinstance(message_or_callback, Message):
        for c in configs:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False, encoding='utf-8') as tmp:
                tmp.write(c['config'])
                tmp_path = tmp.name
            document = FSInputFile(tmp_path, filename=f"{c['remarks']}.conf")
            await message_or_callback.answer_document(
                document,
                caption=f"🔸 {c['remarks']}\nفایل کانفیگ WireGuard را دانلود کنید."
            )
            os.unlink(tmp_path)
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="menu_main"))
        await message_or_callback.answer("برای بازگشت به منوی اصلی:", reply_markup=builder.as_markup())
        return
    
    # اگر CallbackQuery باشد
    await message_or_callback.message.delete()
    for c in configs:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False, encoding='utf-8') as tmp:
            tmp.write(c['config'])
            tmp_path = tmp.name
        document = FSInputFile(tmp_path, filename=f"{c['remarks']}.conf")
        await message_or_callback.message.answer_document(
            document,
            caption=f"🔸 {c['remarks']}\nفایل کانفیگ WireGuard را دانلود کنید."
        )
        os.unlink(tmp_path)
    
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="menu_main"))
    await message_or_callback.message.answer("برای بازگشت به منوی اصلی:", reply_markup=builder.as_markup())
    await message_or_callback.answer()

@router.message(F.text == "🔒 WireGuard")
async def wireguard_menu_message(message: Message):
    await db.update_activity(message.from_user.id)
    await db.log_usage(message.from_user.id, "wireguard")
    await show_wireguard_list(message)

@router.callback_query(F.data == "menu_wireguard")
async def wireguard_menu_callback(callback: CallbackQuery):
    await db.update_activity(callback.from_user.id)
    await db.log_usage(callback.from_user.id, "wireguard")
    await show_wireguard_list(callback)
    await callback.answer()
