from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
import database as db
import config
import aiosqlite

router = Router()

# ========== منوی اصلی با دکمه‌های پایین صفحه (Reply Keyboard) ==========
def main_menu_keyboard(user_id: int = None):
    buttons = [
        [KeyboardButton(text="🚀 پروکسی"), KeyboardButton(text="📡 V2Ray")],
        [KeyboardButton(text="🔒 WireGuard"), KeyboardButton(text="🎮 DNS")],
        [KeyboardButton(text="🛒 خرید سرویس"), KeyboardButton(text="💰 کیف پول")],
        [KeyboardButton(text="👥 دعوت دوستان"), KeyboardButton(text="🎫 تیکت پشتیبانی")],
        [KeyboardButton(text="📞 پشتیبانی"), KeyboardButton(text="📜 قوانین")],
    ]
    if user_id and user_id in config.ADMIN_IDS:
        buttons.append([KeyboardButton(text="⚙️ مدیریت ربات")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# ========== دستور /start ==========
@router.message(Command("start"))
async def start_handler(message: Message):
    user = message.from_user
    await db.add_user(user.id, user.username, user.first_name)
    await db.update_activity(user.id)
    await db.log_usage(user.id, "start")
    
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
    await message.answer(text, reply_markup=main_menu_keyboard(user.id))

# ====================== دکمه‌های منو (Reply Keyboard) ======================

@router.message(F.text == "🚀 پروکسی")
async def proxy_button(message: Message):
    from handlers.proxy import proxy_menu_message
    await proxy_menu_message(message)

@router.message(F.text == "📡 V2Ray")
async def v2ray_button(message: Message):
    from handlers.v2ray import v2ray_menu_message
    await v2ray_menu_message(message)

@router.message(F.text == "🔒 WireGuard")
async def wireguard_button(message: Message):
    from handlers.wireguard import wireguard_menu_message
    await wireguard_menu_message(message)

@router.message(F.text == "🎮 DNS")
async def dns_button(message: Message):
    from handlers.dns import dns_menu_message
    await dns_menu_message(message)

@router.message(F.text == "🛒 خرید سرویس")
async def shop_button(message: Message):
    from handlers.shop import services_kb
    await message.answer("🛒 لطفاً نوع سرویس مورد نظر را انتخاب کنید:", reply_markup=services_kb())

@router.message(F.text == "💰 کیف پول")
async def wallet_button(message: Message):
    balance = await db.get_wallet_balance(message.from_user.id)
    text = f"💰 **کیف پول شما**\n\nموجودی فعلی: {balance:,} تومان"
    await message.answer(text, reply_markup=main_menu_keyboard(message.from_user.id))

@router.message(F.text == "👥 دعوت دوستان")
async def invite_button(message: Message):
    from handlers.referral import invite_command
    await invite_command(message)

@router.message(F.text == "🎫 تیکت پشتیبانی")
async def ticket_button(message: Message):
    from handlers.ticket import ticket_menu_message
    await ticket_menu_message(message)

@router.message(F.text == "📞 پشتیبانی")
async def support_button(message: Message):
    text = f"📞 **پشتیبانی {config.BRAND_NAME}**\n\nبرای ارتباط با پشتیبانی:\n📩 پیوی ادمین: @{config.SUPPORT_USERNAME}\n🎫 سیستم تیکت: از منو گزینه تیکت پشتیبانی"
    await message.answer(text, reply_markup=main_menu_keyboard(message.from_user.id))

@router.message(F.text == "📜 قوانین")
async def rules_button(message: Message):
    text = f"📜 **قوانین {config.BRAND_NAME}**\n\n۱. استفاده از سرویس به معنای پذیرش قوانین است.\n۲. هرگونه سوءاستفاده منجر به مسدود شدن می‌شود.\n۳. پشتیبانی فقط از طریق ربات و پیوی ادمین."
    await message.answer(text, reply_markup=main_menu_keyboard(message.from_user.id))

@router.message(F.text == "⚙️ مدیریت ربات")
async def admin_button(message: Message):
    if message.from_user.id not in config.ADMIN_IDS:
        await message.answer("❌ شما دسترسی ادمین ندارید!")
        return
    text = "⚙️ **پنل مدیریت**\n\nدستورات موجود:\n/stats - آمار کاربران\n/broadcast - ارسال همگانی\n/backup - بکاپ دیتابیس\n/restore - بازیابی دیتابیس\n/orders - مشاهده سفارشات\n/add_proxy - افزودن پروکسی\n/add_v2ray - افزودن V2Ray\n/add_wireguard - افزودن WireGuard"
    await message.answer(text, reply_markup=main_menu_keyboard(message.from_user.id))

@router.callback_query(F.data == "menu_main")
async def back_to_main(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer("منوی اصلی:", reply_markup=main_menu_keyboard(callback.from_user.id))
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
