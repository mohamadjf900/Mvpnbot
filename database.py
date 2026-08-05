import aiosqlite
import secrets
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

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
        
        # ====== جدول رفرال ======
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
        
        # ====== جدول سفارشات ======
        await db.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                full_name TEXT,
                plan_id INTEGER,
                plan_name TEXT,
                price INTEGER,
                user_count INTEGER DEFAULT 1,
                receipt_file_id TEXT,
                status TEXT DEFAULT 'pending',
                panel_info TEXT,
                coupon_code TEXT,
                original_price INTEGER,
                created_at TEXT
            )
        ''')
        
        # ====== جدول کیف پول ======
        await db.execute('''
            CREATE TABLE IF NOT EXISTS wallets (
                user_id INTEGER PRIMARY KEY,
                balance INTEGER NOT NULL DEFAULT 0
            )
        ''')
        
        # ====== جدول کوپن‌ها ======
        await db.execute('''
            CREATE TABLE IF NOT EXISTS coupons (
                code TEXT PRIMARY KEY,
                percent INTEGER NOT NULL,
                max_uses INTEGER,
                used_count INTEGER NOT NULL DEFAULT 0,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT
            )
        ''')
        
        # ====== جدول پلن‌های عادی ======
        await db.execute('''
            CREATE TABLE IF NOT EXISTS normal_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                volume_gb INTEGER NOT NULL,
                price INTEGER NOT NULL,
                user_count INTEGER DEFAULT 1,
                active INTEGER DEFAULT 1
            )
        ''')
        
        # ====== جدول پلن‌های ویژه ======
        await db.execute('''
            CREATE TABLE IF NOT EXISTS vip_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL,
                price INTEGER NOT NULL,
                user_count INTEGER DEFAULT 1,
                active INTEGER DEFAULT 1
            )
        ''')
        
        # ====== جدول لاگ ======
        await db.execute('''
            CREATE TABLE IF NOT EXISTS usage_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                section TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await db.commit()
        
        # ====== پر کردن پلن‌های پیش‌فرض ======
        await init_default_plans(db)
        
        # ====== اضافه کردن کوپن تست ======
        await init_default_coupon(db)

async def init_default_plans(db):
    cursor = await db.execute("SELECT COUNT(*) FROM normal_plans")
    row = await cursor.fetchone()
    if row[0] == 0:
        from config import DEFAULT_NORMAL_PLANS, DEFAULT_VIP_PLANS
        for volume, price in DEFAULT_NORMAL_PLANS:
            await db.execute(
                "INSERT INTO normal_plans (volume_gb, price, user_count) VALUES (?, ?, ?)",
                (volume, price, 1)
            )
        for label, price in DEFAULT_VIP_PLANS:
            await db.execute(
                "INSERT INTO vip_plans (label, price, user_count) VALUES (?, ?, ?)",
                (label, price, 1)
            )
        await db.commit()

async def init_default_coupon(db):
    cursor = await db.execute("SELECT COUNT(*) FROM coupons")
    row = await cursor.fetchone()
    if row[0] == 0:
        await db.execute(
            "INSERT INTO coupons (code, percent, max_uses, active, created_at) VALUES (?, ?, ?, ?, ?)",
            ("TEST10", 10, 100, 1, datetime.now().isoformat())
        )
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
    async with aiosqlite.connect(DB_PATH) as db:
        if url:
            await db.execute(
                "INSERT OR IGNORE INTO proxies (url, remarks, added_date, is_active) VALUES (?, ?, CURRENT_TIMESTAMP, 1)",
                (url, remarks or "Proxy")
            )
        else:
            await db.execute(
                "INSERT OR IGNORE INTO proxies (type, ip, port, added_date, is_active) VALUES (?, ?, ?, CURRENT_TIMESTAMP, 1)",
                (proxy_type.upper() if proxy_type else "HTTP", ip, port)
            )
        await db.commit()

async def get_active_proxies(limit: int = 50):
    async with aiosqlite.connect(DB_PATH) as db:
        results = []
        async with db.execute(
            "SELECT url, remarks FROM proxies WHERE is_active = 1 AND url IS NOT NULL ORDER BY added_date DESC LIMIT ?",
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                results.append({"url": row[0], "remarks": row[1] or "Proxy"})
        
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
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, type, ip, port, url, remarks, is_active, added_date FROM proxies ORDER BY added_date DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                {"id": r[0], "type": r[1], "ip": r[2], "port": r[3], "url": r[4], 
                 "remarks": r[5], "is_active": bool(r[6]), "added_date": r[7]}
                for r in rows
            ]

