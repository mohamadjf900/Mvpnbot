import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import database as db
import config
import aiosqlite

# تنظیم لاگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()

# State مخصوص ایجاد تیکت
class TicketCreationStates(StatesGroup):
    waiting_for_subject = State()
    waiting_for_message = State()

# State مخصوص پاسخ به تیکت (برای ادمین)
class TicketReplyStates(StatesGroup):
    waiting_for_reply = State()

# ================== منوی اصلی تیکت‌ها ==================
@router.callback_query(F.data == "menu_ticket")
async def ticket_menu(callback: CallbackQuery):
    logger.info(f"User {callback.from_user.id} opened ticket menu")
    await db.update_activity(callback.from_user.id)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 ایجاد تیکت جدید", callback_data="ticket_new")
    builder.button(text="📋 تیکت‌های من", callback_data="ticket_my_list")
    if callback.from_user.id in config.ADMIN_IDS:
        builder.button(text="👑 مدیریت تیکت‌ها", callback_data="ticket_admin")
    builder.button(text="🔙 بازگشت", callback_data="menu_main")
    builder.adjust(1)
    
    await callback.message.edit_text(
        "🎫 **سیستم پشتیبانی (تیکتینگ)**\n\n"
        "از این بخش می‌توانید درخواست‌های خود را ثبت کرده و پاسخ آن‌ها را دریافت کنید.",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

# ================== ایجاد تیکت جدید ==================
@router.callback_query(F.data == "ticket_new")
async def ticket_new(callback: CallbackQuery, state: FSMContext):
    logger.info(f"User {callback.from_user.id} started creating new ticket")
    await state.clear()  # پاک کردن هر state قبلی
    await state.set_state(TicketCreationStates.waiting_for_subject)
    await callback.message.edit_text(
        "📝 عنوان تیکت را وارد کنید:\n"
        "(مثلاً: مشکل در اتصال، درخواست کانفیگ جدید، و ...)"
    )
    await callback.answer()

@router.message(TicketCreationStates.waiting_for_subject)
async def ticket_subject_received(message: Message, state: FSMContext):
    logger.info(f"Received subject from user {message.from_user.id}: {message.text}")
    subject = message.text.strip()
    if len(subject) < 3 or len(subject) > 100:
        await message.answer("عنوان باید بین ۳ تا ۱۰۰ کاراکتر باشد. لطفاً دوباره وارد کنید.")
        return
    
    await state.update_data(subject=subject)
    await state.set_state(TicketCreationStates.waiting_for_message)
    await message.answer(
        "✍️ پیام خود را وارد کنید.\n"
        "می‌توانید متن بفرستید یا فایل (عکس، سند) ضمیمه کنید.\n"
        "برای لغو، /cancel را بزنید."
    )

@router.message(TicketCreationStates.waiting_for_message)
async def ticket_message_received(message: Message, state: FSMContext):
    logger.info(f"Received message from user {message.from_user.id}")
    data = await state.get_data()
    if 'subject' not in data:
        await state.clear()
        await message.answer("خطایی رخ داد. لطفاً دوباره تلاش کنید.")
        return
    
    subject = data['subject']
    ticket_id = await db.create_ticket(message.from_user.id, subject)
    
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
    
    # اطلاع به ادمین‌ها
    for admin_id in config.ADMIN_IDS:
        try:
            await message.bot.send_message(
                admin_id,
                f"🎫 **تیکت جدید #{ticket_id}**\n"
                f"از: {message.from_user.full_name} (ID: {message.from_user.id})\n"
                f"عنوان: {subject}\n"
                f"برای مشاهده، به بخش مدیریت تیکت‌ها بروید."
            )
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")
    
    await message.answer(
        f"✅ تیکت شما با شماره #{ticket_id} ثبت شد.\n"
        "به زودی پاسخ داده خواهد شد."
    )

# ================== مشاهده تیکت‌های من ==================
@router.callback_query(F.data == "ticket_my_list")
async def ticket_my_list(callback: CallbackQuery):
    logger.info(f"User {callback.from_user.id} viewing their tickets")
    tickets = await db.get_user_tickets(callback.from_user.id)
    
    if not tickets:
        await callback.message.edit_text(
            "❌ شما هیچ تیکتی ندارید.",
            reply_markup=InlineKeyboardBuilder().button(text="🔙 بازگشت", callback_data="menu_ticket").as_markup()
        )
        await callback.answer()
        return
    
    text = "📋 **لیست تیکت‌های شما:**\n\n"
    builder = InlineKeyboardBuilder()
    
    for t in tickets:
        status_emoji = "🟢" if t[3] == "open" else "🟡" if t[3] == "in_progress" else "🔴"
        text += f"{status_emoji} #{t[0]}: {t[2]} ({t[3]})\n"
        builder.button(text=f"#{t[0]}", callback_data=f"ticket_view_{t[0]}")
    
    builder.adjust(3)
    builder.button(text="🔙 بازگشت", callback_data="menu_ticket")
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

# ================== مشاهده جزئیات تیکت ==================
@router.callback_query(F.data.startswith("ticket_view_"))
async def ticket_view(callback: CallbackQuery):
    ticket_id = int(callback.data.split("_")[2])
    logger.info(f"User {callback.from_user.id} viewing ticket #{ticket_id}")
    
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)) as cursor:
            ticket = await cursor.fetchone()
    
    if not ticket:
        await callback.answer("تیکت یافت نشد!", show_alert=True)
        return
    
    if callback.from_user.id not in config.ADMIN_IDS and ticket[1] != callback.from_user.id:
        await callback.answer("شما به این تیکت دسترسی ندارید!", show_alert=True)
        return
    
    messages = await db.get_ticket_messages(ticket_id)
    
    await callback.message.delete()
    
    status_emoji = "🟢" if ticket[3] == "open" else "🟡" if ticket[3] == "in_progress" else "🔴"
    header = (
        f"🎫 **تیکت #{ticket_id}**\n"
        f"عنوان: {ticket[2]}\n"
        f"وضعیت: {status_emoji} {ticket[3]}\n"
        f"ایجاد: {ticket[4]}\n\n"
    )
    await callback.message.answer(header)
    
    for msg in messages:
        sender = "شما" if msg[2] == callback.from_user.id else "ادمین"
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
            builder.button(text="🔴 بستن", callback_data=f"ticket_status_{ticket_id}_closed")
    
    builder.button(text="🔙 بازگشت", callback_data="menu_ticket")
    builder.adjust(1)
    
    await callback.message.answer("انتخاب کنید:", reply_markup=builder.as_markup())
    await callback.answer()

