from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from datetime import datetime, timedelta
import logging

from app.database import SessionLocal, Service, Business, Booking
from app.services import google_cal, scheduler
from .keyboards import get_services_kb, get_slots_kb, get_days_kb

class BookingStates(StatesGroup):
    choosing_service = State()
    choosing_date = State()
    choosing_time = State()
    entering_name = State()
    entering_phone = State() # Stato per il numero di telefono

# --- START & SERVICE SELECTION ---
async def cmd_start(message: types.Message):
    db = SessionLocal()
    try:
        services = db.query(Service).all()
        await message.answer("Benvenuto! Scegli un servizio per prenotare:", reply_markup=get_services_kb(services))
        await BookingStates.choosing_service.set()
    finally: 
        db.close()

async def process_service(callback_query: types.CallbackQuery, state: FSMContext):
    service_id = callback_query.data.split("_")[1]
    await state.update_data(service_id=service_id)
    
    await callback_query.message.answer(
        "📅 Per quando vuoi prenotare? (Prossimi 7 giorni):", 
        reply_markup=get_days_kb() 
    )
    await BookingStates.choosing_date.set()
    await callback_query.answer()

# --- DATE SELECTION ---
async def process_date(callback_query: types.CallbackQuery, state: FSMContext):
    date_str = callback_query.data.split("_")[1]
    selected_date = datetime.strptime(date_str, "%Y-%m-%d")
    
    await state.update_data(date=date_str)
    
    db = SessionLocal()
    try:
        user_data = await state.get_data()
        service = db.query(Service).filter(Service.id == user_data['service_id']).first()
        biz = db.query(Business).first()
        
        busy = google_cal.fetch_busy_slots(biz.google_creds, selected_date) if biz.google_creds else []
        
        day_name = selected_date.strftime("%a").lower()[:3]
        if isinstance(biz.opening_hours, dict):
            day_schedule = biz.opening_hours.get(day_name)
        else:
            day_schedule = biz.opening_hours

        if not day_schedule:
            await callback_query.message.answer(f"Spiacenti, siamo chiusi il {selected_date.strftime('%d/%m')}.")
            return

        slots = scheduler.get_available_slots(
            day_schedule, 
            busy, 
            service.duration, 
            selected_date.date()
        )
        
        if not slots:
            await callback_query.message.answer("Nessun orario disponibile per questa data.")
            return

        await callback_query.message.answer(
            f"⏰ Orari per {selected_date.strftime('%d %B')}:", 
            reply_markup=get_slots_kb(slots, date_str)
        )
        await BookingStates.choosing_time.set()
        
    except Exception as e:
        logging.error(f"Errore nel recupero slot: {e}")
        await callback_query.message.answer("Errore nel recupero orari.")
    finally:
        db.close()
        await callback_query.answer()

# --- TIME SELECTION ---
async def process_time(callback_query: types.CallbackQuery, state: FSMContext):
    selected_time = callback_query.data.split("_")[2]
    await state.update_data(chosen_time=selected_time)
    
    await callback_query.message.answer("Perfetto! Ora inserisci il tuo **Nome e Cognome**:")
    await BookingStates.entering_name.set()
    await callback_query.answer()

# --- NAME SELECTION ---
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(customer_name=message.text)
    
    # Tastiera speciale per richiedere il contatto
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("📱 Condividi il mio numero", request_contact=True))
    
    await message.answer(
        "Grazie! Infine, clicca sul pulsante qui sotto per inviarci il tuo **numero di telefono**:",
        reply_markup=kb
    )
    await BookingStates.entering_phone.set()

# --- PHONE SELECTION & FINAL SAVING ---
async def process_phone(message: types.Message, state: FSMContext):
    # Gestiamo sia il pulsante 'condividi contatto' che il testo manuale
    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text

    data = await state.get_data()
    db = SessionLocal()
    
    try:
        biz = db.query(Business).first()
        service = db.query(Service).filter(Service.id == data['service_id']).first()
        
        if not service:
            await message.answer("Errore: Servizio non trovato.")
            return

        # Calcolo orari per il DB
        selected_date = datetime.strptime(data['date'], "%Y-%m-%d").date()
        start_t = datetime.strptime(data['chosen_time'], "%H:%M").time()
        dummy_dt = datetime.combine(selected_date, start_t)
        end_t = (dummy_dt + timedelta(minutes=service.duration)).time()

        # Creazione record nel Database
        new_booking = Booking(
            business_id=biz.id,
            service_id=service.id,
            customer_name=data['customer_name'],
            customer_phone=phone,
            booking_date=selected_date,
            start_time=start_t,
            end_time=end_t,
            status='confirmed'
        )
        
        db.add(new_booking)
        db.commit()
        db.refresh(new_booking)

        # Google Calendar
        sync_status = ""
        if biz.google_creds:
            try:
                google_cal.create_event(biz.google_creds, new_booking, service.name)
                sync_status = "\n✅ Sincronizzato con Google Calendar."
            except Exception as ge:
                logging.error(f"Google Error: {ge}")
                sync_status = "\n⚠️ Nota: Calendario non aggiornato."

        await message.answer(
            f"✅ **Prenotazione confermata!**\n\n"
            f"👤 Cliente: {data['customer_name']}\n"
            f"📞 Telefono: {phone}\n"
            f"🔹 Servizio: {service.name}\n"
            f"📅 Data: {data['date']}\n"
            f"🕒 Orario: {data['chosen_time']} - {end_t.strftime('%H:%M')}"
            f"{sync_status}",
            reply_markup=ReplyKeyboardRemove() # Rimuove il pulsante del contatto
        )
        await state.finish()

    except Exception as e:
        logging.error(f"ERRORE CRITICO: {e}")
        await message.answer("Si è verificato un errore nel salvataggio. Riprova con /start.")
    finally:
        db.close()
