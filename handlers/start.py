from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import database as db
import config

router = Router()

async def main_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🚀 پروکسی", callback_data="menu_proxy")
    builder.button(text="📡 V2Ray", callback_data="menu_v2ray")
    builder.button(text="🔒 WireGuard", callback_data="menu_wireguard")
    builder.button(text="🎮 DNS گیمرها", callback_data="menu_dns")
    builder.button(text="💼 خرید", callback_data="menu_buy")
    builder.button(text="📞 پشتیبانی", callback_data="menu_support")
    builder.adjust(2)
    return builder.as_markup()

@router.message(Command("start"))
async def start_handler(message: Message):
    user = message.from_user
    await db.add_user(user.id, user.username, user.first_name)
    await db.update_activity(user.id)
    text = "به ربات VPN و پروکسی خوش آمدید!\nاز منوی زیر انتخاب کنید:"
    await message.answer(text, reply_markup=await main_menu_keyboard())

@router.callback_query(F.data == "menu_main")
async def back_to_main(callback: CallbackQuery):
    await callback.message.edit_text("منوی اصلی:", reply_markup=await main_menu_keyboard())
    await callback.answer()

@router.callback_query(F.data == "check_join")
async def check_join_callback(callback: CallbackQuery, bot):
    try:
        member = await bot.get_chat_member(chat_id=config.CHANNEL_ID, user_id=callback.from_user.id)
        if member.status not in ["left", "kicked"]:
            await callback.message.delete()
            await start_handler(callback.message)
        else:
            await callback.answer("شما هنوز عضو نشده‌اید!", show_alert=True)
    except:
        await callback.answer("خطا در بررسی عضویت!", show_alert=True)
