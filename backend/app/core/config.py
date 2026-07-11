"""
Application Configuration – Pydantic BaseSettings
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import os


class Settings(BaseSettings):
    # ─── App ────────────────────────────────────────────────
    APP_NAME: str = "WebPilot AI"
    APP_ENV: str = "development"
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # ─── Database ────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://webpilot:webpilot_pass@localhost:5432/webpilot_db"

    # ─── Redis ───────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ─── AI Provider ─────────────────────────────────────────
    AI_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"

    # ─── Browser ─────────────────────────────────────────────
    BROWSER_TYPE: str = "chromium"
    BROWSER_HEADLESS: bool = True
    BROWSER_SCREENSHOT_INTERVAL: int = 500
    BROWSER_DEFAULT_TIMEOUT: int = 30000
    BROWSER_SLOW_MO: int = 50

    # ─── Storage ─────────────────────────────────────────────
    SCREENSHOTS_DIR: str = "/app/screenshots"
    DOWNLOADS_DIR: str = "/app/downloads"
    REPORTS_DIR: str = "/app/reports"
    LOGS_DIR: str = "/app/logs"

    # ─── CORS ────────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1",
    ]

    # ─── Recovery ────────────────────────────────────────────
    MAX_RETRY_COUNT: int = 3
    RECOVERY_TIMEOUT: int = 10000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"

    def is_production(self) -> bool:
        return self.APP_ENV == "production"


settings = Settings()
