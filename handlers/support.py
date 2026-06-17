from aiogram import Router, F
from aiogram.types import CallbackQuery
from utils.helpers import back_button  # این خط اضافه شد
import database as db

router = Router()

@router.callback_query(F.data == "menu_support")
async def support_menu(callback: CallbackQuery):
    await db.update_activity(callback.from_user.id)
    await db.log_usage(callback.from_user.id, "support")
    
    # اگر متغیر ADMIN_USERNAME را در config دارید، از آن استفاده کنید
    admin_username = getattr(config, 'ADMIN_USERNAME', '@YourAdminUsername')
    
    text = (
        "📞 **پشتیبانی**\n\n"
        "برای ارتباط با ادمین و دریافت کمک، از روش‌های زیر استفاده کنید:\n\n"
        "👉 **سیستم تیکتینگ**: از منوی اصلی گزینه «🎫 تیکت پشتیبانی» را انتخاب کنید.\n"
        "👉 **ارسال پیام خصوصی**: با ادمین در ارتباط باشید.\n\n"
        f"🆔 ادمین: {admin_username}"
    )
    
    await callback.message.edit_text(text, reply_markup=back_button())
    await callback.answer()
