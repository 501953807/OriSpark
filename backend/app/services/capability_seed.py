"""创作者能力评估种子数据 — 8 维能力维度."""


def seed_capability_dimensions(db):
    """初始化 8 个能力维度."""
    from app.models.capability import CapabilityDimension

    existing = db.query(CapabilityDimension).count()
    if existing > 0:
        return

    dimensions_data = [
        {
            "dimension_key": "artistic_skill",
            "name_zh": "艺术技法",
            "description": "绘画、构图、色彩搭配等基础艺术功底",
            "weight": 1.2,
        },
        {
            "dimension_key": "creative_vision",
            "name_zh": "创意视野",
            "description": "独特视角、概念创新能力、风格辨识度",
            "weight": 1.3,
        },
        {
            "dimension_key": "market_awareness",
            "name_zh": "市场洞察",
            "description": "对市场需求、趋势、受众偏好的理解",
            "weight": 1.0,
        },
        {
            "dimension_key": "technical_proficiency",
            "name_zh": "技术熟练度",
            "description": "软件工具使用、AI 辅助创作能力",
            "weight": 0.8,
        },
        {
            "dimension_key": "brand_building",
            "name_zh": "品牌建设",
            "description": "个人品牌塑造、视觉一致性、IP 运营",
            "weight": 1.1,
        },
        {
            "dimension_key": "business_acumen",
            "name_zh": "商业思维",
            "description": "定价策略、合同谈判、收入多元化",
            "weight": 1.0,
        },
        {
            "dimension_key": "audience_engagement",
            "name_zh": "受众连接",
            "description": "社群运营、粉丝互动、私域流量管理",
            "weight": 0.9,
        },
        {
            "dimension_key": "continuous_learning",
            "name_zh": "持续学习",
            "description": "技能迭代速度、新知识吸收能力",
            "weight": 1.0,
        },
    ]

    for d in dimensions_data:
        db.add(CapabilityDimension(**d))

    db.commit()
