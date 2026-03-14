"""MCP Resources - data sources exposed via URI templates."""
import json
from datetime import date
from mcp.server import Server
from sqlalchemy import select, and_
from app.models.database import AsyncSessionLocal, Doctor, Appointment, AppointmentStatus


def register_resources(server: Server):

    @server.list_resources()
    async def list_resources():
        from mcp.types import Resource
        return [
            Resource(
                uri="doctors://list",
                name="All Doctors",
                description="Full list of doctors with their specializations",
                mimeType="application/json",
            ),
            Resource(
                uri="doctors://schedule_template",
                name="Doctor Schedule (template)",
                description="Use doctors://{doctor_id}/schedule for a specific doctor's today schedule",
                mimeType="application/json",
            ),
            Resource(
                uri="appointments://history_template",
                name="Appointment History (template)",
                description="Use appointments://history?doctor_id={id}&date={date}",
                mimeType="application/json",
            ),
        ]

    @server.read_resource()
    async def read_resource(uri: str):
        from mcp.types import TextResourceContents

        async with AsyncSessionLocal() as db:
            # ── doctors://list ────────────────────────────────────────────────
            if uri == "doctors://list":
                result = await db.execute(select(Doctor))
                doctors = result.scalars().all()
                data = [
                    {"id": d.id, "name": d.name, "specialization": d.specialization}
                    for d in doctors
                ]
                return [TextResourceContents(uri=uri, text=json.dumps(data), mimeType="application/json")]

            # ── doctors://{doctor_id}/schedule ────────────────────────────────
            if uri.startswith("doctors://") and "/schedule" in uri:
                parts = uri.replace("doctors://", "").split("/")
                doctor_id = int(parts[0])
                today = date.today()
                result = await db.execute(
                    select(Appointment).where(
                        and_(
                            Appointment.doctor_id == doctor_id,
                            Appointment.start_time >= today.isoformat(),
                        )
                    )
                )
                appts = result.scalars().all()
                data = [
                    {
                        "id": a.id,
                        "patient_id": a.patient_id,
                        "start": a.start_time.isoformat(),
                        "end": a.end_time.isoformat(),
                        "status": a.status.value,
                        "symptoms": a.symptoms,
                    }
                    for a in appts
                ]
                return [TextResourceContents(uri=uri, text=json.dumps(data), mimeType="application/json")]

            # ── appointments://history ────────────────────────────────────────
            if uri.startswith("appointments://history"):
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(uri)
                qs = parse_qs(parsed.query)
                doctor_id = int(qs.get("doctor_id", [0])[0])
                filter_date = qs.get("date", [str(date.today())])[0]

                filters = [Appointment.doctor_id == doctor_id]
                if filter_date:
                    filters.append(Appointment.start_time >= filter_date)

                result = await db.execute(select(Appointment).where(and_(*filters)))
                appts = result.scalars().all()
                data = [
                    {
                        "id": a.id,
                        "patient_id": a.patient_id,
                        "start": a.start_time.isoformat(),
                        "end": a.end_time.isoformat(),
                        "status": a.status.value,
                        "symptoms": a.symptoms,
                    }
                    for a in appts
                ]
                return [TextResourceContents(uri=uri, text=json.dumps(data), mimeType="application/json")]

        from mcp.types import McpError, ErrorCode
        raise McpError(ErrorCode.InvalidParams, f"Unknown resource URI: {uri}")
