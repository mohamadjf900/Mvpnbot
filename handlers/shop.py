from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import database as db
import config

router = Router()

# ========== State برای خرید ==========
class BuyStates(StatesGroup):
    waiting_for_receipt = State()
    entering_coupon_code = State()

# ========== کیبورد سرویس‌ها (Reply Keyboard) ==========
def services_kb():
    buttons = [
        [KeyboardButton(text="🎮 گیمینگ")],
        [KeyboardButton(text="🌐 مولتی لوکیشن")],
        [KeyboardButton(text="🔙 بازگشت به منو")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# ========== منوی خرید (دستور /shop) ==========
@router.message(Command("shop"))
async def shop_command(message: Message):
    await message.answer(
        "🛒 **خرید سرویس**\n\nلطفاً نوع سرویس مورد نظر را انتخاب کنید:",
        reply_markup=services_kb()
    )

# ========== دکمه گیمینگ ==========
@router.message(F.text == "🎮 گیمینگ")
async def gaming_plans(message: Message):
    plans = await db.get_gaming_plans()
    if not plans:
        await message.answer("❌ در حال حاضر هیچ پلن گیمینگی موجود نیست.", reply_markup=services_kb())
        return
    
    text = "🎮 **پلن‌های سرویس گیمینگ:**\n\n"
    for plan in plans:
        plan_id, volume_gb, price = plan
        text += f"📦 {volume_gb} گیگ → {price:,} تومان\n"
        text += f"برای خرید: `/buy_gaming_{plan_id}`\n\n"
    
    await message.answer(text, reply_markup=services_kb())

# ========== دکمه مولتی لوکیشن ==========
@router.message(F.text == "🌐 مولتی لوکیشن")
async def multi_plans(message: Message):
    plans = await db.get_multi_plans()
    if not plans:
        await message.answer("❌ در حال حاضر هیچ پلن مولتی لوکیشنی موجود نیست.", reply_markup=services_kb())
        return
    
    text = "🌐 **پلن‌های سرویس مولتی لوکیشن:**\n\n"
    for plan in plans:
        plan_id, label, price = plan
        text += f"📦 {label} → {price:,} تومان\n"
        text += f"برای خرید: `/buy_multi_{plan_id}`\n\n"
    
    await message.answer(text, reply_markup=services_kb())

# ========== دکمه بازگشت به منو ==========
@router.message(F.text == "🔙 بازگشت به منو")
async def back_to_main(message: Message):
    from handlers.start import main_menu_keyboard
    await message.answer("منوی اصلی:", reply_markup=main_menu_keyboard(message.from_user.id))

# ========== خرید گیمینگ با دستور ==========
@router.message(Command("buy_gaming_"))
async def buy_gaming(message: Message, state: FSMContext):
    try:
        plan_id = int(message.text.split("_")[2])
        plan = await db.get_gaming_plan(plan_id)
        if not plan:
            await message.answer("❌ پلن یافت نشد!", reply_markup=services_kb())
            return
        
        plan_name = f"{plan[1]} گیگ"
        price = plan[2]
        
        await state.update_data(
            plan_id=plan_id,
            plan_name=plan_name,
            price=price,
            service_type="gaming"
        )
        
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
        await message.answer(text, reply_markup=services_kb())
        await state.set_state(BuyStates.waiting_for_receipt)
        
    except Exception as e:
        await message.answer(f"❌ خطا در پردازش سفارش: {e}", reply_markup=services_kb())

# ========== خرید مولتی با دستور ==========
@router.message(Command("buy_multi_"))
async def buy_multi(message: Message, state: FSMContext):
    try:
        plan_id = int(message.text.split("_")[2])
        plan = await db.get_multi_plan(plan_id)
        if not plan:
            await message.answer("❌ پلن یافت نشد!", reply_markup=services_kb())
            return
        
        plan_name = plan[1]
        price = plan[2]
        
        await state.update_data(
            plan_id=plan_id,
            plan_name=plan_name,
            price=price,
            service_type="multi"
        )
        
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
        await message.answer(text, reply_markup=services_kb())
        await state.set_state(BuyStates.waiting_for_receipt)
        
    except Exception as e:
        await message.answer(f"❌ خطا در پردازش سفارش: {e}", reply_markup=services_kb())

# ========== دریافت رسید ==========
@router.message(BuyStates.waiting_for_receipt, F.photo)
async def receive_receipt(message: Message, state: FSMContext):
    data = await state.get_data()
    if not data:
        await message.answer("❌ هیچ سفارشی در حال پردازش نیست!\nلطفاً دوباره از منوی خرید اقدام کنید.", reply_markup=services_kb())
        await state.clear()
        return
    
    file_id = message.photo[-1].file_id
    caption = message.caption or ""
    
    # ایجاد سفارش در دیتابیس
    order_id = await db.create_order(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        plan_id=data.get('plan_id'),
        plan_name=data.get('plan_name'),
        price=data.get('price'),
        coupon_code=data.get('coupon_code'),
        original_price=data.get('original_price')
    )
    
    await db.update_order_receipt(order_id, file_id)
    
    # ذخیره توضیحات اضافی اگر کاربر پیام داده باشد
    if caption:
        await db.add_ticket_message(order_id, message.from_user.id, caption)
    
    await state.clear()
    
    # اطلاع به ادمین‌ها
    for admin_id in config.ADMIN_IDS:
        try:
            await message.bot.send_photo(
                admin_id,
                photo=file_id,
                caption=f"""
🆕 **سفارش جدید!**

🆔 شماره سفارش: #{order_id}
👤 کاربر: {message.from_user.full_name} (@{message.from_user.username})
📦 سرویس: {data.get('plan_name')}
💰 قیمت: {data.get('price'):,} تومان

✅ برای تأیید: /confirm_{order_id}
❌ برای رد: /reject_{order_id}
📡 برای تحویل: /deliver_{order_id} اطلاعات پنل
"""
            )
        except Exception as e:
            print(f"خطا در ارسال به ادمین: {e}")
    
    await message.answer(
        "✅ رسید شما دریافت شد!\n"
        "سفارش شما برای تأیید به ادمین ارسال شد.\n"
        "به زودی نتیجه به شما اطلاع داده می‌شود.",
        reply_markup=services_kb()
    )

# ========== دریافت پیام غیرعکس در حالت انتظار رسید ==========
@router.message(BuyStates.waiting_for_receipt)
async def invalid_receipt(message: Message):
    await message.answer(
        "❌ لطفاً یک عکس از رسید پرداخت ارسال کنید.\n"
        "اگر نیاز به راهنمایی دارید با ادمین تماس بگیرید.",
        reply_markup=services_kb()
    )

# ========== کوپن تخفیف ==========
@router.message(Command("coupon"))
async def enter_coupon(message: Message, state: FSMContext):
    await state.set_state(BuyStates.entering_coupon_code)
    await message.answer(
        "📝 کد تخفیف خود را وارد کنید:",
        reply_markup=services_kb()
    )

@router.message(BuyStates.entering_coupon_code)
async def apply_coupon(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    coupon = await db.get_coupon(code)
    
    if not coupon:
        await message.answer("❌ کد تخفیف نامعتبر است!", reply_markup=services_kb())
        await state.clear()
        return
    
    if not coupon[4] or (coupon[2] and coupon[3] >= coupon[2]):
        await message.answer("❌ این کد تخفیف منقضی شده است!", reply_markup=services_kb())
        await state.clear()
        return
    
    data = await state.get_data()
    if not data or 'price' not in data:
        await message.answer("❌ هیچ سفارشی در حال پردازش نیست!\nلطفاً ابتدا یک سرویس انتخاب کنید.", reply_markup=services_kb())
        await state.clear()
        return
    
    original_price = data.get('price', 0)
    discount = int(original_price * coupon[1] / 100)
    new_price = original_price - discount
    
    await state.update_data(
        coupon_code=code,
        original_price=original_price,
        price=new_price
    )
    
    await message.answer(
        f"✅ کد تخفیف {coupon[1]}% اعمال شد!\n"
        f"💰 قیمت قبلی: {original_price:,} تومان\n"
        f"💰 قیمت جدید: {new_price:,} تومان\n\n"
        f"💳 لطفاً رسید پرداخت را ارسال کنید.",
        reply_markup=services_kb()
    )
    await state.set_state(BuyStates.waiting_for_receipt)

# ========== کیف پول (دستور) ==========
@router.message(Command("wallet"))
async def wallet_command(message: Message):
    balance = await db.get_wallet_balance(message.from_user.id)
    text = f"💰 **کیف پول شما**\n\nموجودی فعلی: {balance:,} تومان"
    await message.answer(text, reply_markup=services_kb())

# ========== سفارشات من (دستور) ==========
@router.message(Command("myorders"))
async def my_orders_command(message: Message):
    orders = await db.get_user_orders(message.from_user.id)
    if not orders:
        await message.answer("📭 شما هیچ سفارشی ندارید.", reply_markup=services_kb())
        return
    
    text = "📋 **لیست سفارش‌های شما:**\n\n"
    status_map = {
        'pending': '⏳ در انتظار تأیید',
        'receipt_sent': '📸 رسید ارسال شده',
        'confirmed': '✅ تأیید شده',
        'rejected': '❌ رد شده',
        'delivered': '🚀 تحویل داده شده'
    }
    
    for order in orders:
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
    
    await message.answer(text, reply_markup=services_kb())
