"""维权ROI种子数据 — 参考案例 + 四层防御."""


def seed_enforcement_roi_data(db):
    """初始化参考案例和防御预算层级."""
    from app.models.enforcement_roi import CaseReference, DefenseBudgetTier

    existing_ref = db.query(CaseReference).count()
    existing_tier = db.query(DefenseBudgetTier).count()

    if existing_ref > 0 or existing_tier > 0:
        return

    # 参考案例
    case_refs = [
        {
            "infringement_type": "platform_copy",
            "target_platform": "xiaohongshu",
            "typical_cost_range_low": 0,
            "typical_cost_range_high": 0,
            "resolution_time_days_low": 3,
            "resolution_time_days_high": 14,
            "win_rate_percent": 70.0,
            "avg_compensation_yuan": 500,
            "roi_tier": "medium",
            "description_zh": "小红书图片被直接搬运，通过平台投诉删除，成功率约70%，但赔偿较少。",
        },
        {
            "infringement_type": "commercial_use",
            "target_platform": "taobao",
            "typical_cost_range_low": 2000,
            "typical_cost_range_high": 15000,
            "resolution_time_days_low": 30,
            "resolution_time_days_high": 180,
            "win_rate_percent": 65.0,
            "avg_compensation_yuan": 15000,
            "roi_tier": "high",
            "description_zh": "淘宝店铺盗用插画作品销售衍生品，律师函+诉讼组合拳，平均获赔¥1.5万。",
        },
        {
            "infringement_type": "commercial_use",
            "target_platform": "amazon",
            "typical_cost_range_low": 5000,
            "typical_cost_range_high": 30000,
            "resolution_time_days_low": 60,
            "resolution_time_days_high": 365,
            "win_rate_percent": 72.0,
            "avg_compensation_yuan": 50000,
            "roi_tier": "high",
            "description_zh": "Amazon上盗用设计作品销售，DMCA投诉+诉讼，美国法定赔偿$300-$150,000/作品。",
        },
        {
            "infringement_type": "ai_training",
            "target_platform": "generic",
            "typical_cost_range_low": 10000,
            "typical_cost_range_high": 50000,
            "resolution_time_days_low": 180,
            "resolution_time_days_high": 730,
            "win_rate_percent": 45.0,
            "avg_compensation_yuan": 30000,
            "roi_tier": "medium",
            "description_zh": "AI公司未经许可使用作品训练模型，新兴领域判例较少，胜率和赔偿不确定性高。",
        },
        {
            "infringement_type": "social_share",
            "target_platform": "weibo",
            "typical_cost_range_low": 0,
            "typical_cost_range_high": 2000,
            "resolution_time_days_low": 1,
            "resolution_time_days_high": 7,
            "win_rate_percent": 80.0,
            "avg_compensation_yuan": 200,
            "roi_tier": "low_negative",
            "description_zh": "微博社交分享未署名，平台投诉即可删除，但赔偿极低，ROI为负。",
        },
        {
            "infringement_type": "reverse_image",
            "target_platform": "etsy",
            "typical_cost_range_low": 0,
            "typical_cost_range_high": 500,
            "resolution_time_days_low": 7,
            "resolution_time_days_high": 30,
            "win_rate_percent": 75.0,
            "avg_compensation_yuan": 3000,
            "roi_tier": "medium",
            "description_zh": "Etsy商家通过反向图片搜索找到作品后制作周边销售，平台投诉下架+索赔。",
        },
        {
            "infringement_type": "platform_copy",
            "target_platform": "douyin",
            "typical_cost_range_low": 0,
            "typical_cost_range_high": 0,
            "resolution_time_days_low": 3,
            "resolution_time_days_high": 10,
            "win_rate_percent": 60.0,
            "avg_compensation_yuan": 300,
            "roi_tier": "low_negative",
            "description_zh": "抖音短视频截取原创插画制作内容，平台投诉删除为主，赔偿有限。",
        },
    ]

    for cr in case_refs:
        db.add(CaseReference(**cr))

    # 四层防御预算
    tiers = [
        {
            "tier_key": "zero",
            "tier_name_zh": "零成本防御",
            "monthly_cost_low": 0,
            "monthly_cost_high": 0,
            "annual_cost_low": 0,
            "annual_cost_high": 0,
            "features": ["原创时间戳存证", "作品元数据标注", "社交媒体版权声明"],
            "description_zh": "利用平台自带功能和免费工具进行基础保护。",
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
            "description_zh": "低成本自动化监测和存证方案。",
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
            "description_zh": "包含专业监控和法律咨询。",
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
            "description_zh": "全方位版权保护方案。",
            "recommended_for": "机构/工作室、月收入 > ¥100K",
        },
    ]

    for t in tiers:
        db.add(DefenseBudgetTier(**t))

    db.commit()
