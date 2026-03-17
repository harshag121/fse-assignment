import unittest
from types import SimpleNamespace
from unittest import mock

from app.services.llm_service import AgentContext, LLMService


class _DummySSEClient:
    async def __aenter__(self):
        return ("read", "write")

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _DummyMCPSession:
    tool_payloads = {
        "book_appointment": '{"appointment_id": 99, "doctor_id": 7, "doctor_name": "Dr. Right"}',
        "query_appointments_stats": '{"doctor_id": 7, "date_range": "2026-03-18 to 2026-03-18", "total_appointments": 1, "confirmed": 1, "completed": 0, "cancelled": 0, "pending": 0, "symptom_breakdown": {"fever": 1}, "busiest_day": "2026-03-18"}',
        "check_doctor_availability": '{"doctor_id": 7, "doctor_name": "Dr. Right", "date": "2026-03-18", "available_slots": [{"start": "10:00", "end": "10:30"}]}',
        "auto_reschedule": '{"preferred_date": "2026-03-18", "suggestions": [{"date": "2026-03-18", "start": "10:00", "end": "10:30", "day": "Wednesday"}], "message": "Found 1 alternative slots."}',
    }

    def __init__(self, *_args, **_kwargs):
        self.called_tools = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def initialize(self):
        return None

    async def list_tools(self):
        tools = [
            SimpleNamespace(name="book_appointment", description="Book", inputSchema={"type": "object"}),
            SimpleNamespace(name="query_appointments_stats", description="Stats", inputSchema={"type": "object"}),
            SimpleNamespace(name="check_doctor_availability", description="Availability", inputSchema={"type": "object"}),
            SimpleNamespace(name="auto_reschedule", description="Reschedule", inputSchema={"type": "object"}),
        ]
        return SimpleNamespace(tools=tools)

    async def call_tool(self, name, args):
        self.called_tools.append((name, args))
        payload = self.tool_payloads.get(name, "{}")
        return SimpleNamespace(content=[SimpleNamespace(text=payload)])


def _tool_call(name: str, arguments: str):
    return SimpleNamespace(
        id=f"call-{name}",
        function=SimpleNamespace(name=name, arguments=arguments),
    )


def _response_with_tool_call(name: str, arguments: str):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=None,
                    tool_calls=[_tool_call(name, arguments)],
                )
            )
        ]
    )


def _response_with_text(text: str):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=text,
                    tool_calls=[],
                )
            )
        ]
    )


class LLMServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_rate_limited_primary_model_falls_back_to_8b(self):
        service = LLMService()

        async def create_completion(**kwargs):
            if kwargs["model"] == "llama-3.3-70b-versatile":
                raise RuntimeError("429 rate_limit_exceeded")
            return _response_with_text("Fallback model worked.")

        fake_openai = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create_completion)))

        with mock.patch("app.services.llm_service.settings.LLM_MODEL", "llama-3.3-70b-versatile"), \
             mock.patch("app.services.llm_service.settings.GROQ_API_KEY", "gsk_test"):
            response = await service._create_completion(
                fake_openai,
                messages=[{"role": "user", "content": "hello"}],
                tools=[],
            )

        self.assertEqual(response.choices[0].message.content, "Fallback model worked.")

    async def test_invalid_tool_json_becomes_recoverable_tool_error(self):
        service = LLMService()
        completions = mock.AsyncMock(side_effect=[
            _response_with_tool_call("book_appointment", '{"doctor_id": 1,'),
            _response_with_text("Recovered after bad tool args."),
        ])
        fake_openai = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=completions)))

        with mock.patch.object(service, "_get_openai", return_value=fake_openai), \
             mock.patch.object(service, "_load_history", new=mock.AsyncMock(return_value=[])), \
             mock.patch.object(service, "_save_message", new=mock.AsyncMock()), \
             mock.patch.object(service, "_load_tool_context", new=mock.AsyncMock(return_value=AgentContext(role="patient", user_id=1))), \
             mock.patch("app.services.llm_service.sse_client", return_value=_DummySSEClient()), \
             mock.patch("app.services.llm_service.ClientSession", _DummyMCPSession):
            result = await service.chat(
                session_id="test-session",
                user_message="Book the slot",
                role="patient",
                user_id=1,
            )

        self.assertEqual(result["reply"], "Recovered after bad tool args.")
        self.assertEqual(result["tool_calls_made"], ["book_appointment"])

    async def test_patient_booking_tool_args_are_pinned_to_context(self):
        service = LLMService()
        completions = mock.AsyncMock(side_effect=[
            _response_with_tool_call(
                "book_appointment",
                '{"doctor_id": 1, "patient_id": 999, "datetime": "2026-03-18T09:30:00"}',
            ),
            _response_with_text("Booked with the correct doctor."),
        ])
        fake_openai = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=completions)))
        session_holder = {}

        def _client_session_factory(*args, **kwargs):
            session = _DummyMCPSession(*args, **kwargs)
            session_holder["session"] = session
            return session

        context = AgentContext(
            role="patient",
            user_id=6,
            explicit_doctor_id=7,
            explicit_doctor_name="Dr. Right",
            preferred_date="2026-03-18",
            preferred_time="09:30",
        )

        with mock.patch.object(service, "_get_openai", return_value=fake_openai), \
             mock.patch.object(service, "_load_history", new=mock.AsyncMock(return_value=[])), \
             mock.patch.object(service, "_save_message", new=mock.AsyncMock()), \
             mock.patch.object(service, "_load_tool_context", new=mock.AsyncMock(return_value=context)), \
             mock.patch("app.services.llm_service.sse_client", return_value=_DummySSEClient()), \
             mock.patch("app.services.llm_service.ClientSession", _client_session_factory):
            result = await service.chat(
                session_id="patient-booking",
                user_message="Book 09:30 with Dr. Right",
                role="patient",
                user_id=6,
            )

        self.assertEqual(result["reply"], "Booked with the correct doctor.")
        self.assertEqual(session_holder["session"].called_tools[0][1]["doctor_id"], 7)
        self.assertEqual(session_holder["session"].called_tools[0][1]["patient_id"], 6)

    async def test_doctor_stats_tool_uses_authenticated_doctor_id(self):
        service = LLMService()
        completions = mock.AsyncMock(side_effect=[
            _response_with_tool_call("query_appointments_stats", '{"doctor_id": 1, "date_range": "today"}'),
            _response_with_text("Report ready."),
        ])
        fake_openai = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=completions)))
        session_holder = {}

        def _client_session_factory(*args, **kwargs):
            session = _DummyMCPSession(*args, **kwargs)
            session_holder["session"] = session
            return session

        context = AgentContext(role="doctor", user_id=7)

        with mock.patch.object(service, "_get_openai", return_value=fake_openai), \
             mock.patch.object(service, "_load_history", new=mock.AsyncMock(return_value=[])), \
             mock.patch.object(service, "_save_message", new=mock.AsyncMock()), \
             mock.patch.object(service, "_load_tool_context", new=mock.AsyncMock(return_value=context)), \
             mock.patch("app.services.llm_service.sse_client", return_value=_DummySSEClient()), \
             mock.patch("app.services.llm_service.ClientSession", _client_session_factory):
            result = await service.chat(
                session_id="doctor-report",
                user_message="How many patients visited today?",
                role="doctor",
                user_id=7,
            )

        self.assertEqual(result["reply"], "Report ready.")
        self.assertEqual(session_holder["session"].called_tools[0][1]["doctor_id"], 7)

    async def test_alternative_request_forces_auto_reschedule(self):
        service = LLMService()
        completions = mock.AsyncMock(side_effect=[
            _response_with_tool_call("check_doctor_availability", '{"doctor_name": "Dr. Right", "date": "2026-03-18"}'),
            _response_with_text("Here are the alternative slots."),
        ])
        fake_openai = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=completions)))
        session_holder = {}

        def _client_session_factory(*args, **kwargs):
            session = _DummyMCPSession(*args, **kwargs)
            session_holder["session"] = session
            return session

        context = AgentContext(
            role="patient",
            user_id=6,
            explicit_doctor_id=7,
            explicit_doctor_name="Dr. Right",
            preferred_date="2026-03-18",
            preferred_time="09:30",
            wants_alternatives=True,
        )

        with mock.patch.object(service, "_get_openai", return_value=fake_openai), \
             mock.patch.object(service, "_load_history", new=mock.AsyncMock(return_value=[])), \
             mock.patch.object(service, "_save_message", new=mock.AsyncMock()), \
             mock.patch.object(service, "_load_tool_context", new=mock.AsyncMock(return_value=context)), \
             mock.patch("app.services.llm_service.sse_client", return_value=_DummySSEClient()), \
             mock.patch("app.services.llm_service.ClientSession", _client_session_factory):
            result = await service.chat(
                session_id="auto-reschedule",
                user_message="Book 09:30, and if unavailable suggest alternatives.",
                role="patient",
                user_id=6,
            )

        self.assertEqual(result["reply"], "Here are the alternative slots.")
        self.assertEqual([name for name, _args in session_holder["session"].called_tools], [
            "check_doctor_availability",
            "auto_reschedule",
        ])
        self.assertEqual(result["tool_calls_made"], ["check_doctor_availability", "auto_reschedule"])


if __name__ == "__main__":
    unittest.main()
