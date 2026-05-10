from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_services_kb(services):
    # In Aiogram 2 si definisce row_width nell'inizializzazione
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    for s in services:
        # Usiamo il metodo .add() che appartiene all'oggetto InlineKeyboardMarkup
        keyboard.add(InlineKeyboardButton(
            text=f"{s.name} - {s.price}€", 
            callback_data=f"srv_{s.id}"
        ))
    
    return keyboard

def get_slots_kb(slots, date_str):
    keyboard = InlineKeyboardMarkup(row_width=3)
    
    # Creiamo la lista di bottoni
    buttons = [
        InlineKeyboardButton(
            text=s, 
            callback_data=f"time_{date_str}_{s}"
        ) for s in slots
    ]
    
    # Usiamo l'asterisco (*) per scompattare la lista dentro .add()
    keyboard.add(*buttons)
    
    return keyboard
