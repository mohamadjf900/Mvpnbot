from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import database as db
import config
import aiosqlite

router = Router()

async def main_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🚀 پروکسی", callback_data="menu_proxy")
    builder.button(text="📡 V2Ray", callback_data="menu_v2ray")
    builder.button(text="🔒 WireGuard", callback_data="menu_wireguard")
    builder.button(text="🎮 DNS گیمرها", callback_data="menu_dns")
    builder.button(text="🛒 خرید سرویس", callback_data="menu_shop")  # جدید
    builder.button(text="💰 کیف پول", callback_data="menu_wallet")   # جدید
    builder.button(text="👥 دعوت دوستان", callback_data="menu_invite")
    builder.button(text="🎫 تیکت پشتیبانی", callback_data="menu_ticket")
    builder.button(text="📞 پشتیبانی", callback_data="menu_support")
    builder.adjust(2)
    return builder.as_markup()

@router.message(Command("start"))
async def start_handler(message: Message):
    user = message.from_user
    await db.add_user(user.id, user.username, user.first_name)
    await db.update_activity(user.id)
    await db.log_usage(user.id, "start")
    
    # بررسی لینک دعوت
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        code = args[1][4:]
        async with aiosqlite.connect(db.DB_PATH) as conn:
            cursor = await conn.execute("SELECT user_id FROM referrals WHERE code = ?", (code,))
            row = await cursor.fetchone()
            if row and row[0] != user.id:
                await db.register_referral(row[0], user.id)
                await message.answer("🎉 شما با دعوت دوست خود وارد شدید!")
    
    text = "به ربات VPN و پروکسی خوش آمدید!\nاز منوی زیر انتخاب کنید:"
    await message.answer(text, reply_markup=await main_menu_keyboard())

@router.callback_query(F.data == "menu_main")
async def back_to_main(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer("منوی اصلی:", reply_markup=await main_menu_keyboard())
    await callback.answer()

@router.callback_query(F.data == "check_join")
async def check_join_callback(callback: CallbackQuery, bot):
    try:
        member = await bot.get_chat_member(chat_id=config.CHANNEL_ID, user_id=callback.from_user.id)
        if member.status not in ["left", "kicked"]:
            await callback.message.delete()
            await start_handler(callback.message)
        else:
            await callback.answer("❌ شما هنوز عضو نشده‌اید!", show_alert=True)
    except:
        await callback.answer("خطا در بررسی عضویت!", show_alert=True)

# ====== دکمه‌های جدید ======
@router.callback_query(F.data == "menu_shop")
async def shop_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "🛒 **خرید سرویس**\n\n"
        "لطفاً نوع سرویس مورد نظر خود را انتخاب کنید:\n"
        "🎮 گیمینگ\n"
        "🌐 مولتی لوکیشن",
        reply_markup=services_kb()
    )
    await callback.answer()

@router.callback_query(F.data == "menu_wallet")
async def wallet_menu(callback: CallbackQuery):
    balance = await db.get_wallet_balance(callback.from_user.id)
    text = f"💰 **کیف پول شما**\n\nموجودی فعلی: {balance:,} تومان"
    await callback.message.edit_text(text, reply_markup=back_menu_kb())
    await callback.answer()
