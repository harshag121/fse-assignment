# Smart Doctor Appointment & Reporting Assistant (MCP)

A full-stack agentic AI application built on the **Model Context Protocol (MCP)** — Anthropic's open standard for connecting AI applications to external tools and data sources. Patients book appointments through natural language; doctors query statistics and receive reports via Slack.

---

## Proper MCP Architecture

This application implements a **true MCP client–server separation** across two independent processes:

```
┌─────────────────────────────────────────────────────────────────┐
│                      Docker Network                              │
│                                                                  │
│  ┌──────────────────┐   MCP protocol (SSE)   ┌───────────────┐  │
│  │                  │  ──────────────────────►│               │  │
│  │  FastAPI Backend │   GET  /sse             │  MCP Server   │  │
│  │  (port 8000)     │   POST /messages/       │  (port 8001)  │  │
│  │                  │◄────────────────────────│               │  │
│  │  MCP *Client*    │   tool results via SSE  │  MCP *Server* │  │
│  └──────────────────┘                         └───────────────┘  │
│          ▲                                            │           │
│          │ REST/JSON                                 │ SQL       │
│          │                                           ▼           │
│  ┌───────────────┐                          ┌────────────────┐   │
│  │ React / Node  │                          │  PostgreSQL 15 │   │
│  │  (port 3000)  │                          │  (port 5432)   │   │
│  └───────────────┘                          └────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### How the MCP protocol is used

**MCP Server** (`backend/mcp_server_main.py`) — standalone process on port 8001:
- Exposes 6 tools, 2 resource URIs, and 2 prompts via the MCP SSE transport
- Any MCP-compatible client can connect to it independently
- Registers tools with `@server.list_tools()` and `@server.call_tool()`

**MCP Client** (`backend/app/services/llm_service.py`) — lives inside the FastAPI process:
- Opens a real SSE connection to the MCP server at `http://mcp-server:8001/sse`
- Calls `session.list_tools()` — **dynamic discovery** at runtime, zero hardcoded schemas
- Passes tools to the LLM (Groq) in OpenAI function-calling format
- When the LLM requests a tool, calls `session.call_tool(name, args)` — **protocol-based invocation**, no direct Python function calls
- One MCP session is held open for the entire agentic loop per chat turn

```python
# llm_service.py — the key pattern
async with sse_client(settings.MCP_SERVER_URL) as (read, write):
    async with ClientSession(read, write) as mcp_session:

        await mcp_session.initialize()                    # MCP handshake

        tools = await mcp_session.list_tools()            # dynamic discovery
        openai_tools = [mcp_tool_to_openai(t) for t in tools.tools]

        # ... LLM agentic loop ...
        result = await mcp_session.call_tool(name, args)  # protocol invocation
```

### What was wrong before (and how it's fixed)

The previous version had the MCP server running but the LLM service completely bypassed it — it hardcoded tool schemas in a Python list and called tool functions directly as Python imports. **No MCP protocol was used.** The fix:

| Before (broken) | After (correct) |
|---|---|
| `OPENAI_TOOLS = [...]` hardcoded in llm_service.py | `session.list_tools()` — discovered from server at runtime |
| `handler = TOOL_HANDLERS[name]; await handler(**args)` | `session.call_tool(name, args)` — invoked through SSE protocol |
| MCP server mounted inside FastAPI (`/mcp/sse`) | MCP server runs as a **separate process** on port 8001 |
| LLM service never connects to MCP server | LLM service connects via `sse_client` + `ClientSession` |

---

## Project Structure

