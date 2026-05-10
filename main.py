import os
import uvicorn
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# 1. Importa i nuovi handler e BookingStates
from app.bot.handlers import (
    cmd_start, 
    process_service, 
    process_date, 
    process_time,    # <--- Aggiunto
    process_name,    # <--- Aggiunto
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

# Start
dp.register_message_handler(cmd_start, commands=['start'], state="*")

# Scelta Servizio -> Passa a Scelta Data
dp.register_callback_query_handler(
    process_service, 
    lambda c: c.data and c.data.startswith('srv_'), 
    state=BookingStates.choosing_service
)

# Scelta Data -> Passa a Scelta Orario
dp.register_callback_query_handler(
    process_date, 
    lambda c: c.data and c.data.startswith('date_'), 
    state=BookingStates.choosing_date
)

# 2. NUOVO: Scelta Orario -> Passa a Inserimento Nome
dp.register_callback_query_handler(
    process_time, 
    lambda c: c.data and c.data.startswith('time_'), 
    state=BookingStates.choosing_time
)

# 3. NUOVO: Inserimento Nome -> Conferma Finale e salvataggio
dp.register_message_handler(
    process_name, 
    state=BookingStates.entering_name
)

# --- LOGICA WEBHOOK ---

@app.on_event("startup")
async def on_startup():
    if BASE_URL:
        # Assicuriamoci che l'URL sia HTTPS (richiesto da Telegram)
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
        
        # Imposta il contesto per Aiogram 2.x
        Bot.set_current(bot)
        Dispatcher.set_current(dp)
        
        await dp.process_update(update)
    except Exception as e:
        print(f"Update Error: {e}")
    return {"status": "ok"}

@app.get("/")
def home():
    return {"status": "online"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
