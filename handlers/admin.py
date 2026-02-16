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

# ================== دستورات آماری و همگانی ==================

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

# ================== بکاپ و بازیابی دیتابیس ==================

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

# ================== توابع کمکی برای پروکسی ==================

def is_valid_proxy_url(url: str) -> bool:
    return url.startswith(('http://', 'https://', 't.me/proxy?'))

# ================== دستورات پروکسی ==================

@router.message(Command("add_proxy"))
async def add_proxy_command(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) == 2:
        _, url = parts
        url = url.strip()
        remarks = "Proxy"
    elif len(parts) >= 3:
        _, url, remarks = parts
        url = url.strip()
        remarks = remarks.strip()
    else:
        await message.answer(
            "فرمت: /add_proxy <url> [remarks]\n"
            "مثال: /add_proxy https://t.me/proxy?server=195.254.165.211&port=4455&secret=... پروکسی روسیه"
        )
        return
    try:
        await db.delete_all_proxies()
        await db.add_proxy(url, remarks)
        await message.answer(f"✅ پروکسی جدید با نام «{remarks}» جایگزین شد.")
    except Exception as e:
        await message.answer(f"خطا: {e}")

@router.message(Command("add_proxies"))
async def add_proxies_command(message: Message):
    if not is_admin(message.from_user.id):
        return
    text = message.text.replace("/add_proxies", "").strip()
    if not text:
        await message.answer(
            "لطفاً لیست پروکسی‌ها را ارسال کنید.\n"
            "هر خط می‌تواند یک لینک مستقیم باشد (مثلاً https://t.me/proxy?server=...)."
        )
        return
    lines = text.split('\n')
    added = 0
    errors = []
    await db.delete_all_proxies()
    for line in lines:
        line = line.strip()
        if not line or len(line) < 10:
            continue
        if '|' in line:
            url, remarks = line.split('|', 1)
            url = url.strip()
            remarks = remarks.strip()
        else:
            url = line
            remarks = "Proxy"
        try:
            await db.add_proxy(url, remarks)
            added += 1
        except Exception as e:
            errors.append(f"خطا در افزودن {url[:30]}... : {e}")
    result = f"✅ {added} پروکسی جدید جایگزین شد."
    if errors:
        result += "\n\n❌ خطاها:\n" + "\n".join(errors[:5])
    await message.answer(result)

# ================== توابع کمکی برای V2Ray ==================

def is_valid_v2ray_link(link: str) -> bool:
    """تشخیص اینکه آیا یک رشته می‌تونه لینک V2Ray باشه"""
    return any(link.startswith(prefix) for prefix in ['vless://', 'vmess://', 'trojan://', 'ss://'])

def extract_remarks_from_link(link: str) -> str:
    """استخراج remarks از انتهای لینک (بعد از #)"""
    if '#' in link:
        return link.split('#', 1)[1].strip()
    return "V2Ray Config"

# ================== دستورات V2Ray ==================

@router.message(Command("add_v2ray"))
async def add_v2ray_command(message: Message):
    if not is_admin(message.from_user.id):
        return
    text = message.text.replace("/add_v2ray", "", 1).strip()
    if not text:
        await message.answer(
            "فرمت: /add_v2ray <link>\n"
            "مثال: /add_v2ray vless://6919e588-cff3-4c1b-b7a3-3ca0ada5fb69@85.133.200.78:26480?security=none&encryption=none&headerType=none&type=tcp#shankamil"
        )
        return
    
    if '|' in text:
        link, remarks = text.split('|', 1)
        link = link.strip()
        remarks = remarks.strip()
    else:
        link = text
        remarks = extract_remarks_from_link(link)
    
    try:
        await db.delete_all_v2ray()
        await db.add_v2ray(link, remarks)
        await message.answer(f"✅ کانفیگ V2Ray جدید با نام «{remarks}» جایگزین شد.")
    except Exception as e:
        await message.answer(f"خطا: {e}")

