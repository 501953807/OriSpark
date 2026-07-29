"""创作者成长阶段路由."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user_id
from app.schemas.growth_stage import GrowthStageResponse, GrowthTaskResponse, ProgressDashboard
from app.services.growth_stage_service import get_progress_dashboard, update_growth_stage, complete_task
from app.utils.audit import AuditLog

router = APIRouter(prefix="/growth-stages", tags=["growth-stages"])


@router.get("/dashboard", response_model=ProgressDashboard)
def dashboard(actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """获取成长进度仪表盘."""
    # 🔑 Log dashboard access
    AuditLog.log(db, "view_growth_dashboard", f"Viewed growth dashboard by {actor_id}", actor_id)
    return get_progress_dashboard(db, actor_id)


@router.put("/update", response_model=dict)
def update(data: dict, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """更新成长指标."""
    result = update_growth_stage(db, actor_id, data)
    # 🔑 Log growth update
    AuditLog.log(db, "update_growth_stage", f"Updated growth metrics for {actor_id}", actor_id)
    return result


@router.patch("/tasks/{task_id}/complete")
def mark_complete(task_id: str, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """标记任务完成."""
    result = complete_task(db, user_id=actor_id, task_key=task_id)
    # 🔑 Log task completion
    AuditLog.log(db, "complete_growth_task", f"Completed task {task_id} by {actor_id}", actor_id)
    return result
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
