from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def back_button(callback_data: str = "menu_main"):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔙 بازگشت", callback_data=callback_data))
    return builder.as_markup()
