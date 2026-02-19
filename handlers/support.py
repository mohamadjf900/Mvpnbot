from aiogram import Router, F
from aiogram.types import CallbackQuery
from utils.helpers import back_button
import database as db

router = Router()

@router.callback_query(F.data == "menu_support")
async def support_menu(callback: CallbackQuery):
    await db.update_activity(callback.from_user.id)
    await db.log_usage(callback.from_user.id, "support")
    text = (
        "📞 برای پشتیبانی و ارتباط با ادمین:\n\n"
        f"👉 @Mj054 (پیام خصوصی)\n"
        "یا می‌توانید مشکل خود را در قالب یک پیام به ربات بفرستید (تیکت پشتیبانی بزنید)"
    )
    await callback.message.edit_text(text, reply_markup=back_button())
    await callback.answer()
