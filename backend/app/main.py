"""
WebPilot AI – FastAPI Application Factory
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.core.database import engine, Base
from app.core.logging import setup_logging
from app.api import auth, tasks, browser, reports, analytics, settings as settings_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    setup_logging()
    
    # Ensure storage directories exist
    for directory in [
        settings.SCREENSHOTS_DIR,
        settings.DOWNLOADS_DIR,
        settings.REPORTS_DIR,
        settings.LOGS_DIR,
    ]:
        os.makedirs(directory, exist_ok=True)
    
    from loguru import logger
    logger.info(f"CORS Allowed Origins: {settings.ALLOWED_ORIGINS} (Type: {type(settings.ALLOWED_ORIGINS)})")
    yield
    
    # Cleanup on shutdown
    await engine.dispose()


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    application = FastAPI(
        title="WebPilot AI",
        description="Autonomous Browser AI Agent API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    
    # ─── Middleware ──────────────────────────────────────────
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # ─── Static File Serving ─────────────────────────────────
    os.makedirs(settings.SCREENSHOTS_DIR, exist_ok=True)
    os.makedirs(settings.DOWNLOADS_DIR, exist_ok=True)
    os.makedirs(settings.REPORTS_DIR, exist_ok=True)
    
    application.mount(
        "/screenshots",
        StaticFiles(directory=settings.SCREENSHOTS_DIR),
        name="screenshots",
    )
    application.mount(
        "/downloads",
        StaticFiles(directory=settings.DOWNLOADS_DIR),
        name="downloads",
    )
    application.mount(
        "/reports-files",
        StaticFiles(directory=settings.REPORTS_DIR),
        name="reports_files",
    )
    
    # ─── API Routers ─────────────────────────────────────────
    application.include_router(auth.router, prefix="/auth", tags=["Authentication"])
    application.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
    application.include_router(browser.router, prefix="/browser", tags=["Browser"])
    application.include_router(reports.router, prefix="/reports", tags=["Reports"])
    application.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
    application.include_router(settings_router.router, prefix="/settings", tags=["Settings"])
    
    @application.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "healthy", "service": "WebPilot AI"}
    
    return application


app = create_application()
