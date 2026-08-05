from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
import database as db
import config
import os
import re
import aiosqlite

router = Router()
DB_PATH = "bot_database.db"

def is_admin(user_id):
    return user_id in config.ADMIN_IDS

# ========== آمار ==========
@router.message(Command("stats"))
async def stats_command(message: Message):
    if not is_admin(message.from_user.id):
        return
    total = await db.get_total_users()
    active_today = await db.get_active_users(1)
    active_week = await db.get_active_users(7)
    text = f"📊 **آمار ربات:**\n\n👥 کل کاربران: {total}\n📈 کاربران فعال امروز: {active_today}\n📈 کاربران فعال هفته: {active_week}"
    await message.answer(text)

# ========== ارسال همگانی ==========
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

# ========== بکاپ و بازیابی ==========
@router.message(Command("backup"))
async def backup_db(message: Message):
    if not is_admin(message.from_user.id):
        return
    try:
        if os.path.exists(DB_PATH):
            await message.answer_document(
                FSInputFile(DB_PATH, filename="bot_database.db"),
                caption="✅ بکاپ دیتابیس"
            )
        else:
            await message.answer("❌ فایل دیتابیس وجود ندارد.")
    except Exception as e:
        await message.answer(f"❌ خطا در بکاپ: {e}")

@router.message(Command("restore"))
async def restore_db(message: Message):
    if not is_admin(message.from_user.id):
        return
    if not message.document:
        await message.answer("❌ لطفاً فایل دیتابیس را ارسال کنید.")
        return
    try:
        file = await message.bot.get_file(message.document.file_id)
        await message.bot.download_file(file.file_path, DB_PATH)
        await message.answer("✅ دیتابیس با موفقیت بازیابی شد. ربات را ری‌استارت کنید.")
    except Exception as e:
        await message.answer(f"❌ خطا در بازیابی: {e}")

# ========== اضافه کردن پروکسی ==========
@router.message(Command("add_proxy"))
async def add_proxy_command(message: Message):
    if not is_admin(message.from_user.id):
        return
    text = message.text.replace("/add_proxy", "").strip()
    if not text:
        await message.answer("❌ فرمت: /add_proxy HTTP 1.2.3.4 8080 یا /add_proxy https://t.me/proxy?server=...&port=... توضیحات")
        return
    
    if text.startswith("https://t.me/proxy?"):
        parts = text.split(maxsplit=1)
        url = parts[0].strip()
        remarks = parts[1].strip() if len(parts) > 1 else "Proxy"
        try:
            await db.add_proxy(None, None, None, url, remarks)
            await message.answer(f"✅ پروکسی لینک با نام «{remarks}» اضافه شد.")
        except Exception as e:
            await message.answer(f"❌ خطا: {e}")
        return
    
    args = text.split()
    if len(args) != 3:
        await message.answer("❌ فرمت: /add_proxy <type> <ip> <port>")
        return
    ptype, ip, port = args
    if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
        await message.answer("❌ فرمت IP نامعتبر است!")
        return
    try:
        port = int(port)
        if port < 1 or port > 65535:
            await message.answer("❌ پورت باید بین ۱ تا ۶۵۵۳۵ باشد!")
            return
        await db.add_proxy(ptype.upper(), ip, port)
        await message.answer(f"✅ پروکسی {ptype} {ip}:{port} اضافه شد.")
    except Exception as e:
        await message.answer(f"❌ خطا: {e}")

# ========== اضافه کردن V2Ray ==========
def extract_remarks_from_link(link: str) -> str:
    if '#' in link:
        return link.split('#', 1)[1].strip()
    if '@' in link:
        parts = link.split('@')
        if len(parts) > 1 and '?' in parts[1]:
            return parts[1].split('?')[0][:20]
    return "V2Ray Config"

@router.message(Command("add_v2ray"))
async def add_v2ray_command(message: Message):
    if not is_admin(message.from_user.id):
        return
    text = message.text.replace("/add_v2ray", "", 1).strip()
    if not text:
        await message.answer("❌ لطفاً لینک V2Ray را ارسال کنید.\nمثال: `/add_v2ray vless://...@... توضیحات`")
        return
    parts = text.split(maxsplit=1)
    link = parts[0].strip()
    remarks = parts[1].strip() if len(parts) > 1 else extract_remarks_from_link(link)
    try:
        await db.add_v2ray(link, remarks)
        await message.answer(f"✅ کانفیگ V2Ray با نام «{remarks}» اضافه شد.")
    except Exception as e:
        await message.answer(f"❌ خطا: {e}")

