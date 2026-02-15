from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
import database as db
import config

router = Router()

def is_admin(user_id):
    return user_id in config.ADMIN_IDS

@router.message(Command("stats"))
async def stats_command(message: Message):
    if not is_admin(message.from_user.id):
        return
    total = await db.get_total_users()
    active_today = await db.get_active_users(1)
    active_week = await db.get_active_users(7)
    text = f"📊 آمار ربات:\nکل کاربران: {total}\nکاربران فعال امروز: {active_today}\nکاربران فعال هفته: {active_week}"
    await message.answer(text)

@router.message(Command("broadcast"))
async def broadcast_command(message: Message):
    if not is_admin(message.from_user.id):
        return
    text = message.text.replace("/broadcast", "").strip()
    if not text:
        await message.answer("لطفاً متن پیام را وارد کنید.\nمثال: /broadcast سلام")
        return
    users = await db.get_all_users()
    success = 0
    fail = 0
    for uid in users:
        try:
            await message.bot.send_message(uid, text)
            success += 1
        except:
            fail += 1
    await message.answer(f"✅ ارسال شد: {success}\n❌ ناموفق: {fail}")

@router.message(Command("add_proxy"))
async def add_proxy_command(message: Message):
    if not is_admin(message.from_user.id):
        return
    args = message.text.split()
    if len(args) != 4:
        await message.answer("فرمت: /add_proxy <type> <ip> <port>")
        return
    _, ptype, ip, port = args
    try:
        port = int(port)
        await db.add_proxy(ptype, ip, port)
        await message.answer("✅ پروکسی اضافه شد.")
    except:
        await message.answer("خطا در افزودن.")

@router.message(Command("add_v2ray"))
async def add_v2ray_command(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("فرمت: /add_v2ray <link> <remarks>")
        return
    _, link, remarks = parts
    await db.add_v2ray(link, remarks)
    await message.answer("✅ کانفیگ V2Ray اضافه شد.")

@router.message(Command("add_wireguard"))
async def add_wireguard_command(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("فرمت: /add_wireguard <config_text> <remarks>")
        return
    _, config_text, remarks = parts
    await db.add_wireguard(config_text, remarks)
    await message.answer("✅ کانفیگ WireGuard اضافه شد.")
