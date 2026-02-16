import aiosqlite
import asyncio

DB_PATH = "bot_database.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Users table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP
            )
        ''')
        # Proxies table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS proxies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT,
                ip TEXT,
                port INTEGER,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_check TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        ''')
        # V2Ray configs table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS v2ray (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                link TEXT UNIQUE,
                remarks TEXT,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # WireGuard configs table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS wireguard (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config TEXT UNIQUE,
                remarks TEXT,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Usage logs table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS usage_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                section TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.commit()

# ---------- User functions ----------
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
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def get_active_users(days: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM users WHERE last_activity >= datetime('now', '-' || ? || ' days')",
            (days,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

# ---------- Proxy functions ----------
async def add_proxy(proxy_type: str, ip: str, port: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO proxies (type, ip, port, added_date, last_check, is_active) VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)",
            (proxy_type, ip, port)
        )
        await db.commit()

async def get_active_proxies(limit: int = 50):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT type, ip, port FROM proxies WHERE is_active = 1 ORDER BY RANDOM() LIMIT ?",
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [{"type": row[0], "ip": row[1], "port": row[2]} for row in rows]

async def delete_all_proxies():
    """حذف تمام پروکسی‌ها"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM proxies")
        await db.commit()

# ---------- V2Ray functions ----------
async def add_v2ray(link: str, remarks: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO v2ray (link, remarks) VALUES (?, ?)",
            (link, remarks)
        )
        await db.commit()

async def get_all_v2ray():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT link, remarks FROM v2ray ORDER BY added_date DESC") as cursor:
            rows = await cursor.fetchall()
            return [{"link": row[0], "remarks": row[1]} for row in rows]

async def delete_all_v2ray():
    """حذف تمام کانفیگ‌های V2Ray"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM v2ray")
        await db.commit()

# ---------- WireGuard functions ----------
async def add_wireguard(config: str, remarks: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO wireguard (config, remarks) VALUES (?, ?)",
            (config, remarks)
        )
        await db.commit()

async def get_all_wireguard():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT config, remarks FROM wireguard ORDER BY added_date DESC") as cursor:
            rows = await cursor.fetchall()
            return [{"config": row[0], "remarks": row[1]} for row in rows]

async def delete_all_wireguard():
    """حذف تمام کانفیگ‌های WireGuard"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM wireguard")
        await db.commit()

# ---------- Usage logs ----------
async def log_usage(user_id: int, section: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO usage_logs (user_id, section) VALUES (?, ?)",
            (user_id, section)
        )
        await db.commit()
