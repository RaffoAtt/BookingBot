import aiogram.types # Importiamo l'intero modulo
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_services_kb(services):
    # Usiamo il percorso completo per sicurezza
    keyboard = aiogram.types.InlineKeyboardMarkup(row_width=1)
    
    for s in services:
        keyboard.add(aiogram.types.InlineKeyboardButton(
            text=f"{s.name} - {s.price}€", 
            callback_data=f"srv_{s.id}"
        ))
    
    return keyboard

def get_slots_kb(slots, date_str):
    # Usiamo il percorso completo anche qui
    keyboard = aiogram.types.InlineKeyboardMarkup(row_width=3)
    
    buttons = [
        aiogram.types.InlineKeyboardButton(
            text=s, 
            callback_data=f"time_{date_str}_{s}"
        ) for s in slots
    ]
    
    keyboard.add(*buttons)
    
    return keyboard
