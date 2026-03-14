# Smart Doctor Appointment & Reporting Assistant with MCP

A full-stack agentic AI application that uses the **Model Context Protocol (MCP)** for dynamic tool discovery and orchestration. Patients can book appointments through natural language; doctors can query statistics and receive reports via Slack or WhatsApp.

---

## Architecture

```
React Frontend (port 3000)
       │  REST / JSON
       ▼
FastAPI Backend (port 8000)
       │
       ├── /api/*       ← REST routes (auth, doctors, patients, chat, reports)
       ├── /mcp/sse     ← MCP Server (SSE transport)
       │       ├── Tools     (check_availability, book_appointment, …)
       │       ├── Resources (doctors://*, appointments://*)
       │       └── Prompts   (booking_assistant, report_assistant)
       │
       ├── LLM Service  ← OpenAI function-calling agentic loop
       └── Services     ← Calendar, Email, Notification
               │
PostgreSQL 15
```

### MCP Client–Server–Tool pattern
- **MCP Server** (`app/mcp_server/`) exposes six tools, two resource URIs, and two prompt templates via SSE transport.
- **MCP Client** is the `LLMService` which dynamically selects and chains tools based on user intent, without hardcoded workflows.
- **Tools** are independently callable by the LLM and also importable by the REST API layer for direct invocation.

---

## Project Structure

```
doctor-appointment-mcp/
├── backend/
│   ├── app/
│   │   ├── mcp_server/
│   │   │   ├── server.py       # MCP server init + SSE mount
│   │   │   ├── tools.py        # All 6 MCP tools
│   │   │   ├── resources.py    # doctors:// + appointments:// URIs
│   │   │   └── prompts.py      # Booking + report system prompts
│   │   ├── api/
│   │   │   ├── routes.py       # FastAPI REST endpoints
│   │   │   └── dependencies.py
│   │   ├── services/
│   │   │   ├── calendar_service.py    # Google Calendar
│   │   │   ├── email_service.py       # SendGrid
│   │   │   ├── notification_service.py # Slack + Twilio WhatsApp
│   │   │   └── llm_service.py         # Agentic LLM loop
│   │   ├── models/
│   │   │   ├── database.py    # SQLAlchemy async models
│   │   │   └── schemas.py     # Pydantic request/response schemas
│   │   ├── core/
│   │   │   ├── config.py      # Pydantic settings
│   │   │   └── security.py    # JWT helpers
│   │   └── main.py            # FastAPI app factory
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatInterface.jsx        # AI chat UI
│   │   │   ├── DoctorDashboard.jsx      # Stats + report generator
│   │   │   └── AppointmentCard.jsx      # Single appointment card
│   │   ├── contexts/
│   │   │   ├── AuthContext.jsx          # JWT auth state
│   │   │   └── SessionContext.jsx       # Conversation session
│   │   ├── services/api.js              # Axios API wrapper
│   │   ├── App.jsx                      # Routing + layout
│   │   └── index.js
│   └── package.json
├── docker-compose.yml
└── .env.example
```

---

## Quick Start

### Option A — Docker Compose (recommended)

```bash
# 1. Clone and enter the project
cd doctor-appointment-mcp

# 2. Configure environment variables
cp .env.example .env
# Edit .env with your API keys

# 3. Start everything
docker compose up --build

# Frontend → http://localhost:3000
# Backend  → http://localhost:8000
# API docs → http://localhost:8000/docs
# MCP SSE  → http://localhost:8000/mcp/sse
```

### Option B — Local development

#### Backend
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env (from project root .env.example)
cp ../.env.example .env
# Edit .env with your values

# Start PostgreSQL (ensure it's running locally or via Docker)
docker run -d -e POSTGRES_USER=docuser -e POSTGRES_PASSWORD=docpass \
  -e POSTGRES_DB=docappointment -p 5432:5432 postgres:15-alpine

