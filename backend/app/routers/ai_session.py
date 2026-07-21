"""AI 创作会话 API 路由 — Phase 0."""

from typing import Optional, Union

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.work import Work
from app.models.ai_session import AiCreationSession
from app.schemas.common import ApiResponse
from app.deps import require_auth

router = APIRouter(prefix="/works", tags=["ai-sessions"])


class AiSessionCreate(BaseModel):
    tool_name: str
    prompt: Optional[str] = None
    tool_version: Optional[str] = None
    prompt_history: Optional[str] = None
    seed: Optional[int] = None
    parameters: Optional[dict] = None
    negative_prompt: Optional[str] = None
    model_name: Optional[str] = None
    lora_names: Optional[list[str]] = None
    output_images: Optional[Union[int, list[str]]] = None
    human_interventions: Optional[list[str]] = None


class AiSessionResponse(BaseModel):
    id: str
    work_id: str
    tool_name: str
    tool_version: Optional[str] = None
    prompt: Optional[str] = None
    prompt_history: Optional[str] = None
    seed: Optional[int] = None
    parameters: Optional[dict] = None
    negative_prompt: Optional[str] = None
    model_name: Optional[str] = None
    lora_names: Optional[list[str]] = None
    output_images: Optional[Union[int, list[str]]] = None
    human_interventions: Optional[list[str]] = None
    created_at: str
    updated_at: Optional[str] = None

    model_config = {"from_attributes": True}


@router.post("/{work_id}/ai-session", response_model=ApiResponse[AiSessionResponse], dependencies=[Depends(require_auth)])
def create_ai_session(
    work_id: str,
    data: AiSessionCreate,
    db: Session = Depends(get_db),
):
    """记录 AI 创作会话."""
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    session = AiCreationSession(
        work_id=work_id,
        tool_name=data.tool_name,
        tool_version=data.tool_version,
        prompt=data.prompt,
        prompt_history=data.prompt_history,
        seed=data.seed,
        parameters=data.parameters,
        negative_prompt=data.negative_prompt,
        model_name=data.model_name,
        lora_names=data.lora_names,
        output_images=data.output_images,
        human_interventions=data.human_interventions,
    )
    db.add(session)

    work.ai_assisted = True
    tools = work.ai_tools_used or []
    if not any(t.get("name") == data.tool_name for t in tools):
        tools.append({"name": data.tool_name, "version": data.tool_version})
    work.ai_tools_used = tools

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(session)

    return ApiResponse(
        message="AI 创作会话已记录",
        data=AiSessionResponse(
            id=session.id,
            work_id=session.work_id,
            tool_name=session.tool_name,
            tool_version=session.tool_version,
            prompt=session.prompt,
            prompt_history=session.prompt_history,
            seed=session.seed,
            parameters=session.parameters,
            negative_prompt=session.negative_prompt,
            model_name=session.model_name,
            lora_names=session.lora_names,
            output_images=session.output_images,
            human_interventions=session.human_interventions,
            created_at=session.created_at.isoformat() if session.created_at else None,
            updated_at=session.updated_at.isoformat() if session.updated_at else None,
        ),
    )


@router.get("/{work_id}/ai-sessions", response_model=ApiResponse[list])
def list_ai_sessions(
    work_id: str,
    db: Session = Depends(get_db),
):
    """获取作品的 AI 创作时间线."""
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    sessions = (
        db.query(AiCreationSession)
        .filter(AiCreationSession.work_id == work_id)
        .order_by(AiCreationSession.created_at.asc())
        .all()
    )

    return ApiResponse(
        data=[
            {
                "id": s.id,
                "work_id": s.work_id,
                "tool_name": s.tool_name,
                "tool_version": s.tool_version,
                "prompt": s.prompt,
                "prompt_history": s.prompt_history,
                "seed": s.seed,
                "parameters": s.parameters,
                "negative_prompt": s.negative_prompt,
                "model_name": s.model_name,
                "lora_names": s.lora_names,
                "output_images": s.output_images,
                "human_interventions": s.human_interventions,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            }
            for s in sessions
        ],
    )


@router.patch("/{work_id}/ai-session/{session_id}", response_model=ApiResponse[AiSessionResponse], dependencies=[Depends(require_auth)])
def update_ai_session(
    work_id: str,
    session_id: str,
    data: AiSessionCreate,
    db: Session = Depends(get_db),
):
    """编辑创作会话记录."""
    session = (
        db.query(AiCreationSession)
        .filter(AiCreationSession.id == session_id, AiCreationSession.work_id == work_id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="会话记录不存在")

    for key in ["prompt", "tool_version", "parameters", "negative_prompt", "model_name",
                "lora_names", "output_images", "human_interventions"]:
        val = getattr(data, key, None)
        if val is not None:
            setattr(session, key, val)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(session)
    return ApiResponse(message="会话记录更新成功")


@router.delete("/{work_id}/ai-session/{session_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_ai_session(
    work_id: str,
    session_id: str,
    db: Session = Depends(get_db),
):
    """删除创作会话记录."""
    session = (
        db.query(AiCreationSession)
        .filter(AiCreationSession.id == session_id, AiCreationSession.work_id == work_id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="会话记录不存在")

    db.delete(session)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(message="会话记录已删除")
