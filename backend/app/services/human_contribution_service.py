"""人类贡献度评分器 — 区分人工/AI创作比例,支撑L1-L4防御策略选择."""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.ai_session import AiCreationSession
from app.models.contribution import HumanContributionScore
from app.models.mcp_client import ToolEvent


DECISION_THRESHOLDS = {
    "pass": 0.60,
    "declare": 0.40,
    "reject": 0.0,
}


def calculate_contribution_score(
    db: Session,
    work_id: str,
    author_id: str,
) -> dict:
    """计算人类贡献度评分.

    评分维度:
    1. AI 会话记录交叉验证 (权重 0.3)
    2. MCP 事件流分析 (权重 0.3)
    3. 自声明验证 (权重 0.2)
    4. 创作时长模式 (权重 0.2)

    阈值:
    - >= 0.60: 通过, 进入L3/L4版权防御
    - 0.40-0.60: 需声明, 进入L2平台工具监测
    - < 0.40: 不进入确权, 仅L1本地签名存证
    """
    scores: dict[str, float] = {}

    # 维度1: AI 会话记录交叉验证
    ai_score = _evaluate_ai_sessions(db, work_id, author_id)
    scores["ai_sessions"] = round(ai_score, 3)

    # 维度2: MCP 事件流分析
    mcp_score = _evaluate_mcp_events(db, work_id, author_id)
    scores["mcp_events"] = round(mcp_score, 3)

    # 维度3: 自声明验证
    self_declare_score = _evaluate_self_declaration(db, work_id, author_id)
    scores["self_declaration"] = round(self_declare_score, 3)

    # 维度4: 创作时长模式
    duration_score = _evaluate_creation_duration(db, work_id, author_id)
    scores["creation_duration"] = round(duration_score, 3)

    # 加权计算总分
    weights = {
        "ai_sessions": 0.3,
        "mcp_events": 0.3,
        "self_declaration": 0.2,
        "creation_duration": 0.2,
    }

    total = sum(scores[k] * weights[k] for k in weights)
    total = round(max(0.0, min(1.0, total)), 3)

    # 确定结论
    conclusion = _determine_conclusion(total)

    return {
        "work_id": work_id,
        "author_id": author_id,
        "total_score": total,
        "dimension_scores": scores,
        "thresholds": DECISION_THRESHOLDS,
        "conclusion": conclusion,
        "defense_tier_recommendation": conclusion["defense_tier"],
        "requires_disclosure": conclusion["requires_disclosure"],
        "eligible_for_registration": conclusion["eligible_for_registration"],
    }


def _evaluate_ai_sessions(
    db: Session,
    work_id: str,
    author_id: str,
) -> float:
    """评估 AI 会话记录对贡献度的影响."""
    sessions = (
        db.query(AiCreationSession)
        .filter(AiCreationSession.work_id == work_id)
        .all()
    )

    if not sessions:
        return 1.0  # 无 AI 会话记录, 满分

    ai_ratio = len(sessions) / max(1, len(sessions) + 1)
    # AI 会话越多, 人类贡献越低
    return max(0.0, 1.0 - ai_ratio * 0.8)


def _evaluate_mcp_events(
    db: Session,
    work_id: str,
    author_id: str,
) -> float:
    """评估 MCP 事件流对贡献度的影响."""
    events = (
        db.query(ToolEvent)
        .filter(ToolEvent.work_id == work_id)
        .filter(ToolEvent.user_id == author_id)
        .all()
    )

    if not events:
        return 0.8  # 无 MCP 事件, 中等分

    human_actions = sum(
        1 for e in events
        if e.event_type in ("file_upload", "edit", "tag", "comment")
    )
    ai_actions = sum(
        1 for e in events
        if e.event_type in ("ai_generate", "ai_edit", "ai_optimize")
    )
    total_actions = len(events)

    if total_actions == 0:
        return 0.8

    human_ratio = human_actions / total_actions
    return round(max(0.0, min(1.0, human_ratio * 0.9 + 0.1)), 3)


def _evaluate_self_declaration(
    db: Session,
    work_id: str,
    author_id: str,
) -> float:
    """评估自声明验证."""
    score_record = (
        db.query(HumanContributionScore)
        .filter(HumanContributionScore.work_id == work_id)
        .first()
    )

    if score_record:
        return score_record.verification_score
    return 0.5  # 无自声明记录, 中等分


def _evaluate_creation_duration(
    db: Session,
    work_id: str,
    author_id: str,
) -> float:
    """评估创作时长模式."""
    sessions = (
        db.query(AiCreationSession)
        .filter(AiCreationSession.work_id == work_id)
        .all()
    )

    if not sessions:
        return 1.0  # 无 AI 会话, 人类独立创作

    # 使用 created_at 跨度估算创作时长
    timestamps = [s.created_at for s in sessions if s.created_at]
    if len(timestamps) < 2:
        return 0.7  # 只有少量会话, 中等分

    timestamps.sort()
    total_duration = (timestamps[-1] - timestamps[0]).total_seconds()

    # 创作时长越长, 人类贡献越高
    if total_duration > 3600:  # > 1小时
        return 1.0
    elif total_duration > 600:  # > 10分钟
        return 0.8
    elif total_duration > 60:  # > 1分钟
        return 0.6
    else:
        return 0.4


def _determine_conclusion(score: float) -> dict:
    """根据总分确定结论."""
    pass_threshold = DECISION_THRESHOLDS["pass"]
    declare_threshold = DECISION_THRESHOLDS["declare"]

    if score >= pass_threshold:
        return {
            "conclusion": "pass",
            "conclusion_zh": "通过",
            "defense_tier": "L3",
            "defense_tier_zh": "法律登记确证",
            "requires_disclosure": False,
            "eligible_for_registration": True,
        }
    elif score >= declare_threshold:
        return {
            "conclusion": "declare",
            "conclusion_zh": "需声明",
            "defense_tier": "L2",
            "defense_tier_zh": "平台工具监测",
            "requires_disclosure": True,
            "eligible_for_registration": False,
        }
    else:
        return {
            "conclusion": "reject",
            "conclusion_zh": "不进入确权",
            "defense_tier": "L1",
            "defense_tier_zh": "本地签名存证",
            "requires_disclosure": False,
            "eligible_for_registration": False,
        }


def save_contribution_score(
    db: Session,
    work_id: str,
    author_id: str,
    score: dict,
) -> HumanContributionScore:
    """保存贡献度评分记录."""
    record = HumanContributionScore(
        work_id=work_id,
        author_id=author_id,
        total_score=score["total_score"],
        ai_session_score=score["dimension_scores"]["ai_sessions"],
        mcp_event_score=score["dimension_scores"]["mcp_events"],
        self_declare_score=score["dimension_scores"]["self_declaration"],
        duration_score=score["dimension_scores"]["creation_duration"],
        conclusion=score["conclusion"],
        defense_tier=score["defense_tier_recommendation"],
        requires_disclosure=score["requires_disclosure"],
        eligible_for_registration=score["eligible_for_registration"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
