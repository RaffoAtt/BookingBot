import uvicorn
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from app.core.config import Config
from app.bot.handlers import cmd_start, process_service, process_date, BookingStates
from aiogram.contrib.fsm_storage.memory import MemoryStorage

app = FastAPI()
bot = Bot(token="8794293727:AAHhEzMQioo1bpQqIuVUbBs1sX8bG8osWko")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Registrazione Handlers
dp.register_message_handler(cmd_start, commands=['start'], state="*")
dp.register_callback_query_handler(process_service, lambda c: c.data.startswith('srv_'), state=BookingStates.choosing_service)
dp.register_callback_query_handler(process_date, lambda c: c.data.startswith('date_'), state=BookingStates.choosing_date)

@app.on_event("startup")
async def on_startup():
    # Comunica a Telegram dove inviare i messaggi
    webhook_url = f"{Config.BASE_URL}/webhook"
    await bot.set_webhook(webhook_url)

@app.post("/webhook")
async def telegram_webhook(request: Request):
    update = await request.json()
    telegram_update = types.Update.to_object(update)
    Dispatcher.set_current(dp)
    Bot.set_current(bot)
    await dp.process_update(telegram_update)
    return {"status": "ok"}

@app.get("/")
def index():
    return {"message": "Booking Bot SaaS is running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
