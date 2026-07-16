"""维权ROI计算服务层 — 决策树 + ROI预测 + 四层防御."""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.enforcement_roi import EnforcementCase, CaseReference, DefenseBudgetTier


# 维权路径决策树规则
DECISION_RULES = {
    "cease_desist": {
        "name_zh": "律师函/警告信",
        "cost_range": [2000, 8000],
        "expected_days": [7, 30],
        "win_rate": 0.475,  # 40-55% 中值
        "description_zh": "通过律师向侵权方发送正式警告函，要求立即停止侵权行为并删除内容。适用于大多数平台侵权场景。",
    },
    "platform_complaint": {
        "name_zh": "平台投诉",
        "cost_range": [0, 0],
        "expected_days": [3, 14],
        "win_rate": 0.65,
        "description_zh": "利用平台DMCA/侵权举报机制直接删除侵权内容。零成本，响应速度快。",
    },
    "civil_lawsuit": {
        "name_zh": "民事诉讼",
        "cost_range": [5000, 50000],
        "expected_days": [180, 540],
        "win_rate": 0.72,
        "description_zh": "向法院提起著作权侵权诉讼。中国周期6-18个月，法定赔偿¥500-¥5,000,000。",
    },
    "criminal_report": {
        "name_zh": "刑事报案",
        "cost_range": [10000, 100000],
        "expected_days": [90, 365],
        "win_rate": 0.80,
        "description_zh": "针对大规模商业盗版，向公安机关报案。适用于非法经营数额较大（通常≥5万元）的案件。",
    },
}

# 不同侵权类型的推荐优先级
INFRINGEMENT_PRIORITY = {
    "platform_copy": ["platform_complaint", "cease_desist", "civil_lawsuit"],
    "commercial_use": ["cease_desist", "civil_lawsuit", "platform_complaint"],
    "ai_training": ["civil_lawsuit", "cease_desist", "platform_complaint"],
    "social_share": ["platform_complaint", "cease_desist"],
    "reverse_image": ["platform_complaint", "cease_desist", "civil_lawsuit"],
}

# 四层防御预算
DEFENSE_TIERS_DATA = [
    {
        "tier_key": "zero",
        "tier_name_zh": "零成本防御",
        "monthly_cost_low": 0,
        "monthly_cost_high": 0,
        "annual_cost_low": 0,
        "annual_cost_high": 0,
        "features": ["原创时间戳存证", "作品元数据标注", "社交媒体版权声明"],
        "description_zh": "利用平台自带功能和免费工具进行基础保护，适合刚起步的创作者。",
        "recommended_for": "新手创作者、月收入 < ¥5,000",
    },
    {
        "tier_key": "low",
        "tier_name_zh": "基础防御 ($5-20/月)",
        "monthly_cost_low": 5,
        "monthly_cost_high": 20,
        "annual_cost_low": 60,
        "annual_cost_high": 240,
        "features": ["数字水印(C2PA)", "反向图片搜索", "RSS订阅监测", "自动备份"],
        "description_zh": "低成本自动化监测和存证方案，覆盖日常版权保护需求。",
        "recommended_for": "活跃创作者、月收入 ¥5K-¥30K",
    },
    {
        "tier_key": "mid",
        "tier_name_zh": "中等防御 ($500-3K/年)",
        "monthly_cost_low": 42,
        "monthly_cost_high": 250,
        "annual_cost_low": 500,
        "annual_cost_high": 3000,
        "features": ["专业监控服务", "侵权自动发现", "律师函模板库", "版权注册"],
        "description_zh": "包含专业监控和法律咨询，适合有稳定收入的专业创作者。",
        "recommended_for": "专业创作者、月收入 ¥30K-¥100K",
    },
    {
        "tier_key": "high",
        "tier_name_zh": "高级防御 ($5K+/年)",
        "monthly_cost_low": 420,
        "monthly_cost_high": 2000,
        "annual_cost_low": 5000,
        "annual_cost_high": 24000,
        "features": ["专属法律顾问", "24/7全网监控", "维权基金池", "跨境版权登记"],
        "description_zh": "全方位版权保护方案，含法律顾问和维权基金，适合高价值IP持有者。",
        "recommended_for": "机构/工作室、月收入 > ¥100K",
    },
]

# 各平台典型特征
PLATFORM_BENCHMARKS = {
    "xiaohongshu": {"name_zh": "小红书", "complaint_ease": 0.8, "compensation_likelihood": 0.1},
    "weibo": {"name_zh": "微博", "complaint_ease": 0.7, "compensation_likelihood": 0.1},
    "douyin": {"name_zh": "抖音", "complaint_ease": 0.6, "compensation_likelihood": 0.15},
    "taobao": {"name_zh": "淘宝", "complaint_ease": 0.9, "compensation_likelihood": 0.3},
    "amazon": {"name_zh": "Amazon", "complaint_ease": 0.85, "compensation_likelihood": 0.4},
    "etsy": {"name_zh": "Etsy", "complaint_ease": 0.8, "compensation_likelihood": 0.35},
    "youtube": {"name_zh": "YouTube", "complaint_ease": 0.75, "compensation_likelihood": 0.25},
    "deviantart": {"name_zh": "DeviantArt", "complaint_ease": 0.6, "compensation_likelihood": 0.1},
    "github": {"name_zh": "GitHub", "complaint_ease": 0.5, "compensation_likelihood": 0.05},
    "generic": {"name_zh": "通用平台", "complaint_ease": 0.5, "compensation_likelihood": 0.15},
}


