"""
Agent Orchestrator – The core engine that coordinates all agent modules
"""

import asyncio
import json
import os
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, AsyncGenerator
from loguru import logger

from app.agent.planner.task_planner import TaskPlanner
from app.agent.planner.schemas import ExecutionPlan, AgentStep, PlannerRequest
from app.agent.browser.browser_controller import BrowserController
from app.agent.executor.playwright_executor import PlaywrightExecutor, StepResult
from app.agent.dom.dom_analyzer import DOMAnalyzer
from app.agent.recovery.recovery_engine import RecoveryEngine
from app.agent.reports.report_generator import ReportGenerator
from app.core.config import settings


class TaskEvent:
    """Events emitted during task execution for real-time streaming."""
    
    # Event types
    PLANNING = "planning"
    PLAN_READY = "plan_ready"
    STEP_START = "step_start"
    STEP_COMPLETE = "step_complete"
    STEP_FAILED = "step_failed"
    STEP_RECOVERY = "step_recovery"
    LOG = "log"
    SCREENSHOT = "screenshot"
    DATA_EXTRACTED = "data_extracted"
    BROWSER_UPDATE = "browser_update"
    COMPLETE = "complete"
    ERROR = "error"
    PROGRESS = "progress"

    def __init__(self, type: str, data: dict):
        self.type = type
        self.data = data
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "data": self.data,
            "timestamp": self.timestamp,
        }


