"""创作者导航服务层 — 进度引擎 + 表达式评估."""

import re
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.navigation import NavigationTask, CreatorNavigation
from app.schemas.navigation import NavigationTaskSchema


def _safe_eval_expression(expression: str, context: dict) -> bool:
    """安全评估检查表达式，禁用所有 builtins."""
    if not expression:
        return False
    try:
        result = eval(expression, {"__builtins__": {}}, context)
        return bool(result)
    except Exception:
        return False


def _get_current_task_key(completed_tasks: list[str], category: str, tasks: list[NavigationTask]) -> Optional[str]:
    """获取当前进行中的任务 key（第一个未完成的）."""
    for task in sorted(tasks, key=lambda t: t.priority):
        if task.category == category and task.task_key not in completed_tasks:
            return task.task_key
    return None


def get_navigation_status(
    db: Session,
    user_id: str,
    active_path: str = "onboarding",
) -> dict:
    """获取创作者导航状态."""
    # 确保用户导航记录存在
    nav = (
        db.query(CreatorNavigation)
        .filter(CreatorNavigation.user_id == user_id)
        .first()
    )
    if not nav:
        nav = CreatorNavigation(
            user_id=user_id,
            active_path=active_path,
            completed_tasks=[],
            progress_percent=0.0,
        )
        db.add(nav)
        db.commit()
        db.refresh(nav)

    # 获取当前路径的任务列表
    tasks = (
        db.query(NavigationTask)
        .filter(NavigationTask.category == active_path)
        .all()
    )

    completed_keys = nav.completed_tasks or []
    total = len(tasks)

    # 计算进度
    progress_percent = round((len(completed_keys) / total * 100) if total > 0 else 0.0, 1)

    # 更新当前任务
    current_task_key = _get_current_task_key(completed_keys, active_path, tasks)
    nav.current_task_key = current_task_key
    nav.progress_percent = progress_percent
    nav.active_path = active_path
    db.commit()

    # 构建响应
    completed_tasks = []
    remaining_tasks = []

    for task in sorted(tasks, key=lambda t: t.priority):
        is_checked = task.task_key in completed_keys
        task_schema = NavigationTaskSchema(
            task_key=task.task_key,
            category=task.category,
            title=task.title,
            description=task.description,
            priority=task.priority,
            is_checked=is_checked,
        )
        if is_checked:
            completed_tasks.append(task_schema)
        else:
            remaining_tasks.append(task_schema)

    current_task_obj = None
    if current_task_key and remaining_tasks:
        current_task_obj = next(
            (t for t in remaining_tasks if t.task_key == current_task_key),
            remaining_tasks[0] if remaining_tasks else None,
        )

    return {
        "active_path": nav.active_path,
        "progress_percent": progress_percent,
        "current_task": current_task_obj,
        "completed_tasks": completed_tasks,
        "remaining_tasks": remaining_tasks,
        "last_completed_at": nav.last_completed_at,
    }


def complete_task(db: Session, user_id: str, task_key: str, context: Optional[dict] = None) -> dict:
    """标记任务为已完成."""
    nav = (
        db.query(CreatorNavigation)
        .filter(CreatorNavigation.user_id == user_id)
        .first()
    )
    if not nav:
        return {"error": "No navigation record found"}

    # 验证任务是否存在于当前路径
    active_path = nav.active_path or "onboarding"
    task = (
        db.query(NavigationTask)
        .filter(
            NavigationTask.task_key == task_key,
            NavigationTask.category == active_path,
        )
        .first()
    )
    if not task:
        return {"error": f"Task '{task_key}' not found in path '{active_path}'"}

    # 检查是否已完成
    completed_keys = nav.completed_tasks or []
    if task_key in completed_keys:
        return {"status": "already_completed", "task_key": task_key}

    # 安全检查表达式
    if task.check_expression:
        if not _safe_eval_expression(task.check_expression, context or {}):
            return {"error": "Preconditions not met for this task"}

    # 标记完成
    completed_keys.append(task_key)
    nav.completed_tasks = completed_keys
    nav.last_completed_at = datetime.utcnow()

    # 重新计算进度
    tasks = (
        db.query(NavigationTask)
        .filter(NavigationTask.category == active_path)
        .all()
    )
    total = len(tasks)
    progress_percent = round((len(completed_keys) / total * 100) if total > 0 else 0.0, 1)
    nav.progress_percent = progress_percent

    # 查找下一个任务
    next_task_key = _get_current_task_key(completed_keys, active_path, tasks)
    next_task_obj = None
    if next_task_key:
        next_task = next((t for t in tasks if t.task_key == next_task_key), None)
        if next_task:
            next_task_obj = NavigationTaskSchema(
                task_key=next_task.task_key,
                category=next_task.category,
                title=next_task.title,
                priority=next_task.priority,
                is_checked=False,
            )

    db.commit()

    return {
        "status": "completed",
        "task_key": task_key,
        "new_progress": progress_percent,
        "next_task": next_task_obj,
    }


def switch_path(db: Session, user_id: str, new_path: str) -> dict:
    """切换活跃路径."""
    valid_paths = ["onboarding", "compliance", "growth"]
    if new_path not in valid_paths:
        return {"error": f"Invalid path '{new_path}'. Must be one of: {valid_paths}"}

    nav = (
        db.query(CreatorNavigation)
        .filter(CreatorNavigation.user_id == user_id)
        .first()
    )
    if not nav:
        nav = CreatorNavigation(user_id=user_id, active_path=new_path)
        db.add(nav)
    else:
        nav.active_path = new_path

    db.commit()
    db.refresh(nav)

    task_count = (
        db.query(NavigationTask)
        .filter(NavigationTask.category == new_path)
        .count()
    )

    return {"active_path": new_path, "task_count": task_count}
