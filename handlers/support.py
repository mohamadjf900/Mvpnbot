import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from utils.helpers import back_button
import database as db
import config  # 👈 این خط جا افتاده بود که اضافه شد تا ایدی ادمین خوانده شود

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(F.data == "menu_support")
async def support_menu(callback: CallbackQuery):
    logger.info(f"User {callback.from_user.id} opened support menu")
    
    # به‌روزرسانی فعالیت کاربر در دیتابیس
    try:
        await db.update_activity(callback.from_user.id)
        await db.log_usage(callback.from_user.id, "support")
    except Exception as e:
        logger.error(f"Database error in support menu: {e}")
    
    # خواندن آیدی ادمین از کانفیگ
    admin_username = getattr(config, 'ADMIN_USERNAME', '@Mj054')
    
    text = (
        "📞 *پشتیبانی*\n\n"
        "برای ارتباط با ادمین و دریافت کمک، از روش‌های زیر استفاده کنید:\n\n"
        "👉 *سیستم تیکتینگ*: از منوی اصلی گزینه «🎫 تیکت پشتیبانی» را انتخاب کنید.\n"
        "👉 *ارسال پیام خصوصی*: با ادمین در ارتباط باشید.\n\n"
        f"🆔 ادمین: {admin_username}"
    )
    
    try:
        # اضافه کردن parse_mode برای اینکه متن‌ها درست و ضخیم نمایش داده شوند
        await callback.message.edit_text(text, reply_markup=back_button(), parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Failed to edit text in support menu: {e}")
        # لایه پشتیبان در صورت ارور دادن مارک‌داون تلگرام
        await callback.message.edit_text(text.replace('*', ''), reply_markup=back_button())
        
    await callback.answer()