@router.message(Command("add_v2rays"))
async def add_v2rays_command(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    text = message.text.replace("/add_v2rays", "", 1).strip()
    if not text:
        await message.answer(
            "لطفاً لیست کانفیگ‌های V2Ray را ارسال کنید.\n"
            "هر خط می‌تواند یک لینک باشد (مثلاً vless://... یا vmess://...).\n"
            "اگر می‌خواهید remarks جداگانه بدهید، از فرمت link|remarks استفاده کنید."
        )
        return
    
    # مرحله 1: حذف خطوط فارسی و بی‌ربط
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        # اگه خط شامل کلمات فارسی خاص مثل "خطاها" یا "کانفیگ" باشه، نادیده بگیر
        if re.search(r'[آ-ی]', line) and not is_valid_v2ray_link(line):
            continue
        cleaned_lines.append(line)
    
    # مرحله 2: ادغام خطوطی که با فاصله یا خط تیره شروع می‌شن با خط قبلی
    merged_lines = []
    current = ""
    for line in cleaned_lines:
        if not line:
            continue
        if line.startswith(('-', ' ')) or (current and not is_valid_v2ray_link(line) and '://' not in line):
            current += line
        else:
            if current:
                merged_lines.append(current)
            current = line
    if current:
        merged_lines.append(current)
    
    # مرحله 3: استخراج لینک‌های معتبر (شامل مواردی که ممکنه در یک خط نباشن)
    all_links = []
    for raw in merged_lines:
        # اگه کل خط با پروتکل شروع نشه، با regex دنبال لینک می‌گردیم
        if not is_valid_v2ray_link(raw):
            # الگوی ساده برای پیدا کردن لینک‌های vless، vmess، trojan
            found = re.findall(r'(vless://[^\s]+|vmess://[^\s]+|trojan://[^\s]+|ss://[^\s]+)', raw)
            all_links.extend(found)
        else:
            all_links.append(raw)
    
    if not all_links:
        await message.answer("❌ هیچ لینک معتبری یافت نشد.")
        return
    
    added = 0
    errors = []
    await db.delete_all_v2ray()
    
    for raw_link in all_links:
        if '|' in raw_link:
            link, remarks = raw_link.split('|', 1)
            link = link.strip()
            remarks = remarks.strip()
        else:
            link = raw_link
            remarks = extract_remarks_from_link(link)
        
        try:
            await db.add_v2ray(link, remarks)
            added += 1
        except Exception as e:
            errors.append(f"خطا در افزودن {link[:30]}... : {e}")
    
    result = f"✅ {added} کانفیگ V2Ray جدید جایگزین شد."
    if errors:
        result += "\n\n❌ خطاها:\n" + "\n".join(errors[:5])
    await message.answer(result)

# ================== دستورات WireGuard ==================

@router.message(Command("add_wireguard"))
async def add_wireguard_command(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer(
            "فرمت: /add_wireguard <config_text> <remarks>\n"
            "مثال: /add_wireguard [Interface]... سرور اول"
        )
        return
    _, config_text, remarks = parts
    try:
        await db.delete_all_wireguard()
        await db.add_wireguard(config_text, remarks)
        await message.answer(f"✅ کانفیگ WireGuard جدید با نام «{remarks}» جایگزین شد.")
    except Exception as e:
        await message.answer(f"خطا: {e}")

@router.message(Command("add_wireguards"))
async def add_wireguards_command(message: Message):
    if not is_admin(message.from_user.id):
        return
    text = message.text.replace("/add_wireguards", "").strip()
    if not text:
        await message.answer(
            "لطفاً لیست کانفیگ‌های WireGuard را به فرمت زیر ارسال کنید:\n"
            "config_text|remarks\n"
            "[Interface]...|اتصال اول\n"
            "[Interface]...|اتصال دوم\n"
            "(هر خط یک کانفیگ، با | جدا شود)"
        )
        return
    lines = text.split('\n')
    added = 0
    errors = []
    await db.delete_all_wireguard()
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
    result = f"✅ {added} کانفیگ WireGuard جدید جایگزین شد."
    if errors:
        result += "\n\n❌ خطاها:\n" + "\n".join(errors[:5])
    await message.answer(result)
