"""多平台内容分发流水线路由."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.database import get_db
from app.deps import get_current_user_id
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
def list_platform_accounts(actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """获取已绑定的平台账号列表."""
    result = list_accounts(db, actor_id)
    AuditLog.log(db, "list_platform_accounts", f"Listed accounts by {actor_id}", actor_id)
    return result


@router.post("/accounts", response_model=PlatformAccountResponse)
def add_platform_account(data: PlatformAccountCreate, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """绑定第三方平台账号."""
    result = add_account(
        db, actor_id,
        platform=data.platform,
        account_name=data.account_name,
        account_id=data.account_id,
        follower_count=data.follower_count,
    )
    acc = db.query(PlatformAccount).filter(PlatformAccount.id == result["id"]).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Failed to retrieve account")
    AuditLog.log(db, "add_platform_account", f"Added account for {data.platform} by {actor_id}", actor_id)
    return acc


@router.delete("/accounts/{platform}")
def delete_platform_account(platform: str, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """解绑平台账号."""
    if not remove_account(db, actor_id, platform):
        raise HTTPException(status_code=404, detail="Account not found")
    AuditLog.log(db, "remove_platform_account", f"Removed account {platform} by {actor_id}", actor_id)
    return {"message": f"Account {platform} removed"}


@router.get("/schedules", response_model=list[PublishScheduleResponse])
def list_schedules(status: Optional[str] = None, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """获取定时发布计划列表."""
    result = get_scheduled_publishes(db, actor_id, status)
    AuditLog.log(db, "list_schedules", f"Scheduled publishes by {actor_id}", actor_id)
    return result


@router.post("/schedules", response_model=dict)
def create_schedule(data: ScheduleCreate, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """创建定时发布计划."""
    scheduled_at = datetime.fromisoformat(data.scheduled_at)
    result = create_schedule(
        db, actor_id,
        title=data.title,
        description=data.description,
        work_id=data.work_id,
        platforms=data.platforms,
        scheduled_at=scheduled_at,
        is_recurring=data.is_recurring,
        recurring_pattern=data.recurring_pattern,
    )
    AuditLog.log(db, "create_schedule", f"Created schedule by {actor_id}", actor_id)
    return result


@router.delete("/schedules/{schedule_id}")
def cancel_schedule_endpoint(schedule_id: str, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """取消发布计划."""
    if not cancel_schedule(db, actor_id, schedule_id):
        raise HTTPException(404, "Schedule not found or unauthorized")
    AuditLog.log(db, "cancel_schedule", f"Canceled schedule {schedule_id} by {actor_id}", actor_id)
    return {"message": "Schedule cancelled"}


@router.post("/simulate")
def simulate_multiplatform_publish(data: ScheduleCreate):
    """模拟发布到多个平台，返回适配建议."""
    platform_names = [p.get("platform", "") for p in data.platforms]
    results = simulate_publish(data.title, data.description, platform_names)
    return {"adaptations": results}


@router.get("/stats", response_model=PublishStats)
def get_stats(actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """获取发布统计信息."""
    result = get_publish_stats(db, actor_id)
    AuditLog.log(db, "publish_stats", f"Viewed publish stats by {actor_id}", actor_id)
    return result
