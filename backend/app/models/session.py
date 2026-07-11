"""
BrowserSession, Screenshot, Report, ExecutionLog, Download Models
"""

import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Enum, DateTime, JSON, Text, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base


class BrowserStatus(str, enum.Enum):
    IDLE = "idle"
    NAVIGATING = "navigating"
    INTERACTING = "interacting"
    WAITING = "waiting"
    CLOSED = "closed"
    ERROR = "error"


class BrowserSession(Base):
    """Tracks a browser session for a task."""
    __tablename__ = "browser_sessions"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    
    browser_type = Column(String(50), default="chromium")
    status = Column(Enum(BrowserStatus), default=BrowserStatus.IDLE)
    current_url = Column(Text, nullable=True)
    current_title = Column(String(500), nullable=True)
    headless = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    closed_at = Column(DateTime(timezone=True), nullable=True)

    task = relationship("Task", back_populates="browser_sessions")


class Screenshot(Base):
    """Stores references to browser screenshots."""
    __tablename__ = "screenshots"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    
    step_index = Column(Integer, nullable=True)
    step_description = Column(Text, nullable=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    url = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    task = relationship("Task", back_populates="screenshots")


class ReportFormat(str, enum.Enum):
    PDF = "pdf"
    CSV = "csv"
    JSON = "json"


class Report(Base):
    """Generated reports for tasks."""
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    
    format = Column(Enum(ReportFormat), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    file_size = Column(Integer, nullable=True)  # bytes
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    task = relationship("Task", back_populates="reports")


class LogLevel(str, enum.Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class ExecutionLog(Base):
    """Detailed execution logs for each step."""
    __tablename__ = "execution_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    
    step_index = Column(Integer, nullable=True)
    level = Column(Enum(LogLevel), default=LogLevel.INFO)
    action = Column(String(255), nullable=True)
    message = Column(Text, nullable=False)
    url = Column(Text, nullable=True)
    selector = Column(Text, nullable=True)
    success = Column(Boolean, default=True)
    error_detail = Column(Text, nullable=True)
    duration_ms = Column(Float, nullable=True)
    screenshot_id = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    task = relationship("Task", back_populates="logs")


class Download(Base):
    """Files downloaded during task execution."""
    __tablename__ = "downloads"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    
    filename = Column(String(500), nullable=False)
    file_path = Column(Text, nullable=False)
    source_url = Column(Text, nullable=True)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(200), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    task = relationship("Task", back_populates="downloads")
