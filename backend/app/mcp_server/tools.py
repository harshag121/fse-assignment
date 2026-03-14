"""MCP Tools - the six core tools exposed to the AI agent."""
import json
from datetime import datetime, date, timedelta
from typing import Any
from mcp.server import Server
from mcp.types import Tool, TextContent
from sqlalchemy import select, and_, func as sqlfunc
from sqlalchemy.orm import selectinload

from app.models.database import (
    AsyncSessionLocal,
    Doctor,
    Patient,
    Appointment,
    Availability,
    AppointmentStatus,
)


def _ok(data: Any) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(data, default=str))]


def _err(msg: str) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps({"error": msg}))]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _generate_slots(
    start_time_str: str,
    end_time_str: str,
    slot_minutes: int,
    booked_starts: set,
    for_date: date,
) -> list[dict]:
    slots = []
    h0, m0 = map(int, start_time_str.split(":"))
    h1, m1 = map(int, end_time_str.split(":"))
    current = datetime.combine(for_date, datetime.min.time().replace(hour=h0, minute=m0))
    end_dt = datetime.combine(for_date, datetime.min.time().replace(hour=h1, minute=m1))
    while current + timedelta(minutes=slot_minutes) <= end_dt:
        slot_end = current + timedelta(minutes=slot_minutes)
        if current not in booked_starts:
            slots.append({"start": current.strftime("%H:%M"), "end": slot_end.strftime("%H:%M")})
        current = slot_end
    return slots


def register_tools(server: Server):

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="check_doctor_availability",
                description="Check available appointment slots for a doctor on a given date.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "doctor_name": {"type": "string", "description": "Full or partial name of the doctor"},
                        "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                    },
                    "required": ["doctor_name", "date"],
                },
            ),
            Tool(
                name="book_appointment",
                description="Book an appointment for a patient with a doctor and create a Google Calendar event.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "doctor_id": {"type": "integer"},
                        "patient_id": {"type": "integer"},
                        "datetime": {"type": "string", "description": "ISO 8601 datetime string"},
                        "symptoms": {"type": "string", "description": "Patient's described symptoms"},
                    },
                    "required": ["doctor_id", "patient_id", "datetime"],
                },
            ),
            Tool(
                name="send_email_confirmation",
                description="Send an appointment confirmation email to the patient.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "to_email": {"type": "string"},
                        "patient_name": {"type": "string"},
                        "doctor_name": {"type": "string"},
                        "appointment_datetime": {"type": "string", "description": "ISO datetime, e.g. 2026-03-16T10:00:00"},
                    },
                    "required": ["to_email", "patient_name", "doctor_name", "appointment_datetime"],
                },
            ),
            Tool(
                name="query_appointments_stats",
                description="Query appointment statistics for a doctor's report.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "doctor_id": {"type": "integer"},
                        "date_range": {
                            "type": "string",
                            "enum": ["yesterday", "today", "tomorrow", "this_week", "last_week", "custom"],
                            "description": "Predefined range or 'custom' when start_date/end_date are provided",
                        },
                        "start_date": {"type": "string", "description": "YYYY-MM-DD (for custom range)"},
                        "end_date": {"type": "string", "description": "YYYY-MM-DD (for custom range)"},
                        "filter": {"type": "string", "description": "Optional symptom keyword filter"},
                    },
                    "required": ["doctor_id", "date_range"],
                },
            ),
            Tool(
                name="send_doctor_notification",
                description="Send a summary report to a doctor via Slack or WhatsApp.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "doctor_id": {"type": "integer"},
                        "message": {"type": "string"},
                        "channel": {
                            "type": "string",
                            "description": "Slack channel (e.g. #doctor-reports) or phone number for WhatsApp",
                        },
                    },
                    "required": ["doctor_id", "message"],
                },
            ),
            Tool(
                name="auto_reschedule",
                description="Suggest alternative appointment slots when the preferred time is unavailable.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "doctor_id": {"type": "integer"},
                        "preferred_date": {"type": "string", "description": "YYYY-MM-DD"},
                        "symptoms": {"type": "string"},
                    },
                    "required": ["doctor_id", "preferred_date"],
                },
            ),
        ]

    # ── Tool Handlers ──────────────────────────────────────────────────────────

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        if name == "check_doctor_availability":
            return await _check_doctor_availability(**arguments)
        if name == "book_appointment":
            return await _book_appointment(**arguments)
        if name == "send_email_confirmation":
            return await _send_email_confirmation(**arguments)
        if name == "query_appointments_stats":
            return await _query_appointments_stats(**arguments)
        if name == "send_doctor_notification":
            return await _send_doctor_notification(**arguments)
        if name == "auto_reschedule":
            return await _auto_reschedule(**arguments)
        return _err(f"Unknown tool: {name}")


