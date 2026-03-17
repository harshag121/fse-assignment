"""LLM Service - acts as an MCP client."""
import asyncio
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from mcp import ClientSession
from mcp.client.sse import sse_client
from sqlalchemy import select

from app.core.config import settings
from app.models.database import AsyncSessionLocal, Conversation, Doctor


_INT_FIELDS: dict[str, list[str]] = {
    "book_appointment": ["doctor_id", "patient_id"],
    "query_appointments_stats": ["doctor_id"],
    "send_doctor_notification": ["doctor_id"],
    "auto_reschedule": ["doctor_id"],
}

_ALT_REQUEST_MARKERS = (
    "if unavailable",
    "if not available",
    "if it's unavailable",
    "suggest alternatives",
    "suggest another",
    "another slot",
    "alternative slot",
    "alternative time",
    "reschedule",
)


@dataclass
class AgentContext:
    role: str
    user_id: int | None = None
    explicit_doctor_id: int | None = None
    explicit_doctor_name: str | None = None
    preferred_date: str | None = None
    preferred_time: str | None = None
    wants_alternatives: bool = False
    latest_doctor_id: int | None = None
    latest_doctor_name: str | None = None
    latest_date: str | None = None
    latest_available_slots: list[str] = field(default_factory=list)
    latest_booking: dict[str, Any] | None = None

    @property
    def active_doctor_id(self) -> int | None:
        if self.role == "doctor" and self.user_id is not None:
            return self.user_id
        return self.explicit_doctor_id or self.latest_doctor_id

    @property
    def active_doctor_name(self) -> str | None:
        return self.explicit_doctor_name or self.latest_doctor_name

    @property
    def active_date(self) -> str | None:
        return self.preferred_date or self.latest_date


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


