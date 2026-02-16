from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
import database as db
import config

router = Router()

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

# ================== توابع کمکی برای استخراج remarks ==================

def extract_remarks_from_link(link: str) -> str:
    """استخراج remarks از انتهای لینک V2Ray (بعد از #)"""
    if '#' in link:
        return link.split('#', 1)[1].strip()
    return "V2Ray Config"

# ================== دستورات پروکسی (با لینک مستقیم) ==================

@router.message(Command("add_proxy"))
async def add_proxy_command(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) == 2:
        # فقط url داده شده
        _, url = parts
        url = url.strip()
        remarks = "Proxy"
    elif len(parts) >= 3:
        # url و remarks داده شده
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
            "هر خط می‌تواند یک لینک مستقیم باشد (مثلاً https://t.me/proxy?server=...) یا به فرمت url|remarks."
        )
        return
    lines = text.split('\n')
    added = 0
    errors = []
    await db.delete_all_proxies()
    for line in lines:
        line = line.strip()
        # نادیده گرفتن خطوط خالی یا بی‌محتوا (مثل رشته‌های بلند A)
        if not line or len(line) < 10 or line.replace('A', '') == '':
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

# ================== دستورات V2Ray (با پشتیبانی از # در لینک) ==================

@router.message(Command("add_v2ray"))
async def add_v2ray_command(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) == 2:
        # فقط لینک داده شده
        _, link = parts
        link = link.strip()
        remarks = extract_remarks_from_link(link)
    elif len(parts) >= 3:
        # هم لینک و هم remarks داده شده
        _, link, remarks = parts
        link = link.strip()
        remarks = remarks.strip()
    else:
        await message.answer(
            "فرمت: /add_v2ray <link> [remarks]\n"
            "اگر remarks ذکر نشود، از قسمت # در لینک استخراج می‌شود.\n"
            "مثال: /add_v2ray vless://...@...?...#name"
        )
        return
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
    text = message.text.replace("/add_v2rays", "").strip()
    if not text:
        await message.answer(
            "لطفاً لیست کانفیگ‌های V2Ray را به فرمت زیر ارسال کنید:\n"
            "link|remarks\n"
            "vless://...|سرور اول\n"
            "vmess://...|سرور دوم\n"
            "(هر خط یک کانفیگ، با | جدا شود)"
        )
        return
    lines = text.split('\n')
    added = 0
    errors = []
    await db.delete_all_v2ray()
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
