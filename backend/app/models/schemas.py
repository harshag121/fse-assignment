from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Optional, List
from app.models.database import AppointmentStatus


# ── Auth ────────────────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    role: str  # "patient" | "doctor"


# ── Doctor ───────────────────────────────────────────────────────────────────

class DoctorCreate(BaseModel):
    name: str
    specialization: str
    email: EmailStr
    phone: Optional[str] = None
    password: str
    slack_user_id: Optional[str] = None
    whatsapp_number: Optional[str] = None


class DoctorOut(BaseModel):
    id: int
    name: str
    specialization: str
    email: str
    phone: Optional[str]
    slack_user_id: Optional[str]
    whatsapp_number: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Patient ──────────────────────────────────────────────────────────────────

class PatientCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    password: str


class PatientOut(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Availability ─────────────────────────────────────────────────────────────

class AvailabilityCreate(BaseModel):
    doctor_id: int
    day_of_week: int  # 0-6
    start_time: str   # "HH:MM"
    end_time: str
    slot_duration_minutes: int = 30
    is_available: bool = True

    @field_validator("day_of_week")
    @classmethod
    def check_day(cls, v: int) -> int:
        if not 0 <= v <= 6:
            raise ValueError("day_of_week must be 0-6")
        return v


class AvailabilityOut(AvailabilityCreate):
    id: int
    model_config = {"from_attributes": True}


# ── Appointment ───────────────────────────────────────────────────────────────

class AppointmentCreate(BaseModel):
    doctor_id: int
    patient_id: int
    start_time: datetime
    end_time: datetime
    symptoms: Optional[str] = None
    notes: Optional[str] = None


class AppointmentOut(BaseModel):
    id: int
    doctor_id: int
    patient_id: int
    start_time: datetime
    end_time: datetime
    status: AppointmentStatus
    symptoms: Optional[str]
    notes: Optional[str]
    google_calendar_event_id: Optional[str]
    created_at: datetime
    doctor: Optional[DoctorOut] = None
    patient: Optional[PatientOut] = None

    model_config = {"from_attributes": True}


# ── Conversation / Chat ───────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    session_id: str
    message: str
    role: str = "patient"  # "patient" | "doctor"
    user_id: Optional[int] = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    tool_calls_made: List[str] = []
    appointments_affected: List[int] = []


# ── MCP Tool Responses (internal) ────────────────────────────────────────────

class TimeSlot(BaseModel):
    start: str
    end: str


class AvailabilityResponse(BaseModel):
    doctor_id: int
    doctor_name: str
    date: str
    available_slots: List[TimeSlot]


class BookingResponse(BaseModel):
    appointment_id: int
    doctor_name: str
    patient_name: str
    start_time: str
    end_time: str
    status: str
    google_calendar_link: Optional[str] = None


class StatsResponse(BaseModel):
    doctor_id: int
    date_range: str
    total_appointments: int
    completed: int
    cancelled: int
    pending: int
    symptom_breakdown: dict
    busiest_day: Optional[str] = None


# ── Doctor Report Request ─────────────────────────────────────────────────────

class ReportRequest(BaseModel):
    doctor_id: int
    query: str
    session_id: Optional[str] = None