# ── Individual Tool Implementations ───────────────────────────────────────────

async def _check_doctor_availability(doctor_name: str, date: str):
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        return _err("Invalid date format. Use YYYY-MM-DD.")

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Doctor).where(Doctor.name.ilike(f"%{doctor_name}%"))
        )
        doctor = result.scalars().first()
        if not doctor:
            return _err(f"Doctor '{doctor_name}' not found.")

        day_of_week = target_date.weekday()  # 0=Mon
        avail_result = await db.execute(
            select(Availability).where(
                and_(
                    Availability.doctor_id == doctor.id,
                    Availability.day_of_week == day_of_week,
                    Availability.is_available == True,
                )
            )
        )
        avail_rows = avail_result.scalars().all()
        if not avail_rows:
            return _ok({
                "doctor_id": doctor.id,
                "doctor_name": doctor.name,
                "date": str(target_date),
                "available_slots": [],
                "message": f"Dr. {doctor.name} is not available on {target_date.strftime('%A, %d %b %Y')}.",
            })

        # Get existing bookings
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())
        booked_result = await db.execute(
            select(Appointment.start_time).where(
                and_(
                    Appointment.doctor_id == doctor.id,
                    Appointment.start_time >= start_of_day,
                    Appointment.start_time <= end_of_day,
                    Appointment.status != AppointmentStatus.CANCELLED,
                )
            )
        )
        booked_starts = {row[0].replace(second=0, microsecond=0) for row in booked_result.all()}

        all_slots = []
        for row in avail_rows:
            slots = _generate_slots(
                row.start_time,
                row.end_time,
                row.slot_duration_minutes,
                booked_starts,
                target_date,
            )
            all_slots.extend(slots)

        return _ok({
            "doctor_id": doctor.id,
            "doctor_name": doctor.name,
            "specialization": doctor.specialization,
            "date": str(target_date),
            "available_slots": all_slots,
        })


async def _book_appointment(
    doctor_id: int,
    patient_id: int,
    datetime: str,
    symptoms: str = "",
):
    try:
        start_dt = datetime.fromisoformat(datetime) if hasattr(datetime, "fromisoformat") else __import__("datetime").datetime.fromisoformat(datetime)
    except Exception:
        return _err("Invalid datetime format. Use ISO 8601.")

    # Import at call time to avoid circular imports
    from app.services.calendar_service import CalendarService

    async with AsyncSessionLocal() as db:
        doctor = await db.get(Doctor, doctor_id)
        patient = await db.get(Patient, patient_id)
        if not doctor:
            return _err(f"Doctor ID {doctor_id} not found.")
        if not patient:
            return _err(f"Patient ID {patient_id} not found.")

        # Check conflicts
        end_dt = start_dt + timedelta(minutes=30)
        conflict = await db.execute(
            select(Appointment).where(
                and_(
                    Appointment.doctor_id == doctor_id,
                    Appointment.start_time == start_dt,
                    Appointment.status != AppointmentStatus.CANCELLED,
                )
            )
        )
        if conflict.scalars().first():
            return _err(f"Slot {start_dt.strftime('%H:%M')} is already booked. Try auto_reschedule.")

        # Create Google Calendar event
        calendar_event_id = None
        calendar_link = None
        try:
            cal_service = CalendarService()
            event = await cal_service.create_event(
                title=f"Appointment: {patient.name} with Dr. {doctor.name}",
                start=start_dt,
                end=end_dt,
                description=f"Symptoms: {symptoms}" if symptoms else "",
                attendee_emails=[doctor.email, patient.email],
            )
            calendar_event_id = event.get("id")
            calendar_link = event.get("htmlLink")
        except Exception as exc:
            calendar_event_id = None
            calendar_link = None

        appointment = Appointment(
            doctor_id=doctor_id,
            patient_id=patient_id,
            start_time=start_dt,
            end_time=end_dt,
            symptoms=symptoms,
            status=AppointmentStatus.CONFIRMED,
            google_calendar_event_id=calendar_event_id,
        )
        db.add(appointment)
        await db.commit()
        await db.refresh(appointment)

        return _ok({
            "appointment_id": appointment.id,
            "doctor_name": doctor.name,
            "patient_name": patient.name,
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat(),
            "status": appointment.status.value,
            "google_calendar_link": calendar_link,
        })


