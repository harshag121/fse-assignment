import unittest
from types import SimpleNamespace
from unittest import mock

from app.services.llm_service import LLMService


class _DummySSEClient:
    async def __aenter__(self):
        return ("read", "write")

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _DummyMCPSession:
    def __init__(self, *_args, **_kwargs):
        self.called_tools = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def initialize(self):
        return None

    async def list_tools(self):
        tool = SimpleNamespace(
            name="book_appointment",
            description="Book",
            inputSchema={"type": "object"},
        )
        return SimpleNamespace(tools=[tool])

    async def call_tool(self, name, args):
        self.called_tools.append((name, args))
        return SimpleNamespace(content=[SimpleNamespace(text='{"appointment_id": 99}')])


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


if __name__ == "__main__":
    unittest.main()
