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
        [KeyboardButton(text="📦 عادی")],
        [KeyboardButton(text="⭐ ویژه")],
        [KeyboardButton(text="🔙 بازگشت به منو")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# ========== دکمه عادی (نمایش پلن‌ها با دکمه‌های Inline) ==========
@router.message(F.text == "📦 عادی")
async def normal_plans(message: Message):
    plans = await db.get_normal_plans()
    if not plans:
        await message.answer("❌ در حال حاضر هیچ پلن عادی موجود نیست.", reply_markup=services_kb())
        return
    
    text = "📦 **پلن‌های عادی:**\n\n"
    buttons = []
    for plan in plans:
        plan_id, volume_gb, price = plan
        text += f"📦 {volume_gb} گیگ → {price:,} تومان\n"
        buttons.append([InlineKeyboardButton(
            text=f"خرید {volume_gb} گیگ",
            callback_data=f"buy_normal_{plan_id}"
        )])
    
    # دکمه بازگشت
    buttons.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_services")])
    
    await message.answer(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

# ========== دکمه ویژه (نمایش پلن‌ها با دکمه‌های Inline) ==========
@router.message(F.text == "⭐ ویژه")
async def vip_plans(message: Message):
    plans = await db.get_vip_plans()
    if not plans:
        await message.answer("❌ در حال حاضر هیچ پلن ویژه‌ای موجود نیست.", reply_markup=services_kb())
        return
    
    text = "⭐ **پلن‌های ویژه:**\n\n"
    buttons = []
    for plan in plans:
        plan_id, label, price = plan
        text += f"⭐ {label} → {price:,} تومان\n"
        buttons.append([InlineKeyboardButton(
            text=f"خرید {label}",
            callback_data=f"buy_vip_{plan_id}"
        )])
    
    buttons.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_services")])
    
    await message.answer(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

# ========== بازگشت از لیست پلن‌ها به منوی خرید ==========
@router.callback_query(F.data == "back_to_services")
async def back_to_services(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(
        "🛒 **خرید سرویس**\n\n"
        "لطفاً نوع سرویس مورد نظر را انتخاب کنید:\n"
        "📦 عادی - مناسب کاربری روزمره\n"
        "⭐ ویژه - سرعت و کیفیت بالاتر",
        reply_markup=services_kb()
    )
    await callback.answer()

# ========== بازگشت به منوی اصلی ==========
@router.message(F.text == "🔙 بازگشت به منو")
async def back_to_main(message: Message):
    from handlers.start import main_menu_keyboard
    await message.answer("منوی اصلی:", reply_markup=main_menu_keyboard(message.from_user.id))

# ========== خرید عادی (Callback) ==========
@router.callback_query(F.data.startswith("buy_normal_"))
async def buy_normal_callback(callback: CallbackQuery, state: FSMContext):
    plan_id = int(callback.data.split("_")[2])
    plan = await db.get_normal_plan(plan_id)
    if not plan:
        await callback.answer("❌ پلن یافت نشد!", show_alert=True)
        return
    
    plan_name = f"{plan[1]} گیگ (عادی)"
    price = plan[2]
    
    await state.update_data(
        plan_id=plan_id,
        plan_name=plan_name,
        price=price,
        service_type="normal"
    )
    
    text = f"""
📋 **سفارش شما:**

📦 سرویس: {plan_name}
💰 قیمت: {price:,} تومان

💳 **روش پرداخت:**
برای پرداخت، لطفاً با ادمین در ارتباط باشید.

📩 پیوی ادمین: @{config.SUPPORT_USERNAME}

📸 بعد از واریز، رسید را (عکس) در همینجا ارسال کنید.
"""
    await callback.message.edit_text(text)
    await callback.message.answer("📸 لطفاً رسید را ارسال کنید:", reply_markup=services_kb())
    await state.set_state(BuyStates.waiting_for_receipt)
    await callback.answer()

# ========== خرید ویژه (Callback) ==========
@router.callback_query(F.data.startswith("buy_vip_"))
async def buy_vip_callback(callback: CallbackQuery, state: FSMContext):
    plan_id = int(callback.data.split("_")[2])
    plan = await db.get_vip_plan(plan_id)
    if not plan:
        await callback.answer("❌ پلن یافت نشد!", show_alert=True)
        return
    
    plan_name = f"{plan[1]} (ویژه)"
    price = plan[2]
    
    await state.update_data(
        plan_id=plan_id,
        plan_name=plan_name,
        price=price,
        service_type="vip"
    )
    
    text = f"""
📋 **سفارش شما:**

⭐ سرویس ویژه: {plan_name}
💰 قیمت: {price:,} تومان

💳 **روش پرداخت:**
برای پرداخت، لطفاً با ادمین در ارتباط باشید.

📩 پیوی ادمین: @{config.SUPPORT_USERNAME}

📸 بعد از واریز، رسید را (عکس) در همینجا ارسال کنید.
"""
    await callback.message.edit_text(text)
    await callback.message.answer("📸 لطفاً رسید را ارسال کنید:", reply_markup=services_kb())
    await state.set_state(BuyStates.waiting_for_receipt)
    await callback.answer()

# ========== دریافت رسید ==========
@router.message(BuyStates.waiting_for_receipt, F.photo)
async def receive_receipt(message: Message, state: FSMContext):
    data = await state.get_data()
    if not data:
        await message.answer("❌ هیچ سفارشی در حال پردازش نیست!", reply_markup=services_kb())
        await state.clear()
        return
    
    file_id = message.photo[-1].file_id
    
    # ایجاد سفارش
    order_id = await db.create_order(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        plan_id=data.get('plan_id'),
        plan_name=data.get('plan_name'),
        price=data.get('price')
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
📦 سرویس: {data.get('plan_name')}
💰 قیمت: {data.get('price'):,} تومان

✅ تأیید: /confirm_{order_id}
❌ رد: /reject_{order_id}
📡 تحویل: /deliver_{order_id} اطلاعات پنل
"""
            )
        except:
            pass
    
    await message.answer(
        "✅ رسید شما دریافت شد!\nسفارش شما برای تأیید به ادمین ارسال شد.",
        reply_markup=services_kb()
    )

@router.message(BuyStates.waiting_for_receipt)
async def invalid_receipt(message: Message):
    await message.answer(
        "❌ لطفاً یک عکس از رسید پرداخت ارسال کنید.",
        reply_markup=services_kb()
    )

# ========== دستورات خرید به‌عنوان Command (اختیاری) ==========
@router.message(Command("buy_normal_"))
async def buy_normal_command(message: Message, state: FSMContext):
    # همانند کالبک، اما برای کاربرانی که دستور تایپ می‌کنند
    try:
        plan_id = int(message.text.split("_")[2])
        plan = await db.get_normal_plan(plan_id)
        if not plan:
            await message.answer("❌ پلن یافت نشد!", reply_markup=services_kb())
            return
        # ادامه مثل کالبک
        plan_name = f"{plan[1]} گیگ (عادی)"
        price = plan[2]
        await state.update_data(plan_id=plan_id, plan_name=plan_name, price=price, service_type="normal")
        text = f"..."
        await message.answer(text, reply_markup=services_kb())
        await state.set_state(BuyStates.waiting_for_receipt)
    except:
        await message.answer("❌ خطا در پردازش دستور.", reply_markup=services_kb())

@router.message(Command("buy_vip_"))
async def buy_vip_command(message: Message, state: FSMContext):
    # مشابه
    try:
        plan_id = int(message.text.split("_")[2])
        plan = await db.get_vip_plan(plan_id)
        if not plan:
            await message.answer("❌ پلن یافت نشد!", reply_markup=services_kb())
            return
        plan_name = f"{plan[1]} (ویژه)"
        price = plan[2]
        await state.update_data(plan_id=plan_id, plan_name=plan_name, price=price, service_type="vip")
        text = f"..."
        await message.answer(text, reply_markup=services_kb())
        await state.set_state(BuyStates.waiting_for_receipt)
    except:
        await message.answer("❌ خطا در پردازش دستور.", reply_markup=services_kb())

# ========== کوپن تخفیف ==========
@router.message(Command("coupon"))
async def enter_coupon(message: Message, state: FSMContext):
    await state.set_state(BuyStates.entering_coupon_code)
    await message.answer("📝 کد تخفیف خود را وارد کنید:", reply_markup=services_kb())

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
        await message.answer("❌ هیچ سفارشی در حال پردازش نیست!", reply_markup=services_kb())
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
        f"📸 لطفاً رسید پرداخت را ارسال کنید.",
        reply_markup=services_kb()
    )
    await state.set_state(BuyStates.waiting_for_receipt)