async def _send_email_confirmation(
    to_email: str,
    patient_name: str,
    doctor_name: str,
    appointment_datetime: str,
):
    from app.services.email_service import EmailService
    appointment_details = {
        "doctor_name": doctor_name,
        "appointment_datetime": appointment_datetime,
    }
    try:
        svc = EmailService()
        result = await svc.send_appointment_confirmation(
            to_email=to_email,
            patient_name=patient_name,
            details=appointment_details,
        )
        return _ok({"status": "sent", "to": to_email, "message_id": result})
    except Exception as exc:
        return _err(f"Failed to send email: {exc}")


async def _query_appointments_stats(
    doctor_id: int,
    date_range: str,
    start_date: str = None,
    end_date: str = None,
    filter: str = None,
):
    today = date.today()
    if date_range == "yesterday":
        start = end = today - timedelta(days=1)
    elif date_range == "today":
        start = end = today
    elif date_range == "tomorrow":
        start = end = today + timedelta(days=1)
    elif date_range == "this_week":
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
    elif date_range == "last_week":
        start = today - timedelta(days=today.weekday() + 7)
        end = start + timedelta(days=6)
    elif date_range == "custom" and start_date and end_date:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    else:
        start = end = today

    start_dt = datetime.combine(start, datetime.min.time())
    end_dt = datetime.combine(end, datetime.max.time())

    async with AsyncSessionLocal() as db:
        base_query = select(Appointment).where(
            and_(
                Appointment.doctor_id == doctor_id,
                Appointment.start_time >= start_dt,
                Appointment.start_time <= end_dt,
            )
        )
        if filter:
            base_query = base_query.where(Appointment.symptoms.ilike(f"%{filter}%"))

        result = await db.execute(base_query)
        appts = result.scalars().all()

        symptom_counts: dict = {}
        for a in appts:
            if a.symptoms:
                for word in a.symptoms.lower().split():
                    symptom_counts[word] = symptom_counts.get(word, 0) + 1

        status_counts = {s.value: 0 for s in AppointmentStatus}
        for a in appts:
            status_counts[a.status.value] += 1

        # busiest day
        day_counts: dict = {}
        for a in appts:
            d = a.start_time.date().isoformat()
            day_counts[d] = day_counts.get(d, 0) + 1
        busiest_day = max(day_counts, key=day_counts.get) if day_counts else None

        return _ok({
            "doctor_id": doctor_id,
            "date_range": f"{start} to {end}",
            "total_appointments": len(appts),
            "completed": status_counts.get("completed", 0),
            "confirmed": status_counts.get("confirmed", 0),
            "cancelled": status_counts.get("cancelled", 0),
            "pending": status_counts.get("pending", 0),
            "symptom_breakdown": dict(sorted(symptom_counts.items(), key=lambda x: -x[1])[:10]),
            "busiest_day": busiest_day,
        })


async def _send_doctor_notification(
    doctor_id: int,
    message: str,
    channel: str = None,
):
    from app.services.notification_service import NotificationService

    async with AsyncSessionLocal() as db:
        doctor = await db.get(Doctor, doctor_id)
        if not doctor:
            return _err(f"Doctor ID {doctor_id} not found.")

    svc = NotificationService()
    try:
        result = await svc.send(
            doctor=doctor,
            message=message,
            channel=channel,
        )
        return _ok({"status": "sent", "channel": result.get("channel"), "method": result.get("method")})
    except Exception as exc:
        return _err(f"Notification failed: {exc}")


async def _auto_reschedule(
    doctor_id: int,
    preferred_date: str,
    symptoms: str = "",
):
    try:
        pref_date = datetime.strptime(preferred_date, "%Y-%m-%d").date()
    except ValueError:
        return _err("Invalid date format. Use YYYY-MM-DD.")

    suggestions = []
    # Check the preferred date and the 3 following days
    for delta in range(0, 4):
        check_date = pref_date + timedelta(days=delta)
        result = await _check_doctor_availability(
            doctor_name=str(doctor_id),  # will refetch by id
            date=str(check_date),
        )
        # parse result
        content = json.loads(result[0].text)
        if isinstance(content, dict) and content.get("available_slots"):
            slots = content["available_slots"][:3]  # top 3 per day
            for slot in slots:
                suggestions.append({
                    "date": str(check_date),
                    "start": slot["start"],
                    "end": slot["end"],
                    "day": check_date.strftime("%A"),
                })
        if len(suggestions) >= 5:
            break

    if not suggestions:
        return _ok({
            "message": "No alternative slots found in the next 4 days.",
            "suggestions": [],
        })

    return _ok({
        "preferred_date": preferred_date,
        "suggestions": suggestions,
        "message": f"Found {len(suggestions)} alternative slots.",
    })
