import json
import os
import unittest
from datetime import datetime, timedelta
from unittest import mock

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://docuser:docpass@127.0.0.1:5434/docappointment_test",
)
os.environ.setdefault("SECRET_KEY", "test-secret-key")

from httpx import ASGITransport, AsyncClient

from app.main import app
from app.core.security import get_password_hash
from app.models.database import (
    Base,
    AsyncSessionLocal,
    Appointment,
    AppointmentStatus,
    Availability,
    Doctor,
    Patient,
    engine,
)
from app.mcp_server.tools import (
    _ok,
    _auto_reschedule,
    _invoke_tool_handler,
    _query_appointments_stats,
    _send_doctor_notification,
)
from app.services.email_service import EmailService
from app.core.config import settings


class BackendFlowTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await engine.dispose()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

        async with AsyncSessionLocal() as db:
            self.doctor_primary = Doctor(
                name="Dr. Alpha",
                specialization="General Medicine",
                email="alpha@example.com",
                phone="555-0100",
                password_hash=get_password_hash("test123"),
            )
            self.doctor_secondary = Doctor(
                name="Dr. Beta",
                specialization="Cardiology",
                email="beta@example.com",
                phone="555-0101",
                password_hash=get_password_hash("test123"),
            )
            self.patient = Patient(
                name="Patient One",
                email="patient@example.com",
                phone="555-0200",
                password_hash=get_password_hash("test123"),
            )
            db.add_all([self.doctor_primary, self.doctor_secondary, self.patient])
            await db.flush()

            # Wednesday availability for the primary doctor (2026-03-18)
            db.add(
                Availability(
                    doctor_id=self.doctor_primary.id,
                    day_of_week=2,
                    start_time="09:00",
                    end_time="12:00",
                    slot_duration_minutes=30,
                    is_available=True,
                )
            )
            # Distinct window for the secondary doctor so wrong-doctor suggestions are obvious.
            db.add(
                Availability(
                    doctor_id=self.doctor_secondary.id,
                    day_of_week=2,
                    start_time="14:00",
                    end_time="16:00",
                    slot_duration_minutes=30,
                    is_available=True,
                )
            )

            booked_start = datetime(2026, 3, 18, 9, 30)
            db.add(
                Appointment(
                    doctor_id=self.doctor_primary.id,
                    patient_id=self.patient.id,
                    start_time=booked_start,
                    end_time=booked_start + timedelta(minutes=30),
                    status=AppointmentStatus.CONFIRMED,
                    symptoms="fever and cough",
                )
            )
            cancellable_start = datetime(2026, 3, 18, 11, 0)
            self.cancellable_appointment = Appointment(
                doctor_id=self.doctor_primary.id,
                patient_id=self.patient.id,
                start_time=cancellable_start,
                end_time=cancellable_start + timedelta(minutes=30),
                status=AppointmentStatus.CONFIRMED,
                symptoms="follow up",
            )
            db.add(self.cancellable_appointment)
            await db.commit()

        self.primary_id = self.doctor_primary.id
        self.patient_id = self.patient.id
        self.cancellable_id = self.cancellable_appointment.id

    async def asyncTearDown(self):
        await engine.dispose()

    async def test_auto_reschedule_uses_requested_doctor(self):
        result = await _auto_reschedule(
            doctor_name="Dr. Alpha",
            date="2026-03-18",
        )
        payload = json.loads(result[0].text)

        self.assertNotIn("error", payload)
        self.assertTrue(payload["suggestions"])
        self.assertTrue(all(item["date"] == "2026-03-18" for item in payload["suggestions"]))
        self.assertTrue(all(item["start"] < "12:00" for item in payload["suggestions"]))
        self.assertTrue(all(item["start"] != "14:00" for item in payload["suggestions"]))

    async def test_query_stats_accepts_exact_date_and_symptom_aliases(self):
        result = await _invoke_tool_handler(
            "query_appointments_stats",
            _query_appointments_stats,
            {
                "doctor_name": "Dr. Alpha",
                "date": "2026-03-18",
                "symptom": "fever",
                "unexpected": "ignored",
            },
        )
        payload = json.loads(result[0].text)

        self.assertEqual(payload["doctor_id"], self.primary_id)
        self.assertEqual(payload["date_range"], "2026-03-18 to 2026-03-18")
        self.assertEqual(payload["total_appointments"], 1)
        self.assertEqual(payload["confirmed"], 1)
        self.assertIn("fever", payload["symptom_breakdown"])

    async def test_send_notification_aliases_do_not_crash_tool_dispatch(self):
        result = await _invoke_tool_handler(
            "send_doctor_notification",
            _send_doctor_notification,
            {
                "doctor_name": "Dr. Alpha",
                "report": "Daily summary",
                "unused_field": "ignored",
            },
        )
        payload = json.loads(result[0].text)

        self.assertIn("error", payload)
        self.assertNotIn("Tool 'send_doctor_notification' failed", payload["error"])

    async def test_cancel_endpoint_returns_loaded_appointment(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.patch(f"/api/appointments/{self.cancellable_id}/cancel")

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["status"], "cancelled")
        self.assertEqual(payload["doctor"]["id"], self.primary_id)
        self.assertEqual(payload["patient"]["id"], self.patient_id)

    async def test_generate_report_uses_direct_stats_and_notification_flow(self):
        transport = ASGITransport(app=app)

        async def fake_notify(**_kwargs):
            return _ok({"status": "sent", "channel": "#doctor-reports", "method": "slack"})

        with mock.patch("app.api.routes._send_doctor_notification", side_effect=fake_notify):
            async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                response = await client.post(
                    "/api/reports/generate",
                    json={
                        "doctor_id": self.primary_id,
                        "query": "How many patients with fever do I have on 2026-03-18? Send it to #doctor-reports.",
                        "session_id": "report-test-session",
                    },
                )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["tool_calls_made"], ["query_appointments_stats", "send_doctor_notification"])
        self.assertIn("Doctor report for 2026-03-18 to 2026-03-18", payload["reply"])
        self.assertIn("Report sent via slack", payload["reply"])


class EmailServiceTests(unittest.TestCase):
    @mock.patch("app.services.email_service.smtplib.SMTP")
    @mock.patch("app.services.email_service.smtplib.SMTP_SSL")
    def test_send_smtp_falls_back_to_starttls(self, smtp_ssl_mock, smtp_mock):
        smtp_ssl_mock.side_effect = OSError("port 465 blocked")
        smtp_instance = smtp_mock.return_value.__enter__.return_value

        with mock.patch.object(settings, "GMAIL_ADDRESS", "sender@example.com"), mock.patch.object(
            settings, "GMAIL_APP_PASSWORD", "app-password"
        ):
            service = EmailService()
            result = service._send_smtp(
                to_email="patient@example.com",
                subject="Test",
                html_body="<p>Hello</p>",
            )

        self.assertEqual(result, "sent")
        smtp_instance.starttls.assert_called_once()
        smtp_instance.login.assert_called_once_with("sender@example.com", "app-password")


if __name__ == "__main__":
    unittest.main()
