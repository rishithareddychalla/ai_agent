"""
Analytics API – Task metrics, daily usage, and site analytics
"""

from datetime import datetime, timedelta, timezone
from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.task import Task, TaskStatus

router = APIRouter()


class AnalyticsSummary(BaseModel):
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    running_tasks: int
    avg_success_rate: float
    avg_execution_time_ms: float
    total_execution_time_ms: float


class DailyTaskCount(BaseModel):
    date: str
    total: int
    completed: int
    failed: int


class SiteVisit(BaseModel):
    domain: str
    visit_count: int


@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get overall analytics summary for the current user."""
    result = await db.execute(
        select(Task).where(Task.user_id == current_user.id)
    )
    tasks = result.scalars().all()
    
    if not tasks:
        return AnalyticsSummary(
            total_tasks=0,
            completed_tasks=0,
            failed_tasks=0,
            running_tasks=0,
            avg_success_rate=0.0,
            avg_execution_time_ms=0.0,
            total_execution_time_ms=0.0,
        )
    
    completed = [t for t in tasks if t.status == TaskStatus.COMPLETED]
    failed = [t for t in tasks if t.status == TaskStatus.FAILED]
    running = [t for t in tasks if t.status in [TaskStatus.RUNNING, TaskStatus.PLANNING]]
    
    success_rates = [t.success_rate for t in completed if t.success_rate is not None]
    exec_times = [t.execution_time_ms for t in completed if t.execution_time_ms is not None]
    
    return AnalyticsSummary(
        total_tasks=len(tasks),
        completed_tasks=len(completed),
        failed_tasks=len(failed),
        running_tasks=len(running),
        avg_success_rate=sum(success_rates) / max(len(success_rates), 1),
        avg_execution_time_ms=sum(exec_times) / max(len(exec_times), 1),
        total_execution_time_ms=sum(exec_times),
    )


@router.get("/daily", response_model=List[DailyTaskCount])
async def get_daily_tasks(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get daily task counts for the last N days."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    
    result = await db.execute(
        select(Task).where(
            Task.user_id == current_user.id,
            Task.created_at >= since,
        ).order_by(Task.created_at)
    )
    tasks = result.scalars().all()
    
    # Group by date
    from collections import defaultdict
    daily_counts = defaultdict(lambda: {"total": 0, "completed": 0, "failed": 0})
    
    for task in tasks:
        if task.created_at:
            date_key = task.created_at.date().isoformat()
            daily_counts[date_key]["total"] += 1
            if task.status == TaskStatus.COMPLETED:
                daily_counts[date_key]["completed"] += 1
            elif task.status == TaskStatus.FAILED:
                daily_counts[date_key]["failed"] += 1
    
    # Fill in missing dates with zeros
    result_list = []
    for i in range(days):
        date = (datetime.now(timezone.utc) - timedelta(days=days - 1 - i)).date()
        date_str = date.isoformat()
        counts = daily_counts.get(date_str, {"total": 0, "completed": 0, "failed": 0})
        result_list.append(DailyTaskCount(
            date=date_str,
            **counts,
        ))
    
    return result_list


@router.get("/sites", response_model=List[SiteVisit])
async def get_top_sites(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the most visited domains across all tasks."""
    result = await db.execute(
        select(Task).where(
            Task.user_id == current_user.id,
            Task.websites_visited.isnot(None),
        )
    )
    tasks = result.scalars().all()
    
    from collections import Counter
    domain_counter: Counter = Counter()
    
    for task in tasks:
        if task.websites_visited:
            for domain in task.websites_visited:
                if domain:
                    domain_counter[domain] += 1
    
    return [
        SiteVisit(domain=domain, visit_count=count)
        for domain, count in domain_counter.most_common(limit)
    ]


@router.get("/execution-times")
async def get_execution_time_distribution(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get execution time distribution across completed tasks."""
    result = await db.execute(
        select(Task).where(
            Task.user_id == current_user.id,
            Task.status == TaskStatus.COMPLETED,
            Task.execution_time_ms.isnot(None),
        ).order_by(Task.created_at.desc()).limit(50)
    )
    tasks = result.scalars().all()
    
    return [
        {
            "task_id": t.id,
            "prompt": t.prompt[:50] + "..." if len(t.prompt) > 50 else t.prompt,
            "execution_time_ms": t.execution_time_ms,
            "success_rate": t.success_rate,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in tasks
    ]
