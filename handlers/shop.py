from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import database as db
import config

router = Router()

# ========== States ==========
class BuyStates(StatesGroup):
    waiting_for_receipt = State()
    entering_coupon_code = State()

class AdminStates(StatesGroup):
    waiting_for_panel_info = State()

# ========== منوی اصلی (Reply Keyboard) ==========
def main_menu_kb(user_id: int = None):
    keyboard = [
        [types.KeyboardButton(text="🛒 خرید سرویس"), types.KeyboardButton(text="📋 سرویس‌های من")],
        [types.KeyboardButton(text="💰 کیف پول"), types.KeyboardButton(text="📞 پشتیبانی")],
        [types.KeyboardButton(text="👥 دعوت دوستان"), types.KeyboardButton(text="📜 قوانین")],
    ]
    if user_id and user_id in config.ADMIN_IDS:
        keyboard.append([types.KeyboardButton(text="⚙️ مدیریت ربات")])
    return types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def back_menu_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="back:menu")]]
    )

def services_kb():
    rows = [
        [InlineKeyboardButton(text="🎮 سرویس گیمینگ", callback_data="svc:gaming")],
        [InlineKeyboardButton(text="🌐 سرویس مولتی لوکیشن", callback_data="svc:multi")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back:menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

# ========== منوی اصلی ==========
@router.message(Command("start"))
async def start_command(message: Message):
    user = message.from_user
    await db.save_user(user.id, user.username, user.full_name)
    
    # بررسی لینک رفرال
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        code = args[1][4:]
        import aiosqlite
        async with aiosqlite.connect(config.DB_PATH) as conn:
            cursor = await conn.execute(
                "SELECT user_id FROM referrals WHERE code = ?",
                (code,)
            )
            row = await cursor.fetchone()
            if row and row[0] != user.id:
                await db.add_referral(row[0], user.id, user.username)
                await message.answer("🎉 شما با دعوت دوست خود وارد شدید!")
    
    welcome_text = f"""
🎯 به ربات {config.BRAND_NAME} خوش آمدید!

📌 از منوی زیر یکی از گزینه‌ها را انتخاب کنید:
• 🛒 خرید سرویس
• 📋 سرویس‌های من
• 💰 کیف پول
• 👥 دعوت دوستان
• 📜 قوانین
• 📞 پشتیبانی
"""
    await message.answer(welcome_text, reply_markup=main_menu_kb(user.id))

# ========== خرید سرویس ==========
@router.message(F.text == "🛒 خرید سرویس")
async def buy_menu(message: Message):
    await message.answer(
        "لطفاً نوع سرویس مورد نظر خود را انتخاب کنید:",
        reply_markup=services_kb()
    )

@router.callback_query(F.data == "svc:gaming")
async def gaming_plans(callback: CallbackQuery):
    plans = await db.get_gaming_plans()
    if not plans:
        await callback.message.edit_text(
            "❌ در حال حاضر هیچ پلن گیمینگی موجود نیست.",
            reply_markup=back_menu_kb()
        )
        await callback.answer()
        return
    
    text = "🎮 **پلن‌های سرویس گیمینگ:**\n\n"
    buttons = []
    for plan in plans:
        plan_id, volume_gb, price = plan
        text += f"📦 {volume_gb} گیگ → {price:,} تومان\n"
        buttons.append([InlineKeyboardButton(
            f"خرید {volume_gb} گیگ", 
            callback_data=f"buy:gaming:{plan_id}"
        )])
    buttons.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data="back:services")])
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()

