"""
Browser Controller – Manages Playwright browser lifecycle with human-like behavior
"""

import asyncio
import base64
import os
import random
import time
from datetime import datetime, timezone
from typing import Optional, Callable, AsyncGenerator
from loguru import logger
from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Playwright,
)

from app.core.config import settings


class BrowserController:
    """
    Manages Playwright browser instances with human-like interaction patterns.
    
    Features:
    - Chromium, Firefox, Edge support
    - Headless and headed modes
    - Human-like delays and mouse movements
    - Screenshot streaming
    - File download handling
    - Multi-tab support
    """

    def __init__(
        self,
        browser_type: str = "chromium",
        headless: bool = True,
        slow_mo: int = 50,
        downloads_dir: str = "/app/downloads",
    ):
        self.browser_type = browser_type
        self.headless = headless
        self.slow_mo = slow_mo
        self.downloads_dir = downloads_dir
        
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._is_running = False
        self._screenshot_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Launch the browser and create a new context."""
        logger.info(f"Starting {self.browser_type} browser (headless={self.headless})")
        
        self._playwright = await async_playwright().start()
        
        # Select browser type
        browser_launcher = {
            "chromium": self._playwright.chromium,
            "firefox": self._playwright.firefox,
            "edge": self._playwright.chromium,  # Edge uses Chromium engine
        }.get(self.browser_type, self._playwright.chromium)
        
        launch_kwargs = {
            "headless": self.headless,
            "slow_mo": self.slow_mo,
        }
        
        if self.browser_type == "edge":
            launch_kwargs["channel"] = "msedge"
        
        self._browser = await browser_launcher.launch(**launch_kwargs)
        
        # Create context with realistic settings
        self._context = await self._browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="America/New_York",
            accept_downloads=True,
        )
        
        # Set download path
        os.makedirs(self.downloads_dir, exist_ok=True)
        await self._context.set_extra_http_headers({
            "Accept-Language": "en-US,en;q=0.9",
        })
        
        self._page = await self._context.new_page()
        self._is_running = True
        
        # Handle download events
        self._page.on("download", self._handle_download)
        
        logger.info("Browser started successfully")

    async def stop(self) -> None:
        """Clean up browser resources."""
        self._is_running = False
        
        if self._screenshot_task and not self._screenshot_task.done():
            self._screenshot_task.cancel()
        
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        
        logger.info("Browser stopped")

    @property
    def page(self) -> Optional[Page]:
        return self._page

    @property
    def current_url(self) -> str:
        if self._page:
            return self._page.url
        return ""

    async def navigate(self, url: str, wait_until: str = "networkidle") -> bool:
        """Navigate to a URL with proper waiting."""
        if not self._page:
            raise RuntimeError("Browser not started")
        
        try:
            logger.info(f"Navigating to: {url}")
            await self._page.goto(url, wait_until=wait_until, timeout=settings.BROWSER_DEFAULT_TIMEOUT)
            return True
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            try:
                # Fallback: try with domcontentloaded
                await self._page.goto(url, wait_until="domcontentloaded", timeout=settings.BROWSER_DEFAULT_TIMEOUT)
                return True
            except Exception:
                return False

    async def type_humanlike(self, locator, text: str) -> None:
        """Type text with random delays to simulate human typing."""
        try:
            await locator.click(timeout=3000)
        except Exception as e:
            logger.warning(f"Standard click before typing failed ({e}). Retrying with force=True...")
            try:
                await locator.click(force=True, timeout=3000)
            except Exception:
                pass
        await asyncio.sleep(random.uniform(0.1, 0.3))
        
        # Clear the field first if possible
        try:
            await locator.fill("")
        except Exception:
            pass
            
        for char in text:
            await locator.press(char)
            # Randomized delay between keystrokes (30-150ms)
            await asyncio.sleep(random.uniform(0.03, 0.15))
        
        await asyncio.sleep(random.uniform(0.2, 0.5))

    async def smooth_scroll(self, direction: str = "down", amount: int = 300) -> None:
        """Perform smooth scrolling."""
        if not self._page:
            return
        
        if direction == "down":
            await self._page.evaluate(f"window.scrollBy({{top: {amount}, behavior: 'smooth'}})")
        elif direction == "up":
            await self._page.evaluate(f"window.scrollBy({{top: -{amount}, behavior: 'smooth'}})")
        
        await asyncio.sleep(0.5)

    async def hover_then_click(self, locator) -> None:
        """Hover over an element briefly before clicking (human-like)."""
        try:
            await locator.hover(timeout=3000)
            await asyncio.sleep(random.uniform(0.1, 0.4))
            await locator.click(timeout=5000)
        except Exception as e:
            logger.warning(f"Standard click/hover failed ({e}). Retrying with force=True...")
            await locator.click(force=True)

    async def take_screenshot(self, path: Optional[str] = None) -> bytes:
        """Take a screenshot and return as bytes."""
        if not self._page:
            return b""
        try:
            if path:
                return await self._page.screenshot(path=path, full_page=False)
            return await self._page.screenshot(full_page=False)
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return b""

    async def take_screenshot_base64(self) -> str:
        """Take a screenshot and return as base64 string."""
        screenshot_bytes = await self.take_screenshot()
        if screenshot_bytes:
            return base64.b64encode(screenshot_bytes).decode("utf-8")
        return ""

    async def stream_screenshots(
        self,
        interval_ms: int = 500,
        callback: Optional[Callable] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream screenshots as base64 strings at the given interval.
        Yields base64-encoded JPEG strings.
        """
        while self._is_running:
            try:
                data = await self.take_screenshot_base64()
                if data:
                    if callback:
                        await callback(data)
                    yield data
            except Exception as e:
                logger.debug(f"Screenshot stream error: {e}")
            await asyncio.sleep(interval_ms / 1000)

    async def wait_for_element(self, selector: str, timeout_ms: int = 10000) -> bool:
        """Wait for an element to appear on the page."""
        if not self._page:
            return False
        try:
            await self._page.wait_for_selector(selector, timeout=timeout_ms)
            return True
        except Exception:
            return False

    async def get_page_text(self) -> str:
        """Extract all visible text from the page."""
        if not self._page:
            return ""
        try:
            return await self._page.inner_text("body")
        except Exception:
            return ""

    async def execute_javascript(self, script: str) -> any:
        """Execute JavaScript in the browser context."""
        if not self._page:
            return None
        try:
            return await self._page.evaluate(script)
        except Exception as e:
            logger.error(f"JavaScript execution failed: {e}")
            return None

    async def new_tab(self) -> Page:
        """Open a new browser tab."""
        if not self._context:
            raise RuntimeError("Browser not started")
        page = await self._context.new_page()
        return page

    async def _handle_download(self, download) -> None:
        """Handle file downloads automatically."""
        try:
            filename = download.suggested_filename
            save_path = os.path.join(self.downloads_dir, filename)
            await download.save_as(save_path)
            logger.info(f"Downloaded file: {filename}")
        except Exception as e:
            logger.error(f"Download handling failed: {e}")

    async def get_page_info(self) -> dict:
        """Get current page information."""
        if not self._page:
            return {}
        return {
            "url": self._page.url,
            "title": await self._page.title(),
            "is_loading": not await self._page.evaluate("document.readyState === 'complete'"),
        }
