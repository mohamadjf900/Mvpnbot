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

# ========== پروکسی (اصلاح‌شده با اعتبارسنجی) ==========
@router.message(Command("add_proxy"))
async def add_proxy_command(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    text = message.text.replace("/add_proxy", "").strip()
    
    # تشخیص فرمت لینک مستقیم تخصصی پروکسی تلگرام
    if text.startswith("https://t.me/proxy?"):
        parts = text.split(maxsplit=1)
        url = parts[0].strip()
        remarks = parts[1].strip() if len(parts) > 1 else "Proxy"
        try:
            await db.add_proxy(None, None, None, url, remarks)
            await message.answer(f"✅ پروکسی لینک با نام «{remarks}» اضافه شد.")
        except Exception as e:
            await message.answer(f"خطا: {e}")
        return
    
    # فرمت معمولی type ip port
    args = text.split()
    if len(args) != 3:
        await message.answer(
            "❌ فرمت صحیح:\n"
            "1. برای پروکسی معمولی:\n`/add_proxy HTTP 1.2.3.4 8080`\n"
            "2. برای لینک مخصوص تلگرام:\n`/add_proxy https://t.me/proxy?server=...&port=...&secret=... توضیحات`"
        )
        return
    
    ptype, ip, port = args
    # اعتبارسنجی ساده IP
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
        await message.answer(f"خطا: {e}")

@router.message(Command("add_proxies"))
async def add_proxies_command(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    text = message.text.replace("/add_proxies", "").strip()
    if not text:
        await message.answer(
            "❌ لطفاً لیست پروکسی‌ها را ارسال کنید.\n"
            "فرمت صحیح:\n"
            "هر خط یک پروکسی به فرمت `type ip port` یا لینک `https://t.me/proxy?...`"
        )
        return
    
    lines = text.split('\n')
    added = 0
    errors = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # تشخیص لینک تخصصی پروکسی تلگرام
        if line.startswith("https://t.me/proxy?"):
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
            continue
        
        # فرمت معمولی type ip port
        parts = line.split()
        if len(parts) != 3:
            errors.append(f"❌ خطای فرمت: {line}")
            continue
        
        ptype, ip, port = parts
        if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
            errors.append(f"❌ IP نامعتبر: {ip}")
            continue
        
        try:
            port = int(port)
            if port < 1 or port > 65535:
                errors.append(f"❌ پورت نامعتبر: {port}")
                continue
            await db.add_proxy(ptype.upper(), ip, port)
            added += 1
        except Exception as e:
            errors.append(f"خطا در افزودن {line}: {e}")
    
    result = f"✅ {added} پروکسی با موفقیت اضافه شد."
    if errors:
        result += f"\n\n❌ خطاها ({len(errors)} مورد):\n" + "\n".join(errors[:5])
    await message.answer(result)

# ========== V2Ray (اصلاح‌شده با پشتیبانی از لینک‌های بلند) ==========
def is_valid_v2ray_link(link: str) -> bool:
    """تشخیص لینک V2Ray معتبر"""
    return any(link.startswith(prefix) for prefix in [
        'vless://', 'vmess://', 'trojan://', 'ss://',
        'https://shadowmere.xyz', 'https://t.me/'
    ])

def extract_remarks_from_link(link: str) -> str:
    """استخراج توضیحات از لینک"""
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
        await message.answer(
            "❌ لطفاً لینک V2Ray را ارسال کنید.\n"
            "مثال: `/add_v2ray vless://...@...`\n"
            "یا: `/add_v2ray https://shadowmere.xyz/api/b64sub/ توضیحات`"
        )
        return
    
    # اگر کاربر با فاصله جدا کرده باشد
    parts = text.split(maxsplit=1)
    link = parts[0].strip()
    remarks = parts[1].strip() if len(parts) > 1 else extract_remarks_from_link(link)
    
    try:
        await db.add_v2ray(link, remarks)
        await message.answer(f"✅ کانفیگ V2Ray با نام «{remarks}» اضافه شد.")
    except Exception as e:
        await message.answer(f"❌ خطا: {e}")

@router.message(Command("add_v2rays"))
async def add_v2rays_command(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    text = message.text.replace("/add_v2rays", "", 1).strip()
    if not text:
        await message.answer(
            "❌ لطفاً لیست کانفیگ‌های V2Ray را ارسال کنید.\n"
            "فرمت: `link|remarks` (هر خط یک کانفیگ)"
        )
        return
    
    lines = text.split('\n')
    added = 0
    errors = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if '|' in line:
            link, remarks = line.split('|', 1)
            link = link.strip()
            remarks = remarks.strip()
        else:
            link = line
            remarks = extract_remarks_from_link(link)
        
        try:
            await db.add_v2ray(link, remarks)
            added += 1
        except Exception as e:
            errors.append(f"خطا در افزودن {link[:30]}... : {e}")
    
    result = f"✅ {added} کانفیگ V2Ray اضافه شد."
    if errors:
        result += f"\n\n❌ خطاها ({len(errors)} مورد):\n" + "\n".join(errors[:5])
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

# ========== لیست پروکسی‌ها (برای ادمین) ==========
@router.message(Command("list_proxies"))
async def list_proxies_command(message: Message):
    if not is_admin(message.from_user.id):
        return
    proxies = await db.get_active_proxies(limit=100)
    if not proxies:
        await message.answer("📭 هیچ پروکسی فعالی وجود ندارد.")
        return
    text = "📋 **لیست پروکسی‌های فعال:**\n\n"
    for idx, p in enumerate(proxies, 1):
        if "url" in p and p["url"]:
            text += f"{idx}. 🔗 {p['remarks']}: {p['url'][:50]}...\n"
        else:
            text += f"{idx}. {p['type']} {p['ip']}:{p['port']}\n"
    await message.answer(text[:4000])  # محدودیت پیام تلگرام