def get_decision_tree(infringement_type: str, loss_amount: float) -> dict:
    """
    根据侵权类型和损失金额推荐维权路径。

    决策逻辑：
    - 损失 < ¥5K → 平台投诉 + 律师函
    - 损失 ¥5K-¥50K → 律师函 + 民事诉讼
    - 损失 > ¥50K → 民事诉讼 + 刑事报案
    """
    priority = INFRINGEMENT_PRIORITY.get(infringement_type, ["platform_complaint", "cease_desist", "civil_lawsuit"])

    recommended = []
    for action_key in priority:
        rule = DECISION_RULES[action_key]
        entry = {
            "action_key": action_key,
            "name_zh": rule["name_zh"],
            "estimated_cost": rule["cost_range"],
            "expected_duration_days": rule["expected_days"],
            "win_rate": rule["win_rate"],
        }

        # 根据损失金额过滤不合适的方案
        if loss_amount < 5000 and action_key in ("civil_lawsuit", "criminal_report"):
            continue
        if loss_amount >= 50000 and action_key == "platform_complaint":
            # 大额损失时平台投诉不够，但仍推荐作为第一步
            entry["note_zh"] = "建议作为辅助手段"

        recommended.append(entry)

    primary = recommended[0] if recommended else {
        "action_key": "platform_complaint",
        "name_zh": "平台投诉",
    }

    return {
        "recommended_actions": recommended,
        "primary_recommendation": primary,
        "reasoning": _build_reasoning(infringement_type, loss_amount, primary),
    }


def _build_reasoning(infringement_type: str, loss_amount: float, primary: dict) -> str:
    """生成决策推理说明."""
    type_map = {
        "platform_copy": "内容复制",
        "commercial_use": "商业滥用",
        "ai_training": "AI训练使用",
        "social_share": "社交分享",
        "reverse_image": "图片反向搜索发现",
    }
    type_name = type_map.get(infringement_type, infringement_type)

    if loss_amount < 5000:
        cost_advice = "损失金额较低，建议优先使用零成本和低成本维权方式"
    elif loss_amount < 50000:
        cost_advice = "损失金额中等，律师函是性价比最高的选择"
    else:
        cost_advice = "损失金额较高，建议考虑民事诉讼获取赔偿"

    return f"检测到{type_name}侵权，预估损失¥{int(loss_amount)}。{cost_advice}。推荐首选方案：{primary.get('name_zh', '平台投诉')}。"


def predict_roi(
    work_value_yuan: float,
    infringement_type: str,
    target_platform: str,
    action_type: str,
) -> dict:
    """
    ROI预测器：输入作品价值和侵权信息，输出维权ROI预测。
    """
    rule = DECISION_RULES.get(action_type, DECISION_RULES["platform_complaint"])
    platform = PLATFORM_BENCHMARKS.get(target_platform, PLATFORM_BENCHMARKS["generic"])

    # 预期成本
    cost_low, cost_high = rule["cost_range"]
    expected_cost = (cost_low + cost_high) / 2 if cost_high > 0 else 0

    # 预期时长
    days_low, days_high = rule["expected_days"]
    expected_days = (days_low + days_high) // 2

    # 胜率（结合平台特性）
    base_win_rate = rule["win_rate"]
    adjusted_win = base_win_rate * (0.5 + platform["complaint_ease"] * 0.5)
    adjusted_win = min(adjusted_win, 0.95)

    # 预期赔偿
    if action_type == "civil_lawsuit":
        # 民事诉讼：基于作品价值的10-50%
        avg_comp = work_value_yuan * 0.25
    elif action_type == "criminal_report":
        avg_comp = work_value_yuan * 0.5
    elif action_type == "cease_desist":
        avg_comp = work_value_yuan * 0.05
    else:
        avg_comp = work_value_yuan * 0.02

    expected_comp = avg_comp * adjusted_win * platform["compensation_likelihood"]

    # ROI 计算
    net_return = expected_comp - expected_cost
    roi_percent = round((net_return / expected_cost * 100), 1) if expected_cost > 0 else (100.0 if expected_comp > 0 else 0.0)

    # 风险等级
    if roi_percent > 200 or (roi_percent > 0 and adjusted_win > 0.7):
        risk = "low"
    elif roi_percent > -50:
        risk = "medium"
    else:
        risk = "high"

    return {
        "expected_cost": round(expected_cost, 2),
        "expected_duration_days": expected_days,
        "win_probability": round(adjusted_win * 100, 1),
        "expected_compensation": round(expected_comp, 2),
        "net_return": round(net_return, 2),
        "roi_percent": roi_percent,
        "risk_level": risk,
    }


