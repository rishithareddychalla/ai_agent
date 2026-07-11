"""
Tasks API – CRUD operations and WebSocket streaming for real-time task progress
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from loguru import logger

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.task import Task, TaskStatus
from app.models.session import ExecutionLog, LogLevel, Report, ReportFormat, Screenshot
from app.agent.orchestrator import AgentOrchestrator

router = APIRouter()

# In-memory map of active orchestrators (task_id -> orchestrator)
_active_orchestrators: dict[int, AgentOrchestrator] = {}


# ─── Schemas ────────────────────────────────────────────────

class CreateTaskRequest(BaseModel):
    prompt: str
    browser: Optional[str] = "chromium"
    headless: Optional[bool] = True


class TaskResponse(BaseModel):
    id: int
    prompt: str
    status: str
    current_step: int
    total_steps: int
    result_summary: Optional[str]
    recommendation: Optional[str]
    execution_time_ms: Optional[float]
    success_rate: Optional[float]
    websites_visited: Optional[List[str]]
    error_message: Optional[str]
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]

    class Config:
        from_attributes = True


# ─── Endpoints ──────────────────────────────────────────────

@router.post("", response_model=TaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_task(
    request: CreateTaskRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create and start a new browser agent task."""
    task = Task(
        user_id=current_user.id,
        prompt=request.prompt,
        status=TaskStatus.PENDING,
        browser_config={
            "browser": request.browser,
            "headless": request.headless,
        },
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    # Run the agent in the background
    background_tasks.add_task(
        _run_agent_task,
        task_id=task.id,
        prompt=request.prompt,
        user_settings=current_user.settings,
        browser_config=task.browser_config,
    )
    
    return _task_to_response(task)


@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all tasks for the current user."""
    result = await db.execute(
        select(Task)
        .where(Task.user_id == current_user.id)
        .order_by(desc(Task.created_at))
        .offset(skip)
        .limit(limit)
    )
    tasks = result.scalars().all()
    return [_task_to_response(t) for t in tasks]


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific task by ID."""
    task = await _get_user_task(task_id, current_user.id, db)
    return _task_to_response(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel a running task or delete a completed task."""
    task = await _get_user_task(task_id, current_user.id, db)
    
    # Stop orchestrator if running
    orchestrator = _active_orchestrators.get(task_id)
    if orchestrator:
        await orchestrator.stop()
        _active_orchestrators.pop(task_id, None)
    
    task.status = TaskStatus.CANCELLED
    await db.commit()


@router.websocket("/ws/{task_id}")
async def task_websocket(
    websocket: WebSocket,
    task_id: int,
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    WebSocket endpoint for real-time task progress streaming.
    
    Connect with: ws://localhost:8000/tasks/ws/{task_id}?token=<jwt>
    
    Emits JSON events:
    - planning, plan_ready, step_start, step_complete, step_failed
    - log, screenshot, data_extracted, browser_update, complete, error, progress
    """
    await websocket.accept()
    
    try:
        # Authenticate via token query param
        from app.core.security import decode_token
        from sqlalchemy import select
        payload = decode_token(token)
        user_id = int(payload.get("sub", 0))
        
        # Verify task belongs to user
        result = await db.execute(
            select(Task).where(Task.id == task_id, Task.user_id == user_id)
        )
        task = result.scalar_one_or_none()
        if not task:
            await websocket.send_json({"type": "error", "data": {"message": "Task not found"}})
            await websocket.close()
            return
        
        # Wait for orchestrator and stream its events
        max_wait = 30  # seconds
        waited = 0
        while task_id not in _active_orchestrators and waited < max_wait:
            await asyncio.sleep(0.5)
            waited += 0.5
        
        orchestrator = _active_orchestrators.get(task_id)
        if not orchestrator:
            await websocket.send_json({
                "type": "error",
                "data": {"message": "Task orchestrator not found"},
            })
            return
        
        # Stream events
        while True:
            try:
                event = await asyncio.wait_for(
                    orchestrator.event_queue.get(),
                    timeout=60.0,
                )
                await websocket.send_json(event)
                
                # Stop streaming after completion
                if event.get("type") in ["complete", "error"]:
                    break
                    
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({"type": "ping", "data": {}})
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for task {task_id}")
    except Exception as e:
        logger.error(f"WebSocket error for task {task_id}: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "data": {"message": str(e)},
            })
        except Exception:
            pass


# ─── Helper Functions ────────────────────────────────────────

async def _run_agent_task(
    task_id: int,
    prompt: str,
    user_settings: dict,
    browser_config: dict,
) -> None:
    """Background task that runs the agent orchestrator."""
    from app.core.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        try:
            # Update task status to running
            result = await db.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one()
            task.status = TaskStatus.PLANNING
            task.started_at = datetime.now(timezone.utc)
            await db.commit()
            
            # Merge user settings with browser config
            settings_merged = {**user_settings, **browser_config}
            
            # Create and register orchestrator
            orchestrator = AgentOrchestrator(
                task_id=task_id,
                user_id=task.user_id,
                user_settings=settings_merged,
            )
            _active_orchestrators[task_id] = orchestrator
            
            # Update status to running
            task.status = TaskStatus.RUNNING
            await db.commit()
            
            # Run the task
            final_result = await orchestrator.run(prompt)
            
            # Save results to DB
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now(timezone.utc)
            task.result_summary = final_result.get("summary", "")
            task.recommendation = final_result.get("recommendation", "")
            task.execution_plan = final_result.get("plan")
            task.extracted_data = final_result.get("extracted_data", {})
            task.websites_visited = final_result["metrics"].get("websites_visited", [])
            task.execution_time_ms = final_result["metrics"].get("execution_time_ms")
            task.success_rate = final_result["metrics"].get("success_rate")
            task.total_steps = final_result["metrics"].get("total_steps", 0)
            task.current_step = task.total_steps
            
            # Save report records
            reports = final_result.get("reports", {})
            for fmt, filename in reports.items():
                import os
                from app.core.config import settings as app_settings
                filepath = os.path.join(app_settings.REPORTS_DIR, filename)
                file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
                
                report = Report(
                    task_id=task_id,
                    format=ReportFormat(fmt),
                    filename=filename,
                    file_path=filepath,
                    file_size=file_size,
                )
                db.add(report)
            
            # Save step logs
            for step_result in final_result.get("step_results", []):
                log = ExecutionLog(
                    task_id=task_id,
                    step_index=step_result.get("step_index"),
                    level=LogLevel.SUCCESS if step_result.get("success") else LogLevel.ERROR,
                    action=step_result.get("action", ""),
                    message=step_result.get("description", ""),
                    url=step_result.get("url"),
                    success=step_result.get("success", False),
                    error_detail=step_result.get("error"),
                    duration_ms=step_result.get("duration_ms"),
                )
                db.add(log)
            
            await db.commit()
            logger.success(f"Task {task_id} completed successfully")
        
        except Exception as e:
            logger.exception(f"Task {task_id} failed: {e}")
            try:
                result = await db.execute(select(Task).where(Task.id == task_id))
                task = result.scalar_one_or_none()
                if task:
                    task.status = TaskStatus.FAILED
                    task.error_message = str(e)
                    task.completed_at = datetime.now(timezone.utc)
                    await db.commit()
            except Exception:
                pass
        
        finally:
            _active_orchestrators.pop(task_id, None)


async def _get_user_task(task_id: int, user_id: int, db: AsyncSession) -> Task:
    """Get a task belonging to the current user."""
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == user_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


def _task_to_response(task: Task) -> dict:
    """Convert a Task ORM object to a response dict."""
    return {
        "id": task.id,
        "prompt": task.prompt,
        "status": task.status.value if task.status else "pending",
        "current_step": task.current_step or 0,
        "total_steps": task.total_steps or 0,
        "result_summary": task.result_summary,
        "recommendation": task.recommendation,
        "execution_time_ms": task.execution_time_ms,
        "success_rate": task.success_rate,
        "websites_visited": task.websites_visited or [],
        "error_message": task.error_message,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }
