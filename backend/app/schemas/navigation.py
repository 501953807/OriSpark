"""创作者导航 Pydantic schemas."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class NavigationTaskSchema(BaseModel):
    """导航任务响应."""
    task_key: str
    category: str
    title: str
    description: Optional[str] = None
    priority: int
    is_checked: bool = False


class NavigationStatusResponse(BaseModel):
    """导航状态响应."""
    active_path: str
    progress_percent: float
    current_task: Optional[NavigationTaskSchema] = None
    completed_tasks: list[NavigationTaskSchema]
    remaining_tasks: list[NavigationTaskSchema]
    last_completed_at: Optional[datetime] = None


class CompleteTaskResponse(BaseModel):
    """完成任务响应."""
    task_key: str
    status: str
    new_progress: float
    next_task: Optional[NavigationTaskSchema] = None


class SwitchPathRequest(BaseModel):
    """切换路径请求."""
    path: str
