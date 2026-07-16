"""多市场扩展服务层 — 地理套利计算器 + 出海规划."""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.multi_market import MarketInfo, ExpansionPlan, TaxGuide


# 四市场基准数据
MARKET_BENCHMARKS = {
    "cn": {
        "name_zh": "中国大陆",
        "name_en": "China",
        "total_creators": 7000,  # 万人
        "revenue_median_yuan": 60000,  # ¥6万/年
        "avg_rpm_yuan": 5,
        "growth_rate_yoy": 20.0,
        "is_open_to_foreign_creators": False,
        "copyright_protection_level": "berne",
        "language_barrier": "high",
    },
    "us": {
        "name_zh": "美国",
        "name_en": "United States",
        "total_creators": 5000,
        "revenue_median_yuan": 280000,  # ~$40K
        "avg_rpm_yuan": 35,
        "growth_rate_yoy": 15.0,
        "is_open_to_foreign_creators": True,
        "copyright_protection_level": "berne",
        "language_barrier": "medium",
    },
    "eu": {
        "name_zh": "欧盟",
        "name_en": "European Union",
        "total_creators": 3000,
        "revenue_median_yuan": 200000,  # ~€28K
        "avg_rpm_yuan": 25,
        "growth_rate_yoy": 12.0,
        "is_open_to_foreign_creators": True,
        "copyright_protection_level": "berne",
        "language_barrier": "high",
    },
    "jp": {
        "name_zh": "日本",
        "name_en": "Japan",
        "total_creators": 800,
        "revenue_median_yuan": 180000,  # ~¥2.8M
        "avg_rpm_yuan": 20,
        "growth_rate_yoy": 10.0,
        "is_open_to_foreign_creators": True,
        "copyright_protection_level": "berne",
        "language_barrier": "high",
    },
}

# 出海三阶段
EXPANSION_PHASES = [
    {
        "phase_key": "validation",
        "phase_name_zh": "验证期",
        "duration_months": 6,
        "key_actions": [
            "选择 1 个目标市场进行小规模测试",
            "适配内容格式（语言/尺寸/节奏）",
            "建立基础社交媒体账号",
            "测试内容反响和数据",
        ],
        "milestones": [
            "目标市场粉丝达到 100+",
            "单条内容平均播放量 > 1000",
            "月收入 > ¥500",
        ],
    },
    {
        "phase_key": "expansion",
        "phase_name_zh": "扩展期",
        "duration_months": 12,
        "key_actions": [
            "增加内容发布频率至每周 3-5 次",
            "尝试本地化内容（配音/字幕）",
            "探索变现渠道（广告/赞助/订阅）",
            "分析数据优化内容策略",
        ],
        "milestones": [
            "目标市场粉丝达到 5000+",
            "月收入达到本地创作者中位数的 10%",
            "至少 1 种稳定变现渠道",
        ],
    },
    {
        "phase_key": "diversified",
        "phase_name_zh": "多元化期",
        "duration_months": 18,
        "key_actions": [
            "扩展到第 2-3 个目标市场",
            "建立跨平台分发体系",
            "发展品牌合作和自有产品",
            "考虑实体公司架构优化税务",
        ],
        "milestones": [
            "多市场月收入总和 > 原市场 2 倍",
            "收入来源 ≥ 3 种",
            "建立品牌辨识度",
        ],
    },
]


def get_all_markets(db: Optional[Session] = None) -> list[dict]:
    """获取所有市场信息."""
    if db:
        markets = db.query(MarketInfo).filter(MarketInfo.is_active == True).all()
        if markets:
            return [
                {
                    "id": m.id,
                    "market_code": m.market_code,
                    "name_zh": m.name_zh,
                    "name_en": m.name_en,
                    "total_creators": m.total_creators,
                    "revenue_median_yuan": m.revenue_median_yuan,
                    "avg_rpm_yuan": m.avg_rpm_yuan,
                    "growth_rate_yoy": m.growth_rate_yoy,
                    "is_open_to_foreign_creators": m.is_open_to_foreign_creators,
                    "copyright_protection_level": m.copyright_protection_level,
                    "language_barrier": m.language_barrier,
                }
                for m in markets
            ]
    # Fallback to benchmark data
    return [
        {**MARKET_BENCHMARKS[code], "market_code": code}
        for code in MARKET_BENCHMARKS
    ]


def calculate_geo_arbitrage(
    current_markets: list[str],
    monthly_revenue_yuan: float,
    creator_type: str = "illustrator",
) -> dict:
    """
    地理套利计算器：
    基于 AnaReports 数据：仅中国 $5K → 中美双市场 $28K(+460%) → 中美日三市场 $52K(+940%)
    """
    if not current_markets:
        current_markets = ["cn"]

    current_total = monthly_revenue_yuan

    # 每个市场的收入乘数（基于收入中位数比例）
    cn_base = MARKET_BENCHMARKS["cn"]["revenue_median_yuan"]
    multipliers = {}
    for code in MARKET_BENCHMARKS:
        if code != "cn":
            multipliers[code] = MARKET_BENCHMARKS[code]["revenue_median_yuan"] / cn_base
        else:
            multipliers[code] = 1.0

    # 计算各市场的预期收入
    projected = {}
    for code in current_markets:
        if code in multipliers:
            projected[code] = round(current_total * multipliers[code], 2)

    # 添加新市场的增量
    new_markets = [c for c in MARKET_BENCHMARKS if c not in current_markets]
    for nm in new_markets:
        # 每个新市场带来当前总收入的 multiplier 倍
        projected[nm] = round(current_total * multipliers.get(nm, 1.0) * 0.6, 2)  # 60% 效率因子

    total_projected = sum(projected.values())
    increase_pct = round((total_projected - current_total) / current_total * 100, 1) if current_total > 0 else 0

    # 推荐优先扩展的市场（按收入中位数排序）
    recommended = sorted(
        [c for c in MARKET_BENCHMARKS if c not in current_markets],
        key=lambda x: MARKET_BENCHMARKS[x]["revenue_median_yuan"],
        reverse=True,
    )[:2]

    return {
        "current_total_monthly": current_total,
        "projected_with_targets": projected,
        "total_projected_monthly": round(total_projected, 2),
        "increase_percent": increase_pct,
        "recommended_markets": recommended,
    }


def get_expansion_phases() -> list[dict]:
    """获取出海三阶段规划."""
    return EXPANSION_PHASES


def create_expansion_plan(
    db: Session,
    user_id: str,
    target_markets: list[str],
    phase: str,
    start_date=None,
    notes: Optional[str] = None,
) -> dict:
    """创建出海规划."""
    plan = ExpansionPlan(
        user_id=user_id,
        current_markets=["cn"],
        target_markets=target_markets,
        phase=phase,
        start_date=start_date,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    return {
        "id": plan.id,
        "user_id": plan.user_id,
        "current_markets": plan.current_markets,
        "target_markets": plan.target_markets,
        "phase": plan.phase,
        "start_date": plan.start_date,
    }


def get_tax_guide(db: Session, source: str, target: str) -> Optional[dict]:
    """获取跨境税务指南."""
    guide = db.query(TaxGuide).filter(
        TaxGuide.source_market == source,
        TaxGuide.target_market == target,
        TaxGuide.is_active == True,
    ).first()
    if guide:
        return {
            "source_market": guide.source_market,
            "target_market": guide.target_market,
            "withholding_tax_rate": guide.withholding_tax_rate,
            "tax_treaty_reduction": guide.tax_treaty_reduction,
            "recommended_entity": guide.recommended_entity,
            "required_forms": guide.required_forms,
            "description_zh": guide.description_zh,
        }
    return None
