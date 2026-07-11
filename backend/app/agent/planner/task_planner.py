"""
Task Planner – Uses Gemini AI to generate structured execution plans
"""

import asyncio
import json
from typing import Optional, Dict, Any
from loguru import logger
import google.generativeai as genai

from app.core.config import settings
from app.agent.planner.schemas import ExecutionPlan, AgentStep, ActionType, PlannerRequest


PLAN_SYSTEM_PROMPT = """You are an expert browser automation planner for WebPilot AI.

Your job is to analyze a user's natural language request and create a detailed, step-by-step execution plan 
for an autonomous browser agent to complete the task.

RULES:
1. Always plan before acting – never jump straight to clicking
2. Break complex tasks into atomic, executable steps
3. Think about what websites to visit and in what order
4. Include data extraction steps where relevant
5. Include comparison and summarization steps at the end
6. Mark optional steps with is_optional: true
7. Estimate realistic durations

AVAILABLE ACTIONS:
- navigate: Go to a specific URL
- search: Search on a search engine or website
- click: Click on an element
- type: Type text into a field
- scroll: Scroll the page
- wait: Wait for something to load
- extract: Extract data from the page
- screenshot: Take a screenshot
- download: Download a file
- compare: Compare extracted data
- summarize: Summarize information
- filter: Apply filters on a page
- hover: Hover over an element
- select: Select from a dropdown
- new_tab: Open a new browser tab
- close_tab: Close a tab
- back: Navigate back
- refresh: Refresh the page
- evaluate: Execute JavaScript

Respond ONLY with valid JSON matching this exact structure:
{
  "task_understanding": "Clear explanation of what the user wants",
  "goal": "Primary goal in one sentence",
  "approach": "How you will approach this task",
  "risk_level": "low|medium|high",
  "estimated_duration_ms": 60000,
  "notes": "Any important notes or warnings",
  "steps": [
    {
      "index": 0,
      "action": "navigate",
      "description": "Human-readable description",
      "url": "https://...",
      "query": null,
      "selector": null,
      "value": null,
      "wait_ms": null,
      "scroll_direction": null,
      "extract_schema": null,
      "expected_result": "What we expect to happen",
      "is_optional": false,
      "depends_on": []
    }
  ]
}
"""


