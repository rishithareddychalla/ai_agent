"""
Playwright Executor – Executes individual AgentSteps using the browser
"""

import asyncio
import time
from typing import Optional, Callable, Any
from loguru import logger

from app.agent.browser.browser_controller import BrowserController
from app.agent.dom.dom_analyzer import DOMAnalyzer
from app.agent.planner.schemas import AgentStep, ActionType


class StepResult:
    """Result of executing a single step."""
    def __init__(
        self,
        success: bool,
        step_index: int,
        action: str,
        description: str,
        result: Any = None,
        error: Optional[str] = None,
        duration_ms: float = 0,
        screenshot_b64: Optional[str] = None,
        url: Optional[str] = None,
    ):
        self.success = success
        self.step_index = step_index
        self.action = action
        self.description = description
        self.result = result
        self.error = error
        self.duration_ms = duration_ms
        self.screenshot_b64 = screenshot_b64
        self.url = url

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "step_index": self.step_index,
            "action": self.action,
            "description": self.description,
            "result": self.result,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "url": self.url,
        }


class PlaywrightExecutor:
    """
    Executes individual AgentStep objects using the BrowserController.
    
    Handles:
    - Navigation
    - Search queries
    - Element clicking
    - Text typing
    - Scrolling
    - Data extraction
    - Screenshots
    - File downloads
    - JavaScript evaluation
    """

    def __init__(
        self,
        browser: BrowserController,
        dom_analyzer: DOMAnalyzer,
        on_log: Optional[Callable] = None,
    ):
        self.browser = browser
        self.dom = dom_analyzer
        self.on_log = on_log
        self._extracted_data: dict = {}

    async def execute_step(self, step: AgentStep) -> StepResult:
        """Execute a single agent step."""
        start_time = time.monotonic()
        
        await self._log(f"Executing step {step.index}: {step.description}", "info")
        
        # Detect and handle bot-detection/block pages before running the step
        await self._handle_anti_bot_pages()
        
        try:
            result = await self._dispatch(step)
            duration_ms = (time.monotonic() - start_time) * 1000
            
            # Take screenshot after key actions
            screenshot = None
            if step.action in [
                ActionType.NAVIGATE,
                ActionType.SEARCH,
                ActionType.EXTRACT,
                ActionType.COMPARE,
                ActionType.SUMMARIZE,
            ]:
                screenshot = await self.browser.take_screenshot_base64()
            
            return StepResult(
                success=True,
                step_index=step.index,
                action=step.action,
                description=step.description,
                result=result,
                duration_ms=duration_ms,
                screenshot_b64=screenshot,
                url=self.browser.current_url,
            )
        
        except Exception as e:
            duration_ms = (time.monotonic() - start_time) * 1000
            error_msg = str(e)
            await self._log(f"Step {step.index} failed: {error_msg}", "error")
            
            screenshot = await self.browser.take_screenshot_base64()
            
            return StepResult(
                success=False,
                step_index=step.index,
                action=step.action,
                description=step.description,
                error=error_msg,
                duration_ms=duration_ms,
                screenshot_b64=screenshot,
                url=self.browser.current_url,
            )

    async def _dispatch(self, step: AgentStep) -> Any:
        """Route step execution to the appropriate handler."""
        handlers = {
            ActionType.NAVIGATE: self._handle_navigate,
            ActionType.SEARCH: self._handle_search,
            ActionType.CLICK: self._handle_click,
            ActionType.TYPE: self._handle_type,
            ActionType.SCROLL: self._handle_scroll,
            ActionType.WAIT: self._handle_wait,
            ActionType.EXTRACT: self._handle_extract,
            ActionType.SCREENSHOT: self._handle_screenshot,
            ActionType.DOWNLOAD: self._handle_download,
            ActionType.COMPARE: self._handle_compare,
            ActionType.SUMMARIZE: self._handle_summarize,
            ActionType.FILTER: self._handle_filter,
            ActionType.HOVER: self._handle_hover,
            ActionType.SELECT: self._handle_select,
            ActionType.NEW_TAB: self._handle_new_tab,
            ActionType.BACK: self._handle_back,
            ActionType.REFRESH: self._handle_refresh,
            ActionType.EVALUATE: self._handle_evaluate,
        }
        
        handler = handlers.get(step.action)
        if not handler:
            raise ValueError(f"Unknown action type: {step.action}")
        
        return await handler(step)

    async def _handle_anti_bot_pages(self) -> None:
        """Detect and dismiss typical automated access checks or robot-check overlays."""
        page = self.browser.page
        if not page:
            return

        try:
            # 1. Amazon "Continue shopping" block page
            url = page.url.lower()
            if "amazon" in url:
                # Find any button, link, or element containing "continue shopping"
                btn = page.get_by_text("Continue shopping", exact=False).first
                if await btn.count() == 0:
                    # Fallback to any button or link containing "continue"
                    btn = page.locator('a, button, input[type="submit"]').get_by_text("Continue", exact=False).first
                
                if await btn.count() > 0 and await btn.is_visible():
                    await self._log("Detected Amazon automated access block page. Clicking 'Continue shopping'...", "warning")
                    await btn.click(timeout=3000)
                    await asyncio.sleep(4)
                    
            # 2. General CAPTCHA / Robot Check warning
            body_text = await self.browser.get_page_text()
            body_text_lower = body_text.lower()
            if "robot" in body_text_lower or "captcha" in body_text_lower or "verify you are human" in body_text_lower:
                await self._log("WARNING: Page contains CAPTCHA or Robot Check keywords. Automation might be blocked.", "warning")
        except Exception as e:
            logger.debug(f"Anti-bot handler failed: {e}")

    async def _handle_navigate(self, step: AgentStep) -> str:
        """Navigate to a URL."""
        url = step.url or "https://www.google.com"
        success = await self.browser.navigate(url)
        await self.dom.wait_for_navigation_complete(self.browser.page)
        return f"Navigated to {url}"

    async def _handle_search(self, step: AgentStep) -> str:
        """Perform a search query on the current page or Google."""
        query = step.query or step.value or ""
        page = self.browser.page
        
        if not page:
            raise RuntimeError("No active browser page")
        
        # Try to find search box on the current page first (useful for web apps like WhatsApp, Amazon, etc.)
        search_box = await self.dom.find_element(page, "search box", "search", timeout_ms=5000)
        
        if not search_box:
            # If not found, and we are not on a search engine, navigate to Google
            current_url = self.browser.current_url
            if not any(domain in current_url for domain in ["google.com", "bing.com", "duckduckgo.com"]):
                await self.browser.navigate("https://www.google.com")
                await asyncio.sleep(1)
                search_box = await self.dom.find_element(page, "search box", "search", timeout_ms=8000)
        
        if search_box:
            await search_box.clear()
            await self.browser.type_humanlike(search_box, query)
            await page.keyboard.press("Enter")
            await self.dom.wait_for_navigation_complete(page)
            return f"Searched for: '{query}'"
        else:
            # Fallback: navigate to Google search URL
            import urllib.parse
            search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
            await self.browser.navigate(search_url)
            return f"Searched via URL for: '{query}'"

    async def _handle_click(self, step: AgentStep) -> str:
        """Click on an element."""
        page = self.browser.page
        if not page:
            raise RuntimeError("No active browser page")
        
        description = step.description or step.value or ""
        element_type = "link" if "link" in description.lower() else "button"
        
        locator = await self.dom.find_element(page, description, element_type)
        
        if locator:
            await self.browser.hover_then_click(locator)
            try:
                # Wait for any navigation page load triggered by the click
                await page.wait_for_load_state("load", timeout=5000)
            except Exception:
                pass
            await asyncio.sleep(1.0)
            return f"Clicked: {description}"
        else:
            # Check if this click is a search/submission click (fallback to Enter keypress)
            desc_lower = description.lower()
            if any(k in desc_lower for k in ["submit", "search", "enter", "go", "query"]):
                await self._log(f"Search/submit button '{description}' not found. Fallback: Pressing 'Enter' key...", "info")
                await page.keyboard.press("Enter")
                try:
                    await page.wait_for_load_state("load", timeout=5000)
                except Exception:
                    pass
                await asyncio.sleep(1.5)
                return f"Submitted search/form via Enter keypress fallback for: {description}"
                
            raise Exception(f"Element not found: {description}")

    async def _handle_type(self, step: AgentStep) -> str:
        """Type text into a field."""
        page = self.browser.page
        if not page:
            raise RuntimeError("No active browser page")
        
        text = step.value or ""
        description = step.description or "input field"
        
        locator = await self.dom.find_element(page, description, "input")
        
        if locator:
            await self.browser.type_humanlike(locator, text)
            
            # Smart fallback: if the description contains 'search' or 'find', automatically press Enter.
            desc_lower = description.lower()
            if "search" in desc_lower or "find" in desc_lower:
                await self._log(f"Auto-submitting search input '{description}' via Enter keypress...", "info")
                await page.keyboard.press("Enter")
                try:
                    await page.wait_for_load_state("load", timeout=5000)
                except Exception:
                    pass
                await asyncio.sleep(1.5)
                return f"Typed '{text}' into {description} and pressed Enter to search"
                
            return f"Typed '{text}' into {description}"
        else:
            raise Exception(f"Input field not found: {description}")

    async def _handle_scroll(self, step: AgentStep) -> str:
        """Scroll the page."""
        direction = step.scroll_direction or "down"
        await self.browser.smooth_scroll(direction, amount=400)
        return f"Scrolled {direction}"

    async def _handle_wait(self, step: AgentStep) -> str:
        """Wait for specified time or element."""
        wait_ms = step.wait_ms or 2000
        await asyncio.sleep(wait_ms / 1000)
        return f"Waited {wait_ms}ms"

    async def _handle_extract(self, step: AgentStep) -> dict:
        """Extract data from the current page."""
        page = self.browser.page
        if not page:
            raise RuntimeError("No active browser page")
        
        data = await self.dom.extract_page_data(page, step.extract_schema)
        
        # Store for later comparison steps
        step_key = f"step_{step.index}"
        self._extracted_data[step_key] = data
        
        await self._log(f"Extracted {len(data)} data fields from {page.url}", "success")
        return data

    async def _handle_screenshot(self, step: AgentStep) -> str:
        """Take and save a screenshot."""
        b64 = await self.browser.take_screenshot_base64()
        return b64 if b64 else "Screenshot failed"

    async def _handle_download(self, step: AgentStep) -> str:
        """Trigger a file download."""
        page = self.browser.page
        if not page:
            raise RuntimeError("No active browser page")
        
        url = step.url
        if url:
            # Direct download by navigating to URL
            async with page.expect_download(timeout=30000) as download_info:
                await page.evaluate(f"window.location.href = '{url}'")
            download = await download_info.value
            return f"Downloaded: {download.suggested_filename}"
        
        return "Download step completed"

    async def _handle_compare(self, step: AgentStep) -> dict:
        """Compare previously extracted data sets."""
        all_data = list(self._extracted_data.values())
        if len(all_data) < 2:
            return {"comparison": "Not enough data to compare", "data": all_data}
        
        comparison = {
            "datasets_compared": len(all_data),
            "items_per_dataset": [len(d) for d in all_data],
            "data": all_data,
        }
        return comparison

    async def _handle_summarize(self, step: AgentStep) -> str:
        """Summarize collected data using AI."""
        # This will be enhanced by the orchestrator's AI summarization
        all_keys = list(self._extracted_data.keys())
        summary = f"Processed {len(all_keys)} data sources: {', '.join(all_keys)}"
        return summary

    async def _handle_filter(self, step: AgentStep) -> str:
        """Apply filters on the current page."""
        page = self.browser.page
        if not page:
            raise RuntimeError("No active browser page")
        
        filter_description = step.description or step.value or ""
        locator = await self.dom.find_element(page, filter_description)
        
        if locator:
            await locator.click()
            await asyncio.sleep(1)
            return f"Applied filter: {filter_description}"
        
        return "Filter element not found (skipped)"

    async def _handle_hover(self, step: AgentStep) -> str:
        """Hover over an element."""
        page = self.browser.page
        if not page:
            raise RuntimeError("No active browser page")
        
        description = step.description or ""
        locator = await self.dom.find_element(page, description)
        
        if locator:
            await locator.hover()
            await asyncio.sleep(0.3)
            return f"Hovered over: {description}"
        
        return "Hover target not found"

    async def _handle_select(self, step: AgentStep) -> str:
        """Select from a dropdown."""
        page = self.browser.page
        if not page:
            raise RuntimeError("No active browser page")
        
        description = step.description or ""
        value = step.value or ""
        
        locator = await self.dom.find_element(page, description, "select")
        if locator:
            await locator.select_option(label=value)
            return f"Selected '{value}' from {description}"
        
        return "Select element not found"

    async def _handle_new_tab(self, step: AgentStep) -> str:
        """Open a new browser tab."""
        new_page = await self.browser.new_tab()
        if step.url:
            await new_page.goto(step.url)
        return f"Opened new tab"

    async def _handle_back(self, step: AgentStep) -> str:
        """Navigate back in browser history."""
        page = self.browser.page
        if page:
            await page.go_back()
            await asyncio.sleep(0.5)
        return "Navigated back"

    async def _handle_refresh(self, step: AgentStep) -> str:
        """Refresh the current page."""
        page = self.browser.page
        if page:
            await page.reload()
            await self.dom.wait_for_navigation_complete(page)
        return "Page refreshed"

    async def _handle_evaluate(self, step: AgentStep) -> Any:
        """Execute JavaScript."""
        script = step.value or "return document.title"
        result = await self.browser.execute_javascript(script)
        return result

    async def _log(self, message: str, level: str = "info"):
        """Send a log message through the callback."""
        if self.on_log:
            await self.on_log(message, level)
        
        log_fn = getattr(logger, level, logger.info)
        log_fn(message)

    @property
    def extracted_data(self) -> dict:
        return self._extracted_data
