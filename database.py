import aiosqlite
from datetime import datetime
from config import DB_PATH

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
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
                receipt_file_id TEXT,
                status TEXT DEFAULT 'pending',
                panel_info TEXT,
                payment_method TEXT DEFAULT 'receipt',
                coupon_code TEXT,
                original_price INTEGER,
                created_at TEXT
            )
        ''')
        
        # ====== جدول کاربران ======
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                joined_at TEXT,
                last_seen TEXT
            )
        ''')
        
        # ====== جدول رفرال ======
        await db.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                referred_id INTEGER NOT NULL UNIQUE,
                referred_username TEXT,
                converted INTEGER DEFAULT 0,
                created_at TEXT
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS reward_claims (
                referrer_id INTEGER PRIMARY KEY,
                claimed_at TEXT
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS referral_commissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                referred_id INTEGER NOT NULL,
                order_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                created_at TEXT
            )
        ''')
        
        # ====== جدول پلن‌ها ======
        await db.execute('''
            CREATE TABLE IF NOT EXISTS gaming_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                volume_gb INTEGER NOT NULL,
                price INTEGER NOT NULL,
                active INTEGER DEFAULT 1
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS multi_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL,
                price INTEGER NOT NULL,
                active INTEGER DEFAULT 1
            )
        ''')
        
        # ====== جدول کیف پول ======
        await db.execute('''
            CREATE TABLE IF NOT EXISTS wallets (
                user_id INTEGER PRIMARY KEY,
                balance INTEGER NOT NULL DEFAULT 0
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS wallet_topups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                full_name TEXT,
                amount INTEGER NOT NULL,
                receipt_file_id TEXT,
                status TEXT DEFAULT 'awaiting_receipt',
                created_at TEXT
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
        
        # ====== جدول تنظیمات ======
        await db.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # ====== جدول ادمین‌ها ======
        await db.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                role TEXT NOT NULL,
                added_by INTEGER,
                added_at TEXT
            )
        ''')
        
        await db.commit()
        
        # ====== پر کردن پلن‌های پیش‌فرض ======
        await init_default_plans(db)
        
        # ====== اضافه کردن ادمین اول ======
        await init_default_admin(db)

async def init_default_plans(db):
    cursor = await db.execute("SELECT COUNT(*) FROM gaming_plans")
    row = await cursor.fetchone()
    if row[0] == 0:
        from config import DEFAULT_GAMING_PLANS, DEFAULT_MULTI_PLANS
        for volume, price in DEFAULT_GAMING_PLANS:
            await db.execute(
                "INSERT INTO gaming_plans (volume_gb, price) VALUES (?, ?)",
                (volume, price)
            )
        for label, price in DEFAULT_MULTI_PLANS:
            await db.execute(
                "INSERT INTO multi_plans (label, price) VALUES (?, ?)",
                (label, price)
            )
        await db.commit()

async def init_default_admin(db):
    from config import ADMIN_IDS
    for admin_id in ADMIN_IDS:
        await db.execute(
            "INSERT OR IGNORE INTO admins (user_id, role, added_at) VALUES (?, ?, ?)",
            (admin_id, "owner", datetime.now().isoformat())
        )
    await db.commit()

# ============================================================
# ====================== توابع سفارشات ======================
# ============================================================

async def create_order(user_id: int, username: str, full_name: str, plan_id: int, 
                       plan_name: str, price: int, coupon_code: str = None, 
                       original_price: int = None) -> int:
    from datetime import datetime
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('''
            INSERT INTO orders (
                user_id, username, full_name, plan_id, plan_name, price,
                coupon_code, original_price, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING id
        ''', (user_id, username, full_name, plan_id, plan_name, price,
              coupon_code, original_price or price, datetime.now().isoformat()))
        row = await cursor.fetchone()
        await db.commit()
        return row[0] if row else None

async def get_user_orders(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('''
            SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC
        ''', (user_id,))
        rows = await cursor.fetchall()
        return rows

async def get_all_pending_orders():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('''
            SELECT * FROM orders WHERE status = 'pending' ORDER BY created_at DESC
        ''')
        rows = await cursor.fetchall()
        return rows

async def update_order_status(order_id: int, status: str, panel_info: str = None):
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

async def update_order_receipt(order_id: int, file_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            UPDATE orders SET receipt_file_id = ?, status = 'receipt_sent' WHERE id = ?
        ''', (file_id, order_id))
        await db.commit()

# ============================================================
# ====================== توابع کاربران ======================
# ============================================================

async def save_user(user_id: int, username: str = None, full_name: str = None):
    from datetime import datetime
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT OR REPLACE INTO users (user_id, username, full_name, last_seen)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, full_name, datetime.now().isoformat()))
        await db.commit()