@router.callback_query(F.data == "svc:multi")
async def multi_plans(callback: CallbackQuery):
    plans = await db.get_multi_plans()
    if not plans:
        await callback.message.edit_text(
            "❌ در حال حاضر هیچ پلن مولتی لوکیشنی موجود نیست.",
            reply_markup=back_menu_kb()
        )
        await callback.answer()
        return
    
    text = "🌐 **پلن‌های سرویس مولتی لوکیشن:**\n\n"
    buttons = []
    for plan in plans:
        plan_id, label, price = plan
        text += f"📦 {label} → {price:,} تومان\n"
        buttons.append([InlineKeyboardButton(
            f"خرید {label}", 
            callback_data=f"buy:multi:{plan_id}"
        )])
    buttons.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data="back:services")])
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("buy:"))
async def start_buy_process(callback: CallbackQuery, state: FSMContext):
    _, service_type, plan_id = callback.data.split(":")
    plan_id = int(plan_id)
    
    if service_type == "gaming":
        plan = await db.get_gaming_plan(plan_id)
        plan_name = f"{plan[1]} گیگ"
        price = plan[2]
    else:
        plan = await db.get_multi_plan(plan_id)
        plan_name = plan[1]
        price = plan[2]
    
    await state.update_data(
        service_type=service_type,
        plan_id=plan_id,
        plan_name=plan_name,
        price=price
    )
    
    # متن بدون شماره کارت
    text = f"""
📋 **سفارش شما:**

📦 سرویس: {plan_name}
💰 قیمت: {price:,} تومان

💳 **روش پرداخت:**

برای پرداخت، لطفاً با ادمین در ارتباط باشید و پس از واریز، رسید را برای ربات ارسال کنید.

📩 پیوی ادمین: @{config.SUPPORT_USERNAME}

📸 بعد از واریز، رسید را (عکس) در همینجا ارسال کنید.

💡 اگر کد تخفیف دارید، /coupon را بزنید.
"""
    await callback.message.edit_text(text, reply_markup=back_menu_kb())
    await state.set_state(BuyStates.waiting_for_receipt)
    await callback.answer()

# ========== دریافت رسید ==========
@router.message(BuyStates.waiting_for_receipt, F.photo)
async def receive_receipt(message: Message, state: FSMContext):
    data = await state.get_data()
    file_id = message.photo[-1].file_id
    
    order_id = await db.create_order(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        plan_id=data['plan_id'],
        plan_name=data['plan_name'],
        price=data['price'],
        coupon_code=data.get('coupon_code'),
        original_price=data.get('original_price', data['price'])
    )
    
    await db.update_order_receipt(order_id, file_id)
    await state.clear()
    
    # اطلاع به ادمین
    for admin_id in config.ADMIN_IDS:
        try:
            await message.bot.send_photo(
                admin_id,
                photo=file_id,
                caption=f"""
🆕 **سفارش جدید!**

🆔 شماره سفارش: #{order_id}
👤 کاربر: {message.from_user.full_name} (@{message.from_user.username})
📦 سرویس: {data['plan_name']}
💰 قیمت: {data['price']:,} تومان

✅ برای تأیید: /confirm_{order_id}
❌ برای رد: /reject_{order_id}
📡 برای تحویل: /deliver_{order_id} اطلاعات پنل
"""
            )
        except:
            pass
    
    await message.answer(
        "✅ رسید شما دریافت شد!\n"
        "سفارش شما برای تأیید به ادمین ارسال شد.\n"
        "به زودی نتیجه به شما اطلاع داده می‌شود.",
        reply_markup=main_menu_kb(message.from_user.id)
    )

@router.message(BuyStates.waiting_for_receipt)
async def invalid_receipt(message: Message):
    await message.answer(
        "❌ لطفاً یک عکس از رسید پرداخت ارسال کنید.",
        reply_markup=back_menu_kb()
    )

# ========== سرویس‌های من ==========
@router.message(F.text == "📋 سرویس‌های من")
async def my_orders(message: Message):
    orders = await db.get_user_orders(message.from_user.id)
    if not orders:
        await message.answer(
            "📭 شما هیچ سفارشی ندارید.",
            reply_markup=main_menu_kb(message.from_user.id)
        )
        return
    
    text = "📋 **لیست سفارش‌های شما:**\n\n"
    for order in orders:
        status_map = {
            'pending': '⏳ در انتظار تأیید',
            'receipt_sent': '📸 رسید ارسال شده',
            'confirmed': '✅ تأیید شده',
            'rejected': '❌ رد شده',
            'delivered': '🚀 تحویل داده شده'
        }
        status_text = status_map.get(order[6], order[6])
        text += f"""
🆔 #{order[0]}
📦 {order[5]}
💰 {order[4]:,} تومان
📌 وضعیت: {status_text}
"""
        if order[7]:
            text += f"📡 اطلاعات: {order[7]}\n"
        text += "─" * 20 + "\n"
    
    await message.answer(text, reply_markup=main_menu_kb(message.from_user.id))

