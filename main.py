import os
import uvicorn
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# Importa i tuoi handler e stati
from app.bot.handlers import cmd_start, process_service, process_date, BookingStates

app = FastAPI()

# Configurazione variabili
TOKEN = os.getenv("MASTER_BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL")

# Inizializzazione Bot e Dispatcher
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Registrazione Handlers
dp.register_message_handler(cmd_start, commands=['start'], state="*")
dp.register_callback_query_handler(process_service, lambda c: c.data and c.data.startswith('srv_'), state=BookingStates.choosing_service)
dp.register_callback_query_handler(process_date, lambda c: c.data and c.data.startswith('date_'), state=BookingStates.choosing_date)

@app.on_event("startup")
async def on_startup():
    print("Avvio della procedura di startup...")
    try:
        if BASE_URL:
            clean_url = BASE_URL.strip().rstrip('/')
            webhook_url = f"{clean_url}/webhook"
            print(f"Tentativo di impostare il Webhook su: {webhook_url}")
            await bot.set_webhook(webhook_url)
            print("✅ Webhook impostato con successo!")
        else:
            print("⚠️ BASE_URL non trovato nelle variabili d'ambiente.")
    except Exception as e:
        print(f"❌ Errore durante set_webhook: {e}")

@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        update_data = await request.json()
        telegram_update = types.Update.to_object(update_data)
        
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
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)            await bot.set_webhook(webhook_url)
            print("✅ Webhook impostato con successo!")
        else:
            print("⚠️ ATTENZIONE: BASE_URL non configurato nelle variabili d'ambiente.")
    except Exception as e:
        print(f"❌ ERRORE CRITICO durante set_webhook: {e}")
        # Non rilanciamo l'errore, così il server FastAPI resta vivo (niente 502)

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

@app.get("/")
def index():
    return {"message": "Booking Bot SaaS is running"}

if __name__ == "__main__":
    # Prendi la porta assegnata da Railway
    port = int(os.environ.get("PORT", 8000))
    # Avvia il server
    uvicorn.run(app, host="0.0.0.0", port=port)
