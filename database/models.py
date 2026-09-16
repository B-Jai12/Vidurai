from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id                 = Column(Integer, primary_key=True, index=True)
    username           = Column(String, unique=True, nullable=False)
    password_hash      = Column(String, nullable=False)
    preferred_language = Column(String, default="English")
    wake_time          = Column(String, default="07:00")
    location_lat       = Column(Float, nullable=True)
    location_lng       = Column(Float, nullable=True)
    created_at         = Column(DateTime, default=datetime.utcnow)

class FamilyProfile(Base):
    __tablename__ = "family_profiles"
    id                 = Column(Integer, primary_key=True, index=True)
    owner_user_id      = Column(String, nullable=False, index=True)
    member_name        = Column(String, nullable=False)
    age                = Column(Integer, nullable=True)
    relationship       = Column(String, nullable=True)
    preferred_language = Column(String, default="English")

class Prescription(Base):
    __tablename__ = "prescriptions"
    id                 = Column(Integer, primary_key=True, index=True)
    user_id            = Column(String, nullable=False, index=True)
    family_profile_id  = Column(Integer, ForeignKey("family_profiles.id"), nullable=True)
    upload_date        = Column(DateTime, default=datetime.utcnow)
    raw_ocr_text       = Column(Text, nullable=True)
    parsed_json        = Column(Text, nullable=True)
    authenticity_score = Column(Float, default=0.0)
    image_path         = Column(String, nullable=True)
    is_active          = Column(Boolean, default=True)

class Medicine(Base):
    __tablename__ = "medicines"
    id                   = Column(Integer, primary_key=True, index=True)
    prescription_id      = Column(Integer, ForeignKey("prescriptions.id"), nullable=False)
    name                 = Column(String, nullable=False)
    dosage               = Column(String, nullable=True)
    frequency            = Column(String, nullable=True)
    timing               = Column(String, nullable=True)
    duration_days        = Column(Integer, nullable=True)
    quantity_given       = Column(Integer, nullable=True)
    start_date           = Column(DateTime, default=datetime.utcnow)
    end_date             = Column(DateTime, nullable=True)
    refill_reminder_sent = Column(Boolean, default=False)

class MedicineLog(Base):
    __tablename__ = "medicine_logs"
    id             = Column(Integer, primary_key=True, index=True)
    medicine_id    = Column(Integer, ForeignKey("medicines.id"), nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    taken_at       = Column(DateTime, nullable=True)
    status         = Column(String, default="pending")

class ChatHistory(Base):
    __tablename__ = "chat_history"
    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(String, nullable=False, index=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"), nullable=True)
    message         = Column(Text, nullable=False)
    response        = Column(Text, nullable=False)
    language        = Column(String, default="English")
    timestamp       = Column(DateTime, default=datetime.utcnow)

class AlarmSchedule(Base):
    __tablename__ = "alarm_schedules"
    id          = Column(Integer, primary_key=True, index=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=False)
    user_id     = Column(String, nullable=False, index=True)
    alarm_time  = Column(String, nullable=False)
    label       = Column(String, nullable=True)
    is_active   = Column(Boolean, default=True)