from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import logging

from app.database import SessionLocal, Service, Business, Booking
from app.services import google_cal, scheduler
from .keyboards import get_services_kb, get_slots_kb

class BookingStates(StatesGroup):
    choosing_service = State()
    choosing_date = State()
    choosing_time = State()
    entering_name = State()

# --- START & SERVICE SELECTION (Identici a prima) ---
async def cmd_start(message: types.Message):
    db = SessionLocal()
    try:
        services = db.query(Service).all()
        await message.answer("Scegli un servizio:", reply_markup=get_services_kb(services))
        await BookingStates.choosing_service.set()
    finally: db.close()

async def process_service(callback_query: types.CallbackQuery, state: FSMContext):
    service_id = callback_query.data.split("_")[1]
    await state.update_data(service_id=service_id)
    kb = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("Oggi", callback_data="date_today"),
        InlineKeyboardButton("Domani", callback_data="date_tomorrow")
    )
    await callback_query.message.answer("Scegli il giorno:", reply_markup=kb)
    await BookingStates.choosing_date.set()
    await callback_query.answer()

# --- DATE SELECTION ---
async def process_date(callback_query: types.CallbackQuery, state: FSMContext):
    selected_date = datetime.now() if "today" in callback_query.data else datetime.now() + timedelta(days=1)
    date_str = selected_date.strftime("%Y-%m-%d")
    await state.update_data(date=date_str)
    
    db = SessionLocal()
    try:
        biz = db.query(Business).first()
        busy = google_cal.fetch_busy_slots(biz.google_creds, selected_date) if biz.google_creds else []
        
        # Logica per estrarre orario da lista o dizionario
        day_name = selected_date.strftime("%a").lower()[:3]
        day_schedule = biz.opening_hours.get(day_name) if isinstance(biz.opening_hours, dict) else biz.opening_hours

        if not day_schedule:
            await callback_query.message.answer("Chiuso in questa data.")
            return

        slots = scheduler.get_available_slots(day_schedule, busy, 30)
        await callback_query.message.answer(f"Orari per il {date_str}:", reply_markup=get_slots_kb(slots, date_str))
        await BookingStates.choosing_time.set()
    finally:
        db.close()
        await callback_query.answer()

# --- TIME SELECTION ---
async def process_time(callback_query: types.CallbackQuery, state: FSMContext):
    selected_time = callback_query.data.split("_")[2]
    await state.update_data(chosen_time=selected_time)
    await callback_query.message.answer(f"Selezionato: {selected_time}. Inserisci il tuo Nome:")
    await BookingStates.entering_name.set()
    await callback_query.answer()

# --- LOGICA REALE: SALVATAGGIO DB & GOOGLE CALENDAR ---
async def process_name(message: types.Message, state: FSMContext):
    user_name = message.text
    data = await state.get_data()
    db = SessionLocal()
    
    try:
        # 1. Recupero Dati Business e Servizio
        biz = db.query(Business).first()
        service = db.query(Service).filter(Service.id == int(data['service_id'])).first()
        
        # 2. Creazione Oggetto Booking (DB Locale)
        start_dt = datetime.strptime(f"{data['date']} {data['chosen_time']}", "%Y-%m-%d %H:%M")
        new_booking = Booking(
            business_id=biz.id,
            service_id=service.id,
            customer_name=user_name,
            start_time=start_dt
        )
        
        db.add(new_booking)
        db.commit() # Salvataggio su Postgres
        db.refresh(new_booking)

        # 3. Sincronizzazione Google Calendar
        if biz.google_creds:
            try:
                google_cal.create_event(biz.google_creds, new_booking, service.name)
                sync_status = "✅ Sincronizzato con Google Calendar."
            except Exception as e:
                logging.error(f"Errore Google: {e}")
                sync_status = "⚠️ Salvato localmente, errore sincronizzazione Google."
        else:
            sync_status = ""

        # 4. Risposta Finale
        await message.answer(
            f"Prenotazione confermata per **{user_name}**!\n"
            f"🔹 {service.name}\n"
            f"📅 {data['date']} ore {data['chosen_time']}\n\n"
            f"{sync_status}"
        )
        await state.finish()

    except Exception as e:
        logging.error(f"Errore Finale: {e}")
        await message.answer("Errore durante la conferma. Riprova.")
    finally:
        db.close()
