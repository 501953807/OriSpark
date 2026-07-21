from sqlalchemy.orm import Session

from app.models.credit import (
    CreditRating, CreditBehavior, BEHAVIOR_SCORES, apply_behavior,
)


def get_or_create_rating(db: Session, user_id: str, user_type: str) -> CreditRating:
    """获取或创建信用评级."""
    rating = db.query(CreditRating).filter(
        CreditRating.user_id == user_id,
        CreditRating.user_type == user_type,
    ).first()
    if not rating:
        rating = CreditRating(user_id=user_id, user_type=user_type, total_score=100)
        db.add(rating)
        # Don't commit here — let record_behavior handle the single commit
    return rating


def record_behavior(db: Session, req: dict) -> tuple[CreditRating, CreditBehavior]:
    """记录一条信用行为并更新评分."""
    rating = get_or_create_rating(db, req["user_id"], req.get("user_type", "creator"))

    behavior_type = req["behavior_type"]
    score_delta = req.get("score_delta", BEHAVIOR_SCORES.get(behavior_type, 0))

    behavior = CreditBehavior(
        rating_id=rating.id,
        user_id=req["user_id"],
        behavior_type=behavior_type,
        score_delta=score_delta,
        related_transaction_id=req.get("related_transaction_id"),
        description=req.get("description"),
    )
    db.add(behavior)

    rating = apply_behavior(rating, behavior_type, score_delta)

    db.commit()
    db.refresh(rating)
    db.refresh(behavior)
    return rating, behavior


def get_rating_by_user(db: Session, user_id: str) -> CreditRating | None:
    """按用户ID查询信用评级."""
    return db.query(CreditRating).filter(CreditRating.user_id == user_id).first()


def get_behaviors(db: Session, user_id: str, limit: int = 50) -> list[CreditBehavior]:
    """查询用户信用行为记录."""
    return (db.query(CreditBehavior)
            .filter(CreditBehavior.user_id == user_id)
            .order_by(CreditBehavior.created_at.desc())
            .limit(limit)
            .all())


def get_improvement_suggestions(user_id: str, db: Session) -> dict:
    """获取信用提升建议 — 基于当前信用评级和行为历史."""
    rating = get_rating_by_user(db, user_id)
    if not rating:
        return {
            "user_id": user_id,
            "current_score": None,
            "tier": None,
            "suggestions": [
                {"priority": "high", "title": "创建信用评级", "description": "您还没有信用评级，建议先建立信用档案。"},
                {"priority": "medium", "title": "完善个人资料", "description": "补充创作者信息以提高可信度。"},
            ],
        }

    behaviors = get_behaviors(db, user_id, limit=100)

    # 分析行为模式
    recent_30 = [b for b in behaviors if b.created_at and (datetime.utcnow() - b.created_at).days <= 30]
    recent_7 = [b for b in behaviors if b.created_at and (datetime.utcnow() - b.created_at).days <= 7]

    # 计算关键指标
    total_positive = sum(b.score_delta for b in behaviors if b.score_delta > 0)
    total_negative = abs(sum(b.score_delta for b in behaviors if b.score_delta < 0))
    dispute_count = sum(1 for b in behaviors if b.behavior_type == BehaviorType.DISPUTE_RAISED)
    late_delivery_count = sum(1 for b in behaviors if b.behavior_type == BehaviorType.LATE_DELIVERY)
    bad_review_count = sum(1 for b in behaviors if b.behavior_type == BehaviorType.BAD_REVIEW)

    suggestions = []

    # 根据信用等级给出建议
    if rating.tier == CreditTier.NEWBIE:
        suggestions.append({
            "priority": "high",
            "title": "提升信用等级",
            "description": f"您当前是新手等级（{rating.total_score}分），建议通过完成交易和准时交付来提升。",
            "action": "完成至少 3 笔交易并准时交付",
        })

    if rating.total_score < 100:
        suggestions.append({
            "priority": "high",
            "title": "信用评分较低",
            "description": f"您的信用评分为 {rating.total_score} 分，低于良好等级（100分）。",
            "action": "避免违约和纠纷，保持良好履约记录",
        })

    if dispute_count > 0:
        suggestions.append({
            "priority": "high",
            "title": "减少纠纷",
            "description": f"近期有 {dispute_count} 次纠纷记录，这会严重影响信用评级。",
            "action": "加强合同管理，明确交付标准，及时沟通",
        })

    if late_delivery_count > 0:
        suggestions.append({
            "priority": "high",
            "title": "提高准时交付率",
            "description": f"有 {late_delivery_count} 次迟到交付记录。",
            "action": "合理安排工作时间，设置交付提醒，预留缓冲时间",
        })

    if bad_review_count > 0:
        suggestions.append({
            "priority": "medium",
            "title": "改善客户评价",
            "description": f"有 {bad_review_count} 次差评记录。",
            "action": "主动收集反馈，及时改进服务质量",
        })

    if total_negative > total_positive * 1.5:
        suggestions.append({
            "priority": "high",
            "title": "负面行为过多",
            "description": "负面行为累计超过正面行为的 1.5 倍，需要重点改善。",
            "action": "暂停高风险操作，专注于建立正面记录",
        })

    if len(recent_7) == 0 and len(behaviors) > 0:
        suggestions.append({
            "priority": "medium",
            "title": "增加近期活跃度",
            "description": "最近 7 天没有新的信用行为记录。",
            "action": "继续完成交易或积累正面行为",
        })

    # 通用建议
    suggestions.append({
        "priority": "low",
        "title": "保持良好记录",
        "description": "持续的正面行为会逐步提升信用评级。",
        "action": "按时交付、积极沟通、遵守平台规则",
    })

    return {
        "user_id": user_id,
        "current_score": rating.total_score,
        "tier": rating.tier,
        "transaction_count": rating.transaction_count,
        "successful_transactions": rating.successful_transactions,
        "dispute_count": rating.dispute_count,
        "recent_30_days": len(recent_30),
        "recent_7_days": len(recent_7),
        "suggestions": suggestions,
    }