# ================== پاسخ به تیکت (بخش اصلی مشکل) ==================
@router.callback_query(F.data.startswith("ticket_reply_"))
async def ticket_reply(callback: CallbackQuery, state: FSMContext):
    ticket_id = int(callback.data.split("_")[2])
    logger.info(f"Admin {callback.from_user.id} is replying to ticket #{ticket_id}")
    
    # بررسی دسترسی ادمین
    if callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("شما دسترسی ادمین ندارید!", show_alert=True)
        return
    
    # پاک کردن state قبلی و تنظیم state جدید
    await state.clear()
    await state.update_data(ticket_id=ticket_id)
    await state.set_state(TicketReplyStates.waiting_for_reply)
    
    await callback.message.edit_text(
        "✍️ پاسخ خود را وارد کنید (متن یا فایل):\n"
        "برای لغو، /cancel را بزنید."
    )
    await callback.answer()

@router.message(TicketReplyStates.waiting_for_reply)
async def ticket_reply_received(message: Message, state: FSMContext):
    logger.info(f"Received reply from user {message.from_user.id}")
    
    data = await state.get_data()
    if 'ticket_id' not in data:
        await state.clear()
        await message.answer("خطا: اطلاعات تیکت یافت نشد. لطفاً دوباره از منوی تیکت اقدام کنید.")
        return
    
    ticket_id = data['ticket_id']
    
    # ذخیره پیام در دیتابیس
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
    
    # دریافت user_id صاحب تیکت
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT user_id FROM tickets WHERE id = ?", (ticket_id,)) as cursor:
            ticket = await cursor.fetchone()
            if ticket:
                user_id = ticket[0]
            else:
                user_id = None
    
    # ارسال پیام به کاربر
    if user_id:
        try:
            await message.bot.send_message(
                user_id,
                f"📨 پاسخ جدید برای تیکت #{ticket_id} دریافت شد.\n"
                f"برای مشاهده، به بخش تیکت‌های من بروید."
            )
            logger.info(f"Notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to notify user {user_id}: {e}")
    
    await message.answer("✅ پاسخ شما با موفقیت ثبت و به کاربر ارسال شد.")
    logger.info(f"Reply saved for ticket #{ticket_id}")

