from sqlalchemy import create_engine, Column, String, Integer, DateTime, ForeignKey, JSON,Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB  # <--- AGGIUNGI QUESTA RIGA
import uuid # Serve per generare i default lato Python
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/dbname")

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Business(Base):
    __tablename__ = "businesses"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    telegram_token = Column(String, unique=True)
    google_creds = Column(JSONB) # Assicurati di aver importato JSONB da postgresql
    opening_hours = Column(JSONB)

class Service(Base):
    __tablename__ = "services"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"))
    name = Column(String, nullable=False)
    duration = Column(Integer, nullable=False) # In minuti
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
    
# Funzione per creare le tabelle (da lanciare una volta)
def init_db():
    Base.metadata.create_all(bind=engine)
