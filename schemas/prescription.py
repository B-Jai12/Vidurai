"""Pydantic schemas for prescription and medicine endpoints."""
from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime


class ParseTextRequest(BaseModel):
    text: str = Field(..., description="Raw prescription text to parse")
    language: str = Field(default="English", description="Target language for explanations")
    save: bool = Field(default=False, description="Whether to save to DB (requires auth)")


class TranslateRequest(BaseModel):
    medicines: list[dict[str, Any]]
    language: str


class PrescriptionOut(BaseModel):
    id: int
    upload_date: datetime
    authenticity_score: float
    parsed_json: Optional[str]
    raw_ocr_text: Optional[str]

    class Config:
        from_attributes = True


class MedicineOut(BaseModel):
    id: int
    name: str
    dosage: Optional[str]
    frequency: Optional[str]
    timing: Optional[str]
    duration_days: Optional[int]
    quantity_given: Optional[int]
    refill_reminder_sent: bool

    class Config:
        from_attributes = True


class RefillReminderRequest(BaseModel):
    medicine_name: str
    days_left: int
    to_email: str


class SavingsAlertRequest(BaseModel):
    medicines: list[dict[str, Any]]
    to_email: str


class SpeakRequest(BaseModel):
    text: str
    language_code: str = "en"


class SpeakFullRequest(BaseModel):
    medicines: list[dict[str, Any]]
    language_code: str = "en"


class DrugWarningRequest(BaseModel):
    interactions: list[dict[str, Any]]
    language_code: str = "en"


class ChatRequest(BaseModel):
    question: str
    prescription_id: int
    language: str = "English"


class FamilyMemberCreate(BaseModel):
    member_name: str
    age: Optional[int] = None
    relationship: Optional[str] = None
    preferred_language: str = "English"
