"""
Unit tests for RecoveryEngine
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.agent.recovery.recovery_engine import RecoveryEngine
from app.agent.planner.schemas import AgentStep, ActionType


@pytest.mark.asyncio
async def test_recovery_attempts():
    mock_browser = MagicMock()
    mock_browser.page = MagicMock()
    mock_browser.smooth_scroll = AsyncMock()
    
    mock_dom = MagicMock()
    mock_dom.wait_for_navigation_complete = AsyncMock()
    
    mock_planner = MagicMock()
    mock_planner.get_recovery_action = AsyncMock(return_value={
        "strategy": "retry",
        "description": "AI retry recommendation",
        "wait_before_ms": 100
    })
    
    recovery = RecoveryEngine(
        browser=mock_browser,
        dom=mock_dom,
        planner=mock_planner,
        max_retries=3
    )
    
    step = AgentStep(
        index=0,
        action=ActionType.CLICK,
        description="Click test button"
    )
    
    # Mock executor
    mock_executor = MagicMock()
    # First execution fails, second fails, third succeeds
    mock_result_fail = MagicMock()
    mock_result_fail.success = False
    mock_result_fail.error = "Element not found"
    
    mock_result_success = MagicMock()
    mock_result_success.success = True
    
    # Configure executor.execute_step mock return values
    mock_executor.execute_step = AsyncMock()
    mock_executor.execute_step.side_effect = [mock_result_fail, mock_result_success]
    
    # Attempt recovery (Strategy 1: Wait and retry)
    recovered = await recovery.attempt_recovery(step, "Element not found", mock_executor)
    
    assert recovered is True
    assert mock_executor.execute_step.call_count == 2
    mock_browser.smooth_scroll.assert_not_called()


@pytest.mark.asyncio
async def test_recovery_scroll_retry():
    mock_browser = MagicMock()
    mock_browser.page = MagicMock()
    mock_browser.smooth_scroll = AsyncMock()
    
    mock_dom = MagicMock()
    
    recovery = RecoveryEngine(
        browser=mock_browser,
        dom=mock_dom,
        max_retries=3
    )
    
    step = AgentStep(
        index=0,
        action=ActionType.CLICK,
        description="Click scroll button"
    )
    
    mock_executor = MagicMock()
    mock_result_fail = MagicMock()
    mock_result_fail.success = False
    mock_result_fail.error = "Element not clickable"
    
    mock_result_success = MagicMock()
    mock_result_success.success = True
    
    mock_executor.execute_step = AsyncMock()
    # 1st try (wait-and-retry): fails
    # 2nd try (scroll-and-retry): succeeds
    mock_executor.execute_step.side_effect = [mock_result_fail, mock_result_success]
    
    # Run recovery for the first time (wait-and-retry fails, mock_executor returns fail)
    recovered_first = await recovery.attempt_recovery(step, "Element not clickable", mock_executor)
    assert recovered_first is False
    
    # Second recovery attempt (will trigger Strategy 2: Scroll and retry)
    recovered_second = await recovery.attempt_recovery(step, "Element not clickable", mock_executor)
    assert recovered_second is True
    
    mock_browser.smooth_scroll.assert_called_with("down", amount=300)


@pytest.mark.asyncio
async def test_recovery_optional_step():
    mock_browser = MagicMock()
    mock_dom = MagicMock()
    
    recovery = RecoveryEngine(
        browser=mock_browser,
        dom=mock_dom,
        max_retries=1
    )
    
    # Step is optional
    step = AgentStep(
        index=0,
        action=ActionType.CLICK,
        description="Optional click",
        is_optional=True
    )
    
    mock_executor = MagicMock()
    mock_result_fail = MagicMock()
    mock_result_fail.success = False
    mock_result_fail.error = "Failed"
    mock_executor.execute_step = AsyncMock(return_value=mock_result_fail)
    
    # Attempt recovery once – will fail the retry
    recovered = await recovery.attempt_recovery(step, "Failed", mock_executor)
    assert recovered is False
    
    # Next attempt triggers optional step skip
    recovered_skipped = await recovery.attempt_recovery(step, "Failed", mock_executor)
    assert recovered_skipped is True  # Optional step returns True to continue workflow
