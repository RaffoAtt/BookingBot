from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

# Import dai moduli del tuo progetto
from app.database import SessionLocal, Service, Business
from app.services import google_cal, scheduler
from .keyboards import get_services_kb, get_slots_kb

class BookingStates(StatesGroup):
    choosing_service = State()
    choosing_date = State()
    choosing_time = State()
    entering_name = State()

async def cmd_start(message: types.Message):
    db = SessionLocal()
    try:
        services = db.query(Service).all()
        if not services:
            await message.answer("Al momento non ci sono servizi disponibili.")
            return
            
        await message.answer(
            "Benvenuto! Scegli un servizio per iniziare la prenotazione:", 
            reply_markup=get_services_kb(services)
        )
        await BookingStates.choosing_service.set()
    finally:
        db.close()

async def process_service(callback_query: types.CallbackQuery, state: FSMContext):
    # Estraiamo l'ID del servizio dalla callback (es: srv_1)
    service_id = callback_query.data.split("_")[1]
    await state.update_data(service_id=service_id)
    
    # Creazione tastiera per la scelta della data
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("Oggi", callback_data="date_today"),
        InlineKeyboardButton("Domani", callback_data="date_tomorrow")
    )
    
    await callback_query.message.answer(
        "Ottima scelta! Per quale giorno vuoi prenotare?", 
        reply_markup=kb
    )
    await BookingStates.choosing_date.set()
    await callback_query.answer()

async def process_date(callback_query: types.CallbackQuery, state: FSMContext):
    # Calcolo della data selezionata
    if "today" in callback_query.data:
        selected_date = datetime.now()
    else:
        selected_date = datetime.now() + timedelta(days=1)
    
    date_str = selected_date.strftime("%Y-%m-%d")
    await state.update_data(date=date_str)
    
    db = SessionLocal()
    try:
        # Recupero del business (assicurati che esista almeno un record in questa tabella)
        biz = db.query(Business).first()
        
        # Validazione dati per evitare 'NoneType' object has no attribute 'keys'
        if not biz or not biz.opening_hours:
            await callback_query.message.answer("Errore: Orari del locale non configurati correttamente.")
            return

        # Recupero impegni da Google Calendar
        # Nota: busy sarà None o [] se le credenziali mancano o sono errate
        busy = []
        if biz.google_creds:
            try:
                busy = google_cal.fetch_busy_slots(biz.google_creds, selected_date)
            except Exception as e:
                print(f"Google API Error: {e}")

# Calcolo slot disponibili
        day_name = selected_date.strftime("%a").lower()[:3] # es: 'mon', 'tue'
        
        # Gestione Robusta di opening_hours
        if isinstance(biz.opening_hours, dict):
            # Se è un dizionario: {"mon": ["09:00", "18:00"]}
            day_schedule = biz.opening_hours.get(day_name)
        elif isinstance(biz.opening_hours, list):
            # Se è una lista: ["09:00", "18:00"] (valida per tutti i giorni)
            day_schedule = biz.opening_hours
        else:
            day_schedule = None

        if not day_schedule:
            await callback_query.message.answer(f"Spiacenti, il locale è chiuso il giorno {date_str}.")
            return

        # Passiamo i dati allo scheduler
        slots = scheduler.get_available_slots(day_schedule, busy, 30)
        
        if not slots:
            await callback_query.message.answer("Non ci sono orari disponibili per questa data.")
        else:
            await callback_query.message.answer(
                f"Orari disponibili per il {date_str}:", 
                reply_markup=get_slots_kb(slots, date_str)
            )
            await BookingStates.choosing_time.set()
            
    except Exception as e:
        print(f"Error in process_date: {e}")
        await callback_query.message.answer("Si è verificato un errore tecnico nel recupero degli orari.")
    finally:
        db.close()
        await callback_query.answer()
