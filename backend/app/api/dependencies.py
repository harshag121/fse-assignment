"""FastAPI dependencies shared across routes."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import get_db
from app.core.security import get_current_user, get_current_user_optional

# Re-export so route files only import from here
__all__ = ["get_db", "get_current_user", "get_current_user_optional", "AsyncSession", "Depends"]
