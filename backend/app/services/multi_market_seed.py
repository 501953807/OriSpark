"""多市场扩展种子数据 — 四市场 + 税务指南."""


def seed_multi_market_data(db):
    """初始化四市场数据 + 税务指南."""
    from app.models.multi_market import MarketInfo, TaxGuide

    existing = db.query(MarketInfo).count()
    if existing > 0:
        return

    # 四市场
    markets_data = [
        {"market_code": "cn", **{
            "name_zh": "中国大陆", "name_en": "China",
            "total_creators": 7000, "revenue_median_yuan": 60000,
            "avg_rpm_yuan": 5, "growth_rate_yoy": 20.0,
            "is_open_to_foreign_creators": False,
            "copyright_protection_level": "berne",
            "language_barrier": "high",
        }},
        {"market_code": "us", **{
            "name_zh": "美国", "name_en": "United States",
            "total_creators": 5000, "revenue_median_yuan": 280000,
            "avg_rpm_yuan": 35, "growth_rate_yoy": 15.0,
            "is_open_to_foreign_creators": True,
            "copyright_protection_level": "berne",
            "language_barrier": "medium",
        }},
        {"market_code": "eu", **{
            "name_zh": "欧盟", "name_en": "European Union",
            "total_creators": 3000, "revenue_median_yuan": 200000,
            "avg_rpm_yuan": 25, "growth_rate_yoy": 12.0,
            "is_open_to_foreign_creators": True,
            "copyright_protection_level": "berne",
            "language_barrier": "high",
        }},
        {"market_code": "jp", **{
            "name_zh": "日本", "name_en": "Japan",
            "total_creators": 800, "revenue_median_yuan": 180000,
            "avg_rpm_yuan": 20, "growth_rate_yoy": 10.0,
            "is_open_to_foreign_creators": True,
            "copyright_protection_level": "berne",
            "language_barrier": "high",
        }},
    ]

    for m in markets_data:
        db.add(MarketInfo(**m))

    # 税务指南
    tax_data = [
        {
            "source_market": "cn", "target_market": "us",
            "withholding_tax_rate": 30.0,
            "tax_treaty_reduction": 10.0,
            "recommended_entity": "新加坡控股公司",
            "required_forms": ["W-8BEN"],
            "description_zh": "中美之间无税收协定，通过新加坡实体可将预扣税从30%降至10%。填写W-8BEN表格声明外国身份。",
        },
        {
            "source_market": "cn", "target_market": "eu",
            "withholding_tax_rate": None,
            "tax_treaty_reduction": None,
            "recommended_entity": "欧盟 OSS 注册",
            "required_forms": ["OSS Registration"],
            "description_zh": "欧盟数字服务适用 VAT，可通过 One-Stop-Shop (OSS) 统一申报。建议注册爱尔兰或爱沙尼亚实体。",
        },
        {
            "source_market": "cn", "target_market": "jp",
            "withholding_tax_rate": 20.42,
            "tax_treaty_reduction": 10.0,
            "recommended_entity": "香港控股公司",
            "required_forms": ["W-8BEN-E"],
            "description_zh": "中日之间有税收协定，通过香港实体可将预扣税从20.42%降至10%。",
        },
    ]

    for t in tax_data:
        db.add(TaxGuide(**t))

    db.commit()
