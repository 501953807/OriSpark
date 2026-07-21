"""AI 创作会话 v2 — 对比与批量导入路由."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.ai_session import AiCreationSession
from app.schemas.common import ApiResponse
from app.deps import require_auth
from app.services.ai_session_service import compare_sessions, batch_import_sessions

router = APIRouter(prefix="/works", tags=["ai-sessions-v2"])


class BatchImportPayload(BaseModel):
    tool_name: str = Field(..., max_length=100)
    tool_version: str | None = None
    prompt: str | None = None
    seed: int | None = None
    parameters: dict | None = None
    negative_prompt: str | None = None
    model_name: str | None = None
    lora_names: list[str] | None = None
    output_images: int | list[str] | None = None
    human_interventions: list[str] | None = None


@router.get("/{work_id}/ai-sessions/{session_a_id}/compare/{session_b_id}", response_model=ApiResponse[dict])
def compare_ai_sessions(
    work_id: str,
    session_a_id: str,
    session_b_id: str,
    db: Session = Depends(get_db),
):
    """并排比较两个 AI 创作会话的参数差异."""
    a = db.query(AiCreationSession).filter(
        AiCreationSession.id == session_a_id,
        AiCreationSession.work_id == work_id,
    ).first()
    b = db.query(AiCreationSession).filter(
        AiCreationSession.id == session_b_id,
        AiCreationSession.work_id == work_id,
    ).first()
    if not a or not b:
        raise HTTPException(status_code=404, detail="会话记录不存在")

    result = compare_sessions(db, session_a_id, session_b_id)
    return ApiResponse(data=result)


@router.post("/{work_id}/ai-sessions/batch-import", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def batch_import_ai_sessions(
    work_id: str,
    imports: list[BatchImportPayload],
    db: Session = Depends(get_db),
):
    """批量导入外部工具会话记录（Midjourney/StableDiffusion/DALL-E）."""
    work = db.query(AiCreationSession).filter(AiCreationSession.work_id == work_id).first()
    # work check is implicit; sessions will be linked to work_id

    payload = [i.model_dump() for i in imports]
    result = batch_import_sessions(work_id, payload, db)
    return ApiResponse(data=result, message=f"批量导入完成: {result['created']} 条已创建")
