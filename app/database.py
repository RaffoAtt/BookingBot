from sqlalchemy import create_engine, Column, String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/dbname")

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Business(Base):
    __tablename__ = "businesses"
    id = Column(String, primary_key=True) # UUID o nome univoco
    name = Column(String)
    telegram_token = Column(String, unique=True)
    google_creds = Column(JSON) # Salveremo qui il token OAuth2 (refresh_token)
    opening_hours = Column(JSON) # Es: {"0": ["09:00", "18:00"], "1": [...]}

class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True)
    business_id = Column(String, ForeignKey("businesses.id"))
    name = Column(String)
    duration = Column(Integer) # In minuti
    price = Column(Integer)

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"))
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id"))
    customer_name = Column(String)
    booking_date = Column(Date)       # Deve essere Date
    start_time = Column(Time)         # Deve essere Time
    end_time = Column(Time)           # Deve essere Time
    status = Column(String, default="confirmed")
    
# Funzione per creare le tabelle (da lanciare una volta)
def init_db():
    Base.metadata.create_all(bind=engine)