```
doctor-appointment-mcp/
├── backend/
│   ├── mcp_server_main.py          ← Standalone MCP SERVER (port 8001)
│   ├── app/
│   │   ├── main.py                 ← FastAPI app — pure REST API + MCP CLIENT
│   │   ├── mcp_server/
│   │   │   ├── tools.py            ← 6 tool handlers (called by MCP server)
│   │   │   ├── resources.py        ← doctors:// + appointments:// URIs
│   │   │   └── prompts.py          ← Booking + report system prompts
│   │   ├── api/
│   │   │   ├── routes.py           ← REST endpoints (auth, chat, reports …)
│   │   │   └── dependencies.py
│   │   ├── services/
│   │   │   ├── llm_service.py      ← MCP CLIENT — sse_client + ClientSession
│   │   │   ├── calendar_service.py ← Google Calendar integration
│   │   │   ├── email_service.py    ← Gmail SMTP
│   │   │   └── notification_service.py ← Slack notifications
│   │   ├── models/
│   │   │   ├── database.py         ← SQLAlchemy async models
│   │   │   └── schemas.py          ← Pydantic schemas
│   │   └── core/
│   │       ├── config.py           ← Settings (incl. MCP_SERVER_URL)
│   │       └── security.py         ← JWT helpers
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── LandingPage.jsx         ← Role selection (patient / doctor)
│   │   │   ├── ChatInterface.jsx       ← AI chat with tool pill indicators
│   │   │   ├── DoctorDashboard.jsx     ← Analytics charts (Recharts)
│   │   │   └── NlReportGenerator.jsx  ← Natural-language report generator
│   │   ├── contexts/AuthContext.jsx    ← JWT auth state
│   │   ├── services/api.js             ← Axios wrapper
│   │   └── App.jsx
│   └── package.json
├── docker-compose.yml              ← 4 services: db, mcp-server, backend, frontend
├── docker-compose.prod.yml
└── .env.example
```

---

## Quick Start

### Docker Compose (recommended — starts all 4 services)

```bash
# 1. Clone
git clone https://github.com/harshag121/fse-assignment
cd fse-assignment

# 2. Configure
cp .env.example .env
# Edit .env — fill in GROQ_API_KEY, GMAIL_ADDRESS, GMAIL_APP_PASSWORD, SLACK_BOT_TOKEN

# 3. Start
docker compose up --build

# Services:
#   Frontend  → http://localhost:3000
#   Backend   → http://localhost:8000
#   API docs  → http://localhost:8000/docs
#   MCP Server→ http://localhost:8001/sse   (MCP SSE endpoint)
```

### Local Development (two terminals required)

```bash
# --- Shared: start PostgreSQL ---
docker run -d \
  -e POSTGRES_USER=docuser -e POSTGRES_PASSWORD=docpass \
  -e POSTGRES_DB=docappointment -p 5432:5432 postgres:15-alpine

cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env    # fill in your keys

# Terminal 1 — MCP SERVER (must start first)
python mcp_server_main.py
# → Listening on http://localhost:8001
# → SSE endpoint: http://localhost:8001/sse

# Terminal 2 — FastAPI + MCP CLIENT
uvicorn app.main:app --reload --port 8000
# → Connects to MCP server at localhost:8001
# → REST API: http://localhost:8000
# → Swagger:  http://localhost:8000/docs

# Terminal 3 — React frontend
cd frontend && npm install && npm start
# → http://localhost:3000
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | `postgresql+asyncpg://user:pass@host/db` |
| `SECRET_KEY` | Yes | JWT signing secret |
| `GROQ_API_KEY` | Yes | Groq API key (free at console.groq.com) |
| `LLM_MODEL` | No | Default: `llama-3.3-70b-versatile` |
| `MCP_SERVER_URL` | No | Default: `http://localhost:8001/sse` (Docker: `http://mcp-server:8001/sse`) |
| `GMAIL_ADDRESS` | Optional | Gmail address for confirmation emails |
| `GMAIL_APP_PASSWORD` | Optional | Gmail app password (not your account password) |
| `GOOGLE_CREDENTIALS_JSON` | Optional | Service account JSON for Google Calendar |
| `SLACK_BOT_TOKEN` | Optional | Slack bot token for doctor notifications |
| `SLACK_DEFAULT_CHANNEL` | Optional | Slack channel ID or user ID |
| `TWILIO_ACCOUNT_SID` | Optional | Twilio SID (WhatsApp fallback) |
| `TWILIO_AUTH_TOKEN` | Optional | Twilio auth token |
| `TWILIO_WHATSAPP_FROM` | Optional | Twilio WhatsApp sender number |
| `FRONTEND_URL` | Optional | Production frontend URL (CORS) |