# Run the server
uvicorn app.main:app --reload --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm start
# → http://localhost:3000
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL async URL |
| `SECRET_KEY` | Yes | JWT signing secret |
| `OPENAI_API_KEY` | Yes | OpenAI API key for LLM orchestration |
| `LLM_MODEL` | No | Default: `gpt-4o` |
| `GOOGLE_CREDENTIALS_JSON` | Optional | Google service account JSON (Calendar) |
| `SENDGRID_API_KEY` | Optional | SendGrid key for email confirmations |
| `FROM_EMAIL` | Optional | Sender email address |
| `SLACK_BOT_TOKEN` | Optional | Slack bot token for doctor notifications |
| `SLACK_DEFAULT_CHANNEL` | Optional | Default Slack channel |
| `TWILIO_ACCOUNT_SID` | Optional | Twilio SID (WhatsApp fallback) |
| `TWILIO_AUTH_TOKEN` | Optional | Twilio auth token |
| `TWILIO_WHATSAPP_FROM` | Optional | Twilio WhatsApp sender number |

---

## MCP Tools Reference

| Tool | Description |
|------|-------------|
| `check_doctor_availability` | Returns free slots for a doctor on a date |
| `book_appointment` | Creates appointment + Google Calendar event |
| `send_email_confirmation` | Sends HTML confirmation email via SendGrid |
| `query_appointments_stats` | Aggregates appointment statistics for reports |
| `send_doctor_notification` | Sends report via Slack or WhatsApp |
| `auto_reschedule` | Suggests alternative slots on conflict |

### MCP Resources
- `doctors://list` — all doctors
- `doctors://{id}/schedule` — a doctor's upcoming appointments
- `appointments://history?doctor_id={id}&date={date}` — historical data

### MCP Prompts
- `appointment_booking_assistant` — system prompt for patient flow
- `doctor_report_assistant` — system prompt for doctor analytics

---

## API Endpoints

```
POST   /api/auth/token              Login (returns JWT)
POST   /api/doctors                 Register doctor
GET    /api/doctors                 List all doctors
GET    /api/doctors/{id}            Get doctor
GET    /api/doctors/{id}/availability  Doctor availability schedule
POST   /api/patients                Register patient
GET    /api/patients/{id}           Get patient
POST   /api/availability            Set doctor availability slot
GET    /api/appointments            List appointments (filter by doctor/patient)
GET    /api/appointments/{id}       Get appointment
PATCH  /api/appointments/{id}/cancel  Cancel appointment
POST   /api/chat                    Chat with AI agent
GET    /api/chat/{session_id}/history  Get conversation history
POST   /api/reports/generate        Doctor natural-language report

GET    /mcp/sse                     MCP server (SSE)
POST   /mcp/messages/               MCP messages endpoint
GET    /health                      Health check
GET    /docs                        Swagger UI
```

---

## Sample Prompts

### Patient flow
```
"I want to book an appointment with Dr. Ahuja tomorrow at 3PM"
"Check Dr. Smith's availability for next Monday morning"
"Book any available slot with Dr. Ahuja this week for fever consultation"
```

### Doctor flow
```
"How many patients visited yesterday?"
"How many appointments do I have today and tomorrow?"
"How many patients came in with fever last week?"
"Send me a summary of this week's appointments"
```

### Multi-turn context
```
Turn 1: "Check Dr. Ahuja's availability for Friday afternoon"
Turn 2: "Book the 3PM slot"          ← agent remembers doctor + date
Turn 3: "Actually, reschedule to 4PM" ← agent remembers the booking
```

---

## Seeding Demo Data

After the server is running, use the Swagger UI at `/docs` to:

1. `POST /api/doctors` — create a doctor (e.g. Dr. Ahuja, Cardiology)
2. `POST /api/availability` — add doctor availability slots (day_of_week 0-6, HH:MM times)
3. `POST /api/patients` — create a patient
4. Use the chat interface to test natural language booking

---

## Key Design Decisions

- **Agentic loop** (max 10 rounds) — the LLM keeps calling tools until it has enough data to reply, without hardcoded workflows.
- **Session-based memory** — last 10 messages loaded per session from PostgreSQL, giving multi-turn context.
- **MCP + REST dual interface** — tools are reachable both via MCP SSE (for external MCP clients) and directly from the REST API's LLM service.
- **Graceful degradation** — email/calendar integrations are optional; the booking still succeeds if they're not configured.
- **Slack → WhatsApp fallback** — notification service automatically falls back to Twilio WhatsApp if Slack token is absent.
