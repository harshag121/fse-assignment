"""Google Calendar integration service."""
import json
from datetime import datetime
from typing import Optional

from app.core.config import settings


class CalendarService:
    def __init__(self):
        self._service = None

    def _get_service(self):
        if self._service:
            return self._service
        if not settings.GOOGLE_CREDENTIALS_JSON:
            raise RuntimeError("GOOGLE_CREDENTIALS_JSON not configured")

        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        creds_info = json.loads(settings.GOOGLE_CREDENTIALS_JSON)
        scopes = ["https://www.googleapis.com/auth/calendar"]
        creds = service_account.Credentials.from_service_account_info(creds_info, scopes=scopes)
        self._service = build("calendar", "v3", credentials=creds)
        return self._service

    async def create_event(
        self,
        title: str,
        start: datetime,
        end: datetime,
        description: str = "",
        attendee_emails: list[str] = None,
        calendar_id: str = "primary",
    ) -> dict:
        import asyncio

        def _create():
            service = self._get_service()
            event_body = {
                "summary": title,
                "description": description,
                "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
                "end": {"dateTime": end.isoformat(), "timeZone": "UTC"},
                "conferenceData": {
                    "createRequest": {"requestId": f"appt-{start.timestamp()}"}
                },
            }
            if attendee_emails:
                event_body["attendees"] = [{"email": e} for e in attendee_emails]

            return (
                service.events()
                .insert(
                    calendarId=calendar_id,
                    body=event_body,
                    conferenceDataVersion=1,
                    sendUpdates="all",
                )
                .execute()
            )

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _create)

    async def update_event(
        self,
        event_id: str,
        start: datetime,
        end: datetime,
        calendar_id: str = "primary",
    ) -> dict:
        import asyncio

        def _update():
            service = self._get_service()
            event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
            event["start"]["dateTime"] = start.isoformat()
            event["end"]["dateTime"] = end.isoformat()
            return (
                service.events()
                .update(calendarId=calendar_id, eventId=event_id, body=event)
                .execute()
            )

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _update)

    async def delete_event(self, event_id: str, calendar_id: str = "primary") -> bool:
        import asyncio

        def _delete():
            service = self._get_service()
            service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
            return True

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _delete)

    async def get_free_busy(
        self,
        email: str,
        start: datetime,
        end: datetime,
    ) -> list[dict]:
        import asyncio

        def _query():
            service = self._get_service()
            body = {
                "timeMin": start.isoformat() + "Z",
                "timeMax": end.isoformat() + "Z",
                "items": [{"id": email}],
            }
            result = service.freebusy().query(body=body).execute()
            return result.get("calendars", {}).get(email, {}).get("busy", [])

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _query)
