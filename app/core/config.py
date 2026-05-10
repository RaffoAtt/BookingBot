import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DATABASE_URL = os.getenv("DATABASE_URL")
    # Credenziali per l'app Google (ottenute dalla Google Console)
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    # URL del tuo server (es. https://tuo-dominio.railway.app)
    BASE_URL = os.getenv("BASE_URL")
