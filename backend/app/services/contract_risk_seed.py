"""合约风险评估默认规则种子数据."""


def seed_contract_risk_rules(db):
    """初始化合约风险评估默认规则 (40+ 条)."""
    from app.models.contract_risk import ContractRiskRule

    existing = db.query(ContractRiskRule).count()
    if existing > 0:
        return  # 已有规则不重复加载

    rules_data = [
        # ========== 通用合同规则 (12 类条款) ==========

        # 1. 版权归属 (copyright_ownership)
        {
            "rule_name": "版权全权转让",
            "category": "general",
            "clause_type": "copyright_ownership",
            "risk_level": "critical",
            "weight": 10,
            "description": "合同要求将作品全部版权转让给甲方，创作者将失去所有权利",
            "suggestion": "建议改为'保留完整著作权，仅授予本合同约定的使用权'",
        },
        {
            "rule_name": "版权共有",
            "category": "general",
            "clause_type": "copyright_ownership",
            "risk_level": "high",
            "weight": 8,
            "description": "合同约定版权由双方共有，可能导致后续使用纠纷",
            "suggestion": "建议明确各自享有的权利范围和使用条件",
        },
        {
            "rule_name": "版权归属不明",
            "category": "general",
            "clause_type": "copyright_ownership",
            "risk_level": "medium",
            "weight": 5,
            "description": "合同未明确约定版权归属",
            "suggestion": "建议明确写明版权归属方",
        },

        # 2. 授权范围 (license_scope)
        {
            "rule_name": "授权范围过宽",
            "category": "general",
            "clause_type": "license_scope",
            "risk_level": "high",
            "weight": 8,
            "description": "授权范围过宽：未限定使用媒介",
            "suggestion": "建议限定为'数字平台发布，非商业使用'",
        },
        {
            "rule_name": "全球永久授权",
            "category": "general",
            "clause_type": "license_scope",
            "risk_level": "critical",
            "weight": 10,
            "description": "全球范围内永久使用作品",
            "suggestion": "建议限定地域范围和期限",
        },
        {
            "rule_name": "全媒介授权",
            "category": "general",
            "clause_type": "license_scope",
            "risk_level": "high",
            "weight": 7,
            "description": "授权用于所有已知和未来的媒介形式",
            "suggestion": "建议列出具体允许的媒介类型",
        },

        # 3. 授权期限 (license_term)
        {
            "rule_name": "无固定期限",
            "category": "general",
            "clause_type": "license_term",
            "risk_level": "medium",
            "weight": 5,
            "description": "合同未约定明确的授权期限",
            "suggestion": "建议约定明确的起止日期",
        },
        {
            "rule_name": "自动续约",
            "category": "general",
            "clause_type": "license_term",
            "risk_level": "medium",
            "weight": 4,
            "description": "合同包含自动续约条款，可能未经同意延长授权",
            "suggestion": "建议要求续约需双方书面确认",
        },

        # 4. 付款条件 (payment_terms)
        {
            "rule_name": "付款周期过长",
            "category": "general",
            "clause_type": "payment_terms",
            "risk_level": "medium",
            "weight": 4,
            "description": "付款周期超过90天",
            "suggestion": "建议缩短至30天内付款",
        },
        {
            "rule_name": "逾期违约金过高",
            "category": "general",
            "clause_type": "payment_terms",
            "risk_level": "high",
            "weight": 7,
            "description": "逾期违约金超过日万分之五",
            "suggestion": "建议将违约金设定为日万分之三以内",
        },

        # 5. 违约责任 (liability)
        {
            "rule_name": "违约责任不对等",
            "category": "general",
            "clause_type": "liability",
            "risk_level": "high",
            "weight": 8,
            "description": "违约责任条款对一方过于苛刻",
            "suggestion": "建议双方承担对等的违约责任",
        },
        {
            "rule_name": "赔偿上限缺失",
            "category": "general",
            "clause_type": "liability",
            "risk_level": "medium",
            "weight": 4,
            "description": "未设定赔偿责任上限",
            "suggestion": "建议设定不超过合同总金额200%的赔偿上限",
        },

        # 6. 独家授权 (exclusivity)
        {
            "rule_name": "长期独家限制",
            "category": "general",
            "clause_type": "exclusivity",
            "risk_level": "high",
            "weight": 8,
            "description": "要求独家授权但期限超过一年",
            "suggestion": "建议缩短独家期限或增加退出机制",
        },
        {
            "rule_name": "独家无补偿",
            "category": "general",
            "clause_type": "exclusivity",
            "risk_level": "medium",
            "weight": 5,
            "description": "要求独家授权但未提供相应补偿",
            "suggestion": "建议独家授权应伴随合理补偿",
        },

        # 7. 分成比例 (revenue_share)
        {
            "rule_name": "分成比例过低",
            "category": "general",
            "clause_type": "revenue_share",
            "risk_level": "medium",
            "weight": 5,
            "description": "创作者分成比例低于行业基准",
            "suggestion": "建议分成比例不低于50%",
        },
        {
            "rule_name": "结算周期过长",
            "category": "general",
            "clause_type": "revenue_share",
            "risk_level": "low",
            "weight": 3,
            "description": "收入结算周期超过一个季度",
            "suggestion": "建议按月或按季度结算",
        },

        # 8. 修改权 (modification_right)
        {
            "rule_name": "单方修改权",
            "category": "general",
            "clause_type": "modification_right",
            "risk_level": "high",
            "weight": 7,
            "description": "甲方有权单方面修改作品内容",
            "suggestion": "建议修改需经创作者书面同意",
        },

        # 9. 署名权 (attribution)
        {
            "rule_name": "署名权缺失",
            "category": "general",
            "clause_type": "attribution",
            "risk_level": "medium",
            "weight": 5,
            "description": "合同未保障创作者署名权",
            "suggestion": "建议明确约定署名方式和位置",
        },

        # 10. 保密条款 (confidentiality)
        {
            "rule_name": "保密期限过长",
            "category": "general",
            "clause_type": "confidentiality",
            "risk_level": "low",
            "weight": 3,
            "description": "保密期限超过合同终止后5年",
            "suggestion": "建议保密期限不超过合同终止后2年",
        },

        # 11. 争议解决 (dispute_resolution)
        {
            "rule_name": "异地仲裁",
            "category": "general",
            "clause_type": "dispute_resolution",
            "risk_level": "medium",
            "weight": 4,
            "description": "争议解决地点在对方所在地",
            "suggestion": "建议约定在创作者所在地或中立地点解决",
        },

        # 12. 终止条款 (termination)
        {
            "rule_name": "终止后版权处理不明",
            "category": "general",
            "clause_type": "termination",
            "risk_level": "high",
            "weight": 7,
            "description": "合同终止后版权归属和处理方式不明确",
            "suggestion": "建议明确合同终止后版权自动回归创作者",
        },

        # ========== 交易合约规则 (8 类条款) ==========

        # 1. 授权用途 (usage_scope)
        {
            "rule_name": "用途超出挂牌描述",
            "category": "transaction",
            "clause_type": "usage_scope",
            "risk_level": "high",
            "weight": 8,
            "description": "授权用途超出挂牌描述范围",
            "suggestion": "建议与挂牌描述保持一致",
        },
        {
            "rule_name": "用途不限",
            "category": "transaction",
            "clause_type": "usage_scope",
            "risk_level": "medium",
            "weight": 5,
            "description": "授权用途无明确限制",
            "suggestion": "建议明确授权用途",
        },

        # 2. 价格合理性 (price_reasonableness)
        {
            "rule_name": "价格偏离市场区间",
            "category": "transaction",
            "clause_type": "price_reasonableness",
            "risk_level": "medium",
            "weight": 4,
            "description": "交易价格偏离同类作品市场区间",
            "suggestion": "建议参考市场均价调整",
        },

        # 3. 交付条件 (delivery_terms)
        {
            "rule_name": "无限次修改",
            "category": "transaction",
            "clause_type": "delivery_terms",
            "risk_level": "high",
            "weight": 7,
            "description": "合同要求无限制次数修改",
            "suggestion": "建议限定修改次数（如3次以内）",
        },
        {
            "rule_name": "交付时间过紧",
            "category": "transaction",
            "clause_type": "delivery_terms",
            "risk_level": "low",
            "weight": 3,
            "description": "交付时间少于合理工作量所需时间",
            "suggestion": "建议根据工作量评估合理交付时间",
        },

        # 4. 平台责任 (platform_liability)
        {
            "rule_name": "平台免责过度",
            "category": "transaction",
            "clause_type": "platform_liability",
            "risk_level": "high",
            "weight": 7,
            "description": "平台免责条款过于宽泛",
            "suggestion": "建议明确平台应承担的责任范围",
        },

        # 5. 知识产权担保 (ip_warranty)
        {
            "rule_name": "买方IP担保缺失",
            "category": "transaction",
            "clause_type": "ip_warranty",
            "risk_level": "medium",
            "weight": 5,
            "description": "未要求买方保证不用于非法用途",
            "suggestion": "建议增加买方知识产权合规承诺",
        },

        # 6. 再授权限制 (sublicense_restriction)
        {
            "rule_name": "未限制再授权",
            "category": "transaction",
            "clause_type": "sublicense_restriction",
            "risk_level": "medium",
            "weight": 5,
            "description": "未限制买方再授权给第三方",
            "suggestion": "建议明确是否允许再授权及条件",
        },

        # 7. 退款条件 (refund_policy)
        {
            "rule_name": "无退款条款",
            "category": "transaction",
            "clause_type": "refund_policy",
            "risk_level": "low",
            "weight": 3,
            "description": "合同未约定退款条件和期限",
            "suggestion": "建议明确交付不合格时的退款机制",
        },

        # 8. 质量验收 (quality_acceptance)
        {
            "rule_name": "验收标准缺失",
            "category": "transaction",
            "clause_type": "quality_acceptance",
            "risk_level": "medium",
            "weight": 4,
            "description": "未约定质量验收标准和异议期",
            "suggestion": "建议明确验收标准和异议提出期限",
        },
    ]

    for r in rules_data:
        db.add(ContractRiskRule(**r))

    db.commit()
