from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import database as db
import config
import aiosqlite

router = Router()

# ========== State های تیکت ==========
class TicketStates(StatesGroup):
    waiting_for_subject = State()
    waiting_for_message = State()
    waiting_for_reply = State()

# ========== کیبورد بازگشت ==========
def back_to_menu_kb():
    buttons = [[KeyboardButton(text="🔙 بازگشت به منو")]]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# ============================================================
# ====================== منوی اصلی تیکت ======================
# ============================================================

async def show_ticket_menu(message: Message):
    """نمایش منوی اصلی تیکت با دکمه‌های Inline"""
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 ایجاد تیکت جدید", callback_data="ticket_new")
    builder.button(text="📋 تیکت‌های من", callback_data="ticket_my_list")
    
    if message.from_user.id in config.ADMIN_IDS:
        builder.button(text="👑 مدیریت تیکت‌ها", callback_data="ticket_admin")
    
    builder.button(text="🔙 بازگشت", callback_data="menu_main")
    builder.adjust(1)
    
    text = "🎫 **سیستم پشتیبانی (تیکتینگ)**\n\nاز این بخش می‌توانید درخواست‌های خود را ثبت کرده و پاسخ آن‌ها را دریافت کنید."
    await message.answer(text, reply_markup=builder.as_markup())

# ========== دکمه تیکت از منوی Reply Keyboard ==========
@router.message(F.text == "🎫 تیکت پشتیبانی")
async def ticket_menu_message(message: Message):
    await db.update_activity(message.from_user.id)
    await db.log_usage(message.from_user.id, "ticket_menu")
    await show_ticket_menu(message)

# ========== دکمه تیکت از منوی Inline ==========
@router.callback_query(F.data == "menu_ticket")
async def ticket_menu_callback(callback: CallbackQuery):
    await db.update_activity(callback.from_user.id)
    await db.log_usage(callback.from_user.id, "ticket_menu")
    await show_ticket_menu(callback.message)
    await callback.answer()

# ============================================================
# ====================== ایجاد تیکت جدید ======================
# ============================================================

