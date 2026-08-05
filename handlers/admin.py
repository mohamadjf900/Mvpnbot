from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
import database as db
import config
import os
import re
import aiosqlite
import logging

logger = logging.getLogger(__name__)

router = Router()
DB_PATH = "bot_database.db"

def is_admin(user_id):
    return user_id in config.ADMIN_IDS

# ============================================================
# ====================== آمار ======================
# ============================================================

@router.message(Command("stats"))
async def stats_command(message: Message):
    if not is_admin(message.from_user.id):
        return
    total = await db.get_total_users()
    active_today = await db.get_active_users(1)
    active_week = await db.get_active_users(7)
    text = f"📊 **آمار ربات:**\n\n👥 کل کاربران: {total}\n📈 کاربران فعال امروز: {active_today}\n📈 کاربران فعال هفته: {active_week}"
    await message.answer(text)

# ============================================================
# ====================== ارسال همگانی ======================
# ============================================================

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

# ============================================================
# ====================== بکاپ ======================
# ============================================================

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

# ============================================================
# ====================== مدیریت پروکسی ======================
# ============================================================

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

@router.message(Command("clear_proxies"))
async def clear_proxies(message: Message):
    if not is_admin(message.from_user.id):
        return
    await db.delete_all_proxies()
    await message.answer("✅ تمام پروکسی‌ها حذف شدند.")

# ============================================================
# ====================== مدیریت V2Ray ======================
# ============================================================

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

@router.message(Command("clear_v2ray"))
async def clear_v2ray(message: Message):
    if not is_admin(message.from_user.id):
        return
    await db.delete_all_v2ray()
    await message.answer("✅ تمام کانفیگ‌های V2Ray حذف شدند.")

# ============================================================
# ====================== مدیریت WireGuard ======================
# ============================================================

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

@router.message(Command("clear_wireguard"))
async def clear_wireguard(message: Message):
    if not is_admin(message.from_user.id):
        return
    await db.delete_all_wireguard()
    await message.answer("✅ تمام کانفیگ‌های WireGuard حذف شدند.")

# ============================================================
# ====================== مدیریت سفارشات ======================
# ============================================================

