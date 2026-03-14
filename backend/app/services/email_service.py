"""Email service using Gmail SMTP (smtplib — no third-party SDK needed)."""
import smtplib
import asyncio
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings


CONFIRMATION_HTML = """
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:24px">
  <h2 style="color:#2563eb">Appointment Confirmed ✓</h2>
  <p>Dear <strong>{patient_name}</strong>,</p>
  <p>Your appointment has been successfully booked.</p>
  <table style="border-collapse:collapse;width:100%;margin:20px 0">
    <tr><td style="padding:8px;border:1px solid #e5e7eb;background:#f9fafb;font-weight:bold">Doctor</td>
        <td style="padding:8px;border:1px solid #e5e7eb">{doctor_name}</td></tr>
    <tr><td style="padding:8px;border:1px solid #e5e7eb;background:#f9fafb;font-weight:bold">Date &amp; Time</td>
        <td style="padding:8px;border:1px solid #e5e7eb">{start_time}</td></tr>
    <tr><td style="padding:8px;border:1px solid #e5e7eb;background:#f9fafb;font-weight:bold">Duration</td>
        <td style="padding:8px;border:1px solid #e5e7eb">30 minutes</td></tr>
    {calendar_row}
  </table>
  <p style="color:#6b7280;font-size:12px">
    If you need to reschedule or cancel, please contact us at least 2 hours before your appointment.
  </p>
</body>
</html>
"""

CALENDAR_ROW = """
  <tr><td style="padding:8px;border:1px solid #e5e7eb;background:#f9fafb;font-weight:bold">Calendar Link</td>
      <td style="padding:8px;border:1px solid #e5e7eb"><a href="{link}">Add to Google Calendar</a></td></tr>
"""


class EmailService:
    def __init__(self):
        if not settings.GMAIL_ADDRESS or not settings.GMAIL_APP_PASSWORD:
            raise RuntimeError("GMAIL_ADDRESS and GMAIL_APP_PASSWORD must be configured")

    def _send_smtp(self, to_email: str, subject: str, html_body: str) -> str:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = settings.GMAIL_ADDRESS
        msg["To"]      = to_email
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(settings.GMAIL_ADDRESS, settings.GMAIL_APP_PASSWORD)
            server.sendmail(settings.GMAIL_ADDRESS, to_email, msg.as_string())
        return "sent"

    async def send_appointment_confirmation(
        self,
        to_email: str,
        patient_name: str,
        details: dict,
    ) -> str:
        cal_row = ""
        if details.get("google_calendar_link"):
            cal_row = CALENDAR_ROW.format(link=details["google_calendar_link"])

        html_body = CONFIRMATION_HTML.format(
            patient_name=patient_name,
            doctor_name=details.get("doctor_name", "your doctor"),
            start_time=details.get("start_time", ""),
            calendar_row=cal_row,
        )

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._send_smtp, to_email, "Your Appointment is Confirmed", html_body
        )

    async def send_generic(self, to_email: str, subject: str, body: str) -> str:
        html_body = f"<pre style='font-family:Arial,sans-serif'>{body}</pre>"
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._send_smtp, to_email, subject, html_body
        )