# ========== کوپن تخفیف ==========
@router.message(Command("coupon"))
async def enter_coupon(message: Message, state: FSMContext):
    await state.set_state(BuyStates.entering_coupon_code)
    await message.answer(
        "📝 کد تخفیف خود را وارد کنید:",
        reply_markup=back_menu_kb()
    )

@router.message(BuyStates.entering_coupon_code)
async def apply_coupon(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    coupon = await db.get_coupon(code)
    
    if not coupon:
        await message.answer("❌ کد تخفیف نامعتبر است!")
        await state.clear()
        return
    
    if not coupon[4] or (coupon[2] and coupon[3] >= coupon[2]):
        await message.answer("❌ این کد تخفیف منقضی شده است!")
        await state.clear()
        return
    
    data = await state.get_data()
    original_price = data.get('price', 0)
    discount = int(original_price * coupon[1] / 100)
    new_price = original_price - discount
    
    await state.update_data(
        coupon_code=code,
        original_price=original_price
    )
    await state.update_data(price=new_price)
    
    await message.answer(
        f"✅ کد تخفیف {coupon[1]}% اعمال شد!\n"
        f"💰 قیمت قبلی: {original_price:,} تومان\n"
        f"💰 قیمت جدید: {new_price:,} تومان\n\n"
        f"💳 لطفاً رسید پرداخت را ارسال کنید."
    )
    await state.set_state(BuyStates.waiting_for_receipt)

# ========== کیف پول ==========
@router.message(F.text == "💰 کیف پول")
async def wallet_menu(message: Message):
    balance = await db.get_wallet_balance(message.from_user.id)
    text = f"""
💰 **کیف پول شما**

موجودی فعلی: {balance:,} تومان

📌 برای شارژ کیف پول، با ادمین در ارتباط باشید:
👤 @{config.SUPPORT_USERNAME}

پس از شارژ، موجودی شما به‌روزرسانی می‌شود.
"""
    await message.answer(text, reply_markup=main_menu_kb(message.from_user.id))

# ========== قوانین ==========
@router.message(F.text == "📜 قوانین")
async def rules(message: Message):
    text = f"""
📜 **قوانین و مقررات {config.BRAND_NAME}**

۱. استفاده از سرویس‌های ما به معنای پذیرش این قوانین است.
۲. هرگونه سوءاستفاده از سرویس منجر به مسدود شدن حساب می‌شود.
۳. پشتیبانی فقط از طریق ربات و پیوی ادمین انجام می‌شود.
۴. در صورت بروز مشکل، با پشتیبانی تماس بگیرید.

📞 پشتیبانی: @{config.SUPPORT_USERNAME}
"""
    await message.answer(text, reply_markup=main_menu_kb(message.from_user.id))

# ========== پشتیبانی ==========
@router.message(F.text == "📞 پشتیبانی")
async def support_menu(message: Message):
    text = f"""
📞 **پشتیبانی {config.BRAND_NAME}**

برای ارتباط با پشتیبانی، از یکی از روش‌های زیر استفاده کنید:

📩 پیوی ادمین: @{config.SUPPORT_USERNAME}
🎫 سیستم تیکت: از منوی اصلی گزینه تیکت پشتیبانی را انتخاب کنید.

ساعات پاسخگویی: ۲۴ ساعته
"""
    await message.answer(text, reply_markup=main_menu_kb(message.from_user.id))

# ========== بازگشت ==========
@router.callback_query(F.data == "back:menu")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(
        "منوی اصلی:",
        reply_markup=main_menu_kb(callback.from_user.id)
    )
    await callback.answer()

@router.callback_query(F.data == "back:services")
async def back_to_services(callback: CallbackQuery):
    await callback.message.edit_text(
        "لطفاً نوع سرویس مورد نظر خود را انتخاب کنید:",
        reply_markup=services_kb()
    )
    await callback.answer()