@router.callback_query(F.data == "ticket_new")
async def ticket_new(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(TicketStates.waiting_for_subject)
    await callback.message.edit_text(
        "📝 **ایجاد تیکت جدید**\n\n"
        "عنوان تیکت را وارد کنید:\n"
        "(مثلاً: مشکل در اتصال، درخواست کانفیگ جدید، و ...)"
    )
    await callback.answer()

@router.message(TicketStates.waiting_for_subject)
async def ticket_subject_received(message: Message, state: FSMContext):
    subject = message.text.strip()
    if len(subject) < 3 or len(subject) > 100:
        await message.answer("❌ عنوان باید بین ۳ تا ۱۰۰ کاراکتر باشد. لطفاً دوباره وارد کنید.")
        return
    
    await state.update_data(subject=subject)
    await state.set_state(TicketStates.waiting_for_message)
    await message.answer(
        "✍️ **پیام خود را وارد کنید**\n\n"
        "می‌توانید متن بفرستید یا فایل (عکس، سند) ضمیمه کنید.\n"
        "برای لغو، /cancel را بزنید.",
        reply_markup=back_to_menu_kb()
    )

@router.message(TicketStates.waiting_for_message)
async def ticket_message_received(message: Message, state: FSMContext):
    data = await state.get_data()
    if 'subject' not in data:
        await state.clear()
        await message.answer("❌ خطایی رخ داد. لطفاً دوباره از /start شروع کنید.")
        return
    
    subject = data['subject']
    
    # ایجاد تیکت
    ticket_id = await db.create_ticket(message.from_user.id, subject)
    
    # ذخیره پیام
    file_id = None
    if message.document:
        file_id = message.document.file_id
    elif message.photo:
        file_id = message.photo[-1].file_id
    
    await db.add_ticket_message(
        ticket_id=ticket_id,
        sender_id=message.from_user.id,
        message=message.caption or message.text,
        file_id=file_id
    )
    
    await state.clear()
    
    # اطلاع به ادمین
    for admin_id in config.ADMIN_IDS:
        try:
            await message.bot.send_message(
                admin_id,
                f"🎫 **تیکت جدید #{ticket_id}**\n"
                f"👤 از: {message.from_user.full_name} (@{message.from_user.username})\n"
                f"📌 عنوان: {subject}\n"
                f"📝 پیام: {message.text[:200] if message.text else 'فایل ارسال شده'}"
            )
        except:
            pass
    
    await message.answer(
        f"✅ **تیکت شما با شماره #{ticket_id} ثبت شد.**\n\n"
        "به زودی پاسخ داده خواهد شد.\n"
        "برای مشاهده تیکت‌های خود از گزینه «تیکت‌های من» استفاده کنید.",
        reply_markup=back_to_menu_kb()
    )

# ============================================================
# ====================== تیکت‌های من ======================
# ============================================================

@router.callback_query(F.data == "ticket_my_list")
async def ticket_my_list(callback: CallbackQuery):
    tickets = await db.get_user_tickets(callback.from_user.id)
    
    if not tickets:
        await callback.message.edit_text(
            "📭 شما هیچ تیکتی ندارید.",
            reply_markup=InlineKeyboardBuilder().button(text="🔙 بازگشت", callback_data="menu_ticket").as_markup()
        )
        await callback.answer()
        return
    
    text = "📋 **لیست تیکت‌های شما:**\n\n"
    builder = InlineKeyboardBuilder()
    
    for t in tickets:
        status_emoji = "🟢" if t[3] == "open" else "🟡" if t[3] == "in_progress" else "🔴"
        status_text = "باز" if t[3] == "open" else "در حال بررسی" if t[3] == "in_progress" else "بسته"
        text += f"{status_emoji} #{t[0]}: {t[2]} ({status_text})\n"
        builder.button(text=f"#{t[0]}", callback_data=f"ticket_view_{t[0]}")
    
    builder.adjust(3)
    builder.button(text="🔙 بازگشت", callback_data="menu_ticket")
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

# ============================================================
# ====================== مشاهده تیکت ======================
# ============================================================

@router.callback_query(F.data.startswith("ticket_view_"))
async def ticket_view(callback: CallbackQuery):
    ticket_id = int(callback.data.split("_")[2])
    
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)) as cursor:
            ticket = await cursor.fetchone()
    
    if not ticket:
        await callback.answer("❌ تیکت یافت نشد!", show_alert=True)
        return
    
    if callback.from_user.id not in config.ADMIN_IDS and ticket[1] != callback.from_user.id:
        await callback.answer("❌ شما به این تیکت دسترسی ندارید!", show_alert=True)
        return
    
    messages = await db.get_ticket_messages(ticket_id)
    
    await callback.message.delete()
    
    status_emoji = "🟢" if ticket[3] == "open" else "🟡" if ticket[3] == "in_progress" else "🔴"
    status_text = "باز" if ticket[3] == "open" else "در حال بررسی" if ticket[3] == "in_progress" else "بسته"
    header = (
        f"🎫 **تیکت #{ticket_id}**\n"
        f"📌 عنوان: {ticket[2]}\n"
        f"📊 وضعیت: {status_emoji} {status_text}\n"
        f"📅 ایجاد: {ticket[4]}\n\n"
    )
    await callback.message.answer(header)
    
    for msg in messages:
        sender = "شما" if msg[2] == callback.from_user.id else "👑 ادمین"
        text = f"**{sender}:** {msg[3] if msg[3] else ''}"
        await callback.message.answer(text)
        if msg[4]:
            await callback.message.answer_document(msg[4])
    
    builder = InlineKeyboardBuilder()
    builder.button(text="✍️ پاسخ", callback_data=f"ticket_reply_{ticket_id}")
    
    if callback.from_user.id in config.ADMIN_IDS:
        if ticket[3] == "open":
            builder.button(text="🟡 در حال بررسی", callback_data=f"ticket_status_{ticket_id}_in_progress")
        elif ticket[3] == "in_progress":
            builder.button(text="🔴 بستن تیکت", callback_data=f"ticket_status_{ticket_id}_closed")
        elif ticket[3] == "closed":
            builder.button(text="🔄 باز کردن", callback_data=f"ticket_status_{ticket_id}_open")
    
    builder.button(text="🔙 بازگشت", callback_data="menu_ticket")
    builder.adjust(1)
    
    await callback.message.answer("انتخاب کنید:", reply_markup=builder.as_markup())
    await callback.answer()

# ============================================================
# ====================== پاسخ به تیکت (ادمین) ======================
# ============================================================

@router.callback_query(F.data.startswith("ticket_reply_"))
async def ticket_reply(callback: CallbackQuery, state: FSMContext):
    ticket_id = int(callback.data.split("_")[2])
    
    if callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("❌ فقط ادمین می‌تواند پاسخ دهد!", show_alert=True)
        return
    
    await state.clear()
    await state.update_data(ticket_id=ticket_id)
    await state.set_state(TicketStates.waiting_for_reply)
    
    await callback.message.edit_text(
        "✍️ **پاسخ خود را وارد کنید**\n\n"
        "می‌توانید متن بفرستید یا فایل ضمیمه کنید.\n"
        "برای لغو، /cancel را بزنید."
    )
    await callback.answer()

