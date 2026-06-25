from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import database as db
import config

router = Router()

# 📥 منوی اصلی دقیقاً با چیدمان و دیتای کدهای قدیمی خودت
async def main_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🚀 پروکسی", callback_data="menu_proxy")
    builder.button(text="📡 V2Ray", callback_data="menu_v2ray")
    builder.button(text="🔒 WireGuard", callback_data="menu_wireguard")
    builder.button(text="🎮 DNS گیمرها", callback_data="menu_dns")
    builder.button(text="🎫 تیکت پشتیبانی", callback_data="menu_ticket")
    builder.button(text="💼 خرید", callback_data="menu_buy")
    builder.button(text="📞 پشتیبانی", callback_data="menu_support")
    builder.button(text="📢 کانال ما", url=config.CHANNEL_LINK) # خواندن لینک از کانفیگ شما
    builder.adjust(2, 2, 2, 1, 1) # چیدمان دقیق خودت: ۲-۲-۲-۱-۱
    return builder.as_markup()

# 📢 ساخت کیبورد شیشه‌ای عضویت اجباری به صورت پویا از روی فایل config
def get_join_keyboard():
    builder = InlineKeyboardBuilder()
    
    # ساخت دکمه برای هر کانالی که در کانفیگ تعریف شده
    for channel in config.REQUIRED_CHANNELS:
        builder.button(text=f"{channel['name']}", url=channel['link'])
    
    # دکمه‌ی نهایی برای بررسی عضویت در همه کانال‌ها
    builder.button(text="✅ عضو شدم! ورود به ربات", callback_data="check_all_joins")
    
    # چیدمان: کانال‌ها هر کدام یک سطر، دکمه تایید هم یک سطر زیر آن‌ها
    builder.adjust(*[1] * len(config.REQUIRED_CHANNELS), 1)
    return builder.as_markup()

@router.message(Command("start"))
async def start_handler(message: Message, bot):
    user = message.from_user
    # ثبت کاربر در دیتابیس (دقیقاً مثل کد خودت)
    await db.add_user(user.id, user.username, user.first_name)
    await db.update_activity(user.id)
    
    # بررسی عضویت کاربر در تمام کانال‌های لیست شده
    not_joined = []
    for channel in config.REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel["id"], user_id=user.id)
            if member.status in ["left", "kicked"]:
                not_joined.append(channel)
        except Exception:
            # اگر ربات در کانالی ادمین نباشد، از آن عبور می‌کند تا ربات قفل نشود
            pass

    # اگر کاربر در کانالی عضو نبود، منوی قفل کانال را نشان بده
    if not_joined:
        text = (
            "⚠️ **جهت استفاده از امکانات رایگان ربات، عضویت در کانال‌های زیر الزامی است!**\n\n"
            "لطفاً ابتدا وارد کانال‌های زیر شده و دکمه عضویت را بزنید، سپس روی دکمه **«✅ عضو شدم!»** کلیک کنید 👇"
        )
        await message.answer(text, reply_markup=get_join_keyboard(), parse_mode="Markdown")
    else:
        # اگر عضو بود، مستقیم منوی اصلی را باز کن
        text = "به ربات VPN و پروکسی خوش آمدید!\nاز منوی زیر انتخاب کنید:"
        await message.answer(text, reply_markup=await main_menu_keyboard())

@router.callback_query(F.data == "check_all_joins")
async def check_all_joins_callback(callback: CallbackQuery, bot):
    user_id = callback.from_user.id
    not_joined = []
    
    # بررسی مجدد تک‌تک کانال‌ها هنگام کلیک روی دکمه عضو شدم
    for channel in config.REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel["id"], user_id=user_id)
            if member.status in ["left", "kicked"]:
                not_joined.append(channel)
        except Exception:
            pass

    if not_joined:
        # اگر هنوز کانالی مانده که کاربر عضو نشده، نام آن را اخطار بده
        channels_names = "\n".join([f"🔹 {c['name']}" for c in not_joined])
        await callback.answer(
            f"❌ شما هنوز عضو تمام کانال‌ها نشده‌اید!\nلطفاً کانال‌های زیر را چک کنید:\n{channels_names}", 
            show_alert=True
        )
    else:
        # اگر در همه عضو شده بود، پیام قبلی را پاک کن و منوی اصلی را باز کن
        await callback.message.delete()
        await callback.message.answer(
            "✅ عضویت شما تایید شد! به منوی اصلی خوش آمدید:", 
            reply_markup=await main_menu_keyboard()
        )
        await callback.answer("خوش آمدید! 🎉")

# 🔙 دکمه بازگشت به منوی اصلی کاملاً هماهنگ با بقیه فایل‌ها (menu_main)
@router.callback_query(F.data == "menu_main")
async def back_to_main(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer("منوی اصلی:", reply_markup=await main_menu_keyboard())
    await callback.answer()
