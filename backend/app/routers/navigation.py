"""创作者导航 API 路由."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
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

router = APIRouter(prefix="/api/navigation", tags=["navigation"])


@router.get("/status/{user_id}", response_model=NavigationStatusResponse)
def get_status(user_id: str, path: str = "onboarding", db: Session = Depends(get_db)):
    """获取创作者导航状态."""
    result = get_navigation_status(db, user_id, active_path=path)
    return NavigationStatusResponse(**result)


@router.post("/complete/{task_key}")
def mark_complete(task_key: str, db: Session = Depends(get_db)):
    """标记任务为已完成."""
    result = complete_task(db, user_id="current_user", task_key=task_key)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/tasks")
def list_tasks(category: str = "onboarding", db: Session = Depends(get_db)):
    """获取任务列表."""
    from app.models.navigation import NavigationTask
    tasks = (
        db.query(NavigationTask)
        .filter(NavigationTask.category == category)
        .order_by(NavigationTask.priority)
        .all()
    )
    return [NavigationTaskSchema(
        task_key=t.task_key,
        category=t.category,
        title=t.title,
        description=t.description,
        priority=t.priority,
        is_checked=False,
    ) for t in tasks]


@router.post("/switch-path")
def do_switch(body: SwitchPathRequest, db: Session = Depends(get_db)):
    """切换活跃路径."""
    result = switch_path(db, user_id="current_user", new_path=body.path)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