class AgentOrchestrator:
    """
    Main orchestrator that coordinates:
    - Task Planner (AI)
    - Browser Controller (Playwright)
    - Step Executor
    - DOM Analyzer
    - Recovery Engine
    - Report Generator
    
    Provides real-time event streaming via asyncio.Queue.
    """

    def __init__(self, task_id: int, user_id: int, user_settings: Optional[dict] = None):
        self.task_id = task_id
        self.user_id = user_id
        self.user_settings = user_settings or {}
        
        # Event queue for real-time streaming
        self.event_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        
        # Module instances
        self.planner = TaskPlanner()
        self.dom = DOMAnalyzer()
        self.report_gen = ReportGenerator()
        
        # Browser settings from user preferences
        browser_type = self.user_settings.get("browser", settings.BROWSER_TYPE)
        headless = self.user_settings.get("headless", settings.BROWSER_HEADLESS)
        
        self.browser = BrowserController(
            browser_type=browser_type,
            headless=headless,
            slow_mo=settings.BROWSER_SLOW_MO,
            downloads_dir=settings.DOWNLOADS_DIR,
        )
        
        # State
        self._plan: Optional[ExecutionPlan] = None
        self._step_results: list = []
        self._is_running = False
        self._start_time: Optional[float] = None
        self._screenshots_dir = settings.SCREENSHOTS_DIR
        
        # Will be set after executor creation
        self.executor: Optional[PlaywrightExecutor] = None
        self.recovery: Optional[RecoveryEngine] = None

    async def run(self, prompt: str) -> dict:
        """
        Execute a complete task from prompt to report.
        
        Args:
            prompt: Natural language task description
            
        Returns:
            Final task result dict
        """
        self._is_running = True
        self._start_time = time.monotonic()
        
        try:
            # Phase 1: AI Planning
            await self._emit(TaskEvent.PLANNING, {
                "message": "AI is analyzing your request and creating an execution plan..."
            })
            
            plan_request = PlannerRequest(
                prompt=prompt,
                user_settings=self.user_settings,
            )
            self._plan = await self.planner.generate_plan(plan_request)
            
            await self._emit(TaskEvent.PLAN_READY, {
                "task_understanding": self._plan.task_understanding,
                "goal": self._plan.goal,
                "approach": self._plan.approach,
                "total_steps": len(self._plan.steps),
                "estimated_duration_ms": self._plan.estimated_duration_ms,
                "steps": [s.model_dump() for s in self._plan.steps],
            })
            
            # Phase 2: Browser Launch
            await self._emit(TaskEvent.LOG, {
                "message": "Launching browser...",
                "level": "info",
            })
            
            await self.browser.start()
            
            # Phase 3: Create executor and recovery engine
            self.executor = PlaywrightExecutor(
                browser=self.browser,
                dom_analyzer=self.dom,
                on_log=self._on_executor_log,
            )
            self.recovery = RecoveryEngine(
                browser=self.browser,
                dom=self.dom,
                planner=self.planner,
                max_retries=self.user_settings.get("retry_count", settings.MAX_RETRY_COUNT),
            )
            
            # Phase 4: Start screenshot streaming
            asyncio.create_task(self._stream_screenshots())
            
            # Phase 5: Execute plan steps
            domains_visited = set()
            error_count = 0
            
            for step in self._plan.steps:
                if not self._is_running:
                    break
                
                await self._emit(TaskEvent.STEP_START, {
                    "step_index": step.index,
                    "action": step.action,
                    "description": step.description,
                    "progress_pct": int((step.index / len(self._plan.steps)) * 100),
                })
                
                result = await self.executor.execute_step(step)
                
                if not result.success:
                    error_count += 1
                    await self._emit(TaskEvent.STEP_FAILED, {
                        "step_index": step.index,
                        "error": result.error,
                        "description": step.description,
                    })
                    
                    # Attempt recovery
                    await self._emit(TaskEvent.STEP_RECOVERY, {
                        "step_index": step.index,
                        "message": "Attempting self-healing recovery...",
                    })
                    
                    recovered = await self.recovery.attempt_recovery(step, result.error or "", self.executor)
                    
                    if not recovered and not step.is_optional:
                        await self._emit(TaskEvent.LOG, {
                            "message": f"Step {step.index} failed after all recovery attempts",
                            "level": "error",
                        })
                        raise RuntimeError(f"Step {step.index} failed: {result.error}")
                else:
                    await self._emit(TaskEvent.STEP_COMPLETE, {
                        "step_index": step.index,
                        "action": step.action,
                        "description": step.description,
                        "duration_ms": result.duration_ms,
                        "url": result.url,
                        "result": result.result if isinstance(result.result, (str, dict, list)) else str(result.result),
                    })
                    
                    # Emit extracted data if any
                    if result.result and isinstance(result.result, dict):
                        await self._emit(TaskEvent.DATA_EXTRACTED, {
                            "step_index": step.index,
                            "data": result.result,
                        })
                
                # Save screenshot
                if result.screenshot_b64:
                    await self._save_step_screenshot(step.index, result.screenshot_b64)
                
                # Track visited domains
                if result.url and "://" in result.url:
                    try:
                        from urllib.parse import urlparse
                        domain = urlparse(result.url).netloc
                        if domain:
                            domains_visited.add(domain)
                    except Exception:
                        pass
                
                self._step_results.append(result.to_dict())
                
                # Progress update
                completed = step.index + 1
                total = len(self._plan.steps)
                await self._emit(TaskEvent.PROGRESS, {
                    "completed": completed,
                    "total": total,
                    "pct": int((completed / total) * 100),
                })
            
            # Wait for final page rendering and screenshot capture before closing browser
            await asyncio.sleep(4.0)
            
            # Phase 6: Generate AI Summary
            summary, recommendation = await self._generate_summary(prompt, domains_visited)
            
            # Phase 7: Generate Reports
            execution_time_ms = (time.monotonic() - self._start_time) * 1000
            steps_completed = sum(1 for r in self._step_results if r.get("success"))
            success_rate = steps_completed / max(len(self._plan.steps), 1)
            
            metrics = {
                "execution_time_ms": execution_time_ms,
                "success_rate": success_rate,
                "steps_completed": steps_completed,
                "total_steps": len(self._plan.steps),
                "error_count": error_count,
                "websites_count": len(domains_visited),
                "websites_visited": list(domains_visited),
            }
            
            plan_dict = self._plan.model_dump()
            
            await self._emit(TaskEvent.LOG, {"message": "Generating reports...", "level": "info"})
            
            pdf_path = await self.report_gen.generate_pdf(
                task_id=self.task_id,
                prompt=prompt,
                plan=plan_dict,
                results=self._step_results,
                extracted_data=self.executor.extracted_data,
                summary=summary,
                recommendation=recommendation,
                metrics=metrics,
            )
            
            csv_path = await self.report_gen.generate_csv(
                task_id=self.task_id,
                prompt=prompt,
                results=self._step_results,
                extracted_data=self.executor.extracted_data,
            )
            
            json_path = await self.report_gen.generate_json(
                task_id=self.task_id,
                prompt=prompt,
                plan=plan_dict,
                results=self._step_results,
                extracted_data=self.executor.extracted_data,
                summary=summary,
                recommendation=recommendation,
                metrics=metrics,
            )
            
            final_result = {
                "status": "completed",
                "summary": summary,
                "recommendation": recommendation,
                "metrics": metrics,
                "reports": {
                    "pdf": os.path.basename(pdf_path),
                    "csv": os.path.basename(csv_path),
                    "json": os.path.basename(json_path),
                },
                "plan": plan_dict,
                "step_results": self._step_results,
                "extracted_data": self.executor.extracted_data,
            }
            
            await self._emit(TaskEvent.COMPLETE, final_result)
            return final_result
        
        except Exception as e:
            logger.exception(f"Task {self.task_id} failed: {e}")
            await self._emit(TaskEvent.ERROR, {
                "message": str(e),
                "task_id": self.task_id,
            })
            raise
        
        finally:
            self._is_running = False
            await self.browser.stop()

    async def stop(self) -> None:
        """Stop the orchestrator and clean up."""
        self._is_running = False
        await self.browser.stop()

    async def _emit(self, event_type: str, data: dict) -> None:
        """Put an event on the queue for streaming."""
        event = TaskEvent(event_type, data)
        try:
            await self.event_queue.put(event.to_dict())
        except asyncio.QueueFull:
            logger.warning("Event queue full – dropping event")

    async def _on_executor_log(self, message: str, level: str) -> None:
        """Callback for executor log messages."""
        await self._emit(TaskEvent.LOG, {
            "message": message,
            "level": level,
        })

    async def _stream_screenshots(self) -> None:
        """Background task to stream browser screenshots."""
        interval = self.user_settings.get(
            "screenshot_frequency", settings.BROWSER_SCREENSHOT_INTERVAL
        )
        while self._is_running and self.browser.page:
            try:
                b64 = await self.browser.take_screenshot_base64()
                if b64:
                    page_info = await self.browser.get_page_info()
                    await self._emit(TaskEvent.BROWSER_UPDATE, {
                        "screenshot": b64,
                        "url": page_info.get("url", ""),
                        "title": page_info.get("title", ""),
                    })
            except Exception:
                pass
            await asyncio.sleep(interval / 1000)

    async def _save_step_screenshot(self, step_index: int, b64_data: str) -> Optional[str]:
        """Save a screenshot to disk and return filename."""
        try:
            import base64
            filename = f"task_{self.task_id}_step_{step_index}_{int(time.time())}.png"
            filepath = os.path.join(self._screenshots_dir, filename)
            os.makedirs(self._screenshots_dir, exist_ok=True)
            
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(b64_data))
            
            return filename
        except Exception as e:
            logger.error(f"Failed to save screenshot: {e}")
            return None

    async def _generate_summary(
        self, prompt: str, domains_visited: set
    ) -> tuple[str, str]:
        """Generate AI summary and recommendation for the completed task."""
        try:
            import google.generativeai as genai
            
            if not settings.GEMINI_API_KEY:
                return self._fallback_summary(domains_visited), ""
            
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(settings.GEMINI_MODEL)
            
            data_summary = json.dumps(
                {k: v for k, v in self.executor.extracted_data.items() if v},
                indent=2,
                default=str,
            )[:3000]
            
            prompt_text = f"""
You are a data analyst. Summarize the results of an autonomous browser task.

ORIGINAL USER REQUEST: {prompt}

WEBSITES VISITED: {', '.join(domains_visited)}

EXTRACTED DATA:
{data_summary}

STEP RESULTS:
{json.dumps([{'step': r['step_index'], 'success': r['success'], 'action': r['action']} for r in self._step_results], indent=2)}

Provide:
1. A clear SUMMARY of what was accomplished (2-3 sentences)
2. A RECOMMENDATION based on the findings (1-2 sentences)

Respond as JSON: {{"summary": "...", "recommendation": "..."}}
"""
            response = model.generate_content(prompt_text)
            result = json.loads(response.text.strip())
            return result.get("summary", ""), result.get("recommendation", "")
        
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return self._fallback_summary(domains_visited), "Review the extracted data for insights."

    def _fallback_summary(self, domains_visited: set) -> str:
        steps_done = sum(1 for r in self._step_results if r.get("success"))
        total = len(self._step_results)
        sites = ", ".join(list(domains_visited)[:5]) if domains_visited else "N/A"
        return (
            f"Task completed {steps_done}/{total} steps successfully. "
            f"Visited sites: {sites}. "
            f"Data has been extracted and saved to the reports."
        )