async def delete_proxy(proxy_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM proxies WHERE id = ?", (proxy_id,))
        await db.commit()

async def delete_all_proxies():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM proxies")
        await db.commit()

# ============================================================
# ====================== توابع V2Ray ======================
# ============================================================

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
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM v2ray")
        await db.commit()

# ============================================================
# ====================== توابع WireGuard ======================
# ============================================================

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
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM wireguard")
        await db.commit()

# ============================================================
# ====================== توابع تیکت ======================
# ============================================================

async def create_ticket(user_id: int, subject: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO tickets (user_id, subject) VALUES (?, ?) RETURNING id",
            (user_id, subject)
        )
        row = await cursor.fetchone()
        await db.commit()
        return row[0] if row else None

async def add_ticket_message(ticket_id: int, sender_id: int, message: str = None, file_id: str = None):
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
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT * FROM tickets WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return rows

async def get_all_tickets():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM tickets ORDER BY created_at DESC") as cursor:
            rows = await cursor.fetchall()
            return rows

async def get_ticket_messages(ticket_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT * FROM ticket_messages WHERE ticket_id = ? ORDER BY created_at ASC",
            (ticket_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return rows

async def update_ticket_status(ticket_id: int, status: str):
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
    code = secrets.token_hex(4)
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
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT new_user_id, registered_at FROM referral_logs WHERE referrer_id = ? ORDER BY registered_at DESC",
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return rows

# ============================================================
# ====================== توابع سفارشات ======================
# ============================================================

async def create_order(user_id: int, username: str, full_name: str, plan_id: int, 
                       plan_name: str, price: int, user_count: int = 1,
                       coupon_code: str = None, original_price: int = None) -> int:
    """ایجاد سفارش جدید و برگرداندن شناسه سفارش"""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute('''
                INSERT INTO orders (
                    user_id, username, full_name, plan_id, plan_name, price, user_count,
                    coupon_code, original_price, created_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id
            ''', (
                user_id, 
                username or "Unknown", 
                full_name or "Unknown", 
                plan_id, 
                plan_name, 
                price, 
                user_count,
                coupon_code, 
                original_price or price, 
                datetime.now().isoformat(),
                "pending"
            ))
            row = await cursor.fetchone()
            await db.commit()
            return row[0] if row else None
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        return None

async def update_order_receipt(order_id: int, file_id: str):
    """ثبت رسید سفارش و تغییر وضعیت به receipt_sent"""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('''
                UPDATE orders SET receipt_file_id = ?, status = 'receipt_sent' WHERE id = ?
            ''', (file_id, order_id))
            await db.commit()
            return True
    except Exception as e:
        logger.error(f"Error updating receipt: {e}")
        return False

async def get_user_orders(user_id: int):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute('''
                SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC
            ''', (user_id,))
            rows = await cursor.fetchall()
            return rows
    except Exception as e:
        logger.error(f"Error getting user orders: {e}")
        return []

async def get_all_pending_orders():
    """دریافت همه سفارش‌های در انتظار تأیید"""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute('''
                SELECT * FROM orders 
                WHERE status IN ('pending', 'receipt_sent') 
                ORDER BY created_at DESC
            ''')
            rows = await cursor.fetchall()
            return rows
    except Exception as e:
        logger.error(f"Error getting pending orders: {e}")
        return []

async def update_order_status(order_id: int, status: str, panel_info: str = None):
    """به‌روزرسانی وضعیت سفارش"""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            if panel_info:
                await db.execute('''
                    UPDATE orders SET status = ?, panel_info = ? WHERE id = ?
                ''', (status, panel_info, order_id))
            else:
                await db.execute('''
                    UPDATE orders SET status = ? WHERE id = ?
                ''', (status, order_id))
            await db.commit()
            return True
    except Exception as e:
        logger.error(f"Error updating order status: {e}")
        return False

# ============================================================
# ====================== توابع کیف پول ======================
# ============================================================

async def get_wallet_balance(user_id: int) -> int:
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT balance FROM wallets WHERE user_id = ?", (user_id,)
            )
            row = await cursor.fetchone()
            return row[0] if row else 0
    except Exception as e:
        logger.error(f"Error getting wallet balance: {e}")
        return 0

async def add_wallet_balance(user_id: int, amount: int):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('''
                INSERT INTO wallets (user_id, balance) VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET balance = balance + ?
            ''', (user_id, amount, amount))
            await db.commit()
            return True
    except Exception as e:
        logger.error(f"Error adding wallet balance: {e}")
        return False

# ============================================================
# ====================== توابع کوپن ======================
# ============================================================

async def get_coupon(code: str):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT * FROM coupons WHERE code = ?", (code.upper(),)
            )
            row = await cursor.fetchone()
            return row
    except Exception as e:
        logger.error(f"Error getting coupon: {e}")
        return None

async def use_coupon(code: str) -> bool:
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute('''
                SELECT max_uses, used_count, active FROM coupons WHERE code = ?
            ''', (code.upper(),))
            row = await cursor.fetchone()
            if not row:
                return False
            max_uses, used_count, active = row
            if not active:
                return False
            if max_uses and used_count >= max_uses:
                return False
            await db.execute('''
                UPDATE coupons SET used_count = used_count + 1 WHERE code = ?
            ''', (code.upper(),))
            await db.commit()
            return True
    except Exception as e:
        logger.error(f"Error using coupon: {e}")
        return False

# ============================================================
# ====================== توابع پلن‌ها ======================
# ============================================================

async def get_normal_plans():
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT id, volume_gb, price, user_count FROM normal_plans WHERE active = 1 ORDER BY volume_gb ASC"
            )
            rows = await cursor.fetchall()
            return rows
    except Exception as e:
        logger.error(f"Error getting normal plans: {e}")
        return []

