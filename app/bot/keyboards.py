from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_services_kb(services):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for s in services:
        keyboard.add(InlineKeyboardButton(
            text=f"{s.name} - {s.price}€", 
            callback_data=f"srv_{s.id}"
        ))
    return keyboard

def get_slots_kb(slots, date_str):
    keyboard = InlineKeyboardMarkup(row_width=3)
    buttons = [InlineKeyboardButton(text=s, callback_data=f"time_{date_str}_{s}") for s in slots]
    keyboard.add(*buttons)
    return keyboard
