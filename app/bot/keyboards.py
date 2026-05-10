import aiogram.types # Importiamo l'intero modulo
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

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


def get_days_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    now = datetime.now()
    
    for i in range(7):
        date_obj = now + timedelta(days=i)
        # Formato per il callback: "date_2026-05-10"
        date_callback = f"date_{date_obj.strftime('%Y-%m-%d')}"
        # Formato per l'utente: "Oggi", "Domani" o "Lun 12 Mag"
        if i == 0:
            label = "Oggi"
        elif i == 1:
            label = "Domani"
        else:
            # Esempio: "Mer 13 Mag" (formato italiano abbreviato)
            label = date_obj.strftime("%a %d %b").capitalize()
            
        kb.add(InlineKeyboardButton(label, callback_data=date_callback))
    
    return kb