@router.message(Command("orders"))
async def list_orders(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ شما دسترسی ادمین ندارید!")
        return
    
    try:
        orders = await db.get_all_pending_orders()
        
        if not orders:
            await message.answer("📭 هیچ سفارش در انتظار تأییدی وجود ندارد.")
            return
        
        text = "📋 **سفارش‌های در انتظار تأیید:**\n\n"
        for o in orders[:20]:
            text += f"🆔 #{o[0]} | 👤 {o[3] or o[2] or o[1]} | 📦 {o[5]} | 👥 {o[7]} نفر | 💰 {o[6]:,} تومان | 📌 {o[9]}\n"
        
        await message.answer(text[:4000])
    except Exception as e:
        logger.error(f"Error in orders command: {e}")
        await message.answer(f"❌ خطا در دریافت سفارشات: {e}")

@router.message(Command("confirm_"))
async def confirm_order(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ شما دسترسی ادمین ندارید!")
        return
    
    try:
        match = re.search(r'confirm_(\d+)', message.text)
        if not match:
            await message.answer("❌ فرمت: /confirm_<order_id>\nمثال: /confirm_2")
            return
        
        order_id = int(match.group(1))
        logger.info(f"Admin {message.from_user.id} confirming order #{order_id}")
        
        async with aiosqlite.connect(db.DB_PATH) as conn:
            cursor = await conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
            order = await cursor.fetchone()
            if not order:
                await message.answer(f"❌ سفارش #{order_id} یافت نشد!")
                return
            
            current_status = order[9]
            if current_status not in ["pending", "receipt_sent"]:
                await message.answer(f"❌ سفارش #{order_id} در وضعیت {current_status} است و قابل تأیید نیست!")
                return
        
        await db.update_order_status(order_id, "confirmed")
        await message.answer(f"✅ سفارش #{order_id} با موفقیت تأیید شد.")
        
        async with aiosqlite.connect(db.DB_PATH) as conn:
            cursor = await conn.execute("SELECT user_id FROM orders WHERE id = ?", (order_id,))
            row = await cursor.fetchone()
            if row:
                try:
                    await message.bot.send_message(
                        row[0],
                        f"✅ **سفارش شما #{order_id} تأیید شد!**\n\n"
                        f"به زودی اطلاعات پنل برای شما ارسال می‌شود.\n"
                        f"لطفاً منتظر پیام بعدی باشید."
                    )
                except Exception as e:
                    logger.error(f"Failed to notify user: {e}")
        
    except Exception as e:
        logger.error(f"Error confirming order: {e}")
        await message.answer(f"❌ خطا در تأیید سفارش: {e}")

@router.message(Command("reject_"))
async def reject_order(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ شما دسترسی ادمین ندارید!")
        return
    
    try:
        match = re.search(r'reject_(\d+)', message.text)
        if not match:
            await message.answer("❌ فرمت: /reject_<order_id>\nمثال: /reject_2")
            return
        
        order_id = int(match.group(1))
        logger.info(f"Admin {message.from_user.id} rejecting order #{order_id}")
        
        async with aiosqlite.connect(db.DB_PATH) as conn:
            cursor = await conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
            order = await cursor.fetchone()
            if not order:
                await message.answer(f"❌ سفارش #{order_id} یافت نشد!")
                return
        
        await db.update_order_status(order_id, "rejected")
        await message.answer(f"❌ سفارش #{order_id} رد شد.")
        
        async with aiosqlite.connect(db.DB_PATH) as conn:
            cursor = await conn.execute("SELECT user_id FROM orders WHERE id = ?", (order_id,))
            row = await cursor.fetchone()
            if row:
                try:
                    await message.bot.send_message(
                        row[0],
                        f"❌ **سفارش شما #{order_id} رد شد.**\n\n"
                        f"برای اطلاعات بیشتر با پشتیبانی تماس بگیرید."
                    )
                except Exception as e:
                    logger.error(f"Failed to notify user: {e}")
        
    except Exception as e:
        logger.error(f"Error rejecting order: {e}")
        await message.answer(f"❌ خطا در رد سفارش: {e}")

@router.message(Command("deliver_"))
async def deliver_order(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ شما دسترسی ادمین ندارید!")
        return
    
    try:
        match = re.search(r'deliver_(\d+)', message.text)
        if not match:
            await message.answer("❌ فرمت: /deliver_<order_id> <اطلاعات پنل>\nمثال: /deliver_2 لینک: ... یوزرنیم: ... پسورد: ...")
            return
        
        order_id = int(match.group(1))
        parts = message.text.split(maxsplit=2)
        if len(parts) < 2:
            await message.answer("❌ لطفاً اطلاعات پنل را وارد کنید!\nمثال: /deliver_2 لینک: ... یوزرنیم: ... پسورد: ...")
            return
        
        panel_info = parts[1] if len(parts) == 2 else parts[1] + " " + parts[2] if len(parts) > 2 else ""
        
        if not panel_info:
            await message.answer("❌ لطفاً اطلاعات پنل را وارد کنید!")
            return
        
        logger.info(f"Admin {message.from_user.id} delivering order #{order_id}")
        
        async with aiosqlite.connect(db.DB_PATH) as conn:
            cursor = await conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
            order = await cursor.fetchone()
            if not order:
                await message.answer(f"❌ سفارش #{order_id} یافت نشد!")
                return
        
        await db.update_order_status(order_id, "delivered", panel_info)
        await message.answer(f"✅ سفارش #{order_id} با موفقیت تحویل داده شد.")
        
        async with aiosqlite.connect(db.DB_PATH) as conn:
            cursor = await conn.execute("SELECT user_id FROM orders WHERE id = ?", (order_id,))
            row = await cursor.fetchone()
            if row:
                try:
                    await message.bot.send_message(
                        row[0],
                        f"🚀 **سفارش شما #{order_id} تحویل داده شد!**\n\n"
                        f"📡 **اطلاعات پنل:**\n{panel_info}\n\n"
                        f"برای راهنمایی بیشتر با پشتیبانی تماس بگیرید."
                    )
                except Exception as e:
                    logger.error(f"Failed to send panel info: {e}")
        
    except Exception as e:
        logger.error(f"Error delivering order: {e}")
        await message.answer(f"❌ خطا در تحویل سفارش: {e}")

# ============================================================
# ====================== مدیریت پلن‌ها ======================
# ============================================================

@router.message(Command("show_plans"))
async def show_plans(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    normal = await db.get_normal_plans()
    vip = await db.get_vip_plans()
    
    text = "📋 **لیست پلن‌های فعلی:**\n\n"
    
    text += "📦 **پلن‌های عادی:**\n"
    for plan in normal:
        plan_id, volume, price, users = plan
        text += f"  🆔 {plan_id} | {volume} گیگ | {price:,} تومان | 👤 {users} کاربر\n"
    
    text += "\n⭐ **پلن‌های ویژه:**\n"
    for plan in vip:
        plan_id, label, price, users = plan
        text += f"  🆔 {plan_id} | {label} | {price:,} تومان | 👤 {users} کاربر\n"
    
    text += "\n📌 **دستورات مدیریت:**\n"
    text += "/add_normal <حجم> <قیمت> <تعداد کاربر> - اضافه کردن پلن عادی\n"
    text += "/add_vip <برچسب> <قیمت> <تعداد کاربر> - اضافه کردن پلن ویژه\n"
    text += "/edit_normal <id> <حجم> <قیمت> <تعداد کاربر> - ویرایش پلن عادی\n"
    text += "/edit_vip <id>|<برچسب>|<قیمت>|<تعداد> - ویرایش پلن ویژه (با | جدا کنید)\n"
    text += "/change_normal_users <id> <تعداد> - تغییر تعداد کاربران پلن عادی\n"
    text += "/change_vip_users <id> <تعداد> - تغییر تعداد کاربران پلن ویژه\n"
    text += "/delete_plan <id> - حذف پلن"
    
    await message.answer(text)

@router.message(Command("add_normal"))
async def add_normal_plan(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split()
    if len(parts) != 4:
        await message.answer("❌ فرمت: /add_normal <حجم> <قیمت> <تعداد کاربر>\nمثال: /add_normal 10 60000 1")
        return
    
    try:
        volume = int(parts[1])
        price = int(parts[2])
        user_count = int(parts[3])
        
        await db.add_normal_plan(volume, price, user_count)
        await message.answer(f"✅ پلن عادی جدید اضافه شد!\n📦 {volume} گیگ | {price:,} تومان | 👤 {user_count} کاربر")
    except Exception as e:
        await message.answer(f"❌ خطا: {e}")

@router.message(Command("add_vip"))
async def add_vip_plan(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split(maxsplit=3)
    if len(parts) != 4:
        await message.answer("❌ فرمت: /add_vip <برچسب> <قیمت> <تعداد کاربر>\nمثال: /add_vip VIP-پرمیوم 300000 2")
        return
    
    try:
        label = parts[1]
        price = int(parts[2])
        user_count = int(parts[3])
        
        await db.add_vip_plan(label, price, user_count)
        await message.answer(f"✅ پلن ویژه جدید اضافه شد!\n⭐ {label} | {price:,} تومان | 👤 {user_count} کاربر")
    except Exception as e:
        await message.answer(f"❌ خطا: {e}")

@router.message(Command("edit_normal"))
async def edit_normal_plan(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split()
    if len(parts) != 5:
        await message.answer("❌ فرمت: /edit_normal <id> <حجم> <قیمت> <تعداد کاربر>\nمثال: /edit_normal 1 20 120000 2")
        return
    
    try:
        plan_id = int(parts[1])
        volume = int(parts[2])
        price = int(parts[3])
        user_count = int(parts[4])
        
        await db.update_normal_plan(plan_id, volume, price, user_count)
        await message.answer(f"✅ پلن عادی {plan_id} با موفقیت ویرایش شد!\n📦 {volume} گیگ | {price:,} تومان | 👤 {user_count} کاربر")
    except Exception as e:
        await message.answer(f"❌ خطا: {e}")

@router.message(Command("edit_vip"))
async def edit_vip_plan(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    text = message.text.replace("/edit_vip", "").strip()
    if not text:
        await message.answer("❌ فرمت: /edit_vip <id>|<برچسب>|<قیمت>|<تعداد>\nمثال: /edit_vip 1|VIP یکماهه نامحدود|250000|1")
        return
    
    try:
        if '|' in text:
            parts = text.split('|')
            if len(parts) != 4:
                await message.answer("❌ فرمت: /edit_vip <id>|<برچسب>|<قیمت>|<تعداد>\nمثال: /edit_vip 1|VIP یکماهه نامحدود|250000|1")
                return
            plan_id = int(parts[0].strip())
            label = parts[1].strip()
            price = int(parts[2].strip())
            user_count = int(parts[3].strip())
        else:
            await message.answer("❌ لطفاً از جداکننده `|` استفاده کنید!\nمثال: /edit_vip 1|VIP یکماهه نامحدود|250000|1")
            return
        
        await db.update_vip_plan(plan_id, label, price, user_count)
        await message.answer(f"✅ پلن ویژه {plan_id} با موفقیت ویرایش شد!\n⭐ {label} | {price:,} تومان | 👤 {user_count} کاربر")
    except ValueError:
        await message.answer("❌ شناسه، قیمت و تعداد کاربران باید عدد باشند!")
    except Exception as e:
        await message.answer(f"❌ خطا: {e}")

@router.message(Command("change_normal_users"))
async def change_normal_users(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("❌ فرمت: /change_normal_users <id> <تعداد>\nمثال: /change_normal_users 1 5")
        return
    
    try:
        plan_id = int(parts[1])
        new_count = int(parts[2])
        
        plan = await db.get_normal_plan(plan_id)
        if not plan:
            await message.answer(f"❌ پلن عادی با شناسه {plan_id} یافت نشد!")
            return
        
        plan_id, volume, price, _ = plan
        await db.update_normal_plan(plan_id, volume, price, new_count)
        await message.answer(f"✅ تعداد کاربران پلن عادی {plan_id} به {new_count} نفر تغییر یافت!\n📦 {volume} گیگ | {price:,} تومان | 👤 {new_count} کاربر")
    except ValueError:
        await message.answer("❌ شناسه و تعداد باید عدد باشند!")
    except Exception as e:
        await message.answer(f"❌ خطا: {e}")

@router.message(Command("change_vip_users"))
async def change_vip_users(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("❌ فرمت: /change_vip_users <id> <تعداد>\nمثال: /change_vip_users 1 5")
        return
    
    try:
        plan_id = int(parts[1])
        new_count = int(parts[2])
        
        plan = await db.get_vip_plan(plan_id)
        if not plan:
            await message.answer(f"❌ پلن ویژه با شناسه {plan_id} یافت نشد!")
            return
        
        plan_id, label, price, _ = plan
        await db.update_vip_plan(plan_id, label, price, new_count)
        await message.answer(f"✅ تعداد کاربران پلن ویژه {plan_id} به {new_count} نفر تغییر یافت!\n⭐ {label} | {price:,} تومان | 👤 {new_count} کاربر")
    except ValueError:
        await message.answer("❌ شناسه و تعداد باید عدد باشند!")
    except Exception as e:
        await message.answer(f"❌ خطا: {e}")

@router.message(Command("delete_plan"))
async def delete_plan(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("❌ فرمت: /delete_plan <id>\nمثال: /delete_plan 3")
        return
    
    try:
        plan_id = int(parts[1])
        
        normal = await db.get_normal_plans()
        vip = await db.get_vip_plans()
        normal_ids = [p[0] for p in normal]
        vip_ids = [p[0] for p in vip]
        
        if plan_id in normal_ids:
            await db.delete_normal_plan(plan_id)
            await message.answer(f"✅ پلن عادی {plan_id} حذف شد.")
        elif plan_id in vip_ids:
            await db.delete_vip_plan(plan_id)
            await message.answer(f"✅ پلن ویژه {plan_id} حذف شد.")
        else:
            await message.answer(f"❌ پلن {plan_id} یافت نشد!")
    except ValueError:
        await message.answer("❌ شناسه پلن باید عدد باشد!")
    except Exception as e:
        await message.answer(f"❌ خطا: {e}")
