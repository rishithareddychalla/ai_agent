"""
Recovery Engine – Self-healing automation that handles failures gracefully
"""

import asyncio
from typing import Optional
from loguru import logger

from app.agent.planner.schemas import AgentStep, ActionType
from app.agent.browser.browser_controller import BrowserController
from app.agent.dom.dom_analyzer import DOMAnalyzer
from app.core.config import settings


class RecoveryEngine:
    """
    Implements self-healing automation strategies.
    
    When a step fails, the recovery engine:
    1. Analyzes the failure type
    2. Tries multiple recovery strategies
    3. Optionally asks AI for suggestions
    4. Continues workflow if recovery succeeds
    5. Marks step as failed/skipped if all strategies exhausted
    """

    def __init__(
        self,
        browser: BrowserController,
        dom: DOMAnalyzer,
        planner=None,  # TaskPlanner instance for AI recovery
        max_retries: int = None,
    ):
        self.browser = browser
        self.dom = dom
        self.planner = planner
        self.max_retries = max_retries or settings.MAX_RETRY_COUNT
        self._retry_counts: dict = {}

    async def attempt_recovery(
        self,
        step: AgentStep,
        error: str,
        executor,
    ) -> bool:
        """
        Attempt to recover from a failed step.
        
        Args:
            step: The failed AgentStep
            error: Error message
            executor: PlaywrightExecutor instance to retry with
            
        Returns:
            True if recovery succeeded, False if all strategies failed
        """
        step_key = f"step_{step.index}"
        retry_count = self._retry_counts.get(step_key, 0)
        
        if retry_count >= self.max_retries:
            logger.warning(f"Max retries ({self.max_retries}) exhausted for step {step.index}")
            return False

        self._retry_counts[step_key] = retry_count + 1
        logger.info(f"Recovery attempt {retry_count + 1}/{self.max_retries} for step {step.index}")

        # ─── Recovery Strategy Chain ─────────────────────────────
        
        # Strategy 1: Wait and retry
        if retry_count == 0:
            logger.info("Recovery: Waiting 2s then retrying")
            await asyncio.sleep(2)
            result = await executor.execute_step(step)
            if result.success:
                logger.success(f"Recovery succeeded via wait-and-retry for step {step.index}")
                return True

        # Strategy 2: Scroll and retry
        if retry_count <= 1:
            logger.info("Recovery: Scrolling down and retrying")
            await self.browser.smooth_scroll("down", amount=300)
            await asyncio.sleep(1)
            result = await executor.execute_step(step)
            if result.success:
                logger.success(f"Recovery succeeded via scroll-and-retry for step {step.index}")
                return True

        # Strategy 3: Reload page and retry
        if retry_count <= 2 and self.browser.page:
            logger.info("Recovery: Reloading page and retrying")
            await self.browser.page.reload()
            await self.dom.wait_for_navigation_complete(self.browser.page)
            await asyncio.sleep(2)
            result = await executor.execute_step(step)
            if result.success:
                logger.success(f"Recovery succeeded via page-reload for step {step.index}")
                return True

        # Strategy 4: AI-guided recovery (if planner is available)
        if self.planner and retry_count <= 2:
            logger.info("Recovery: Asking AI for recovery suggestion")
            context = f"URL: {self.browser.current_url}, Error: {error}"
            
            recovery = await self.planner.get_recovery_action(step, error, context)
            strategy = recovery.get("strategy", "skip")
            
            if strategy == "retry":
                wait_ms = recovery.get("wait_before_ms", 3000)
                await asyncio.sleep(wait_ms / 1000)
                result = await executor.execute_step(step)
                if result.success:
                    logger.success(f"Recovery succeeded via AI-guided retry for step {step.index}")
                    return True
            
            elif strategy == "alternative" and recovery.get("alternative_selector"):
                logger.info(f"Recovery: Trying alternative selector: {recovery['alternative_selector']}")
                try:
                    alt_step = step.model_copy(update={"selector": recovery["alternative_selector"]})
                    result = await executor.execute_step(alt_step)
                    if result.success:
                        logger.success("Recovery succeeded via alternative selector")
                        return True
                except Exception:
                    pass
            
            elif strategy == "skip":
                logger.warning(f"AI suggests skipping step {step.index}: {recovery.get('description', '')}")
                return step.is_optional  # Only skip if optional

        # Strategy 5: Check if step is optional and skip
        if step.is_optional:
            logger.info(f"Step {step.index} is optional – skipping after failed recovery")
            return True  # Return True to continue workflow

        logger.error(f"All recovery strategies exhausted for step {step.index}")
        return False

    async def handle_navigation_error(self, url: str) -> bool:
        """Handle navigation failures with fallback strategies."""
        # Try HTTPS if HTTP failed
        if url.startswith("http://"):
            https_url = "https://" + url[7:]
            logger.info(f"Trying HTTPS: {https_url}")
            return await self.browser.navigate(https_url)
        
        # Try adding www.
        if "//www." not in url:
            parts = url.split("//")
            if len(parts) == 2:
                www_url = f"{parts[0]}//www.{parts[1]}"
                logger.info(f"Trying with www: {www_url}")
                return await self.browser.navigate(www_url)
        
        return False

    async def handle_timeout_error(self) -> bool:
        """Handle page timeout by waiting and retrying."""
        logger.info("Handling timeout – waiting for network idle")
        if self.browser.page:
            try:
                await self.browser.page.wait_for_load_state("networkidle", timeout=10000)
                return True
            except Exception:
                return False
        return False

    def reset_retries(self, step_index: int) -> None:
        """Reset retry count for a step (useful after recovery)."""
        self._retry_counts.pop(f"step_{step_index}", None)
