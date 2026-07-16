"""版权保险种子数据 — 默认产品和保险公司."""


def seed_insurance_data(db):
    """初始化保险产品（5 类 × 3 层）+ 3 家模拟保险公司."""
    from app.models.insurance import InsuranceProvider, InsuranceProduct

    existing = db.query(InsuranceProvider).count()
    if existing > 0:
        return  # 已有数据不重复加载

    # 3 家模拟保险公司
    providers = [
        InsuranceProvider(
            name_zh="安心保险科技",
            name_en="Anxin Insurance Tech",
            license_no="IB-2025-001",
            contact_email="contact@anxin.insure",
        ),
        InsuranceProvider(
            name_zh="创作者保障基金",
            name_en="Creator Protection Fund",
            license_no="CPF-2025-002",
            contact_email="support@cpfund.org",
        ),
        InsuranceProvider(
            name_zh="AI 安全保险",
            name_en="AI SafeGuard Insurance",
            license_no="ASI-2025-003",
            contact_email="info@aisafeguard.com",
        ),
    ]
    for p in providers:
        db.add(p)
    db.commit()
    db.refresh(providers)

    # 5 类保险 × 3 层 = 15 种产品
    categories = [
        {
            "key": "training_indemnity",
            "name": "训练数据赔偿险",
            "desc": "保障因 AI 模型未经授权使用您的作品进行训练而导致的经济损失",
            "weight": 1.0,
        },
        {
            "key": "style_copy",
            "name": "风格模仿覆盖险",
            "desc": "保障因 AI 风格迁移技术模仿您的独特创作风格而导致的收入损失",
            "weight": 0.8,
        },
        {
            "key": "deepfake",
            "name": "深度伪造保护险",
            "desc": "保障因您的肖像/声音被用于深度伪造内容而产生的名誉和经济损失",
            "weight": 1.2,
        },
        {
            "key": "unintentional_infringement",
            "name": "无意侵权险",
            "desc": "保障因 AI 生成内容无意中侵犯他人版权而产生的法律费用",
            "weight": 0.9,
        },
        {
            "key": "voice_portrait_theft",
            "name": "声音肖像盗用险",
            "desc": "保障您的声音或肖像被未经授权复制和使用而产生的损失",
            "weight": 0.7,
        },
    ]

    tiers = [
        ("basic", "基础版", 500, 2000, 50000),
        ("advanced", "进阶版", 3000, 20000, 500000),
        ("pro", "专业版", 20000, 200000, 5000000),
    ]

    product_idx = 0
    for cat in categories:
        for tier_key, tier_name, min_yuan, max_yuan, max_cov in tiers:
            db.add(InsuranceProduct(
                product_key=f"{cat['key']}_{tier_key}",
                provider_id=providers[product_idx % 3].id,
                category=cat["key"],
                tier=tier_key,
                name_zh=f"{cat['name']} · {tier_name}",
                annual_min_yuan=min_yuan,
                annual_max_yuan=max_yuan,
                coverage_description=f"{cat['desc']}（{tier_name}）",
                max_coverage_yuan=max_cov,
            ))
            product_idx += 1

    db.commit()
