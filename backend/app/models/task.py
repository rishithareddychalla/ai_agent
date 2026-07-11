"""
Task Model – Represents an AI agent task execution
"""

import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Enum, DateTime, JSON, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.core.database import Base


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    PLANNING = "planning"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Task input / output
    prompt = Column(Text, nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, index=True)
    
    # AI Planning
    execution_plan = Column(JSON, nullable=True)   # List of AgentStep dicts
    current_step = Column(Integer, default=0)
    total_steps = Column(Integer, default=0)
    
    # Results
    result_summary = Column(Text, nullable=True)
    extracted_data = Column(JSON, nullable=True)
    recommendation = Column(Text, nullable=True)
    
    # Metrics
    execution_time_ms = Column(Float, nullable=True)
    success_rate = Column(Float, nullable=True)
    websites_visited = Column(JSON, default=list)  # List of domains
    
    # Error info
    error_message = Column(Text, nullable=True)
    error_count = Column(Integer, default=0)
    
    # Browser config snapshot
    browser_config = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="tasks")
    browser_sessions = relationship("BrowserSession", back_populates="task", cascade="all, delete-orphan")
    screenshots = relationship("Screenshot", back_populates="task", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="task", cascade="all, delete-orphan")
    logs = relationship("ExecutionLog", back_populates="task", cascade="all, delete-orphan", order_by="ExecutionLog.created_at")
    downloads = relationship("Download", back_populates="task", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Task id={self.id} status={self.status} prompt='{self.prompt[:30]}...'>"
