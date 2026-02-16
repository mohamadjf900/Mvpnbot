from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import database as db
import logging
import qrcode
from io import BytesIO

router = Router()

async def generate_qr_code(data: str) -> BufferedInputFile:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    bio = BytesIO()
    img.save(bio, format='PNG')
    bio.seek(0)
    return BufferedInputFile(bio.read(), filename="v2ray_qr.png")

@router.callback_query(F.data == "menu_v2ray")
async def v2ray_menu(callback: CallbackQuery):
    await db.update_activity(callback.from_user.id)
    await db.log_usage(callback.from_user.id, "v2ray")
    
    configs = await db.get_all_v2ray()
    if not configs:
        await callback.message.edit_text(
            "📡 کانفیگ V2Ray رایگان در حال حاضر موجود نیست.",
            reply_markup=back_button()
        )
        await callback.answer()
        return

    await callback.message.delete()
    for idx, c in enumerate(configs, 1):
        qr_file = await generate_qr_code(c['link'])
        caption = f"🔸 {c['remarks']}\n\nبرای اتصال، این QR کد را اسکن کنید."
        if idx == len(configs):
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="menu_main"))
            await callback.message.answer_photo(
                photo=qr_file,
                caption=caption,
                reply_markup=builder.as_markup()
            )
        else:
            await callback.message.answer_photo(photo=qr_file, caption=caption)
    await callback.answer()