# ========== اضافه کردن WireGuard ==========
@router.message(Command("add_wireguard"))
async def add_wireguard_command(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("❌ فرمت: /add_wireguard <config_text> <remarks>")
        return
    _, config_text, remarks = parts
    try:
        await db.add_wireguard(config_text, remarks)
        await message.answer(f"✅ کانفیگ WireGuard با نام «{remarks}» اضافه شد.")
    except Exception as e:
        await message.answer(f"❌ خطا: {e}")

# ========== سفارشات ==========
@router.message(Command("orders"))
async def list_orders(message: Message):
    if not is_admin(message.from_user.id):
        return
    orders = await db.get_all_pending_orders()
    if not orders:
        await message.answer("📭 هیچ سفارش در انتظار تأییدی وجود ندارد.")
        return
    text = "📋 **سفارش‌های در انتظار تأیید:**\n\n"
    for o in orders[:20]:
        text += f"🆔 #{o[0]} | 👤 {o[3]} | 📦 {o[5]} | 💰 {o[4]:,} تومان\n"
    await message.answer(text[:4000])

@router.message(Command("confirm_"))
async def confirm_order(message: Message):
    if not is_admin(message.from_user.id):
        return
    try:
        order_id = int(message.text.split("_")[1])
        await db.update_order_status(order_id, "confirmed")
        await message.answer(f"✅ سفارش #{order_id} تأیید شد.")
        async with aiosqlite.connect(db.DB_PATH) as conn:
            cursor = await conn.execute("SELECT user_id FROM orders WHERE id = ?", (order_id,))
            row = await cursor.fetchone()
            if row:
                try:
                    await message.bot.send_message(row[0], f"✅ سفارش شما #{order_id} تأیید شد!")
                except:
                    pass
    except:
        await message.answer("❌ خطا در تأیید سفارش.")

@router.message(Command("reject_"))
async def reject_order(message: Message):
    if not is_admin(message.from_user.id):
        return
    try:
        order_id = int(message.text.split("_")[1])
        await db.update_order_status(order_id, "rejected")
        await message.answer(f"❌ سفارش #{order_id} رد شد.")
        async with aiosqlite.connect(db.DB_PATH) as conn:
            cursor = await conn.execute("SELECT user_id FROM orders WHERE id = ?", (order_id,))
            row = await cursor.fetchone()
            if row:
                try:
                    await message.bot.send_message(row[0], f"❌ سفارش شما #{order_id} رد شد.")
                except:
                    pass
    except:
        await message.answer("❌ خطا در رد سفارش.")

@router.message(Command("deliver_"))
async def deliver_order(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("❌ فرمت: /deliver_<order_id> <اطلاعات پنل>")
        return
    try:
        order_id = int(parts[0].split("_")[1])
        panel_info = parts[1] + " " + parts[2] if len(parts) > 2 else parts[1]
        await db.update_order_status(order_id, "delivered", panel_info)
        await message.answer(f"✅ سفارش #{order_id} تحویل داده شد.")
        async with aiosqlite.connect(db.DB_PATH) as conn:
            cursor = await conn.execute("SELECT user_id FROM orders WHERE id = ?", (order_id,))
            row = await cursor.fetchone()
            if row:
                try:
                    await message.bot.send_message(row[0], f"🚀 سفارش #{order_id} تحویل شد!\n📡 {panel_info}")
                except:
                    pass
    except:
        await message.answer("❌ خطا در تحویل سفارش.")

# ========== پاک کردن ==========
@router.message(Command("clear_proxies"))
async def clear_proxies(message: Message):
    if not is_admin(message.from_user.id):
        return
    await db.delete_all_proxies()
    await message.answer("✅ تمام پروکسی‌ها حذف شدند.")

@router.message(Command("clear_v2ray"))
async def clear_v2ray(message: Message):
    if not is_admin(message.from_user.id):
        return
    await db.delete_all_v2ray()
    await message.answer("✅ تمام کانفیگ‌های V2Ray حذف شدند.")

@router.message(Command("clear_wireguard"))
async def clear_wireguard(message: Message):
    if not is_admin(message.from_user.id):
        return
    await db.delete_all_wireguard()
    await message.answer("✅ تمام کانفیگ‌های WireGuard حذف شدند.")
