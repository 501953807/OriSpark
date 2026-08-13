"""作品 AI 描述生成 API 路由."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user_id, require_auth
from app.schemas.common import ApiResponse
from app.services.describe_work_service import DescribeWorkService

router = APIRouter(prefix="/api", tags=["AIDescribe"])


class DescribeWorkRequest(BaseModel):
    options: dict | None = None


@router.post("/works/{work_id}/describe", response_model=ApiResponse)
async def describe_work(
    work_id: str,
    data: DescribeWorkRequest,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    """AI 生成作品描述."""
    svc = DescribeWorkService()
    try:
        result = await svc.describe_work(db, work_id, data.options or {})
        return ApiResponse(data=result, message="描述生成成功")
    except ValueError as e:
        raise HTTPException(status_code=404, detail="描述操作失败，请稍后重试")
    except Exception as e:
        return ApiResponse(data=None, message=f"描述生成失败: {e}")
