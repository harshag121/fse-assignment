"""LLM Service - acts as an MCP client."""
import asyncio
import json
from typing import Any

from mcp import ClientSession
from mcp.client.sse import sse_client
from sqlalchemy import select

from app.core.config import settings
from app.models.database import AsyncSessionLocal, Conversation


_INT_FIELDS: dict[str, list[str]] = {
    "book_appointment": ["doctor_id", "patient_id"],
    "query_appointments_stats": ["doctor_id"],
    "send_doctor_notification": ["doctor_id"],
    "auto_reschedule": ["doctor_id"],
}


def _mcp_tool_to_openai(tool) -> dict:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.inputSchema,
        },
    }


def _assistant_message_to_openai_dict(msg) -> dict:
    payload = {
        "role": "assistant",
        "content": msg.content or "",
    }
    if msg.tool_calls:
        payload["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in msg.tool_calls
        ]
    return payload


def _parse_tool_arguments(raw_args: Any) -> tuple[dict[str, Any] | None, str | None]:
    if raw_args is None:
        return {}, None
    if isinstance(raw_args, dict):
        return raw_args, None
    if not isinstance(raw_args, str):
        return None, f"Tool arguments must be JSON text or an object, got {type(raw_args).__name__}."

    try:
        parsed = json.loads(raw_args)
    except json.JSONDecodeError as exc:
        return None, f"Invalid JSON tool arguments: {exc.msg}. Raw arguments: {raw_args}"

    if not isinstance(parsed, dict):
        return None, f"Tool arguments must decode to a JSON object. Raw arguments: {raw_args}"
    return parsed, None


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
        "4. Never invent data - only use tool results.\n"
        "5. Maintain context across the conversation (doctor, date, time chosen).\n"
        "6. Be concise and friendly. Confirm details before finalising.\n"
        "7. If the user picks a slot from a previous message, reuse the doctor and date from conversation history.\n"
        "8. When the user asks for alternatives because a slot is unavailable, call auto_reschedule for the same doctor.\n"
        "9. CRITICAL: doctor_id and patient_id must be plain integers (e.g. 1, 2). "
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
        "5. If the user mentions an exact date, call query_appointments_stats with "
        "date_range='custom' and set both start_date and end_date to that date.\n"
        "6. If the user asks about a symptom such as fever, pass that word in the filter field.\n"
        "7. Be concise and professional."
    )


class LLMService:
    def __init__(self):
        self._openai_client = None
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

    def _candidate_models(self) -> list[str]:
        models = [settings.LLM_MODEL]
        # Groq free tier commonly rate-limits the larger 70B model; keep a cheap
        # tool-capable fallback ready so agentic flows still complete.
        if settings.GROQ_API_KEY and "llama-3.1-8b-instant" not in models:
            models.append("llama-3.1-8b-instant")
        return models

    async def _create_completion(self, openai, messages: list[dict], tools: list[dict]):
        last_exc = None
        for model_name in self._candidate_models():
            try:
                return await openai.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                )
            except Exception as exc:
                raw = str(exc).lower()
                is_rate_limited = "rate_limit" in raw or "rate limit" in raw or "429" in raw
                if not is_rate_limited:
                    raise
                last_exc = exc

        raise RuntimeError(
            "Groq rate limit exceeded for all configured models. "
            "Try again in a few minutes or switch to a lower-cost model."
        ) from last_exc

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
        openai = self._get_openai()
        history = await self._load_history(session_id)
        await self._save_message(session_id, user_id, "user", user_message)

        system_prompt = _system_doctor() if role == "doctor" else _system_patient()
        messages = [{"role": "system", "content": system_prompt}] + history + [
            {"role": "user", "content": user_message}
        ]

        tools_called: list[str] = []
        appointments_affected: list[int] = []

        try:
            async with self._mcp_lock:
                async with sse_client(settings.MCP_SERVER_URL) as (read, write):
                    async with ClientSession(read, write) as mcp_session:
                        await mcp_session.initialize()
                        tools_result = await mcp_session.list_tools()
                        openai_tools = [_mcp_tool_to_openai(t) for t in tools_result.tools]

                        for _ in range(10):
                            response = await self._create_completion(openai, messages, openai_tools)
                            msg = response.choices[0].message

                            if not msg.tool_calls:
                                assistant_text = msg.content or ""
                                await self._save_message(session_id, user_id, "assistant", assistant_text)
                                return {
                                    "reply": assistant_text,
                                    "tool_calls_made": tools_called,
                                    "appointments_affected": appointments_affected,
                                }

                            messages.append(_assistant_message_to_openai_dict(msg))

                            for tc in msg.tool_calls:
                                fn_name = tc.function.name
                                fn_args, parse_error = _parse_tool_arguments(tc.function.arguments)
                                coerce_error = None

                                if fn_args is not None:
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

                                if parse_error:
                                    result_text = json.dumps({"error": parse_error})
                                    saved_args = {"raw_arguments": tc.function.arguments}
                                elif coerce_error:
                                    result_text = json.dumps({"error": coerce_error})
                                    saved_args = fn_args
                                else:
                                    try:
                                        mcp_result = await mcp_session.call_tool(fn_name, fn_args)
                                        result_text = (
                                            mcp_result.content[0].text
                                            if mcp_result.content and hasattr(mcp_result.content[0], "text")
                                            else "{}"
                                        )
                                    except Exception as tool_exc:
                                        result_text = json.dumps(
                                            {"error": f"Tool '{fn_name}' invocation failed: {tool_exc}"}
                                        )
                                    saved_args = fn_args

                                try:
                                    parsed = json.loads(result_text)
                                    if isinstance(parsed, dict) and "appointment_id" in parsed:
                                        appointments_affected.append(parsed["appointment_id"])
                                except Exception:
                                    pass

                                messages.append({
                                    "role": "tool",
                                    "tool_call_id": tc.id,
                                    "name": fn_name,
                                    "content": result_text,
                                })

                                await self._save_message(
                                    session_id,
                                    user_id,
                                    "tool",
                                    result_text,
                                    tool_calls=[{"name": fn_name, "args": saved_args}],
                                )

        except Exception as exc:
            causes = getattr(exc, "exceptions", None)
            raw = "; ".join(str(c) for c in causes) if causes else str(exc)
            all_causes = list(causes) if causes else [exc]

            conn_types = (ConnectionRefusedError, OSError, ConnectionError)
            is_conn_err = any(isinstance(c, conn_types) for c in all_causes) or any(
                kw in raw.lower() for kw in ("connect", "refused", "unreachable", "nodename")
            )
            if is_conn_err:
                raise RuntimeError(
                    f"Cannot connect to MCP server at {settings.MCP_SERVER_URL}. "
                    "Make sure the MCP server process is running."
                ) from exc
            raise

        final = "I've processed your request. Please check back for results."
        await self._save_message(session_id, user_id, "assistant", final)
        return {
            "reply": final,
            "tool_calls_made": tools_called,
            "appointments_affected": appointments_affected,
        }
