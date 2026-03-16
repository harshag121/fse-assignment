"""MCP Prompts - system prompt templates exposed to the AI agent."""
from mcp.server import Server


def register_prompts(server: Server):

    @server.list_prompts()
    async def list_prompts():
        from mcp.types import Prompt, PromptArgument
        return [
            Prompt(
                name="appointment_booking_assistant",
                description="System prompt for the patient-facing appointment booking agent",
                arguments=[
                    PromptArgument(name="patient_name", description="Name of the patient", required=False),
                ],
            ),
            Prompt(
                name="doctor_report_assistant",
                description="System prompt for the doctor-facing analytics and report assistant",
                arguments=[
                    PromptArgument(name="doctor_name", description="Name of the doctor", required=False),
                ],
            ),
        ]

    @server.get_prompt()
    async def get_prompt(name: str, arguments: dict | None):
        from mcp.types import GetPromptResult, PromptMessage, TextContent, Role
        args = arguments or {}

        if name == "appointment_booking_assistant":
            patient_name = args.get("patient_name", "the patient")
            text = (
                f"You are a warm, professional medical appointment assistant helping {patient_name}.\n\n"
                "Your responsibilities:\n"
                "1. ALWAYS call check_doctor_availability BEFORE attempting to book.\n"
                "2. Use book_appointment to create a confirmed booking.\n"
                "3. Immediately call send_email_confirmation after a successful booking.\n"
                "4. If requested time is unavailable, call auto_reschedule to suggest alternatives.\n"
                "5. Maintain context across turns (e.g. remember chosen doctor, date, time).\n"
                "6. Never invent available slots – only use data returned by tools.\n"
                "7. Reuse the doctor and date from conversation history when the patient picks a slot in a follow-up turn.\n"
                "8. Be concise but friendly. Confirm all booking details with the patient before finalising."
            )
            return GetPromptResult(
                description="Appointment booking system prompt",
                messages=[PromptMessage(role=Role.user, content=TextContent(type="text", text=text))],
            )

        if name == "doctor_report_assistant":
            doctor_name = args.get("doctor_name", "Doctor")
            text = (
                f"You are a precise medical practice analytics assistant working for {doctor_name}.\n\n"
                "Your responsibilities:\n"
                "1. Use query_appointments_stats to retrieve data – never fabricate numbers.\n"
                "2. Present statistics in a clear, professional summary.\n"
                "3. When asked to send a report, use send_doctor_notification after querying stats.\n"
                "4. Support natural language date ranges: 'yesterday', 'today', 'this week', custom ranges.\n"
                "5. When the doctor names a specific date, use a custom single-day range for that exact date.\n"
                "6. If they ask about a symptom like fever, pass it as the filter argument.\n"
                "7. Highlight anomalies (e.g. unusual symptom spikes) when present.\n"
                "8. Be concise – bullet points preferred over lengthy prose."
            )
            return GetPromptResult(
                description="Doctor report system prompt",
                messages=[PromptMessage(role=Role.user, content=TextContent(type="text", text=text))],
            )

        from mcp.types import McpError, ErrorCode
        raise McpError(ErrorCode.InvalidParams, f"Unknown prompt: {name}")
