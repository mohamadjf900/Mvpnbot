import aiosqlite
import secrets

DB_PATH = "bot_database.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # ====== جدول کاربران ======
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP,
                is_blocked BOOLEAN DEFAULT 0
            )
        ''')
        
        # ====== جدول پروکسی ======
        await db.execute('''
            CREATE TABLE IF NOT EXISTS proxies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT,
                ip TEXT,
                port INTEGER,
                url TEXT,
                remarks TEXT,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # ====== جدول V2Ray ======
        await db.execute('''
            CREATE TABLE IF NOT EXISTS v2ray (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                link TEXT UNIQUE,
                remarks TEXT,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ====== جدول WireGuard ======
        await db.execute('''
            CREATE TABLE IF NOT EXISTS wireguard (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config TEXT UNIQUE,
                remarks TEXT,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ====== جدول تیکت‌ها ======
        await db.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                subject TEXT,
                status TEXT DEFAULT 'open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ====== جدول پیام‌های تیکت ======
        await db.execute('''
            CREATE TABLE IF NOT EXISTS ticket_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER,
                sender_id INTEGER,
                message TEXT,
                file_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticket_id) REFERENCES tickets (id) ON DELETE CASCADE
            )
        ''')
        
        # ====== جدول رفرال (دعوت دوستان) ======
        await db.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                user_id INTEGER PRIMARY KEY,
                code TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS referral_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                new_user_id INTEGER,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ====== جدول لاگ استفاده ======
        await db.execute('''
            CREATE TABLE IF NOT EXISTS usage_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                section TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await db.commit()

# ============================================================
# ====================== توابع کاربران ======================
# ============================================================

async def add_user(user_id: int, username: str = None, first_name: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name, last_activity) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
            (user_id, username, first_name)
        )
        await db.commit()

async def update_activity(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET last_activity = CURRENT_TIMESTAMP WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()

async def get_total_users():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_blocked = 0") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def get_active_users(days: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM users WHERE last_activity >= datetime('now', '-' || ? || ' days') AND is_blocked = 0",
            (days,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users WHERE is_blocked = 0") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

# ============================================================
# ====================== توابع پروکسی ======================
# ============================================================

async def add_proxy(proxy_type: str = None, ip: str = None, port: int = None, url: str = None, remarks: str = None):
    """افزودن پروکسی با پشتیبانی از لینک مستقیم و معمولی"""
    async with aiosqlite.connect(DB_PATH) as db:
        if url:
            # لینک مستقیم (فقط لینک‌های معتبر t.me/proxy پشتیبانی می‌شوند)
            if not url.startswith("https://t.me/proxy?"):
                raise ValueError("لینک پروکسی نامعتبر! فقط لینک‌های t.me/proxy پشتیبانی می‌شوند.")
            await db.execute(
                "INSERT OR IGNORE INTO proxies (url, remarks, added_date, is_active) VALUES (?, ?, CURRENT_TIMESTAMP, 1)",
                (url, remarks or "Proxy")
            )
        else:
            # پروکسی معمولی با IP و پورت
            if not ip or not port:
                raise ValueError("IP و پورت برای پروکسی معمولی الزامی است.")
            await db.execute(
                "INSERT OR IGNORE INTO proxies (type, ip, port, added_date, is_active) VALUES (?, ?, ?, CURRENT_TIMESTAMP, 1)",
                (proxy_type.upper() if proxy_type else "HTTP", ip, port)
            )
        await db.commit()

async def get_active_proxies(limit: int = 50):
    """دریافت پروکسی‌های فعال (ابتدا لینک‌ها، سپس معمولی)"""
    async with aiosqlite.connect(DB_PATH) as db:
        results = []
        
        # 1. پروکسی‌های دارای لینک مستقیم
        async with db.execute(
            "SELECT url, remarks FROM proxies WHERE is_active = 1 AND url IS NOT NULL ORDER BY added_date DESC LIMIT ?",
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                results.append({"url": row[0], "remarks": row[1] or "Proxy"})
        
        # 2. پروکسی‌های معمولی (اگر تعداد کافی نبود)
        remaining = max(0, limit - len(results))
        if remaining > 0:
            async with db.execute(
                "SELECT type, ip, port FROM proxies WHERE is_active = 1 AND url IS NULL ORDER BY RANDOM() LIMIT ?",
                (remaining,)
            ) as cursor2:
                rows2 = await cursor2.fetchall()
                for row in rows2:
                    results.append({"type": row[0] or "HTTP", "ip": row[1], "port": row[2]})
        return results

async def get_all_proxies():
    """دریافت همه پروکسی‌ها (برای مدیریت ادمین)"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, type, ip, port, url, remarks, is_active, added_date FROM proxies ORDER BY added_date DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "id": r[0],
                    "type": r[1],
                    "ip": r[2],
                    "port": r[3],
                    "url": r[4],
                    "remarks": r[5],
                    "is_active": bool(r[6]),
                    "added_date": r[7]
                }
                for r in rows
            ]

async def delete_proxy(proxy_id: int):
    """حذف یک پروکسی با شناسه"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM proxies WHERE id = ?", (proxy_id,))
        await db.commit()

async def delete_all_proxies():
    """حذف تمام پروکسی‌ها"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM proxies")
        await db.commit()

async def deactivate_old_proxies():
    """غیرفعال کردن پروکسی‌های قدیمی (بیش از ۱ روز)"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE proxies SET is_active = 0 WHERE added_date < datetime('now', '-1 day')"
        )
        await db.commit()

# ============================================================
# ====================== توابع V2Ray ======================
# ============================================================

async def add_v2ray(link: str, remarks: str):
    """افزودن کانفیگ V2Ray"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO v2ray (link, remarks) VALUES (?, ?)",
            (link, remarks)
        )
        await db.commit()

async def get_all_v2ray():
    """دریافت همه کانفیگ‌های V2Ray"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT link, remarks FROM v2ray ORDER BY added_date DESC") as cursor:
            rows = await cursor.fetchall()
            return [{"link": row[0], "remarks": row[1]} for row in rows]

async def delete_all_v2ray():
    """حذف همه کانفیگ‌های V2Ray"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM v2ray")
        await db.commit()

# ============================================================
# ====================== توابع WireGuard ======================
# ============================================================

async def add_wireguard(config: str, remarks: str):
    """افزودن کانفیگ WireGuard"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO wireguard (config, remarks) VALUES (?, ?)",
            (config, remarks)
        )
        await db.commit()

async def get_all_wireguard():
    """دریافت همه کانفیگ‌های WireGuard"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT config, remarks FROM wireguard ORDER BY added_date DESC") as cursor:
            rows = await cursor.fetchall()
            return [{"config": row[0], "remarks": row[1]} for row in rows]

async def delete_all_wireguard():
    """حذف همه کانفیگ‌های WireGuard"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM wireguard")
        await db.commit()

# ============================================================
# ====================== توابع تیکت ======================
# ============================================================

async def create_ticket(user_id: int, subject: str) -> int:
    """ایجاد تیکت جدید و برگرداندن شناسه آن"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO tickets (user_id, subject) VALUES (?, ?) RETURNING id",
            (user_id, subject)
        )
        row = await cursor.fetchone()
        await db.commit()
        return row[0] if row else None

async def add_ticket_message(ticket_id: int, sender_id: int, message: str = None, file_id: str = None):
    """افزودن پیام به تیکت"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO ticket_messages (ticket_id, sender_id, message, file_id) VALUES (?, ?, ?, ?)",
            (ticket_id, sender_id, message, file_id)
        )
        await db.execute(
            "UPDATE tickets SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (ticket_id,)
        )
        await db.commit()

async def get_user_tickets(user_id: int):
    """دریافت همه تیکت‌های یک کاربر"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT * FROM tickets WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return rows

async def get_all_tickets():
    """دریافت همه تیکت‌ها (برای ادمین)"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM tickets ORDER BY created_at DESC") as cursor:
            rows = await cursor.fetchall()
            return rows

async def get_ticket_messages(ticket_id: int):
    """دریافت همه پیام‌های یک تیکت"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT * FROM ticket_messages WHERE ticket_id = ? ORDER BY created_at ASC",
            (ticket_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return rows

async def update_ticket_status(ticket_id: int, status: str):
    """به‌روزرسانی وضعیت تیکت"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE tickets SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, ticket_id)
        )
        await db.commit()

# ============================================================
# ====================== توابع رفرال ======================
# ============================================================

async def create_referral_code(user_id: int) -> str:
    """ساخت کد دعوت منحصر‌به‌فرد برای کاربر"""
    code = secrets.token_hex(4)  # کد ۸ رقمی مثل a1b2c3d4
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO referrals (user_id, code) VALUES (?, ?)",
            (user_id, code)
        )
        await db.commit()
    return code

async def get_referral_code(user_id: int) -> str:
    """دریافت کد دعوت کاربر"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT code FROM referrals WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def register_referral(referrer_id: int, new_user_id: int):
    """ثبت دعوت جدید"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO referral_logs (referrer_id, new_user_id) VALUES (?, ?)",
            (referrer_id, new_user_id)
        )
        await db.commit()

async def get_referral_count(user_id: int) -> int:
    """تعداد دعوت‌های موفق یک کاربر"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM referral_logs WHERE referrer_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def get_referral_details(user_id: int):
    """جزئیات دعوت‌های یک کاربر (کاربران دعوت‌شده و تاریخ)"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT new_user_id, registered_at FROM referral_logs WHERE referrer_id = ? ORDER BY registered_at DESC",
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return rows

# ============================================================
# ====================== توابع لاگ ======================
# ============================================================

async def log_usage(user_id: int, section: str):
    """ثبت لاگ استفاده از بخش‌های مختلف ربات"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO usage_logs (user_id, section) VALUES (?, ?)",
            (user_id, section)
        )
        await db.commit()

async def get_usage_stats(limit: int = 10):
    """آمار پرکاربردترین بخش‌های ربات"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT section, COUNT(*) FROM usage_logs GROUP BY section ORDER BY COUNT(*) DESC LIMIT ?",
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return rows
