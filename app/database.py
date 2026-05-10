from sqlalchemy import create_engine, Column, String, Integer, DateTime, ForeignKey, Boolean, Numeric, Date, Time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
import os

# --- FIX URL DATABASE ---
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/dbname")
# Railway e Heroku spesso forniscono l'URL che inizia con postgres:// 
# ma SQLAlchemy richiede postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Business(Base):
    __tablename__ = "businesses"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    telegram_token = Column(String, unique=True)
    google_creds = Column(JSONB) 
    opening_hours = Column(JSONB)

class Service(Base):
    __tablename__ = "services"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"))
    name = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)
    price = Column(Numeric)

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"))
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id"))
    customer_name = Column(String, nullable=False)
    booking_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    status = Column(String, default="confirmed")
    customer_phone = Column(String, nullable=True)

# --- FUNZIONE PER INIZIALIZZARE IL DB ---
def init_db():
    Base.metadata.create_all(bind=engine)