def get_all_defense_tiers() -> list[dict]:
    """获取四层防御预算配置."""
    return DEFENSE_TIERS_DATA


def get_case_reference(db: Session, infringement_type: str, platform: str) -> Optional[dict]:
    """获取参考案例数据."""
    case = db.query(CaseReference).filter(
        CaseReference.infringement_type == infringement_type,
        CaseReference.target_platform == platform,
        CaseReference.is_active == True,
    ).first()
    if case:
        return {
            "id": case.id,
            "infringement_type": case.infringement_type,
            "target_platform": case.target_platform,
            "typical_cost_range_low": case.typical_cost_range_low,
            "typical_cost_range_high": case.typical_cost_range_high,
            "resolution_time_days_low": case.resolution_time_days_low,
            "resolution_time_days_high": case.resolution_time_days_high,
            "win_rate_percent": case.win_rate_percent,
            "avg_compensation_yuan": case.avg_compensation_yuan,
            "roi_tier": case.roi_tier,
        }
    return None


def list_case_references(db: Session, infringement_type: Optional[str] = None) -> list[dict]:
    """列出参考案例."""
    query = db.query(CaseReference).filter(CaseReference.is_active == True)
    if infringement_type:
        query = query.filter(CaseReference.infringement_type == infringement_type)
    cases = query.all()
    return [
        {
            "id": c.id,
            "infringement_type": c.infringement_type,
            "target_platform": c.target_platform,
            "typical_cost_range_low": c.typical_cost_range_low,
            "typical_cost_range_high": c.typical_cost_range_high,
            "resolution_time_days_low": c.resolution_time_days_low,
            "resolution_time_days_high": c.resolution_time_days_high,
            "win_rate_percent": c.win_rate_percent,
            "avg_compensation_yuan": c.avg_compensation_yuan,
            "roi_tier": c.roi_tier,
            "description_zh": c.description_zh,
        }
        for c in cases
    ]


def save_enforcement_case(db: Session, user_id: str, data: dict) -> dict:
    """保存维权案例记录."""
    case = EnforcementCase(
        user_id=user_id,
        work_id=data.get("work_id"),
        infringement_type=data["infringement_type"],
        target_platform=data["target_platform"],
        estimated_loss_yuan=data["estimated_loss_yuan"],
        action_taken=data["action_taken"],
        cost_yuan=data.get("cost_yuan", 0),
        compensation_received_yuan=data.get("compensation_received_yuan", 0),
        outcome=data["outcome"],
        notes=data.get("notes"),
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    roi = None
    if case.cost_yuan > 0:
        net = case.compensation_received_yuan - case.cost_yuan
        roi = round(net / case.cost_yuan * 100, 1)
    elif case.compensation_received_yuan > 0:
        roi = 999.9  # 零成本维权成功

    return {
        "id": case.id,
        "user_id": case.user_id,
        "work_id": case.work_id,
        "infringement_type": case.infringement_type,
        "target_platform": case.target_platform,
        "estimated_loss_yuan": case.estimated_loss_yuan,
        "cost_yuan": case.cost_yuan,
        "time_to_resolve_days": case.time_to_resolve_days,
        "compensation_received_yuan": case.compensation_received_yuan,
        "outcome": case.outcome,
        "roi_percent": roi,
        "created_at": case.created_at.isoformat(),
    }


def get_user_cases(db: Session, user_id: str) -> list[dict]:
    """获取用户维权案例列表."""
    cases = db.query(EnforcementCase).filter(
        EnforcementCase.user_id == user_id,
    ).order_by(EnforcementCase.created_at.desc()).all()

    result = []
    total_cost = 0
    total_compensation = 0
    successful_count = 0

    for c in cases:
        roi = None
        if c.cost_yuan > 0:
            net = c.compensation_received_yuan - c.cost_yuan
            roi = round(net / c.cost_yuan * 100, 1)
        elif c.compensation_received_yuan > 0:
            roi = 999.9

        total_cost += c.cost_yuan
        total_compensation += c.compensation_received_yuan
        if c.outcome in ("successful", "settled", "partial"):
            successful_count += 1

        result.append({
            "id": c.id,
            "work_id": c.work_id,
            "infringement_type": c.infringement_type,
            "target_platform": c.target_platform,
            "estimated_loss_yuan": c.estimated_loss_yuan,
            "cost_yuan": c.cost_yuan,
            "time_to_resolve_days": c.time_to_resolve_days,
            "compensation_received_yuan": c.compensation_received_yuan,
            "outcome": c.outcome,
            "roi_percent": roi,
            "created_at": c.created_at.isoformat(),
        })

    overall_roi = None
    if total_cost > 0:
        overall_roi = round((total_compensation - total_cost) / total_cost * 100, 1)

    return {
        "cases": result,
        "summary": {
            "total_cases": len(result),
            "successful_cases": successful_count,
            "success_rate_percent": round(successful_count / len(result) * 100, 1) if result else 0,
            "total_cost": round(total_cost, 2),
            "total_compensation": round(total_compensation, 2),
            "overall_roi_percent": overall_roi,
        },
    }
