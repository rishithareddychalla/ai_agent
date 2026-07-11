"""
Agent Planner Schemas – Pydantic models for execution plans
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """Types of browser actions the agent can take."""
    NAVIGATE = "navigate"
    SEARCH = "search"
    CLICK = "click"
    TYPE = "type"
    SCROLL = "scroll"
    WAIT = "wait"
    EXTRACT = "extract"
    SCREENSHOT = "screenshot"
    DOWNLOAD = "download"
    COMPARE = "compare"
    SUMMARIZE = "summarize"
    FILTER = "filter"
    HOVER = "hover"
    SELECT = "select"
    CLOSE_TAB = "close_tab"
    NEW_TAB = "new_tab"
    BACK = "back"
    REFRESH = "refresh"
    EVALUATE = "evaluate"   # Run JS in browser


class AgentStep(BaseModel):
    """A single step in the execution plan."""
    index: int = Field(..., description="Step index (0-based)")
    action: ActionType
    description: str = Field(..., description="Human-readable description of this step")
    
    # Action parameters
    url: Optional[str] = None
    query: Optional[str] = None
    selector: Optional[str] = None
    value: Optional[str] = None
    wait_ms: Optional[int] = None
    scroll_direction: Optional[str] = None  # up | down | left | right
    extract_schema: Optional[Dict[str, Any]] = None  # Expected data structure
    
    # Metadata
    expected_result: Optional[str] = None
    is_optional: bool = False
    depends_on: Optional[List[int]] = None  # Step indices this depends on
    
    # Runtime state (not from AI plan)
    status: str = "pending"  # pending | running | completed | failed | skipped
    result: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None


class ExecutionPlan(BaseModel):
    """Full execution plan returned by the AI planner."""
    task_understanding: str = Field(..., description="AI's understanding of the user's request")
    goal: str = Field(..., description="Primary goal to achieve")
    approach: str = Field(..., description="High-level approach description")
    steps: List[AgentStep]
    estimated_duration_ms: Optional[int] = None
    risk_level: str = "low"  # low | medium | high
    notes: Optional[str] = None


class PlannerRequest(BaseModel):
    """Input to the task planner."""
    prompt: str
    user_settings: Optional[Dict[str, Any]] = None
    context: Optional[str] = None


class RecoveryAction(BaseModel):
    """AI-suggested recovery action when a step fails."""
    strategy: str  # retry | skip | alternative | abort
    description: str
    alternative_selector: Optional[str] = None
    alternative_action: Optional[ActionType] = None
    wait_before_ms: Optional[int] = None
