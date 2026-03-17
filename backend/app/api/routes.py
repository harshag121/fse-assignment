"""All FastAPI routes."""
import json
import re
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
from app.mcp_server.tools import _query_appointments_stats, _send_doctor_notification

router = APIRouter()
llm_service = LLMService()


def _parse_report_query(query: str) -> tuple[dict, str | None, bool, str | None]:
    lowered = query.lower()
    params: dict[str, str] = {"date_range": "today"}

    exact_date = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", query)
    if exact_date:
        params["date_range"] = "custom"
        params["start_date"] = exact_date.group(1)
        params["end_date"] = exact_date.group(1)
    elif "yesterday" in lowered:
        params["date_range"] = "yesterday"
    elif "tomorrow" in lowered:
        params["date_range"] = "tomorrow"
    elif "last week" in lowered:
        params["date_range"] = "last_week"
    elif "this week" in lowered:
        params["date_range"] = "this_week"

    symptom_filter = None
    for pattern in (
        r"patients?\s+with\s+([a-zA-Z][a-zA-Z\s-]+)",
        r"appointments?\s+with\s+([a-zA-Z][a-zA-Z\s-]+)",
        r"with\s+([a-zA-Z][a-zA-Z\s-]+)",
    ):
        match = re.search(pattern, lowered)
        if not match:
            continue
        candidate = match.group(1).strip(" ?!.,")
        for stop_word in (
            " today",
            " yesterday",
            " tomorrow",
            " this week",
            " last week",
            " on ",
            " send ",
            " notify ",
            " do i have",
            " do we have",
            " are there",
            " visited",
        ):
            if stop_word in candidate:
                candidate = candidate.split(stop_word, 1)[0].strip()
        if candidate:
            candidate = " ".join(candidate.split()[:3])
            symptom_filter = candidate
            params["filter"] = candidate
            break

    should_notify = any(word in lowered for word in ("send", "notify", "slack", "whatsapp"))

    channel = None
    slack_match = re.search(r"(#[-\w]+)", query)
    if slack_match:
        channel = slack_match.group(1)
    else:
        phone_match = re.search(r"(whatsapp:\+\d{7,}|\+\d{7,})", query)
        if phone_match:
            channel = phone_match.group(1)

    return params, symptom_filter, should_notify, channel


def _build_report_summary(stats: dict, symptom_filter: str | None = None) -> str:
    lines = [
        f"Doctor report for {stats['date_range']}:",
        f"- Total appointments: {stats['total_appointments']}",
        f"- Confirmed: {stats['confirmed']}",
        f"- Completed: {stats['completed']}",
        f"- Cancelled: {stats['cancelled']}",
        f"- Pending: {stats['pending']}",
    ]
    if stats.get("busiest_day"):
        lines.append(f"- Busiest day: {stats['busiest_day']}")

    symptom_breakdown = stats.get("symptom_breakdown") or {}
    if symptom_filter:
        lines.append(f"- Patients matching '{symptom_filter}': {stats['total_appointments']}")
    elif symptom_breakdown:
        top_symptoms = ", ".join(
            f"{name} ({count})" for name, count in list(symptom_breakdown.items())[:3]
        )
        lines.append(f"- Top symptoms: {top_symptoms}")

    return "\n".join(lines)


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
    result = await db.execute(
        select(Appointment)
        .options(selectinload(Appointment.doctor), selectinload(Appointment.patient))
        .where(Appointment.id == appointment_id)
    )
    appt = result.scalars().first()
    if not appt:
        raise HTTPException(404, "Appointment not found")
    appt.status = AppointmentStatus.CANCELLED
    await db.commit()
    result = await db.execute(
        select(Appointment)
        .options(selectinload(Appointment.doctor), selectinload(Appointment.patient))
        .where(Appointment.id == appointment_id)
    )
    return result.scalars().first()


# ── Chat (Agentic AI) ─────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat(
    payload: ChatMessage,
    current_user=Depends(get_current_user_optional),
):
    """Main AI chat endpoint. Orchestrates MCP tool calls via LLM."""
    session_id = payload.session_id or str(uuid.uuid4())
    user_id = payload.user_id or (int(current_user["sub"]) if current_user else None)

    # Inject user identity so the LLM can pass the correct ID to tools
    enriched_message = payload.message
    if user_id and payload.role == "patient":
        enriched_message = f"[My patient_id is {user_id}] {enriched_message}"
    elif user_id and payload.role == "doctor":
        enriched_message = f"[My doctor_id is {user_id}] {enriched_message}"

    try:
        result = await llm_service.chat(
            session_id=session_id,
            user_message=enriched_message,
            role=payload.role,
            user_id=user_id,
        )
    except Exception as e:
        err = str(e)
        if "insufficient_quota" in err or "quota" in err.lower():
            detail = "LLM quota exceeded. Please check your Groq API key usage."
        elif "rate_limit" in err.lower():
            detail = "LLM rate limit hit. Please wait a moment and try again."
        elif "invalid_api_key" in err.lower():
            detail = "Invalid API key. Please check your GROQ_API_KEY in .env"
        else:
            detail = f"AI service error: {err}"
        raise HTTPException(status_code=503, detail=detail)

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
    await llm_service._save_message(session_id, payload.doctor_id, "user", payload.query)
    report_args, symptom_filter, should_notify, channel = _parse_report_query(payload.query)
    try:
        stats_result = await _query_appointments_stats(
            doctor_id=payload.doctor_id,
            **report_args,
        )
        stats_payload = json.loads(stats_result[0].text)
        await llm_service._save_message(
            session_id,
            payload.doctor_id,
            "tool",
            stats_result[0].text,
            tool_calls=[{"name": "query_appointments_stats", "args": {"doctor_id": payload.doctor_id, **report_args}}],
        )
        if stats_payload.get("error"):
            raise RuntimeError(stats_payload["error"])

        tools_called = ["query_appointments_stats"]
        reply = _build_report_summary(stats_payload, symptom_filter)

        if should_notify:
            notification_result = await _send_doctor_notification(
                doctor_id=payload.doctor_id,
                message=reply,
                channel=channel,
            )
            notification_payload = json.loads(notification_result[0].text)
            await llm_service._save_message(
                session_id,
                payload.doctor_id,
                "tool",
                notification_result[0].text,
                tool_calls=[{
                    "name": "send_doctor_notification",
                    "args": {
                        "doctor_id": payload.doctor_id,
                        "message": reply,
                        "channel": channel,
                    },
                }],
            )
            if notification_payload.get("error"):
                raise RuntimeError(notification_payload["error"])
            tools_called.append("send_doctor_notification")
            method = notification_payload.get("method", "notification")
            target = notification_payload.get("channel") or channel or "configured channel"
            reply = f"{reply}\n\nReport sent via {method} to {target}."
    except Exception as e:
        err = str(e)
        if "rate_limit" in err.lower():
            detail = "LLM rate limit hit. Please wait a moment and try again."
        else:
            detail = f"AI service error: {err}"
        raise HTTPException(status_code=503, detail=detail)
    await llm_service._save_message(session_id, payload.doctor_id, "assistant", reply)
    return {
        "session_id": session_id,
        "reply": reply,
        "tool_calls_made": tools_called,
        "appointments_affected": [],
    }
