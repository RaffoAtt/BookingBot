from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder # <-- Serve questo per costruire la tastiera

def get_services_kb(services):
    builder = InlineKeyboardBuilder() # Inizializzi il builder
    
    for s in services:
        builder.row(InlineKeyboardButton(
            text=f"{s.name} - {s.price}€", 
            callback_data=f"srv_{s.id}"
        ))
    
    return builder.as_markup() # Trasforma il builder in InlineKeyboardMarkup

def get_slots_kb(slots, date_str):
    builder = InlineKeyboardBuilder()
    
    # Creiamo i bottoni
    for s in slots:
        builder.add(InlineKeyboardButton(
            text=s, 
            callback_data=f"time_{date_str}_{s}"
        ))
    
    # Impostiamo il layout a 3 colonne
    builder.adjust(3)
    
    return builder.as_markup()
