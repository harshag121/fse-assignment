"""LLM Service - orchestrates tool-calling via OpenAI or Anthropic."""
import json
import uuid
from typing import Any

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.database import Conversation, AsyncSessionLocal
from app.mcp_server.tools import (
    _check_doctor_availability,
    _book_appointment,
    _send_email_confirmation,
    _query_appointments_stats,
    _send_doctor_notification,
    _auto_reschedule,
)

# ── Tool definitions for OpenAI function-calling ──────────────────────────────

OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "check_doctor_availability",
            "description": "Check available appointment slots for a doctor on a given date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "doctor_name": {"type": "string"},
                    "date": {"type": "string", "description": "YYYY-MM-DD"},
                },
                "required": ["doctor_name", "date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": "Book an appointment for a patient with a doctor.",
            "parameters": {
                "type": "object",
                "properties": {
                    "doctor_id": {"type": "string", "description": "integer doctor ID"},
                    "patient_id": {"type": "string", "description": "integer patient ID"},
                    "datetime": {"type": "string", "description": "ISO 8601"},
                    "symptoms": {"type": "string"},
                },
                "required": ["doctor_id", "patient_id", "datetime"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_email_confirmation",
            "description": "Send appointment confirmation email to patient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to_email": {"type": "string"},
                    "patient_name": {"type": "string"},
                    "appointment_details": {"type": "object"},
                },
                "required": ["to_email", "patient_name", "appointment_details"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_appointments_stats",
            "description": "Query appointment statistics for a doctor report.",
            "parameters": {
                "type": "object",
                "properties": {
                    "doctor_id": {"type": "string", "description": "integer doctor ID"},
                    "date_range": {
                        "type": "string",
                        "enum": ["yesterday", "today", "tomorrow", "this_week", "last_week", "custom"],
                    },
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "filter": {"type": "string"},
                },
                "required": ["doctor_id", "date_range"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_doctor_notification",
            "description": "Send a summary report to a doctor via Slack.",
            "parameters": {
                "type": "object",
                "properties": {
                    "doctor_id": {"type": "string", "description": "integer doctor ID"},
                    "message": {"type": "string"},
                },
                "required": ["doctor_id", "message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "auto_reschedule",
            "description": "Suggest alternative appointment slots when preferred time is unavailable.",
            "parameters": {
                "type": "object",
                "properties": {
                    "doctor_id": {"type": "string", "description": "integer doctor ID"},
                    "preferred_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "symptoms": {"type": "string"},
                },
                "required": ["doctor_id", "preferred_date"],
            },
        },
    },
]

TOOL_HANDLERS = {
    "check_doctor_availability": _check_doctor_availability,
    "book_appointment": _book_appointment,
    "send_email_confirmation": _send_email_confirmation,
    "query_appointments_stats": _query_appointments_stats,
    "send_doctor_notification": _send_doctor_notification,
    "auto_reschedule": _auto_reschedule,
}

# Integer fields per tool — coerce strings to int (Groq sometimes serialises ints as strings)
_INT_FIELDS: dict[str, list[str]] = {
    "book_appointment": ["doctor_id", "patient_id"],
    "query_appointments_stats": ["doctor_id"],
    "send_doctor_notification": ["doctor_id"],
    "auto_reschedule": ["doctor_id"],
}

def _system_patient() -> str:
    from datetime import date
    today = date.today()
    return (
        f"You are a warm, professional medical appointment assistant.\n"
        f"TODAY'S DATE IS: {today.strftime('%Y-%m-%d')} ({today.strftime('%A, %d %B %Y')}). "
        f"Always use this when interpreting 'today', 'tomorrow', 'this week', etc.\n"
        "Rules:\n"
        "1. Always call check_doctor_availability BEFORE booking.\n"
        "2. After booking, always call send_email_confirmation.\n"
        "3. If the slot is taken, call auto_reschedule.\n"
        "4. Never invent data – only use tool results.\n"
        "5. Maintain context across the conversation (doctor, date, time chosen).\n"
        "6. Be concise and friendly. Confirm details before finalising."
    )


def _system_doctor() -> str:
    from datetime import date
    today = date.today()
    return (
        f"You are a precise medical practice analytics assistant.\n"
        f"TODAY'S DATE IS: {today.strftime('%Y-%m-%d')} ({today.strftime('%A, %d %B %Y')}). "
        f"Always use this when interpreting 'today', 'yesterday', 'this week', etc.\n"
        "Rules:\n"
        "1. Always use query_appointments_stats to get real data.\n"
        "2. After fetching stats, present a clear bullet-point summary.\n"
        "3. When asked to send a report, call send_doctor_notification with the summary.\n"
        "4. Support ranges: today, yesterday, this_week, last_week, custom.\n"
        "5. Be concise and professional."
    )


class LLMService:
    def __init__(self):
        self.client = None

    def _get_openai(self):
        if self.client:
            return self.client
        from openai import AsyncOpenAI
        if settings.GROQ_API_KEY:
            # Groq is OpenAI-compatible — just swap base_url and key
            self.client = AsyncOpenAI(
                api_key=settings.GROQ_API_KEY,
                base_url="https://api.groq.com/openai/v1",
            )
        else:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self.client

    async def _load_history(self, session_id: str, limit: int = 10) -> list[dict]:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Conversation)
                .where(Conversation.session_id == session_id)
                .where(Conversation.role.in_(["user", "assistant"]))
                .order_by(Conversation.timestamp.desc())
                .limit(limit)
            )
            rows = result.scalars().all()
            rows.reverse()
            # Only return role + content — strip tool_calls to avoid format issues
            return [{"role": row.role, "content": row.content or ""} for row in rows]

    async def _save_message(
        self,
        session_id: str,
        user_id: str,
        role: str,
        content: str,
        tool_calls: Any = None,
    ):
        async with AsyncSessionLocal() as db:
            conv = Conversation(
                session_id=session_id,
                user_id=str(user_id) if user_id else None,
                role=role,
                content=content,
                tool_calls=json.dumps(tool_calls) if tool_calls else None,
            )
            db.add(conv)
            await db.commit()

    async def chat(
        self,
        session_id: str,
        user_message: str,
        role: str = "patient",
        user_id: int = None,
    ) -> dict:
        """Run one turn of the agentic loop."""
        openai = self._get_openai()

        # Load history
        history = await self._load_history(session_id)

        # Persist user message
        await self._save_message(session_id, user_id, "user", user_message)

        system_prompt = _system_doctor() if role == "doctor" else _system_patient()
        messages = [{"role": "system", "content": system_prompt}] + history + [
            {"role": "user", "content": user_message}
        ]

        tools_called: list[str] = []
        appointments_affected: list[int] = []

        # Agentic loop – keep running until the model stops calling tools
        for _ in range(10):  # max 10 tool rounds
            response = await openai.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=messages,
                tools=OPENAI_TOOLS,
                tool_choice="auto",
            )
            msg = response.choices[0].message

            if not msg.tool_calls:
                # Final text response
                assistant_text = msg.content or ""
                await self._save_message(session_id, user_id, "assistant", assistant_text)
                return {
                    "reply": assistant_text,
                    "tool_calls_made": tools_called,
                    "appointments_affected": appointments_affected,
                }

            # Append assistant message with tool_calls to context
            messages.append(msg)

            # Execute each tool call
            for tc in msg.tool_calls:
                fn_name = tc.function.name
                fn_args = json.loads(tc.function.arguments)
                # Coerce integer fields that Groq may serialize as strings
                for field in _INT_FIELDS.get(fn_name, []):
                    if field in fn_args and isinstance(fn_args[field], str):
                        try:
                            fn_args[field] = int(fn_args[field])
                        except ValueError:
                            pass
                tools_called.append(fn_name)

                handler = TOOL_HANDLERS.get(fn_name)
                if handler:
                    result_contents = await handler(**fn_args)
                    result_text = result_contents[0].text if result_contents else "{}"

                    # Track appointment IDs
                    try:
                        parsed = json.loads(result_text)
                        if isinstance(parsed, dict) and "appointment_id" in parsed:
                            appointments_affected.append(parsed["appointment_id"])
                    except Exception:
                        pass
                else:
                    result_text = json.dumps({"error": f"Unknown tool: {fn_name}"})

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_text,
                })

                # Persist tool result in conversation
                await self._save_message(
                    session_id,
                    user_id,
                    "tool",
                    result_text,
                    tool_calls=[{"name": fn_name, "args": fn_args}],
                )

        # Fallback if loop exhausted
        final = "I've processed your request. Please check back for results."
        await self._save_message(session_id, user_id, "assistant", final)
        return {
            "reply": final,
            "tool_calls_made": tools_called,
            "appointments_affected": appointments_affected,
        }