@router.message(TicketStates.waiting_for_reply)
async def ticket_reply_received(message: Message, state: FSMContext):
    data = await state.get_data()
    if 'ticket_id' not in data:
        await state.clear()
        await message.answer("❌ خطا: اطلاعات تیکت یافت نشد.")
        return
    
    ticket_id = data['ticket_id']
    
    file_id = None
    if message.document:
        file_id = message.document.file_id
    elif message.photo:
        file_id = message.photo[-1].file_id
    
    await db.add_ticket_message(
        ticket_id=ticket_id,
        sender_id=message.from_user.id,
        message=message.caption or message.text,
        file_id=file_id
    )
    
    await state.clear()
    
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT user_id FROM tickets WHERE id = ?", (ticket_id,)) as cursor:
            ticket = await cursor.fetchone()
            user_id = ticket[0] if ticket else None
    
    if user_id:
        try:
            await message.bot.send_message(
                user_id,
                f"📨 **پاسخ جدید برای تیکت #{ticket_id}**\n\n"
                f"متن پاسخ:\n{message.text[:500] if message.text else 'فایل ارسال شده'}\n\n"
                f"برای مشاهده به بخش «تیکت‌های من» بروید."
            )
        except:
            pass
    
    await message.answer(f"✅ پاسخ شما با موفقیت ثبت شد.\nشماره تیکت: #{ticket_id}")

# ============================================================
# ====================== تغییر وضعیت تیکت (ادمین) ======================
# ============================================================

@router.callback_query(F.data.startswith("ticket_status_"))
async def ticket_status_change(callback: CallbackQuery):
    if callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("❌ شما دسترسی ادمین ندارید!", show_alert=True)
        return
    
    parts = callback.data.split("_")
    ticket_id = int(parts[2])
    new_status = parts[3]
    
    await db.update_ticket_status(ticket_id, new_status)
    
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT user_id FROM tickets WHERE id = ?", (ticket_id,)) as cursor:
            ticket = await cursor.fetchone()
            if ticket:
                try:
                    status_text = {
                        'open': 'باز',
                        'in_progress': 'در حال بررسی',
                        'closed': 'بسته'
                    }.get(new_status, new_status)
                    await callback.bot.send_message(
                        ticket[0],
                        f"🔄 **وضعیت تیکت #{ticket_id} تغییر کرد**\n\n"
                        f"وضعیت جدید: {status_text}"
                    )
                except:
                    pass
    
    await callback.answer("✅ وضعیت تیکت به‌روزرسانی شد.")
    await ticket_view(callback)

# ============================================================
# ====================== مدیریت تیکت‌ها (ادمین) ======================
# ============================================================

@router.callback_query(F.data == "ticket_admin")
async def ticket_admin(callback: CallbackQuery):
    if callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("❌ شما دسترسی ادمین ندارید!", show_alert=True)
        return
    
    tickets = await db.get_all_tickets()
    
    if not tickets:
        await callback.message.edit_text(
            "📭 هیچ تیکتی وجود ندارد.",
            reply_markup=InlineKeyboardBuilder().button(text="🔙 بازگشت", callback_data="menu_ticket").as_markup()
        )
        await callback.answer()
        return
    
    open_count = sum(1 for t in tickets if t[3] == "open")
    in_progress_count = sum(1 for t in tickets if t[3] == "in_progress")
    closed_count = sum(1 for t in tickets if t[3] == "closed")
    
    text = "👑 **مدیریت تیکت‌ها**\n\n"
    text += f"🟢 باز: {open_count} | 🟡 در حال بررسی: {in_progress_count} | 🔴 بسته: {closed_count}\n\n"
    text += "**۱۰ تیکت آخر:**\n"
    
    builder = InlineKeyboardBuilder()
    for idx, t in enumerate(tickets[:10]):
        status_emoji = "🟢" if t[3] == "open" else "🟡" if t[3] == "in_progress" else "🔴"
        text += f"{idx+1}. {status_emoji} #{t[0]}: {t[2]} (کاربر {t[1]})\n"
        builder.button(text=f"#{t[0]}", callback_data=f"ticket_view_{t[0]}")
    
    builder.adjust(5)
    builder.button(text="🔙 بازگشت", callback_data="menu_ticket")
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

# ============================================================
# ====================== دستور لغو ======================
# ============================================================

@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("هیچ عملیاتی در حال انجام نیست.")
        return
    await state.clear()
    await message.answer("❌ عملیات لغو شد.")
