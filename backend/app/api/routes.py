"""All FastAPI routes."""
import uuid
from datetime import timedelta

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user, get_current_user_optional
from app.core.security import verify_password, get_password_hash, create_access_token
from app.models.database import Doctor, Patient, Appointment, Availability, AppointmentStatus
from app.models.schemas import (
    Token,
    LoginRequest,
    DoctorCreate,
    DoctorOut,
    PatientCreate,
    PatientOut,
    AvailabilityCreate,
    AvailabilityOut,
    AppointmentCreate,
    AppointmentOut,
    ChatMessage,
    ChatResponse,
    ReportRequest,
)
from app.services.llm_service import LLMService

router = APIRouter()
llm_service = LLMService()


# ── Auth ──────────────────────────────────────────────────────────────────────

@router.post("/auth/token", response_model=Token, tags=["auth"])
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    if payload.role == "doctor":
        result = await db.execute(select(Doctor).where(Doctor.email == payload.email))
        user = result.scalars().first()
    else:
        result = await db.execute(select(Patient).where(Patient.email == payload.email))
        user = result.scalars().first()

    if not user or not verify_password(payload.password, user.password_hash or ""):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id), "role": payload.role, "email": user.email})
    return Token(access_token=token, role=payload.role, user_id=user.id)


# ── Doctors ───────────────────────────────────────────────────────────────────

@router.post("/doctors", response_model=DoctorOut, status_code=201, tags=["doctors"])
async def create_doctor(payload: DoctorCreate, db: AsyncSession = Depends(get_db)):
    doctor = Doctor(
        name=payload.name,
        specialization=payload.specialization,
        email=payload.email,
        phone=payload.phone,
        password_hash=get_password_hash(payload.password),
        slack_user_id=payload.slack_user_id,
        whatsapp_number=payload.whatsapp_number,
    )
    db.add(doctor)
    await db.commit()
    await db.refresh(doctor)
    return doctor


@router.get("/doctors", response_model=list[DoctorOut], tags=["doctors"])
async def list_doctors(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Doctor))
    return result.scalars().all()


@router.get("/doctors/{doctor_id}", response_model=DoctorOut, tags=["doctors"])
async def get_doctor(doctor_id: int, db: AsyncSession = Depends(get_db)):
    doctor = await db.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(404, "Doctor not found")
    return doctor


# ── Patients ──────────────────────────────────────────────────────────────────

@router.post("/patients", response_model=PatientOut, status_code=201, tags=["patients"])
async def create_patient(payload: PatientCreate, db: AsyncSession = Depends(get_db)):
    patient = Patient(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        password_hash=get_password_hash(payload.password),
    )
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    return patient


@router.get("/patients/{patient_id}", response_model=PatientOut, tags=["patients"])
async def get_patient(patient_id: int, db: AsyncSession = Depends(get_db)):
    patient = await db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(404, "Patient not found")
    return patient


# ── Availability ──────────────────────────────────────────────────────────────

@router.post("/availability", response_model=AvailabilityOut, status_code=201, tags=["availability"])
async def set_availability(payload: AvailabilityCreate, db: AsyncSession = Depends(get_db)):
    avail = Availability(**payload.model_dump())
    db.add(avail)
    await db.commit()
    await db.refresh(avail)
    return avail


@router.get("/doctors/{doctor_id}/availability", response_model=list[AvailabilityOut], tags=["availability"])
async def get_doctor_availability(doctor_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Availability).where(Availability.doctor_id == doctor_id)
    )
    return result.scalars().all()


# ── Appointments ──────────────────────────────────────────────────────────────

@router.get("/appointments", response_model=list[AppointmentOut], tags=["appointments"])
async def list_appointments(
    doctor_id: int = None,
    patient_id: int = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Appointment).options(
        selectinload(Appointment.doctor),
        selectinload(Appointment.patient),
    )
    if doctor_id:
        query = query.where(Appointment.doctor_id == doctor_id)
    if patient_id:
        query = query.where(Appointment.patient_id == patient_id)
    result = await db.execute(query.order_by(Appointment.start_time.desc()))
    return result.scalars().all()


@router.get("/appointments/{appointment_id}", response_model=AppointmentOut, tags=["appointments"])
async def get_appointment(appointment_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Appointment)
        .options(selectinload(Appointment.doctor), selectinload(Appointment.patient))
        .where(Appointment.id == appointment_id)
    )
    appt = result.scalars().first()
    if not appt:
        raise HTTPException(404, "Appointment not found")
    return appt


@router.patch("/appointments/{appointment_id}/cancel", response_model=AppointmentOut, tags=["appointments"])
async def cancel_appointment(appointment_id: int, db: AsyncSession = Depends(get_db)):
    appt = await db.get(Appointment, appointment_id)
    if not appt:
        raise HTTPException(404, "Appointment not found")
    appt.status = AppointmentStatus.CANCELLED
    await db.commit()
    await db.refresh(appt)
    return appt


# ── Chat (Agentic AI) ─────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat(
    payload: ChatMessage,
    current_user=Depends(get_current_user_optional),
):
    """Main AI chat endpoint. Orchestrates MCP tool calls via LLM."""
    session_id = payload.session_id or str(uuid.uuid4())
    user_id = payload.user_id or (int(current_user["sub"]) if current_user else None)

    result = await llm_service.chat(
        session_id=session_id,
        user_message=payload.message,
        role=payload.role,
        user_id=user_id,
    )
    return ChatResponse(session_id=session_id, **result)


@router.get("/chat/{session_id}/history", tags=["chat"])
async def get_chat_history(session_id: str, db: AsyncSession = Depends(get_db)):
    from app.models.database import Conversation
    result = await db.execute(
        select(Conversation)
        .where(Conversation.session_id == session_id)
        .order_by(Conversation.timestamp)
    )
    rows = result.scalars().all()
    return [
        {
            "role": r.role,
            "content": r.content,
            "timestamp": r.timestamp.isoformat(),
        }
        for r in rows
    ]


# ── Doctor Report ─────────────────────────────────────────────────────────────

@router.post("/reports/generate", tags=["reports"])
async def generate_report(payload: ReportRequest):
    """Natural-language report query for a doctor."""
    session_id = payload.session_id or str(uuid.uuid4())
    result = await llm_service.chat(
        session_id=session_id,
        user_message=payload.query,
        role="doctor",
        user_id=payload.doctor_id,
    )
    return {"session_id": session_id, **result}
