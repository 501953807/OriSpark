"""多平台内容分发流水线路由."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.database import get_db
from app.schemas.content_pipeline import (
    PlatformAccountCreate, PlatformAccountResponse,
    ScheduleCreate, PublishScheduleResponse,
    SimulateResult, PublishStats,
)
from app.services.content_pipeline_service import (
    list_accounts, add_account, remove_account,
    get_scheduled_publishes, create_schedule, cancel_schedule,
    simulate_publish, get_publish_stats,
)
from app.models.content_pipeline import PlatformAccount

router = APIRouter(prefix="/content-pipeline", tags=["content-pipeline"])


@router.get("/accounts", response_model=list[PlatformAccountResponse])
def list_platform_accounts(db: Session = Depends(get_db)):
    """获取已绑定的平台账号列表."""
    return list_accounts(db, "current_user")


@router.post("/accounts", response_model=PlatformAccountResponse)
def add_platform_account(data: PlatformAccountCreate, db: Session = Depends(get_db)):
    """绑定第三方平台账号."""
    result = add_account(
        db, "current_user",
        platform=data.platform,
        account_name=data.account_name,
        account_id=data.account_id,
        follower_count=data.follower_count,
    )
    acc = db.query(PlatformAccount).filter(PlatformAccount.id == result["id"]).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Failed to retrieve account")
    return acc


@router.delete("/accounts/{platform}")
def delete_platform_account(platform: str, db: Session = Depends(get_db)):
    """解绑平台账号."""
    if not remove_account(db, "current_user", platform):
        raise HTTPException(status_code=404, detail="Account not found")
    return {"message": f"Account {platform} removed"}


@router.get("/schedules", response_model=list[PublishScheduleResponse])
def list_schedules(status: Optional[str] = None, db: Session = Depends(get_db)):
    """获取定时发布计划列表."""
    return get_scheduled_publishes(db, "current_user", status)


@router.post("/schedules", response_model=dict)
def create_schedule(data: ScheduleCreate, db: Session = Depends(get_db)):
    """创建定时发布计划."""
    scheduled_at = datetime.fromisoformat(data.scheduled_at)
    return create_schedule(
        db, "current_user",
        title=data.title,
        description=data.description,
        work_id=data.work_id,
        platforms=data.platforms,
        scheduled_at=scheduled_at,
        is_recurring=data.is_recurring,
        recurring_pattern=data.recurring_pattern,
    )


@router.delete("/schedules/{schedule_id}")
def cancel_schedule_endpoint(schedule_id: str, db: Session = Depends(get_db)):
    """取消发布计划."""
    if not cancel_schedule(db, "current_user", schedule_id):
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"message": "Schedule cancelled"}


@router.post("/simulate")
def simulate_multiplatform_publish(data: ScheduleCreate):
    """模拟发布到多个平台，返回适配建议."""
    platform_names = [p.get("platform", "") for p in data.platforms]
    results = simulate_publish(data.title, data.description, platform_names)
    return {"adaptations": results}


@router.get("/stats", response_model=PublishStats)
def get_stats(db: Session = Depends(get_db)):
    """获取发布统计信息."""
    return get_publish_stats(db, "current_user")
