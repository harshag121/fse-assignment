"""Notification service - Slack (primary) with Twilio WhatsApp fallback."""
from app.core.config import settings
from app.models.database import Doctor


class NotificationService:
    """
    Tries Slack first; if no Slack token is configured (or channel starts with
    '+' / 'whatsapp:') falls back to Twilio WhatsApp.
    """

    async def send(self, doctor: Doctor, message: str, channel: str = None) -> dict:
        # Decide channel
        target = channel or settings.SLACK_DEFAULT_CHANNEL

        use_whatsapp = (
            not settings.SLACK_BOT_TOKEN
            or (target and (target.startswith("+") or target.startswith("whatsapp:")))
        )

        if use_whatsapp:
            return await self._send_whatsapp(doctor, message, target)
        return await self._send_slack(message, target)

    async def _send_slack(self, message: str, channel: str) -> dict:
        if not settings.SLACK_BOT_TOKEN:
            raise RuntimeError("SLACK_BOT_TOKEN not configured")

        import asyncio
        from slack_sdk.web.async_client import AsyncWebClient

        client = AsyncWebClient(token=settings.SLACK_BOT_TOKEN)
        response = await client.chat_postMessage(channel=channel, text=message)
        return {"method": "slack", "channel": channel, "ts": response["ts"]}

    async def _send_whatsapp(self, doctor: Doctor, message: str, phone: str = None) -> dict:
        if not settings.TWILIO_ACCOUNT_SID:
            raise RuntimeError("Neither SLACK_BOT_TOKEN nor Twilio credentials are configured")

        import asyncio
        from twilio.rest import Client

        to_number = phone or doctor.whatsapp_number
        if not to_number:
            raise RuntimeError(f"No WhatsApp number for doctor {doctor.name}")

        # Ensure "whatsapp:" prefix
        if not to_number.startswith("whatsapp:"):
            to_number = f"whatsapp:{to_number}"

        def _send():
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            msg = client.messages.create(
                body=message,
                from_=settings.TWILIO_WHATSAPP_FROM or "whatsapp:+14155238886",
                to=to_number,
            )
            return msg.sid

        loop = asyncio.get_event_loop()
        sid = await loop.run_in_executor(None, _send)
        return {"method": "whatsapp", "channel": to_number, "sid": sid}
