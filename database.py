import aiosqlite
import secrets

DB_PATH = "bot_database.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # جدول کاربران
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                username TEXT,
                first_name TEXT,
                joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP,
                is_admin BOOLEAN DEFAULT 0,
                is_blocked BOOLEAN DEFAULT 0
            )
        ''')
        # جدول پروکسی
        await db.execute('''
            CREATE TABLE IF NOT EXISTS proxies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT,
                ip TEXT,
                port INTEGER,
                last_checked TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        # جدول کانفیگ V2Ray
        await db.execute('''
            CREATE TABLE IF NOT EXISTS v2ray_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                link TEXT UNIQUE,
                remarks TEXT,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # جدول کانفیگ WireGuard
        await db.execute('''
            CREATE TABLE IF NOT EXISTS wireguard_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_text TEXT UNIQUE,
                remarks TEXT,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # جدول DNS
        await db.execute('''
            CREATE TABLE IF NOT EXISTS dns_servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                primary_dns TEXT,
                secondary_dns TEXT,
                for_gaming BOOLEAN DEFAULT 0
            )
        ''')
        # جدول لاگ استفاده
        await db.execute('''
            CREATE TABLE IF NOT EXISTS usage_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                command TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # ====== جداول جدید سیستم دعوت ======
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
        await db.commit()

# ========== توابع کاربران ==========
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

# ========== توابع پروکسی ==========
async def add_proxy(proxy_type: str, ip: str, port: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO proxies (type, ip, port, last_checked, is_active) VALUES (?, ?, ?, CURRENT_TIMESTAMP, 1)",
            (proxy_type, ip, port)
        )
        await db.commit()

async def get_active_proxies(limit: int = 10):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT type, ip, port FROM proxies WHERE is_active = 1 ORDER BY RANDOM() LIMIT ?",
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [{"type": row[0], "ip": row[1], "port": row[2]} for row in rows]

async def delete_all_proxies():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM proxies")
        await db.commit()

async def deactivate_old_proxies():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE proxies SET is_active = 0 WHERE last_checked < datetime('now', '-1 day')"
        )
        await db.commit()

# ========== توابع V2Ray ==========
async def add_v2ray(link: str, remarks: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO v2ray_configs (link, remarks) VALUES (?, ?)",
            (link, remarks)
        )
        await db.commit()

async def get_all_v2ray():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT link, remarks FROM v2ray_configs ORDER BY added_date DESC") as cursor:
            rows = await cursor.fetchall()
            return [{"link": row[0], "remarks": row[1]} for row in rows]

async def delete_all_v2ray():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM v2ray_configs")
        await db.commit()

# ========== توابع WireGuard ==========
async def add_wireguard(config_text: str, remarks: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO wireguard_configs (config_text, remarks) VALUES (?, ?)",
            (config_text, remarks)
        )
        await db.commit()

async def get_all_wireguard():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT config_text, remarks FROM wireguard_configs ORDER BY added_date DESC") as cursor:
            rows = await cursor.fetchall()
            return [{"config": row[0], "remarks": row[1]} for row in rows]

async def delete_all_wireguard():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM wireguard_configs")
        await db.commit()

# ========== توابع لاگ ==========
async def log_usage(user_id: int, command: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO usage_log (user_id, command) VALUES (?, ?)",
            (user_id, command)
        )
        await db.commit()

async def get_command_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT command, COUNT(*) FROM usage_log GROUP BY command ORDER BY COUNT(*) DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return rows

# ========== توابع سیستم دعوت دوستان ==========
async def create_referral_code(user_id: int) -> str:
    """ساخت کد دعوت برای کاربر"""
    code = secrets.token_hex(4)  # کد ۸ رقمی (مثلاً a1b2c3d4)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO referrals (user_id, code) VALUES (?, ?)",
            (user_id, code)
        )
        await db.commit()
    return code

async def get_referral_code(user_id: int) -> str:
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
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM referral_logs WHERE referrer_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def get_referral_details(user_id: int):
    """دریافت جزئیات دعوت‌های کاربر"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT new_user_id, registered_at FROM referral_logs WHERE referrer_id = ? ORDER BY registered_at DESC",
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return rows