# ================== تغییر وضعیت تیکت (فقط ادمین) ==================
@router.callback_query(F.data.startswith("ticket_status_"))
async def ticket_status_change(callback: CallbackQuery):
    if callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("دسترسی ندارید!", show_alert=True)
        return
    
    parts = callback.data.split("_")
    ticket_id = int(parts[2])
    new_status = parts[3]
    
    logger.info(f"Admin {callback.from_user.id} changed ticket #{ticket_id} status to {new_status}")
    
    await db.update_ticket_status(ticket_id, new_status)
    
    # اطلاع به کاربر
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT user_id FROM tickets WHERE id = ?", (ticket_id,)) as cursor:
            ticket = await cursor.fetchone()
            if ticket:
                try:
                    status_text = "در حال بررسی" if new_status == "in_progress" else "بسته شده"
                    await callback.bot.send_message(
                        ticket[0],
                        f"🔄 وضعیت تیکت #{ticket_id} به «{status_text}» تغییر یافت."
                    )
                except Exception as e:
                    logger.error(f"Failed to notify user: {e}")
    
    await callback.answer("✅ وضعیت تیکت به‌روزرسانی شد.")
    await ticket_view(callback)

# ================== مدیریت تیکت‌ها (ادمین) ==================
@router.callback_query(F.data == "ticket_admin")
async def ticket_admin(callback: CallbackQuery):
    if callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("دسترسی ندارید!", show_alert=True)
        return
    
    logger.info(f"Admin {callback.from_user.id} opened admin panel")
    tickets = await db.get_all_tickets()
    
    if not tickets:
        await callback.message.edit_text(
            "❌ هیچ تیکتی وجود ندارد.",
            reply_markup=InlineKeyboardBuilder().button(text="🔙 بازگشت", callback_data="menu_ticket").as_markup()
        )
        await callback.answer()
        return
    
    text = "👑 **مدیریت تیکت‌ها**\n\n"
    builder = InlineKeyboardBuilder()
    
    open_count = sum(1 for t in tickets if t[3] == "open")
    in_progress_count = sum(1 for t in tickets if t[3] == "in_progress")
    closed_count = sum(1 for t in tickets if t[3] == "closed")
    
    text += f"🟢 باز: {open_count} | 🟡 در حال بررسی: {in_progress_count} | 🔴 بسته: {closed_count}\n\n"
    
    for t in tickets[:10]:
        status_emoji = "🟢" if t[3] == "open" else "🟡" if t[3] == "in_progress" else "🔴"
        text += f"{status_emoji} #{t[0]}: {t[2]} (کاربر {t[1]})\n"
        builder.button(text=f"#{t[0]}", callback_data=f"ticket_view_{t[0]}")
    
    builder.adjust(3)
    builder.button(text="🔙 بازگشت", callback_data="menu_ticket")
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data == "ticket_admin_list")
async def ticket_admin_list(callback: CallbackQuery):
    if callback.from_user.id not in config.ADMIN_IDS:
        return
    
    logger.info(f"Admin {callback.from_user.id} viewing full ticket list")
    tickets = await db.get_all_tickets()
    text = "📋 **لیست تمام تیکت‌ها**\n\n"
    builder = InlineKeyboardBuilder()
    
    for t in tickets:
        status_emoji = "🟢" if t[3] == "open" else "🟡" if t[3] == "in_progress" else "🔴"
        builder.button(text=f"{status_emoji} #{t[0]}", callback_data=f"ticket_view_{t[0]}")
    
    builder.adjust(5)
    builder.button(text="🔙 بازگشت", callback_data="ticket_admin")
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

# ================== دستور لغو ==================
@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    logger.info(f"User {message.from_user.id} cancelled operation")
    await state.clear()
    await message.answer("❌ عملیات لغو شد.")