class TaskPlanner:
    """
    AI-powered task planner that converts natural language prompts
    into structured execution plans using Google Gemini.
    """

    def __init__(self):
        self._configured = False
        self._model = None
        self._setup_ai()

    def _setup_ai(self):
        """Initialize the AI provider."""
        if settings.AI_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self._model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,        # Low temperature for deterministic planning
                    max_output_tokens=8192,
                    response_mime_type="application/json",
                ),
                system_instruction=PLAN_SYSTEM_PROMPT,
            )
            self._configured = True
            logger.info(f"TaskPlanner initialized with Gemini ({settings.GEMINI_MODEL})")
        elif settings.AI_PROVIDER == "openai" and settings.OPENAI_API_KEY:
            self._configured = True
            logger.info("TaskPlanner initialized with OpenAI")
        else:
            logger.warning("No AI provider configured – using fallback planner")

    async def generate_plan(self, request: PlannerRequest) -> ExecutionPlan:
        """
        Generate a structured execution plan from a natural language prompt.
        
        Args:
            request: PlannerRequest with the user's prompt and settings
            
        Returns:
            ExecutionPlan with structured steps
        """
        logger.info(f"Generating plan for prompt: '{request.prompt[:80]}...'")

        if not self._configured:
            return self._fallback_plan(request.prompt)

        try:
            if settings.AI_PROVIDER == "gemini":
                return await self._plan_with_gemini(request)
            else:
                return await self._plan_with_openai(request)
        except Exception as e:
            logger.error(f"AI planning failed ({type(e).__name__}): {e}")
            return self._fallback_plan(request.prompt)

    async def _plan_with_gemini(self, request: PlannerRequest) -> ExecutionPlan:
        """Generate plan using Google Gemini (runs blocking SDK in thread executor)."""
        user_message = f"""
User Request: {request.prompt}

Additional Context: {request.context or 'None'}

User Browser Settings: {json.dumps(request.user_settings or {}, indent=2)}

Generate a comprehensive, step-by-step execution plan for this browser automation task.
IMPORTANT: If the user mentions a specific website URL (like flipkart.com, amazon.com, etc.),
use the 'navigate' action to go directly to that URL. Do NOT use 'search' for known URLs.
"""
        # Run the synchronous SDK call in a thread executor to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        try:
            response = await loop.run_in_executor(
                None, self._model.generate_content, user_message
            )
        except Exception as api_err:
            logger.error(f"Gemini API call failed: {type(api_err).__name__}: {api_err}")
            raise

        raw_json = response.text.strip()
        logger.debug(f"Gemini raw response (first 300 chars): {raw_json[:300]}")

        # Clean potential markdown code fences
        if raw_json.startswith("```"):
            raw_json = raw_json.split("```")[1]
            if raw_json.startswith("json"):
                raw_json = raw_json[4:]

        try:
            plan_data = json.loads(raw_json)
        except json.JSONDecodeError as je:
            logger.error(f"Gemini returned invalid JSON: {je}. Raw: {raw_json[:500]}")
            raise

        # Parse steps into AgentStep objects, skipping any that fail validation
        steps = []
        for i, step_data in enumerate(plan_data.get("steps", [])):
            try:
                step_data["index"] = i
                # Remove unknown keys that aren't in the schema
                allowed = {"index", "action", "description", "url", "query", "selector",
                           "value", "wait_ms", "scroll_direction", "extract_schema",
                           "expected_result", "is_optional", "depends_on"}
                step_data = {k: v for k, v in step_data.items() if k in allowed}
                steps.append(AgentStep(**step_data))
            except Exception as step_err:
                logger.warning(f"Skipping step {i} due to validation error: {step_err} | data: {step_data}")

        if not steps:
            logger.error("Gemini plan produced 0 valid steps – falling back")
            raise ValueError("No valid steps in Gemini plan")

        plan = ExecutionPlan(
            task_understanding=plan_data["task_understanding"],
            goal=plan_data["goal"],
            approach=plan_data["approach"],
            risk_level=plan_data.get("risk_level", "low"),
            estimated_duration_ms=plan_data.get("estimated_duration_ms"),
            notes=plan_data.get("notes"),
            steps=steps,
        )

        logger.success(f"Generated Gemini plan with {len(steps)} steps: {[s.description for s in steps]}")
        return plan

    async def _plan_with_openai(self, request: PlannerRequest) -> ExecutionPlan:
        """Generate plan using OpenAI GPT."""
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": PLAN_SYSTEM_PROMPT},
                {"role": "user", "content": f"User Request: {request.prompt}"},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        
        raw_json = response.choices[0].message.content
        plan_data = json.loads(raw_json)
        
        steps = []
        for i, step_data in enumerate(plan_data.get("steps", [])):
            step_data["index"] = i
            steps.append(AgentStep(**step_data))
        
        return ExecutionPlan(
            task_understanding=plan_data["task_understanding"],
            goal=plan_data["goal"],
            approach=plan_data["approach"],
            steps=steps,
        )

    def _fallback_plan(self, prompt: str) -> ExecutionPlan:
        """
        Fallback plan when AI is not available.
        Creates a basic Google search plan.
        """
        logger.warning("Using fallback plan – AI not configured")
        return ExecutionPlan(
            task_understanding=f"Search the web for: {prompt}",
            goal="Find relevant information for the user's request",
            approach="Search Google and extract results",
            risk_level="low",
            estimated_duration_ms=15000,
            steps=[
                AgentStep(
                    index=0,
                    action=ActionType.NAVIGATE,
                    description="Open Google",
                    url="https://www.google.com",
                    expected_result="Google homepage loaded",
                ),
                AgentStep(
                    index=1,
                    action=ActionType.SEARCH,
                    description=f"Search for: {prompt}",
                    query=prompt,
                    expected_result="Search results displayed",
                ),
                AgentStep(
                    index=2,
                    action=ActionType.EXTRACT,
                    description="Extract search results",
                    expected_result="Results extracted as structured data",
                ),
                AgentStep(
                    index=3,
                    action=ActionType.SUMMARIZE,
                    description="Summarize findings",
                    expected_result="Summary generated",
                ),
            ],
        )

    async def get_recovery_action(
        self, step: AgentStep, error: str, context: str
    ) -> Dict[str, Any]:
        """
        Ask AI to suggest recovery action when a step fails.
        
        Returns:
            dict with keys: strategy, description, alternative_selector, wait_before_ms
        """
        if not self._configured:
            return {"strategy": "retry", "description": "Retry the step", "wait_before_ms": 2000}

        prompt = f"""
A browser automation step failed. Suggest a recovery action.

FAILED STEP:
- Action: {step.action}
- Description: {step.description}
- Target URL: {step.url}
- Selector used: {step.selector}
- Error: {error}

CURRENT CONTEXT: {context}

Respond with JSON:
{{
  "strategy": "retry|skip|alternative|abort",
  "description": "What to do",
  "alternative_selector": "CSS selector or null",
  "wait_before_ms": 2000
}}
"""
        try:
            response = self._model.generate_content(prompt)
            return json.loads(response.text.strip())
        except Exception:
            return {"strategy": "retry", "description": "Retry the failed step", "wait_before_ms": 3000}