---

## MCP Tools Reference

All tools live in `backend/app/mcp_server/tools.py` and are **registered with the MCP server** at startup. The LLM service discovers them dynamically via `session.list_tools()` — they are never imported or called directly by the client.

| Tool | Parameters | Description |
|------|-----------|-------------|
| `check_doctor_availability` | `doctor_name`, `date` | Returns free 30-min slots for a doctor |
| `book_appointment` | `doctor_id`, `patient_id`, `datetime`, `symptoms` | Creates appointment + Google Calendar event |
| `send_email_confirmation` | `to_email`, `patient_name`, `doctor_name`, `appointment_datetime` | Sends confirmation email via Gmail |
| `query_appointments_stats` | `doctor_id`, `date_range`, `filter?` | Aggregates appointment statistics |
| `send_doctor_notification` | `doctor_id`, `message` | Sends report to doctor via Slack |
| `auto_reschedule` | `doctor_id`, `preferred_date`, `symptoms?` | Suggests alternative slots when time is taken |

### MCP Resources
- `doctors://list` — all doctors in the database
- `doctors://{id}/schedule` — a doctor's upcoming appointments
- `appointments://history?doctor_id={id}&date={date}` — historical data

### MCP Prompts
- `appointment_booking_assistant` — system prompt for patient flow
- `doctor_report_assistant` — system prompt for doctor analytics

---

## API Endpoints

```
POST   /api/auth/token                  Login → JWT
POST   /api/doctors                     Register doctor
GET    /api/doctors                     List all doctors
GET    /api/doctors/{id}                Get doctor
GET    /api/doctors/{id}/availability   Availability schedule
POST   /api/patients                    Register patient
GET    /api/patients/{id}               Get patient
POST   /api/availability                Set availability slot
GET    /api/appointments                List (filter by doctor_id / patient_id)
GET    /api/appointments/{id}           Get appointment
PATCH  /api/appointments/{id}/cancel    Cancel appointment
POST   /api/chat                        Chat with AI agent (MCP orchestrated)
GET    /api/chat/{session_id}/history   Conversation history
POST   /api/reports/generate            Doctor natural-language report

GET    /health                          Health check
GET    /docs                            Swagger UI

# Separate MCP Server process (port 8001):
GET    http://localhost:8001/sse         MCP SSE stream (client connects here)
POST   http://localhost:8001/messages/  MCP message endpoint
```

---

## Demo Users

| Role | Email | Password |
|------|-------|----------|
| Patient (Harsha) | gharshavardhan211@gmail.com | test123 |
| Dr. Ahuja (Cardiology) | ahuja@hospital.com | test123 |
| Dr. Smith (General Medicine) | smith@hospital.com | test123 |

---

## Sample Conversations

### Patient — booking flow
```
"Check Dr. Ahuja's availability for tomorrow"
"Book the 10:00 slot for a cough"
"Actually, can you suggest other times if 10AM is taken?"
```

### Doctor — analytics + reporting
```
"How many appointments did I have this week?"
"Show me all fever cases from last week"
"Send a summary report to Slack"
"How many appointments do I have tomorrow?"
```

---

## Key Design Decisions

- **True MCP architecture** — two separate processes with protocol-based communication. The LLM service is a genuine MCP client; the tool server is a genuine MCP server. No direct Python imports or function calls cross the client-server boundary.
- **Dynamic tool discovery** — `session.list_tools()` is called at the start of every chat turn. Adding or removing tools from the MCP server requires zero changes to the LLM service.
- **Single SSE session per chat turn** — one `sse_client` connection is opened and held for the full agentic loop, then closed. This ensures all tool calls in one turn share a session and avoids connection-per-tool overhead.
- **Agentic loop (max 10 rounds)** — the LLM picks tools until it has enough data to reply, supporting multi-step flows (check availability → book → send email) automatically.
- **Session memory** — last 10 messages per session loaded from PostgreSQL for multi-turn context.
- **Graceful degradation** — Calendar / Email / Slack integrations are optional; bookings still succeed if not configured.
