"""
Settings API – User preference management
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()


class UserSettings(BaseModel):
    browser: Optional[str] = "chromium"
    theme: Optional[str] = "dark"
    ai_provider: Optional[str] = "gemini"
    download_folder: Optional[str] = "/downloads"
    default_timeout: Optional[int] = 30000
    screenshot_frequency: Optional[int] = 500
    retry_count: Optional[int] = 3
    headless: Optional[bool] = True


@router.get("", response_model=UserSettings)
async def get_settings(current_user: User = Depends(get_current_user)):
    """Get current user's settings."""
    return current_user.settings or {}


@router.put("")
async def update_settings(
    settings_update: UserSettings,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update user settings."""
    current_settings = current_user.settings or {}
    updated = {**current_settings, **settings_update.model_dump(exclude_none=True)}
    current_user.settings = updated
    await db.commit()
    return {"status": "ok", "settings": updated}
