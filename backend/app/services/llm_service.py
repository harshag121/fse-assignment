"""LLM Service — acts as an MCP *client*.

Architecture:
  1. At the start of every chat turn, connects to the MCP server (port 8001) via SSE.
  2. Calls session.list_tools()  → discovers available tools dynamically (no hardcoding).
  3. Passes the tool schemas to the LLM (Groq/OpenAI).
  4. When the LLM requests a tool call, invokes session.call_tool() through the MCP
     protocol — never calling Python functions directly.
  5. Feeds the tool result back to the LLM and repeats until the model stops calling tools.
"""
import asyncio
import json
from typing import Any

from mcp.client.sse import sse_client
from mcp import ClientSession
from sqlalchemy import select

from app.core.config import settings
from app.models.database import Conversation, AsyncSessionLocal


# ── Integer fields that Groq may serialize as strings ─────────────────────────
# Coerce them before sending to the MCP server so DB lookups work correctly.
_INT_FIELDS: dict[str, list[str]] = {
    "book_appointment": ["doctor_id", "patient_id"],
    "query_appointments_stats": ["doctor_id"],
    "send_doctor_notification": ["doctor_id"],
    "auto_reschedule": ["doctor_id"],
}


def _mcp_tool_to_openai(tool) -> dict:
    """Convert an MCP Tool object to the OpenAI function-calling schema."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.inputSchema,
        },
    }


def _system_patient() -> str:
    from datetime import date
    today = date.today()
    return (
        f"You are a warm, professional medical appointment assistant.\n"
        f"TODAY'S DATE IS: {today.strftime('%Y-%m-%d')} ({today.strftime('%A, %d %B %Y')}). "
        "Always use this when interpreting 'today', 'tomorrow', 'this week', etc.\n"
        "Rules:\n"
        "1. Always call check_doctor_availability BEFORE booking.\n"
        "2. After booking, always call send_email_confirmation.\n"
        "3. If the slot is taken, call auto_reschedule.\n"
        "4. Never invent data – only use tool results.\n"
        "5. Maintain context across the conversation (doctor, date, time chosen).\n"
        "6. Be concise and friendly. Confirm details before finalising.\n"
        "7. CRITICAL: doctor_id and patient_id must be plain integers (e.g. 1, 2). "
        "Get the doctor_id from check_doctor_availability results. "
        "NEVER use a variable name, function name, or placeholder as an ID."
    )


def _system_doctor() -> str:
    from datetime import date
    today = date.today()
    return (
        f"You are a precise medical practice analytics assistant.\n"
        f"TODAY'S DATE IS: {today.strftime('%Y-%m-%d')} ({today.strftime('%A, %d %B %Y')}). "
        "Always use this when interpreting 'today', 'yesterday', 'this week', etc.\n"
        "Rules:\n"
        "1. Always use query_appointments_stats to get real data.\n"
        "2. After fetching stats, present a clear bullet-point summary.\n"
        "3. When asked to send a report, call send_doctor_notification with the summary.\n"
        "4. Support ranges: today, yesterday, this_week, last_week, custom.\n"
        "5. Be concise and professional."
    )


class LLMService:
    def __init__(self):
        self._openai_client = None
        # SSE-based MCP server handles one connection at a time; serialize access.
        self._mcp_lock = asyncio.Semaphore(1)

    def _get_openai(self):
        if self._openai_client:
            return self._openai_client
        from openai import AsyncOpenAI
        if settings.GROQ_API_KEY:
            self._openai_client = AsyncOpenAI(
                api_key=settings.GROQ_API_KEY,
                base_url="https://api.groq.com/openai/v1",
            )
        else:
            self._openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._openai_client

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
            return [{"role": row.role, "content": row.content or ""} for row in rows]

    async def _save_message(
        self,
        session_id: str,
        user_id: Any,
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
        """Run one turn of the agentic loop.

        Uses the MCP protocol for ALL tool interactions:
          - list_tools()  → dynamic discovery (no hardcoded schemas)
          - call_tool()   → protocol-based invocation (no direct function calls)
        """
        openai = self._get_openai()
        history = await self._load_history(session_id)
        await self._save_message(session_id, user_id, "user", user_message)

        system_prompt = _system_doctor() if role == "doctor" else _system_patient()
        messages = [{"role": "system", "content": system_prompt}] + history + [
            {"role": "user", "content": user_message}
        ]

        tools_called: list[str] = []
        appointments_affected: list[int] = []

        # Open a single MCP connection that lasts the entire agentic loop.
        # Semaphore ensures only one SSE connection is open at a time (server limit).
        try:
            async with self._mcp_lock:
                async with sse_client(settings.MCP_SERVER_URL) as (read, write):
                    async with ClientSession(read, write) as mcp_session:

                        # ── MCP: initialise the session ────────────────────────────────
                        await mcp_session.initialize()

                        # ── MCP: dynamic tool discovery ────────────────────────────────
                        # We never hardcode tool schemas here — we ask the server.
                        tools_result = await mcp_session.list_tools()
                        openai_tools = [_mcp_tool_to_openai(t) for t in tools_result.tools]

                        # ── Agentic loop ───────────────────────────────────────────────
                        for _ in range(10):  # max 10 tool rounds
                            response = await openai.chat.completions.create(
                                model=settings.LLM_MODEL,
                                messages=messages,
                                tools=openai_tools,
                                tool_choice="auto",
                            )
                            msg = response.choices[0].message

                            if not msg.tool_calls:
                                # Model returned a final text response — done.
                                assistant_text = msg.content or ""
                                await self._save_message(session_id, user_id, "assistant", assistant_text)
                                return {
                                    "reply": assistant_text,
                                    "tool_calls_made": tools_called,
                                    "appointments_affected": appointments_affected,
                                }

                            # Append the assistant's tool-call message to context.
                            messages.append(msg)

                            # Execute each tool the model requested.
                            for tc in msg.tool_calls:
                                fn_name = tc.function.name
                                fn_args = json.loads(tc.function.arguments)

                                # Coerce integer fields — Groq/Llama may serialize them as strings.
                                coerce_error = None
                                for field in _INT_FIELDS.get(fn_name, []):
                                    if field in fn_args and not isinstance(fn_args[field], int):
                                        try:
                                            fn_args[field] = int(fn_args[field])
                                        except (ValueError, TypeError):
                                            coerce_error = (
                                                f"Invalid value for '{field}': expected a plain integer "
                                                f"(e.g. 1), got '{fn_args[field]}'. "
                                                "Use the numeric ID from a previous tool result."
                                            )
                                            break

                                tools_called.append(fn_name)

                                if coerce_error:
                                    result_text = json.dumps({"error": coerce_error})
                                else:
                                    # ── MCP: protocol-based tool invocation ───────────
                                    # The tool runs inside the MCP server process;
                                    # we receive the result back through the protocol.
                                    mcp_result = await mcp_session.call_tool(fn_name, fn_args)
                                    result_text = (
                                        mcp_result.content[0].text
                                        if mcp_result.content and hasattr(mcp_result.content[0], "text")
                                        else "{}"
                                    )

                                # Track appointment IDs for the response metadata.
                                try:
                                    parsed = json.loads(result_text)
                                    if isinstance(parsed, dict) and "appointment_id" in parsed:
                                        appointments_affected.append(parsed["appointment_id"])
                                except Exception:
                                    pass

                                messages.append({
                                    "role": "tool",
                                    "tool_call_id": tc.id,
                                    "content": result_text,
                                })

                                await self._save_message(
                                    session_id,
                                    user_id,
                                    "tool",
                                    result_text,
                                    tool_calls=[{"name": fn_name, "args": fn_args}],
                                )

        except Exception as exc:
            # Unwrap anyio ExceptionGroup (Python 3.11+) to inspect cause.
            causes = getattr(exc, "exceptions", None)
            raw = "; ".join(str(c) for c in causes) if causes else str(exc)
            all_causes = list(causes) if causes else [exc]

            # Only rewrite the error when the failure is a network connection
            # problem reaching the MCP server.  Other errors (Groq API, DB, ...)
            # are re-raised unchanged so the caller can handle them properly.
            _conn_types = (ConnectionRefusedError, OSError, ConnectionError)
            is_conn_err = any(isinstance(c, _conn_types) for c in all_causes) or any(
                kw in raw.lower() for kw in ("connect", "refused", "unreachable", "nodename")
            )
            if is_conn_err:
                raise RuntimeError(
                    f"Cannot connect to MCP server at {settings.MCP_SERVER_URL}. "
                    "Make sure the MCP server process is running."
                ) from exc
            raise

        # Fallback if the agentic loop exhausted its budget.
        final = "I've processed your request. Please check back for results."
        await self._save_message(session_id, user_id, "assistant", final)
        return {
            "reply": final,
            "tool_calls_made": tools_called,
            "appointments_affected": appointments_affected,
        }
