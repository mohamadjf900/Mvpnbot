from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import database as db
from utils.helpers import back_button
import logging
import qrcode
from io import BytesIO

router = Router()

async def generate_qr_code(data: str) -> BufferedInputFile:
    """تولید QR کد از متن داده شده و برگرداندن به صورت BufferedInputFile"""
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

    # حذف پیام قبلی (منو) تا جایگزین بشه
    await callback.message.delete()

    # ارسال QR کد برای هر کانفیگ
    for idx, c in enumerate(configs, 1):
        # تولید QR کد
        qr_file = await generate_qr_code(c['link'])
        caption = f"🔸 {c['remarks']}\n\nبرای اتصال، این QR کد را اسکن کنید."
        
        # دکمه بازگشت فقط برای آخرین کانفیگ
        if idx == len(configs):
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="menu_main"))
            await callback.message.answer_photo(
                photo=qr_file,
                caption=caption,
                reply_markup=builder.as_markup()
            )
        else:
            await callback.message.answer_photo(
                photo=qr_file,
                caption=caption
            )
    
    await callback.answer()
