from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Doctor Appointment MCP"
    DEBUG: bool = False
    SECRET_KEY: str = "change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/docappointment"

    # LLM — Groq (primary, free) or OpenAI fallback
    GROQ_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "llama-3.3-70b-versatile"

    # Google Calendar
    GOOGLE_CREDENTIALS_JSON: Optional[str] = None

    # Email (Gmail SMTP)
    GMAIL_ADDRESS: Optional[str] = None
    GMAIL_APP_PASSWORD: Optional[str] = None

    # Frontend
    FRONTEND_URL: Optional[str] = None  # e.g. https://my-app.up.railway.app

    # Notifications
    SLACK_BOT_TOKEN: Optional[str] = None
    SLACK_DEFAULT_CHANNEL: str = "#doctor-reports"
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_WHATSAPP_FROM: Optional[str] = None  # e.g. whatsapp:+14155238886

    # MCP
    MCP_SERVER_NAME: str = "doctor-appointment-server"
    MCP_SERVER_VERSION: str = "1.0.0"
    # URL of the standalone MCP server (port 8001).
    # Override to http://mcp-server:8001/sse when running inside Docker.
    MCP_SERVER_URL: str = "http://localhost:8001/sse"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
