import os
import uvicorn
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# Importa i tuoi handler
from app.bot.handlers import cmd_start, process_service, process_date, BookingStates

app = FastAPI()

# 1. Inizializzazione corretta del Bot (Oggetto, non stringa)
TOKEN = os.getenv("MASTER_BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL") # Es: https://bookingbot-production-a03f.up.railway.app

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# 2. Registrazione Handlers
dp.register_message_handler(cmd_start, commands=['start'], state="*")
dp.register_callback_query_handler(process_service, lambda c: c.data.startswith('srv_'), state=BookingStates.choosing_service)
dp.register_callback_query_handler(process_date, lambda c: c.data.startswith('date_'), state=BookingStates.choosing_date)

@app.on_event("startup")
async def on_startup():
    # Rimuove eventuali doppioni di protocollo e imposta il webhook
    if BASE_URL:
        webhook_url = f"{BASE_URL.rstrip('/')}/webhook"
        await bot.set_webhook(webhook_url)
        print(f"Webhook impostato su: {webhook_url}")

@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        update_data = await request.json()
        telegram_update = types.Update.to_object(update_data)
        
        # Imposta il contesto per permettere ad aiogram di funzionare con FastAPI
        Bot.set_current(bot)
        Dispatcher.set_current(dp)
        
        await dp.process_update(telegram_update)
        return {"status": "ok"}
    except Exception as e:
        print(f"Errore nel processare l'update: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/")
def index():
    return {"message": "Booking Bot SaaS is running"}

if __name__ == "__main__":
    # Railway assegna la porta automaticamente tramite la variabile PORT
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
