"""
Reports API – Download generated task reports
"""

import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.task import Task
from app.models.session import Report

router = APIRouter()


class ReportResponse(BaseModel):
    id: int
    task_id: int
    format: str
    filename: str
    file_size: int
    created_at: str

    class Config:
        from_attributes = True


@router.get("/{task_id}", response_model=List[ReportResponse])
async def list_task_reports(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all reports for a given task."""
    # Verify task ownership
    task_result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == current_user.id)
    )
    if not task_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Task not found")
    
    result = await db.execute(select(Report).where(Report.task_id == task_id))
    reports = result.scalars().all()
    
    return [
        {
            "id": r.id,
            "task_id": r.task_id,
            "format": r.format.value,
            "filename": r.filename,
            "file_size": r.file_size or 0,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in reports
    ]


@router.get("/{task_id}/download/{format}")
async def download_report(
    task_id: int,
    format: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download a specific report format for a task."""
    # Verify task ownership
    task_result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == current_user.id)
    )
    if not task_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Task not found")
    
    result = await db.execute(
        select(Report).where(Report.task_id == task_id, Report.format == format)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail=f"No {format.upper()} report found for this task")
    
    if not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="Report file not found on disk")
    
    media_types = {
        "pdf": "application/pdf",
        "csv": "text/csv",
        "json": "application/json",
    }
    
    return FileResponse(
        path=report.file_path,
        filename=report.filename,
        media_type=media_types.get(format, "application/octet-stream"),
    )