def _safe_json_dict(raw_text: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(raw_text)
    except Exception:
        return None
    return parsed if isinstance(parsed, dict) else None


def _normalize_lookup_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _extract_iso_date(value: str) -> str | None:
    match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", value)
    return match.group(1) if match else None


def _extract_time(value: str) -> str | None:
    match = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", value)
    if not match:
        return None
    return f"{int(match.group(1)):02d}:{match.group(2)}"


def _extract_id_hint(value: str, label: str) -> int | None:
    match = re.search(rf"\[My {label} is (\d+)\]", value)
    return int(match.group(1)) if match else None


def _message_mentions_alternatives(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in _ALT_REQUEST_MARKERS)


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

    async def _load_tool_context(
        self,
        session_id: str,
        role: str,
        user_id: int | None,
        current_message: str,
    ) -> AgentContext:
        context = AgentContext(
            role=role,
            user_id=user_id,
            preferred_date=_extract_iso_date(current_message),
            preferred_time=_extract_time(current_message),
            wants_alternatives=_message_mentions_alternatives(current_message),
        )

        hinted_doctor_id = _extract_id_hint(current_message, "doctor_id")
        if hinted_doctor_id is not None:
            context.explicit_doctor_id = hinted_doctor_id

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Conversation)
                .where(Conversation.session_id == session_id)
                .where(Conversation.role == "tool")
                .order_by(Conversation.timestamp.desc())
                .limit(10)
            )
            tool_rows = result.scalars().all()
            tool_rows.reverse()

            for row in tool_rows:
                tool_meta = _safe_json_dict(row.tool_calls or "{}")
                if tool_meta is None:
                    try:
                        parsed_meta = json.loads(row.tool_calls or "[]")
                    except Exception:
                        parsed_meta = []
                else:
                    parsed_meta = tool_meta

                if isinstance(parsed_meta, dict):
                    parsed_meta = [parsed_meta]
                tool_name = parsed_meta[0].get("name") if parsed_meta else None
                payload = _safe_json_dict(row.content)
                if not tool_name or payload is None:
                    continue
                self._update_context_from_tool_result(context, tool_name, payload)

            if context.explicit_doctor_id is not None and not context.explicit_doctor_name:
                doctor = await db.get(Doctor, context.explicit_doctor_id)
                if doctor:
                    context.explicit_doctor_name = doctor.name

            normalized_message = _normalize_lookup_text(current_message)
            doctor_rows = (await db.execute(select(Doctor.id, Doctor.name))).all()
            matches: list[tuple[int, str]] = []
            for doctor_id, doctor_name in doctor_rows:
                if _normalize_lookup_text(doctor_name) in normalized_message:
                    matches.append((doctor_id, doctor_name))

            if matches:
                matches.sort(key=lambda item: len(item[1]), reverse=True)
                context.explicit_doctor_id, context.explicit_doctor_name = matches[0]

        return context

    def _build_context_note(self, context: AgentContext) -> str | None:
        notes: list[str] = []
        if context.role == "patient" and context.user_id is not None:
            notes.append(f"Authenticated patient_id={context.user_id}.")
        if context.role == "doctor" and context.user_id is not None:
            notes.append(f"Authenticated doctor_id={context.user_id}.")
        if context.active_doctor_id is not None:
            label = context.active_doctor_name or "current doctor"
            notes.append(f"Current doctor context: {label} (doctor_id={context.active_doctor_id}).")
        if context.active_date:
            notes.append(f"Current appointment date context: {context.active_date}.")
        if context.preferred_time:
            notes.append(f"Preferred appointment time from the latest user message: {context.preferred_time}.")
        if context.latest_available_slots:
            notes.append(
                "Most recent available slots: "
                + ", ".join(context.latest_available_slots[:8])
                + "."
            )
        if context.wants_alternatives:
            notes.append("The user explicitly wants alternative slots if the requested one is unavailable.")
        if not notes:
            return None
        return "Structured conversation context:\n" + "\n".join(f"- {note}" for note in notes)

    def _apply_tool_context(self, fn_name: str, fn_args: dict[str, Any], context: AgentContext) -> dict[str, Any]:
        args = dict(fn_args)

        if context.role == "doctor" and context.user_id is not None:
            if fn_name in {"query_appointments_stats", "send_doctor_notification"}:
                args["doctor_id"] = context.user_id

        if context.role == "patient":
            if context.user_id is not None and fn_name == "book_appointment":
                args["patient_id"] = context.user_id

            active_doctor_id = context.active_doctor_id
            active_doctor_name = context.active_doctor_name
            active_date = context.active_date

            if fn_name == "check_doctor_availability":
                if active_doctor_name and not args.get("doctor_name"):
                    args["doctor_name"] = active_doctor_name
                if active_doctor_id is not None:
                    args["doctor_id"] = active_doctor_id
                if active_date and not args.get("date"):
                    args["date"] = active_date

            if fn_name == "book_appointment":
                if active_doctor_id is not None:
                    args["doctor_id"] = active_doctor_id
                if active_date and context.preferred_time:
                    desired_datetime = f"{active_date}T{context.preferred_time}:00"
                    raw_datetime = args.get("datetime")
                    if not raw_datetime:
                        args["datetime"] = desired_datetime
                    else:
                        try:
                            parsed_datetime = datetime.fromisoformat(raw_datetime)
                        except ValueError:
                            args["datetime"] = desired_datetime
                        else:
                            if (
                                parsed_datetime.strftime("%Y-%m-%d") != active_date
                                or parsed_datetime.strftime("%H:%M") != context.preferred_time
                            ):
                                args["datetime"] = desired_datetime

            if fn_name == "auto_reschedule":
                if active_doctor_id is not None:
                    args["doctor_id"] = active_doctor_id
                if active_date and not args.get("preferred_date"):
                    args["preferred_date"] = active_date

        return args

    def _update_context_from_tool_result(
        self,
        context: AgentContext,
        fn_name: str,
        payload: dict[str, Any],
    ) -> None:
        if payload.get("doctor_id") is not None:
            try:
                context.latest_doctor_id = int(payload["doctor_id"])
            except (TypeError, ValueError):
                pass
        if payload.get("doctor_name"):
            context.latest_doctor_name = payload["doctor_name"]
        if payload.get("date"):
            context.latest_date = payload["date"]
        if fn_name == "check_doctor_availability":
            slots = payload.get("available_slots")
            if isinstance(slots, list):
                context.latest_available_slots = [
                    slot.get("start")
                    for slot in slots
                    if isinstance(slot, dict) and slot.get("start")
                ]
        elif fn_name == "book_appointment":
            context.latest_booking = payload
            start_time = payload.get("start_time")
            if isinstance(start_time, str):
                context.latest_date = start_time.split("T", 1)[0]

    async def _force_auto_reschedule_if_needed(
        self,
        *,
        mcp_session: ClientSession,
        session_id: str,
        user_id: int | None,
        context: AgentContext,
        source_tool_name: str,
        source_payload: dict[str, Any] | None,
        tools_called: list[str],
        messages: list[dict[str, Any]],
        already_forced: bool,
    ) -> bool:
        if already_forced or context.role != "patient" or not context.wants_alternatives:
            return False
        if context.active_doctor_id is None or context.active_date is None:
            return False

        should_force = False
        if source_tool_name == "check_doctor_availability" and source_payload is not None:
            if context.preferred_time:
                available_slots = {
                    slot.get("start")
                    for slot in source_payload.get("available_slots", [])
                    if isinstance(slot, dict) and slot.get("start")
                }
                should_force = context.preferred_time not in available_slots
        elif source_tool_name == "book_appointment" and source_payload is not None:
            error_text = str(source_payload.get("error", "")).lower()
            should_force = "already booked" in error_text or "auto_reschedule" in error_text

        if not should_force:
            return False

        forced_args = {
            "doctor_id": context.active_doctor_id,
            "preferred_date": context.active_date,
        }
        forced_result = await mcp_session.call_tool("auto_reschedule", forced_args)
        result_text = (
            forced_result.content[0].text
            if forced_result.content and hasattr(forced_result.content[0], "text")
            else "{}"
        )
        tools_called.append("auto_reschedule")
        payload = _safe_json_dict(result_text)
        if payload:
            self._update_context_from_tool_result(context, "auto_reschedule", payload)

        messages.append({
            "role": "tool",
            "tool_call_id": "forced-auto-reschedule",
            "name": "auto_reschedule",
            "content": result_text,
        })
        await self._save_message(
            session_id,
            user_id,
            "tool",
            result_text,
            tool_calls=[{"name": "auto_reschedule", "args": forced_args}],
        )
        return True

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
        context = await self._load_tool_context(session_id, role, user_id, user_message)
        await self._save_message(session_id, user_id, "user", user_message)

        system_prompt = _system_doctor() if role == "doctor" else _system_patient()
        messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]
        context_note = self._build_context_note(context)
        if context_note:
            messages.append({"role": "system", "content": context_note})
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        tools_called: list[str] = []
        appointments_affected: list[int] = []
        forced_auto_reschedule = False

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
                                saved_args: dict[str, Any] | None

                                if fn_args is not None:
                                    fn_args = self._apply_tool_context(fn_name, fn_args, context)
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

                                parsed_payload = _safe_json_dict(result_text)
                                if parsed_payload:
                                    self._update_context_from_tool_result(context, fn_name, parsed_payload)
                                    if "appointment_id" in parsed_payload:
                                        appointments_affected.append(parsed_payload["appointment_id"])

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

                                if (
                                    await self._force_auto_reschedule_if_needed(
                                        mcp_session=mcp_session,
                                        session_id=session_id,
                                        user_id=user_id,
                                        context=context,
                                        source_tool_name=fn_name,
                                        source_payload=parsed_payload,
                                        tools_called=tools_called,
                                        messages=messages,
                                        already_forced=forced_auto_reschedule,
                                    )
                                ):
                                    forced_auto_reschedule = True

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
