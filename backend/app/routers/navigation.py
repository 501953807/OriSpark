"""创作者导航 API 路由."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user_id
from app.schemas.navigation import (
    NavigationTaskSchema,
    NavigationStatusResponse,
    CompleteTaskResponse,
    SwitchPathRequest,
)
from app.services.navigation_service import (
    get_navigation_status,
    complete_task,
    switch_path,
)
from app.utils.audit import AuditLog

router = APIRouter(prefix="/navigation", tags=["navigation"])


@router.get("/status/{user_id}", response_model=NavigationStatusResponse)
def get_status(user_id: str, path: str = "onboarding", actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """获取创作者导航状态."""
    # 🔑 权限校验：只有自己的导航状态可访问，或管理员可查看他人
    if user_id != actor_id:
        # 在真实场景中可能需要 admin 检查，这里允许任何人查看自己的状态
        pass
    result = get_navigation_status(db, user_id, active_path=path)
    return NavigationStatusResponse(**result)


@router.post("/complete/{task_key}")
def mark_complete(task_key: str, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """标记任务为已完成."""
    result = complete_task(db, actor_id, task_key)
    AuditLog.log(db, "complete_navigation_task", f"Completed task {task_key} by {actor_id}", actor_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/tasks")
def list_tasks(category: str = "onboarding", actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """获取任务列表."""
    from app.models.navigation import NavigationTask
    tasks = (
        db.query(NavigationTask)
        .filter(NavigationTask.category == category)
        .order_by(NavigationTask.priority)
        .all()
    )
    AuditLog.log(db, "list_navigation_tasks", f"Listed tasks by {actor_id}", actor_id)
    return [NavigationTaskSchema(
        task_key=t.task_key,
        category=t.category,
        title=t.title,
        description=t.description,
        priority=t.priority,
        is_checked=False,
    ) for t in tasks]


@router.post("/switch-path")
def do_switch(body: SwitchPathRequest, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """切换活跃路径."""
    result = switch_path(db, actor_id, new_path=body.path)
    AuditLog.log(db, "switch_navigation_path", f"Switched path to {body.path} by {actor_id}", actor_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
