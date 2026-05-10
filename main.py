import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse  # Import corretto
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# Importa le funzioni dal tuo google_cal.py e il database
from app.services.google_cal import get_auth_url, fetch_token
from app.database import SessionLocal, Business, Booking

# 1. Importa i nuovi handler inclusa la parte del telefono
from app.bot.handlers import (
    cmd_start, 
    process_service, 
    process_date, 
    process_time, 
    process_name, 
    process_phone,    # <--- AGGIUNTO
    BookingStates
)

app = FastAPI()

# Caricamento variabili
TOKEN = os.getenv("MASTER_BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL")

# Inizializzazione
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- REGISTRAZIONE HANDLERS ---

# 1. Start
dp.register_message_handler(cmd_start, commands=['start'], state="*")

# 2. Scelta Servizio -> Passa a Scelta Data
dp.register_callback_query_handler(
    process_service, 
    lambda c: c.data and c.data.startswith('srv_'), 
    state=BookingStates.choosing_service
)

# 3. Scelta Data -> Passa a Scelta Orario
dp.register_callback_query_handler(
    process_date, 
    lambda c: c.data and c.data.startswith('date_'), 
    state=BookingStates.choosing_date
)

# 4. Scelta Orario -> Passa a Inserimento Nome
dp.register_callback_query_handler(
    process_time, 
    lambda c: c.data and c.data.startswith('time_'), 
    state=BookingStates.choosing_time
)

# 5. Inserimento Nome -> Passa a Richiesta Telefono
dp.register_message_handler(
    process_name, 
    state=BookingStates.entering_name
)

# 6. NUOVO: Inserimento Telefono -> Salvataggio Finale e Google Calendar
# Notare content_types=['contact', 'text'] per accettare sia il pulsante che l'invio manuale
dp.register_message_handler(
    process_phone, 
    content_types=['contact', 'text'], 
    state=BookingStates.entering_phone
)

# --- LOGICA WEBHOOK ---

@app.on_event("startup")
async def on_startup():
    if BASE_URL:
        # Assicuriamoci che l'URL sia HTTPS
        url = f"{BASE_URL.strip().rstrip('/')}/webhook".replace("http://", "https://")
        try:
            await bot.set_webhook(url)
            print(f"Webhook OK: {url}")
        except Exception as e:
            print(f"Webhook Error: {e}")

@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        update = types.Update.to_object(data)
        
        Bot.set_current(bot)
        Dispatcher.set_current(dp)
        
        await dp.process_update(update)
    except Exception as e:
        print(f"Update Error: {e}")
    return {"status": "ok"}

@app.get("/auth/google")
async def auth_google():
    """Inizia il processo di login Google"""
    auth_url = get_auth_url()
    return RedirectResponse(auth_url)

@app.get("/auth/callback")
async def auth_callback(code: str):
    """Riceve il codice da Google e salva il Token nel DB"""
    try:
        # 1. Scambia il codice con il Token (JSON)
        token_data = fetch_token(code)
        
        # 2. Salva il Token nel database (nella tabella Business)
        db = SessionLocal()
        biz = db.query(Business).first()
        if biz:
            biz.google_creds = token_data
            db.commit()
            db.close()
            return {"status": "success", "message": "Autenticazione completata! Il bot ora può scrivere sul calendario."}
        else:
            db.close()
            return {"status": "error", "message": "Nessun business trovato nel DB. Configura prima il bot."}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/")
def home():
    return {"status": "online"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
