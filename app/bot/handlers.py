from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .keyboards import get_days_kb
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
    
    # Usiamo la nuova tastiera dinamica
    await callback_query.message.answer(
        "📅 Per quando vuoi prenotare? (Prossimi 7 giorni):", 
        reply_markup=get_days_kb() 
    )
    await BookingStates.choosing_date.set()
    await callback_query.answer()

# --- DATE SELECTION ---
async def process_date(callback_query: types.CallbackQuery, state: FSMContext):
    # callback_query.data sarà tipo "date_2026-05-10"
    date_str = callback_query.data.split("_")[1]
    selected_date = datetime.strptime(date_str, "%Y-%m-%d")
    
    await state.update_data(date=date_str)
    
    db = SessionLocal()
    try:
        user_data = await state.get_data()
        service = db.query(Service).filter(Service.id == user_data['service_id']).first()
        biz = db.query(Business).first()
        
        # Recupero impegni Google
        busy = google_cal.fetch_busy_slots(biz.google_creds, selected_date) if biz.google_creds else []
        
        # Orari di apertura
        day_name = selected_date.strftime("%a").lower()[:3]
        if isinstance(biz.opening_hours, dict):
            day_schedule = biz.opening_hours.get(day_name)
        else:
            day_schedule = biz.opening_hours

        if not day_schedule:
            await callback_query.message.answer(f"Spiacenti, siamo chiusi il {selected_date.strftime('%d/%m')}.")
            return

        # Generazione slot con la logica corretta dello scheduler aggiornato
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
        logging.error(f"Errore: {e}")
        await callback_query.message.answer("Errore nel recupero orari.")
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

async def process_name(message: types.Message, state: FSMContext):
    user_name = message.text
    data = await state.get_data()
    db = SessionLocal()
    
    try:
        # 1. Recupero Business e Servizio (Usando UUID come stringhe)
        biz = db.query(Business).first()
        service_id = data['service_id'] # Niente int(), è un UUID
        service = db.query(Service).filter(Service.id == service_id).first()
        
        if not service:
            await message.answer("Errore: Servizio non trovato.")
            return

        # 2. Calcolo tempi (Data, Inizio, Fine)
        # Il tuo schema vuole: booking_date (date), start_time (time), end_time (time)
        selected_date = datetime.strptime(data['date'], "%Y-%m-%d").date()
        start_t = datetime.strptime(data['chosen_time'], "%H:%M").time()
        
        # Calcoliamo la fine in base alla durata del servizio (es. 30 min)
        # Usiamo datetime per fare i calcoli e poi estraiamo .time()
        dummy_dt = datetime.combine(selected_date, start_t)
        end_dt = dummy_dt + timedelta(minutes=service.duration)
        end_t = end_dt.time()

        # 3. Creazione Booking secondo il tuo schema SQL
        new_booking = Booking(
            business_id=biz.id,
            service_id=service.id,
            customer_name=user_name,
            booking_date=selected_date,  # Colonna: booking_date
            start_time=start_t,          # Colonna: start_time
            end_time=end_t,              # Colonna: end_time (Obbligatoria!)
            status='confirmed'
        )
        
        db.add(new_booking)
        db.commit()
        db.refresh(new_booking)

        # 4. Google Calendar (opzionale)
        sync_status = ""
        if biz.google_creds:
            try:
                # Passiamo l'oggetto booking completo
                google_cal.create_event(biz.google_creds, new_booking, service.name)
                sync_status = "\n✅ Sincronizzato con Google Calendar."
            except Exception as ge:
                print(f"Google Error: {ge}")
                sync_status = "\n⚠️ Errore sincronizzazione calendario."

        await message.answer(
            f"✅ **Prenotazione completata!**\n\n"
            f"👤 Cliente: {user_name}\n"
            f"🔹 Servizio: {service.name} ({service.duration} min)\n"
            f"📅 Data: {data['date']}\n"
            f"🕒 Orario: {data['chosen_time']} - {end_t.strftime('%H:%M')}"
            f"{sync_status}"
        )
        await state.finish()

    except Exception as e:
        print(f"ERRORE CRITICO: {e}")
        import traceback
        traceback.print_exc()
        await message.answer("Si è verificato un errore nel salvataggio. Riprova.")
    finally:
        db.close()
