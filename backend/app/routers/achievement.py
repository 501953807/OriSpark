"""成就徽章与排行榜路由."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import ApiResponse
from app.deps import require_auth
from app.services.achievement_service import (
    get_available_badges,
    unlock_achievement,
    get_user_achievements,
    get_leaderboard,
    update_leaderboard,
)

router = APIRouter(prefix="/growth", tags=["achievements-leaderboard"])


@router.get("/badges", response_model=ApiResponse[list])
def list_badges(db: Session = Depends(get_db)):
    """获取所有可用成就徽章."""
    return ApiResponse(data=get_available_badges(db))


@router.post("/badges/{badge_key}/unlock", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def unlock_badge(
    badge_key: str,
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """解锁成就徽章."""
    result = unlock_achievement(user_id, badge_key, db)
    if not result:
        raise HTTPException(status_code=404, detail="徽章不存在或未激活")
    return ApiResponse(data=result, message=f"成就已解锁: {result['badge_name']}")


@router.get("/achievements", response_model=ApiResponse[list], dependencies=[Depends(require_auth)])
def my_achievements(user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    """获取用户已获得的成就."""
    return ApiResponse(data=get_user_achievements(user_id, db))


@router.get("/leaderboard", response_model=ApiResponse[list])
def leaderboard(
    creator_type: str = Query("illustrator", description="创作者类型"),
    period: str = Query("monthly", regex="^(weekly|monthly|all_time)$"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """获取排行榜."""
    return ApiResponse(data=get_leaderboard(creator_type, period, limit))


@router.post("/leaderboard/update", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def refresh_leaderboard(
    creator_type: str = Query(...),
    period: str = Query("monthly", regex="^(weekly|monthly|all_time)$"),
    db: Session = Depends(get_db),
):
    """刷新排行榜数据."""
    entries = update_leaderboard(creator_type, period, db)
    return ApiResponse(data={"entries": entries}, message="排行榜已更新")
