"""AI 创作会话 API 路由 — Phase 0."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.work import Work
from app.models.ai_session import AiCreationSession
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/api/works", tags=["ai-sessions"])


@router.post("/{work_id}/ai-session", response_model=ApiResponse)
def create_ai_session(
    work_id: str,
    data: dict,
    db: Session = Depends(get_db),
):
    """记录 AI 创作会话."""
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    if "tool_name" not in data or "prompt" not in data:
        raise HTTPException(status_code=400, detail="tool_name 和 prompt 为必填项")

    session = AiCreationSession(
        work_id=work_id,
        tool_name=data["tool_name"],
        tool_version=data.get("tool_version"),
        prompt=data["prompt"],
        prompt_history=data.get("prompt_history"),
        seed=data.get("seed"),
        parameters=data.get("parameters"),
        negative_prompt=data.get("negative_prompt"),
        model_name=data.get("model_name"),
        lora_names=data.get("lora_names"),
        output_images=data.get("output_images"),
        human_interventions=data.get("human_interventions"),
    )
    db.add(session)

    work.ai_assisted = True
    tools = work.ai_tools_used or []
    if not any(t.get("name") == data["tool_name"] for t in tools):
        tools.append({"name": data["tool_name"], "version": data.get("tool_version")})
    work.ai_tools_used = tools

    db.commit()
    db.refresh(session)

    return ApiResponse(message="创作会话记录成功", data={"id": session.id})


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
                "tool_name": s.tool_name,
                "tool_version": s.tool_version,
                "prompt": s.prompt,
                "seed": s.seed,
                "model_name": s.model_name,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in sessions
        ],
    )


@router.patch("/{work_id}/ai-session/{session_id}", response_model=ApiResponse)
def update_ai_session(
    work_id: str,
    session_id: str,
    data: dict,
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
        if key in data:
            setattr(session, key, data[key])

    db.commit()
    db.refresh(session)
    return ApiResponse(message="会话记录更新成功")


@router.delete("/{work_id}/ai-session/{session_id}", response_model=ApiResponse)
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
    db.commit()
    return ApiResponse(message="会话记录已删除")
