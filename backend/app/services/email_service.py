"""Email confirmation service using SendGrid."""
from typing import Optional
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
        if not settings.SENDGRID_API_KEY:
            raise RuntimeError("SENDGRID_API_KEY not configured")

    async def send_appointment_confirmation(
        self,
        to_email: str,
        patient_name: str,
        details: dict,
    ) -> str:
        """Send HTML confirmation email. Returns message ID."""
        import asyncio
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail

        cal_row = ""
        if details.get("google_calendar_link"):
            cal_row = CALENDAR_ROW.format(link=details["google_calendar_link"])

        html_content = CONFIRMATION_HTML.format(
            patient_name=patient_name,
            doctor_name=details.get("doctor_name", "your doctor"),
            start_time=details.get("start_time", ""),
            calendar_row=cal_row,
        )

        message = Mail(
            from_email=settings.FROM_EMAIL,
            to_emails=to_email,
            subject="Your Appointment is Confirmed",
            html_content=html_content,
        )

        def _send():
            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            response = sg.send(message)
            headers = dict(response.headers)
            return headers.get("X-Message-Id", "sent")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _send)

    async def send_generic(self, to_email: str, subject: str, body: str) -> str:
        """Send a plain-text email."""
        import asyncio
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail

        message = Mail(
            from_email=settings.FROM_EMAIL,
            to_emails=to_email,
            subject=subject,
            plain_text_content=body,
        )

        def _send():
            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            response = sg.send(message)
            return dict(response.headers).get("X-Message-Id", "sent")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _send)
