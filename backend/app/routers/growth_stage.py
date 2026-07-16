"""创作者成长阶段路由."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.growth_stage import GrowthStageResponse, GrowthTaskResponse, ProgressDashboard
from app.services.growth_stage_service import get_progress_dashboard, update_growth_stage, complete_task

router = APIRouter(prefix="/api/growth-stages", tags=["growth-stages"])

USER_ID = "current_user"


@router.get("/dashboard", response_model=ProgressDashboard)
def dashboard(db: Session = Depends(get_db)):
    """获取成长进度仪表盘."""
    return get_progress_dashboard(db, USER_ID)


@router.put("/update", response_model=dict)
def update(data: dict, db: Session = Depends(get_db)):
    """更新成长指标."""
    return update_growth_stage(db, USER_ID, data)


@router.patch("/tasks/{task_id}/complete")
def mark_complete(task_id: str, db: Session = Depends(get_db)):
    """标记任务完成."""
    return complete_task(db, USER_ID, task_id)
