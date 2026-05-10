import os
import uvicorn
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from app.bot.handlers import cmd_start, process_service, process_date, BookingStates

app = FastAPI()

TOKEN = os.getenv("MASTER_BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL")

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

dp.register_message_handler(cmd_start, commands=['start'], state="*")
dp.register_callback_query_handler(process_service, lambda c: c.data and c.data.startswith('srv_'), state=BookingStates.choosing_service)
dp.register_callback_query_handler(process_date, lambda c: c.data and c.data.startswith('date_'), state=BookingStates.choosing_date)

@app.on_event("startup")
async def on_startup():
    if BASE_URL:
        webhook_url = f"{BASE_URL.strip().rstrip('/')}/webhook"
        await bot.set_webhook(webhook_url)
        print(f"Webhook set to: {webhook_url}")

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = types.Update.to_object(data)
    Bot.set_current(bot)
    Dispatcher.set_current(dp)
    await dp.process_update(update)
    return {"status": "ok"}

@app.get("/")
def index():
    return {"status": "online"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)        
    print("✅ Webhook impostato correttamente")
    except Exception as e:
        print(f"❌ Errore durante set_webhook: {e}")

@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        update = types.Update.to_object(data)
        Bot.set_current(bot)
        Dispatcher.set_current(dp)
        await dp.process_update(update)
        return {"status": "ok"}
    except Exception as e:
        print(f"❌ Errore processing update: {e}")
        return {"status": "error", "detail": str(e)}

@app.get("/")
def health_check():
    return {"status": "running"}

# 4. Avvio Server
if __name__ == "__main__":
    port_env = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port_env)        else:
            print("⚠️ BASE_URL non trovata. Il bot non riceverà messaggi.")
    except Exception as e:
        print(f"❌ Errore durante il set_webhook: {e}")

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Punto di ingresso per i messaggi di Telegram"""
    try:
        data = await request.json()
        update = types.Update.to_object(data)
        Bot.set_current(bot)
        Dispatcher.set_current(dp)
        await dp.process_update(update)
        return {"status": "ok"}
    except Exception as e:
        print(f"❌ Errore nel processare l'update: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/")
def home():
    return {"status": "online", "bot": "BookingBot SaaS"}

if __name__ == "__main__":
    # Railway assegna la porta dinamicamente
    port_env = os.environ.get("PORT", "8000")
    print(f"Server in ascolto sulla porta: {port_env}")
    uvicorn.run(app, host="0.0.0.0", port=int(port_env))            
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
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