# ============================================================
# ====================== توابع کیف پول ======================
# ============================================================

async def get_wallet_balance(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT balance FROM wallets WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0

async def add_wallet_balance(user_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO wallets (user_id, balance) VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET balance = balance + ?
        ''', (user_id, amount, amount))
        await db.commit()

async def create_topup_request(user_id: int, username: str, full_name: str, amount: int):
    from datetime import datetime
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('''
            INSERT INTO wallet_topups (user_id, username, full_name, amount, created_at)
            VALUES (?, ?, ?, ?, ?)
            RETURNING id
        ''', (user_id, username, full_name, amount, datetime.now().isoformat()))
        row = await cursor.fetchone()
        await db.commit()
        return row[0] if row else None

async def update_topup_receipt(topup_id: int, file_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            UPDATE wallet_topups SET receipt_file_id = ?, status = 'receipt_sent'
            WHERE id = ?
        ''', (file_id, topup_id))
        await db.commit()

async def get_pending_topups():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('''
            SELECT * FROM wallet_topups WHERE status = 'receipt_sent'
            ORDER BY created_at DESC
        ''')
        rows = await cursor.fetchall()
        return rows

async def confirm_topup(topup_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT user_id, amount FROM wallet_topups WHERE id = ?",
            (topup_id,)
        )
        row = await cursor.fetchone()
        if row:
            user_id, amount = row
            await add_wallet_balance(user_id, amount)
            await db.execute(
                "UPDATE wallet_topups SET status = 'confirmed' WHERE id = ?",
                (topup_id,)
            )
            await db.commit()
            return user_id, amount
    return None, None

# ============================================================
# ====================== توابع کوپن ======================
# ============================================================

async def create_coupon(code: str, percent: int, max_uses: int = None):
    from datetime import datetime
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO coupons (code, percent, max_uses, created_at)
            VALUES (?, ?, ?, ?)
        ''', (code.upper(), percent, max_uses, datetime.now().isoformat()))
        await db.commit()

async def get_coupon(code: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT * FROM coupons WHERE code = ?", (code.upper(),)
        )
        row = await cursor.fetchone()
        return row

async def use_coupon(code: str) -> bool:
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

# ============================================================
# ====================== توابع پلن‌ها ======================
# ============================================================

async def get_gaming_plans():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, volume_gb, price FROM gaming_plans WHERE active = 1 ORDER BY volume_gb ASC"
        )
        rows = await cursor.fetchall()
        return rows

async def get_gaming_plan(plan_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, volume_gb, price FROM gaming_plans WHERE id = ? AND active = 1",
            (plan_id,)
        )
        row = await cursor.fetchone()
        return row

async def get_multi_plans():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, label, price FROM multi_plans WHERE active = 1 ORDER BY price ASC"
        )
        rows = await cursor.fetchall()
        return rows

async def get_multi_plan(plan_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, label, price FROM multi_plans WHERE id = ? AND active = 1",
            (plan_id,)
        )
        row = await cursor.fetchone()
        return row

# ============================================================
# ====================== توابع رفرال ======================
# ============================================================

async def get_referrer_by_referred(referred_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT referrer_id FROM referrals WHERE referred_id = ?",
            (referred_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None

async def get_referral_count(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM referrals WHERE referrer_id = ? AND converted = 1",
            (user_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0

async def can_claim_reward(user_id: int) -> bool:
    from config import REFERRAL_REQUIRED_COUNT
    count = await get_referral_count(user_id)
    if count < REFERRAL_REQUIRED_COUNT:
        return False
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT * FROM reward_claims WHERE referrer_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        return row is None

async def claim_reward(user_id: int):
    from datetime import datetime
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO reward_claims (referrer_id, claimed_at) VALUES (?, ?)",
            (user_id, datetime.now().isoformat())
        )
        await db.commit()

async def add_referral(referrer_id: int, referred_id: int, referred_username: str = None):
    from datetime import datetime
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT OR IGNORE INTO referrals (referrer_id, referred_id, referred_username, created_at)
            VALUES (?, ?, ?, ?)
        ''', (referrer_id, referred_id, referred_username, datetime.now().isoformat()))
        await db.commit()

async def get_referral_code(user_id: int) -> str:
    """دریافت کد دعوت کاربر"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT code FROM referrals WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None

async def create_referral_code(user_id: int) -> str:
    import secrets
    code = secrets.token_hex(4)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO referrals (user_id, code) VALUES (?, ?)",
            (user_id, code)
        )
        await db.commit()
    return code