async def get_normal_plan(plan_id: int):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT id, volume_gb, price, user_count FROM normal_plans WHERE id = ? AND active = 1",
                (plan_id,)
            )
            row = await cursor.fetchone()
            return row
    except Exception as e:
        logger.error(f"Error getting normal plan: {e}")
        return None

async def get_vip_plans():
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT id, label, price, user_count FROM vip_plans WHERE active = 1 ORDER BY price ASC"
            )
            rows = await cursor.fetchall()
            return rows
    except Exception as e:
        logger.error(f"Error getting vip plans: {e}")
        return []

async def get_vip_plan(plan_id: int):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT id, label, price, user_count FROM vip_plans WHERE id = ? AND active = 1",
                (plan_id,)
            )
            row = await cursor.fetchone()
            return row
    except Exception as e:
        logger.error(f"Error getting vip plan: {e}")
        return None

async def update_normal_plan(plan_id: int, volume_gb: int, price: int, user_count: int):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE normal_plans SET volume_gb = ?, price = ?, user_count = ? WHERE id = ?",
                (volume_gb, price, user_count, plan_id)
            )
            await db.commit()
            return True
    except Exception as e:
        logger.error(f"Error updating normal plan: {e}")
        return False

async def update_vip_plan(plan_id: int, label: str, price: int, user_count: int):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE vip_plans SET label = ?, price = ?, user_count = ? WHERE id = ?",
                (label, price, user_count, plan_id)
            )
            await db.commit()
            return True
    except Exception as e:
        logger.error(f"Error updating vip plan: {e}")
        return False

async def add_normal_plan(volume_gb: int, price: int, user_count: int = 1):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO normal_plans (volume_gb, price, user_count) VALUES (?, ?, ?)",
                (volume_gb, price, user_count)
            )
            await db.commit()
            return True
    except Exception as e:
        logger.error(f"Error adding normal plan: {e}")
        return False

async def add_vip_plan(label: str, price: int, user_count: int = 1):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO vip_plans (label, price, user_count) VALUES (?, ?, ?)",
                (label, price, user_count)
            )
            await db.commit()
            return True
    except Exception as e:
        logger.error(f"Error adding vip plan: {e}")
        return False

async def delete_normal_plan(plan_id: int):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM normal_plans WHERE id = ?", (plan_id,))
            await db.commit()
            return True
    except Exception as e:
        logger.error(f"Error deleting normal plan: {e}")
        return False

async def delete_vip_plan(plan_id: int):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM vip_plans WHERE id = ?", (plan_id,))
            await db.commit()
            return True
    except Exception as e:
        logger.error(f"Error deleting vip plan: {e}")
        return False

# ============================================================
# ====================== توابع لاگ ======================
# ============================================================

async def log_usage(user_id: int, section: str):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO usage_logs (user_id, section) VALUES (?, ?)",
                (user_id, section)
            )
            await db.commit()
            return True
    except Exception as e:
        logger.error(f"Error logging usage: {e}")
        return False
