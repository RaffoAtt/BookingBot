from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from app.database import SessionLocal, Service, Business
from app.services import google_cal, scheduler
from datetime import datetime

class BookingStates(StatesGroup):
    choosing_service = State()
    choosing_date = State()
    choosing_time = State()
    entering_name = State()

async def cmd_start(message: types.Message):
    # In un sistema multi-tenant, identifichiamo il business dal token del bot usato
    # Qui semplificato: prendiamo il primo business per test
    db = SessionLocal()
    services = db.query(Service).all()
    from .keyboards import get_services_kb
    await message.answer("Benvenuto! Scegli un servizio:", reply_markup=get_services_kb(services))
    await BookingStates.choosing_service.set()

async def process_service(callback_query: types.CallbackQuery, state: FSMContext):
    service_id = callback_query.data.split("_")[1]
    await state.update_data(service_id=service_id)
    
    # Mostriamo date (es. oggi e domani per semplicità)
    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Oggi", callback_data="date_today"),
        InlineKeyboardButton("Domani", callback_data="date_tomorrow")
    )
    await callback_query.message.answer("Per quale giorno vuoi prenotare?", reply_markup=kb)
    await BookingStates.choosing_date.set()

async def process_date(callback_query: types.CallbackQuery, state: FSMContext):
    selected_date = datetime.now() if "today" in callback_query.data else datetime.now() + timedelta(days=1)
    await state.update_data(date=selected_date.strftime("%Y-%m-%d"))
    
    # Recupero dati per calcolo slot
    db = SessionLocal()
    biz = db.query(Business).first() # In produzione: filtra per business_id
    busy = google_cal.fetch_busy_slots(biz.google_creds, selected_date)
    slots = scheduler.get_available_slots(biz.opening_hours["mon"], busy, 30) # 30 min default
    
    from .keyboards import get_slots_kb
    await callback_query.message.answer("Scegli l'orario:", reply_markup=get_slots_kb(slots, selected_date.strftime("%Y-%m-%d")))
    await BookingStates.choosing_time.set()

# ... Altri handler per nome e conferma finale ...
