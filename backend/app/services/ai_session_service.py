"""AI 创作会话对比与批量导入服务."""

from sqlalchemy.orm import Session
from app.models.ai_session import AiCreationSession


def compare_sessions(db: Session, session_a_id: str, session_b_id: str) -> dict:
    """并排比较两个会话的参数差异."""
    a = db.query(AiCreationSession).filter(AiCreationSession.id == session_a_id).first()
    b = db.query(AiCreationSession).filter(AiCreationSession.id == session_b_id).first()
    if not a or not b:
        raise ValueError("会话不存在")

    differences = {}
    fields = ["tool_name", "tool_version", "prompt", "seed", "negative_prompt", "model_name"]
    json_fields = ["parameters", "lora_names", "output_images", "human_interventions"]

    for f in fields:
        va, vb = getattr(a, f), getattr(b, f)
        if va != vb:
            differences[f] = {"session_a": va, "session_b": vb}

    for f in json_fields:
        va, vb = getattr(a, f), getattr(b, f)
        if va != vb:
            differences[f] = {"session_a": va, "session_b": vb}

    return {
        "session_a": {
            "id": a.id, "tool_name": a.tool_name, "model_name": a.model_name,
            "seed": a.seed, "prompt": a.prompt, "created_at": a.created_at.isoformat() if a.created_at else None,
        },
        "session_b": {
            "id": b.id, "tool_name": b.tool_name, "model_name": b.model_name,
            "seed": b.seed, "prompt": b.prompt, "created_at": b.created_at.isoformat() if b.created_at else None,
        },
        "differences": differences,
    }


def batch_import_sessions(work_id: str, imports: list[dict], db: Session) -> dict:
    """批量导入外部工具会话记录（Midjourney/StableDiffusion/DALL-E）."""
    created = 0
    skipped = 0
    errors = []

    for item in imports:
        try:
            if not item.get("prompt") and not item.get("seed"):
                skipped += 1
                continue

            session = AiCreationSession(
                work_id=work_id,
                tool_name=item.get("tool_name", "Unknown"),
                tool_version=item.get("tool_version"),
                prompt=item.get("prompt"),
                prompt_history=item.get("prompt_history"),
                seed=item.get("seed"),
                parameters=item.get("parameters"),
                negative_prompt=item.get("negative_prompt"),
                model_name=item.get("model_name"),
                lora_names=item.get("lora_names"),
                output_images=item.get("output_images"),
                human_interventions=item.get("human_interventions"),
            )
            db.add(session)
            created += 1
        except Exception as e:
            errors.append(f"导入失败 [{item.get('tool_name', 'unknown')}]: {str(e)}")

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"created": created, "skipped": skipped, "errors": errors}
