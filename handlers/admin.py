from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
import database as db
import config
import re

router = Router()

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

# ========== پروکسی (دستورات جدید) ==========
@router.message(Command("add_proxy"))
async def add_proxy_command(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    # پشتیبانی از دو فرمت:
    # 1. /add_proxy HTTP 1.2.3.4 8080
    # 2. /add_proxy https://t.me/proxy?server=...&port=... "توضیحات"
    text = message.text.replace("/add_proxy", "").strip()
    
    if text.startswith("http://") or text.startswith("https://"):
        # فرمت لینک مستقیم
        parts = text.split(maxsplit=1)
        url = parts[0].strip()
        remarks = parts[1].strip() if len(parts) > 1 else "Proxy"
        try:
            await db.add_proxy(None, None, None, url, remarks)
            await message.answer(f"✅ پروکسی لینک با نام «{remarks}» اضافه شد.")
        except Exception as e:
            await message.answer(f"خطا: {e}")
    else:
        # فرمت معمولی type ip port
        args = text.split()
        if len(args) != 3:
            await message.answer("فرمت: /add_proxy <type> <ip> <port> یا /add_proxy <url> [remarks]")
            return
        ptype, ip, port = args
        try:
            port = int(port)
            await db.add_proxy(ptype.upper(), ip, port)
            await message.answer(f"✅ پروکسی {ptype} {ip}:{port} اضافه شد.")
        except Exception as e:
            await message.answer(f"خطا: {e}")

@router.message(Command("add_proxies"))
async def add_proxies_command(message: Message):
    if not is_admin(message.from_user.id):
        return
    text = message.text.replace("/add_proxies", "").strip()
    if not text:
        await message.answer("لطفاً لیست پروکسی‌ها را ارسال کنید.")
        return
    lines = text.split('\n')
    added = 0
    errors = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # تشخیص فرمت لینک
        if line.startswith("http://") or line.startswith("https://"):
            if '|' in line:
                url, remarks = line.split('|', 1)
                url = url.strip()
                remarks = remarks.strip()
            else:
                url = line
                remarks = "Proxy"
            try:
                await db.add_proxy(None, None, None, url, remarks)
                added += 1
            except Exception as e:
                errors.append(f"خطا در افزودن {url[:30]}... : {e}")
        else:
            parts = line.split()
            if len(parts) != 3:
                errors.append(f"خطای فرمت: {line}")
                continue
            ptype, ip, port = parts
            try:
                port = int(port)
                await db.add_proxy(ptype.upper(), ip, port)
                added += 1
            except Exception as e:
                errors.append(f"خطا در افزودن {line}: {e}")
    result = f"✅ {added} پروکسی اضافه شد."
    if errors:
        result += "\n\n❌ خطاها:\n" + "\n".join(errors[:5])
    await message.answer(result)

# ========== V2Ray ==========
@router.message(Command("add_v2ray"))
async def add_v2ray_command(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("فرمت: /add_v2ray <link> <remarks>")
        return
    _, link, remarks = parts
    try:
        await db.add_v2ray(link, remarks)
        await message.answer(f"✅ کانفیگ V2Ray با نام «{remarks}» اضافه شد.")
    except Exception as e:
        await message.answer(f"خطا: {e}")

@router.message(Command("add_v2rays"))
async def add_v2rays_command(message: Message):
    if not is_admin(message.from_user.id):
        return
    text = message.text.replace("/add_v2rays", "").strip()
    if not text:
        await message.answer("لطفاً لیست کانفیگ‌های V2Ray را به فرمت link|remarks ارسال کنید.")
        return
    lines = text.split('\n')
    added = 0
    errors = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if '|' not in line:
            errors.append(f"خطای فرمت (| یافت نشد): {line}")
            continue
        link, remarks = line.split('|', 1)
        link = link.strip()
        remarks = remarks.strip()
        try:
            await db.add_v2ray(link, remarks)
            added += 1
        except Exception as e:
            errors.append(f"خطا در افزودن {remarks}: {e}")
    result = f"✅ {added} کانفیگ V2Ray اضافه شد."
    if errors:
        result += "\n\n❌ خطاها:\n" + "\n".join(errors[:5])
    await message.answer(result)

# ========== WireGuard ==========
@router.message(Command("add_wireguard"))
async def add_wireguard_command(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("فرمت: /add_wireguard <config_text> <remarks>")
        return
    _, config_text, remarks = parts
    try:
        await db.add_wireguard(config_text, remarks)
        await message.answer(f"✅ کانفیگ WireGuard با نام «{remarks}» اضافه شد.")
    except Exception as e:
        await message.answer(f"خطا: {e}")

@router.message(Command("add_wireguards"))
async def add_wireguards_command(message: Message):
    if not is_admin(message.from_user.id):
        return
    text = message.text.replace("/add_wireguards", "").strip()
    if not text:
        await message.answer("لطفاً لیست کانفیگ‌های WireGuard را به فرمت config|remarks ارسال کنید.")
        return
    lines = text.split('\n')
    added = 0
    errors = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if '|' not in line:
            errors.append(f"خطای فرمت (| یافت نشد): {line}")
            continue
        config_text, remarks = line.split('|', 1)
        config_text = config_text.strip()
        remarks = remarks.strip()
        try:
            await db.add_wireguard(config_text, remarks)
            added += 1
        except Exception as e:
            errors.append(f"خطا در افزودن {remarks}: {e}")
    result = f"✅ {added} کانفیگ WireGuard اضافه شد."
    if errors:
        result += "\n\n❌ خطاها:\n" + "\n".join(errors[:5])
    await message.answer(result)

# ========== پاک کردن ==========
@router.message(Command("clear_proxies"))
async def clear_proxies_command(message: Message):
    if not is_admin(message.from_user.id):
        return
    await db.delete_all_proxies()
    await message.answer("✅ تمام پروکسی‌ها حذف شدند.")

@router.message(Command("clear_v2ray"))
async def clear_v2ray_command(message: Message):
    if not is_admin(message.from_user.id):
        return
    await db.delete_all_v2ray()
    await message.answer("✅ تمام کانفیگ‌های V2Ray حذف شدند.")

@router.message(Command("clear_wireguard"))
async def clear_wireguard_command(message: Message):
    if not is_admin(message.from_user.id):
        return
    await db.delete_all_wireguard()
    await message.answer("✅ تمام کانفیگ‌های WireGuard حذف شدند.")
