from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
import database as db
from utils.helpers import back_button
import qrcode
from io import BytesIO

router = Router()

async def generate_qr_code(data: str) -> BufferedInputFile:
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=8, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    bio = BytesIO()
    img.save(bio, format='PNG')
    bio.seek(0)
    return BufferedInputFile(bio.read(), filename="v2ray_qr.png")

async def show_v2ray_list(message_or_callback):
    configs = await db.get_all_v2ray()
    if not configs:
        text = "📡 کانفیگ V2Ray رایگان در حال حاضر موجود نیست.\nلطفاً بعداً مراجعه کنید."
        if isinstance(message_or_callback, Message):
            await message_or_callback.answer(text, reply_markup=back_button())
        else:
            await message_or_callback.message.edit_text(text, reply_markup=back_button())
        return
    
    # اگر پیام از نوع Message باشد، نمی‌توانیم QR کد را edit کنیم
    if isinstance(message_or_callback, Message):
        for c in configs:
            qr_file = await generate_qr_code(c['link'])
            caption = f"🔸 **{c['remarks']}**\n\n`{c['link'][:100]}...`\n\n📱 QR کد را اسکن کنید."
            await message_or_callback.answer_photo(photo=qr_file, caption=caption)
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="menu_main"))
        await message_or_callback.answer("برای بازگشت به منوی اصلی:", reply_markup=builder.as_markup())
        return
    
    # اگر CallbackQuery باشد
    await message_or_callback.message.delete()
    for idx, c in enumerate(configs, 1):
        qr_file = await generate_qr_code(c['link'])
        caption = f"🔸 **{c['remarks']}**\n\n`{c['link'][:100]}...`\n\n📱 QR کد را اسکن کنید."
        if idx == len(configs):
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="menu_main"))
            await message_or_callback.message.answer_photo(photo=qr_file, caption=caption, reply_markup=builder.as_markup())
        else:
            await message_or_callback.message.answer_photo(photo=qr_file, caption=caption)
    await message_or_callback.answer()

@router.message(F.text == "📡 V2Ray")
async def v2ray_menu_message(message: Message):
    await db.update_activity(message.from_user.id)
    await db.log_usage(message.from_user.id, "v2ray")
    await show_v2ray_list(message)

@router.callback_query(F.data == "menu_v2ray")
async def v2ray_menu_callback(callback: CallbackQuery):
    await db.update_activity(callback.from_user.id)
    await db.log_usage(callback.from_user.id, "v2ray")
    await show_v2ray_list(callback)
    await callback.answer()
