from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
import database as db

router = Router()

@router.message(Command("invite"))
async def invite_command(message: Message):
    user_id = message.from_user.id
    code = await db.get_referral_code(user_id)
    if not code:
        code = await db.create_referral_code(user_id)
    
    bot_username = (await message.bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?start=ref_{code}"
    count = await db.get_referral_count(user_id)
    
    text = (
        f"👥 **سیستم دعوت دوستان**\n\n"
        f"لینک دعوت شما:\n`{invite_link}`\n\n"
        f"📊 تعداد دعوت‌های موفق: **{count}**\n"
        f"🎁 پاداش هر دعوت: ۱ کانفیگ اختصاصی\n\n"
        f"📋 برای کپی لینک، روی دکمه زیر کلیک کنید."
    )
    
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="📋 کپی لینک", callback_data="copy_invite_link"))
    builder.add(InlineKeyboardButton(text="🔙 بازگشت", callback_data="menu_main"))
    builder.adjust(1)
    
    await message.answer(text, reply_markup=builder.as_markup())

@router.callback_query(F.data == "menu_invite")
async def invite_menu(callback: CallbackQuery):
    await invite_command(callback.message)
    await callback.answer()

@router.callback_query(F.data == "copy_invite_link")
async def copy_invite_link(callback: CallbackQuery):
    user_id = callback.from_user.id
    code = await db.get_referral_code(user_id)
    if not code:
        code = await db.create_referral_code(user_id)
    bot_username = (await callback.bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?start=ref_{code}"
    await callback.answer(f"🔗 لینک دعوت شما:\n{invite_link}", show_alert=True)
