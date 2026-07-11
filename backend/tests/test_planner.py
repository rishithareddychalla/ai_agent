"""
Unit tests for TaskPlanner
"""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from app.agent.planner.task_planner import TaskPlanner
from app.agent.planner.schemas import ExecutionPlan, PlannerRequest, ActionType


@pytest.fixture
def planner():
    """Create a TaskPlanner with mocked AI."""
    with patch("app.agent.planner.task_planner.genai"):
        p = TaskPlanner()
        return p


def test_fallback_plan_no_api_key():
    """Test that planner returns fallback plan when no API key is set."""
    with patch("app.agent.planner.task_planner.settings") as mock_settings:
        mock_settings.AI_PROVIDER = "gemini"
        mock_settings.GEMINI_API_KEY = ""
        mock_settings.OPENAI_API_KEY = ""
        
        planner = TaskPlanner()
        plan = planner._fallback_plan("search for Python tutorials")
        
        assert isinstance(plan, ExecutionPlan)
        assert len(plan.steps) > 0
        assert plan.steps[0].action == ActionType.NAVIGATE


@pytest.mark.asyncio
async def test_plan_contains_required_fields():
    """Test that generated plans have all required fields."""
    with patch("app.agent.planner.task_planner.settings") as mock_settings:
        mock_settings.AI_PROVIDER = "gemini"
        mock_settings.GEMINI_API_KEY = ""
        mock_settings.OPENAI_API_KEY = ""
        
        planner = TaskPlanner()
        request = PlannerRequest(prompt="Find iPhone 16 prices on Amazon")
        plan = await planner.generate_plan(request)
        
        assert plan.task_understanding
        assert plan.goal
        assert len(plan.steps) > 0
        
        for step in plan.steps:
            assert step.index >= 0
            assert step.action
            assert step.description


@pytest.mark.asyncio
async def test_gemini_plan_parsing():
    """Test that Gemini response is correctly parsed into ExecutionPlan."""
    mock_response_text = json.dumps({
        "task_understanding": "User wants iPhone 16 prices from Amazon",
        "goal": "Find and compare iPhone 16 prices",
        "approach": "Search Amazon directly",
        "risk_level": "low",
        "estimated_duration_ms": 30000,
        "notes": None,
        "steps": [
            {
                "index": 0,
                "action": "navigate",
                "description": "Go to Amazon",
                "url": "https://www.amazon.com",
                "expected_result": "Amazon homepage",
                "is_optional": False,
                "depends_on": [],
            },
            {
                "index": 1,
                "action": "search",
                "description": "Search for iPhone 16",
                "query": "iPhone 16",
                "is_optional": False,
            },
        ]
    })
    
    mock_model = MagicMock()
    mock_model.generate_content.return_value = MagicMock(text=mock_response_text)
    
    with patch("app.agent.planner.task_planner.genai") as mock_genai:
        mock_genai.configure = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        import app.agent.planner.task_planner as planner_module
        planner_module.settings = MagicMock()
        planner_module.settings.AI_PROVIDER = "gemini"
        planner_module.settings.GEMINI_API_KEY = "test-key"
        planner_module.settings.GEMINI_MODEL = "gemini-1.5-pro"
        
        planner = TaskPlanner()
        request = PlannerRequest(prompt="iPhone 16 prices on Amazon")
        plan = await planner._plan_with_gemini(request)
        
        assert len(plan.steps) == 2
        assert plan.steps[0].action == ActionType.NAVIGATE
        assert plan.steps[1].action == ActionType.SEARCH
