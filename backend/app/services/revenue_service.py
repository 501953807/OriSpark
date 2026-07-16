"""收入多元化分析服务层."""

import math
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models.publish import RevenueRecord


# 8 种变现手段分类
INCOME_CATEGORIES = {
    "ad_revenue": {"name": "广告分成", "color": "#FF6B6B"},
    "sponsorship": {"name": "品牌赞助", "color": "#4ECDC4"},
    "subscription": {"name": "付费订阅", "color": "#45B7D1"},
    "tip": {"name": "打赏", "color": "#96CEB4"},
    "ecommerce": {"name": "电商", "color": "#FFEAA7"},
    "affiliate": {"name": "联盟营销", "color": "#DDA0DD"},
    "knowledge_payment": {"name": "知识付费", "color": "#98D8C8"},
    "ip_licensing": {"name": "IP 授权", "color": "#F7DC6F"},
}

# 预警阈值：单一来源占比超过此值标红
SINGLE_SOURCE_WARNING_THRESHOLD = 0.7


def calculate_diversity_index(records: list) -> dict:
    """计算收入多元化指数（基于香农熵）.

    Returns:
        {
            "diversity_index": float,  # 0-1, 1 表示完全均衡
            "total_sources": int,      # 有收入的来源数
            "warnings": list,          # 预警列表
            "category_distribution": dict,
        }
    """
    if not records:
        return {
            "diversity_index": 0.0,
            "total_sources": 0,
            "warnings": ["暂无收入数据"],
            "category_distribution": {},
        }

    # 按类别汇总金额
    category_totals = {}
    total_amount = 0.0
    for r in records:
        cat = r.income_category
        amount = r.amount
        category_totals[cat] = category_totals.get(cat, 0) + amount
        total_amount += amount

    if total_amount == 0:
        return {
            "diversity_index": 0.0,
            "total_sources": 0,
            "warnings": ["总收入为 0"],
            "category_distribution": {},
        }

    # 计算各来源占比
    proportions = {k: v / total_amount for k, v in category_totals.items()}

    # 香农熵 H = -Σ(p_i * ln(p_i))
    entropy = 0.0
    for p in proportions.values():
        if p > 0:
            entropy -= p * math.log(p)

    # 最大熵 H_max = ln(N)，N 为实际有收入的来源数
    n_sources = len(proportions)
    max_entropy = math.log(n_sources) if n_sources > 1 else 1.0

    # 归一化多样性指数
    diversity_index = entropy / max_entropy if max_entropy > 0 else 0.0

    # 生成预警
    warnings = []
    for cat, prop in proportions.items():
        if prop > SINGLE_SOURCE_WARNING_THRESHOLD:
            cat_name = INCOME_CATEGORIES.get(cat, {}).get("name", cat)
            warnings.append(
                f"⚠️ {cat_name} 占比 {prop:.1%}，建议多元化收入结构"
            )

    if diversity_index < 0.3 and n_sources > 1:
        warnings.append("💡 收入分布不均，建议拓展其他变现渠道")
    elif diversity_index >= 0.6:
        warnings.append("✅ 收入结构健康，保持多元化")

    # 构建分类分布
    category_distribution = {}
    for cat, prop in proportions.items():
        info = INCOME_CATEGORIES.get(cat, {"name": cat, "color": "#CCCCCC"})
        category_distribution[cat] = {
            **info,
            "amount": round(category_totals[cat], 2),
            "proportion": round(prop, 4),
        }

    return {
        "diversity_index": round(diversity_index, 4),
        "total_sources": n_sources,
        "warnings": warnings,
        "category_distribution": category_distribution,
    }


def get_revenue_summary(
    db: Session,
    user_id: str,
    months: int = 12,
) -> dict:
    """获取用户收入汇总统计."""
    cutoff_date = datetime.utcnow() - timedelta(days=30 * months)

    records = (
        db.query(RevenueRecord)
        .filter(
            RevenueRecord.user_id == user_id,
            RevenueRecord.created_at >= cutoff_date,
        )
        .all()
    )

    total_revenue = sum(r.amount for r in records)

    # 按月趋势
    monthly_trend = {}
    for r in records:
        month_key = r.created_at.strftime("%Y-%m") if r.created_at else "unknown"
        monthly_trend[month_key] = monthly_trend.get(month_key, 0) + r.amount

    trend = sorted(
        [{"month": k, "amount": round(v, 2)} for k, v in monthly_trend.items()],
        key=lambda x: x["month"],
    )

    diversity_info = calculate_diversity_index(records)

    return {
        "user_id": user_id,
        "total_revenue": round(total_revenue, 2),
        "currency": "CNY",
        "months": months,
        "monthly_trend": trend,
        "diversity": diversity_info,
    }


def record_revenue(
    db: Session,
    user_id: str,
    income_category: str,
    amount: float,
    currency: str = "CNY",
    platform: Optional[str] = None,
    recorded_date: Optional[datetime] = None,
    source_description: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> RevenueRecord:
    """记录一笔收入."""
    if income_category not in INCOME_CATEGORIES:
        raise ValueError(f"Invalid income_category: {income_category}")

    record = RevenueRecord(
        user_id=user_id,
        income_category=income_category,
        amount=amount,
        currency=currency,
        platform=platform,
        source_description=source_description,
        extra_metadata=metadata,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def bulk_record_revenue(
    db: Session,
    user_id: str,
    records_data: list,
) -> list:
    """批量记录收入（用于 CSV 导入）.

    Args:
        records_data: [{income_category, amount, platform, recorded_date, ...}]
    """
    created = []
    for data in records_data:
        try:
            record = record_revenue(db, user_id, **data)
            created.append(record)
        except Exception:
            continue  # Skip invalid records
    return created
