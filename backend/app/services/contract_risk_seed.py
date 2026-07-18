"""合约风险评估默认规则种子数据 (42 rules)."""


def seed_contract_risk_rules(db):
    """初始化合约风险评估默认规则 (42 条).

    覆盖 12 类通用合同条款 + 8 类交易合约条款.
    """
    from app.models.contract_risk import ContractRiskRule

    existing = db.query(ContractRiskRule).count()
    if existing > 0:
        return  # 已有规则不重复加载

    rules_data = [
        # ================================================================
        # 通用合同规则 (category="general", 12 类条款)
        # ================================================================

        # --- 1. copyright_ownership (1 rule) ---
        {
            "rule_name": "版权全权转让",
            "category": "general",
            "clause_type": "copyright_transfer_critical",
            "risk_level": "critical",
            "weight": 10,
            "description": "版权全权转让可能导致创作者失去所有后续权利",
            "suggestion": "建议保留完整著作权，仅授权特定用途",
        },

        # --- 2. license_scope (1 rule) ---
        {
            "rule_name": "独家授权范围过宽",
            "category": "general",
            "clause_type": "exclusive_rights_broad",
            "risk_level": "high",
            "weight": 8,
            "description": "独家授权范围过于宽泛可能限制创作者商业机会",
            "suggestion": "建议限定授权地域、期限和媒介",
        },

        # --- 3. auto_renewal (1 rule) ---
        {
            "rule_name": "自动续约",
            "category": "general",
            "clause_type": "auto_renewal",
            "risk_level": "medium",
            "weight": 5,
            "description": "自动续约可能导致创作者不知情下被长期约束",
            "suggestion": "建议设置续约需书面确认",
        },

        # --- 4. moral_rights (1 rule) ---
        {
            "rule_name": "放弃署名权",
            "category": "general",
            "clause_type": "moral_rights_waive",
            "risk_level": "high",
            "weight": 7,
            "description": "署名权是人身权不可放弃",
            "suggestion": "建议保留署名权条款",
        },

        # --- 5. derivative_works (1 rule) ---
        {
            "rule_name": "改编权转让",
            "category": "general",
            "clause_type": "derivative_works",
            "risk_level": "high",
            "weight": 7,
            "description": "改编权转让应明确范围和条件",
            "suggestion": "建议限定改编方向和修改幅度",
        },

        # --- 6. indemnity (1 rule) ---
        {
            "rule_name": "单方赔偿义务",
            "category": "general",
            "clause_type": "indemnity_unilateral",
            "risk_level": "medium",
            "weight": 5,
            "description": "赔偿义务应双方对等",
            "suggestion": "建议增加双方对等赔偿条款",
        },

        # --- 7. force_majeure (1 rule) ---
        {
            "rule_name": "不可抗力定义",
            "category": "general",
            "clause_type": "force_majeure",
            "risk_level": "low",
            "weight": 2,
            "description": "不可抗力定义应参照法律规定",
            "suggestion": "建议引用民法典不可抗力条款",
        },

        # --- 8. dispute_resolution (1 rule) ---
        {
            "rule_name": "争议管辖约定",
            "category": "general",
            "clause_type": "dispute_jurisdiction",
            "risk_level": "low",
            "weight": 2,
            "description": "争议管辖应便于创作者维权",
            "suggestion": "建议约定创作者所在地法院管辖",
        },

        # --- 9. confidentiality (1 rule) ---
        {
            "rule_name": "保密条款过严",
            "category": "general",
            "clause_type": "confidentiality_overreach",
            "risk_level": "medium",
            "weight": 4,
            "description": "保密范围不应覆盖公开信息",
            "suggestion": "建议排除已公开信息和法定披露",
        },

        # --- 10. termination (1 rule) ---
        {
            "rule_name": "解约违约金过高",
            "category": "general",
            "clause_type": "termination_penalty",
            "risk_level": "high",
            "weight": 7,
            "description": "违约金应与实际损失相当",
            "suggestion": "建议设定违约金上限",
        },

        # --- 11. payment_terms (1 rule) ---
        {
            "rule_name": "付款条件不明确",
            "category": "general",
            "clause_type": "payment_terms_vague",
            "risk_level": "medium",
            "weight": 4,
            "description": "付款时间、方式、条件应明确",
            "suggestion": "建议明确付款节点和逾期责任",
        },

        # --- 12. quality_standard (1 rule) ---
        {
            "rule_name": "质量标准缺失",
            "category": "general",
            "clause_type": "quality_standard_missing",
            "risk_level": "low",
            "weight": 2,
            "description": "交付成果应有可衡量的质量标准",
            "suggestion": "建议约定验收标准和流程",
        },

        # ================================================================
        # 交易合约规则 (category="transaction", 8+ 类条款)
        # ================================================================

        # --- 13. license_scope_mismatch (1 rule) ---
        {
            "rule_name": "授权用途不一致",
            "category": "transaction",
            "clause_type": "license_scope_mismatch",
            "risk_level": "high",
            "weight": 8,
            "description": "授权范围应与交易标的匹配",
            "suggestion": "建议核实授权用途与商品描述一致",
        },

        # --- 14. no_relicense (1 rule) ---
        {
            "rule_name": "未限制再授权",
            "category": "transaction",
            "clause_type": "no_relicense_restriction",
            "risk_level": "medium",
            "weight": 5,
            "description": "再授权可能导致权利失控",
            "suggestion": "建议明确禁止或限制再授权",
        },

        # --- 15. platform_liability (1 rule) ---
        {
            "rule_name": "平台免责过度",
            "category": "transaction",
            "clause_type": "platform_liability_exempt",
            "risk_level": "high",
            "weight": 7,
            "description": "平台应承担合理审核义务",
            "suggestion": "建议限制免责条款范围",
        },

        # --- 16. price_payment (1 rule) ---
        {
            "rule_name": "价格支付不明确",
            "category": "transaction",
            "clause_type": "price_payment_unclear",
            "risk_level": "medium",
            "weight": 5,
            "description": "交易价格和支付方式应清晰",
            "suggestion": "建议明确含税/不含税及支付方式",
        },

        # --- 17. delivery (1 rule) ---
        {
            "rule_name": "交付期限缺失",
            "category": "transaction",
            "clause_type": "delivery_deadline_missing",
            "risk_level": "medium",
            "weight": 4,
            "description": "交付期限是合同核心条款",
            "suggestion": "建议约定具体交付时间节点",
        },

        # --- 18. refund (1 rule) ---
        {
            "rule_name": "退款政策缺失",
            "category": "transaction",
            "clause_type": "refund_policy_absent",
            "risk_level": "medium",
            "weight": 4,
            "description": "消费者应有合理的退款权利",
            "suggestion": "建议约定退款条件和期限",
        },

        # --- 19. ip_warranty (1 rule) ---
        {
            "rule_name": "IP权属保证不足",
            "category": "transaction",
            "clause_type": "ip_warranty_insufficient",
            "risk_level": "high",
            "weight": 8,
            "description": "卖方应保证拥有完整IP授权",
            "suggestion": "建议要求提供权属证明",
        },

        # --- 20. usage_term (1 rule) ---
        {
            "rule_name": "使用期限未限制",
            "category": "transaction",
            "clause_type": "usage_term_limit",
            "risk_level": "high",
            "weight": 7,
            "description": "授权使用应有明确期限",
            "suggestion": "建议约定授权起止日期",
        },

        # --- 21. territory (1 rule) ---
        {
            "rule_name": "使用地域无限制",
            "category": "transaction",
            "clause_type": "territory_unlimited",
            "risk_level": "medium",
            "weight": 5,
            "description": "地域范围应明确约定",
            "suggestion": "建议限定授权销售区域",
        },

        # --- 22. audit (1 rule) ---
        {
            "rule_name": "审计权缺失",
            "category": "transaction",
            "clause_type": "audit_right_missing",
            "risk_level": "medium",
            "weight": 4,
            "description": "权利人应有合理的审计权利",
            "suggestion": "建议约定定期结算审计条款",
        },

        # --- 23. post_termination (1 rule) ---
        {
            "rule_name": "终止后义务缺失",
            "category": "transaction",
            "clause_type": "post_termination_obligation",
            "risk_level": "medium",
            "weight": 4,
            "description": "合同终止后应停止使用并销毁资料",
            "suggestion": "建议约定终止后的处理义务",
        },

        # --- 24. royalty (1 rule) ---
        {
            "rule_name": "版税计算方式不明",
            "category": "transaction",
            "clause_type": "royalty_calculation",
            "risk_level": "medium",
            "weight": 5,
            "description": "版税计算应透明可验证",
            "suggestion": "建议明确计算基数和分成比例",
        },

        # --- 25. minimum_guarantee (1 rule) ---
        {
            "rule_name": "最低保底缺失",
            "category": "transaction",
            "clause_type": "minimum_guarantee",
            "risk_level": "low",
            "weight": 2,
            "description": "建议约定最低保底收益",
            "suggestion": "建议根据市场情况设定保底",
        },

        # --- 26. account_settlement (1 rule) ---
        {
            "rule_name": "结算周期过长",
            "category": "transaction",
            "clause_type": "account_settlement",
            "risk_level": "low",
            "weight": 2,
            "description": "结算周期应合理",
            "suggestion": "建议约定30-90天结算周期",
        },

        # --- 27. tax_responsibility (1 rule) ---
        {
            "rule_name": "税费承担不明确",
            "category": "transaction",
            "clause_type": "tax_responsibility",
            "risk_level": "low",
            "weight": 2,
            "description": "税费应由谁承担应明确",
            "suggestion": "建议约定含税价或各自承担",
        },

        # --- 28. marketing_restrictions (1 rule) ---
        {
            "rule_name": "营销限制缺失",
            "category": "transaction",
            "clause_type": "marketing_restrictions",
            "risk_level": "medium",
            "weight": 4,
            "description": "品牌方应有营销推广限制",
            "suggestion": "建议约定宣传方式和范围",
        },

        # --- 29. exclusivity_compensation (1 rule) ---
        {
            "rule_name": "排他性补偿",
            "category": "transaction",
            "clause_type": "exclusivity_compensation",
            "risk_level": "medium",
            "weight": 4,
            "description": "排他条款应有对应补偿",
            "suggestion": "建议约定排他期补偿金额",
        },

        # --- 30. content_modification (1 rule) ---
        {
            "rule_name": "内容修改权",
            "category": "transaction",
            "clause_type": "content_modification",
            "risk_level": "low",
            "weight": 2,
            "description": "品牌方修改内容应有限制",
            "suggestion": "建议约定重大修改需创作者同意",
        },

        # --- 31. credit_attribution (1 rule) ---
        {
            "rule_name": "署名要求缺失",
            "category": "transaction",
            "clause_type": "credit_attribution",
            "risk_level": "low",
            "weight": 2,
            "description": "应要求品牌方正确署名",
            "suggestion": "建议约定署名方式和位置",
        },

        # --- 32. brand_reputation (1 rule) ---
        {
            "rule_name": "品牌声誉保护",
            "category": "transaction",
            "clause_type": "brand_reputation",
            "risk_level": "medium",
            "weight": 4,
            "description": "创作者有权拒绝不当品牌关联",
            "suggestion": "建议约定道德条款",
        },

        # --- 33. deliverable_acceptance (1 rule) ---
        {
            "rule_name": "交付物验收标准",
            "category": "transaction",
            "clause_type": "deliverable_acceptance",
            "risk_level": "low",
            "weight": 2,
            "description": "应有明确的验收标准",
            "suggestion": "建议约定验收流程和时限",
        },

        # --- 34. revision_limits (1 rule) ---
        {
            "rule_name": "修改次数限制",
            "category": "transaction",
            "clause_type": "revision_limits",
            "risk_level": "low",
            "weight": 2,
            "description": "无限修改不合理",
            "suggestion": "建议约定免费修改次数",
        },

        # --- 35. cancellation_policy (1 rule) ---
        {
            "rule_name": "取消政策",
            "category": "transaction",
            "clause_type": "cancellation_policy",
            "risk_level": "medium",
            "weight": 4,
            "description": "提前取消应有明确政策",
            "suggestion": "建议约定取消条件和费用",
        },

        # --- 36. force_majeure_transaction (1 rule) ---
        {
            "rule_name": "交易不可抗力",
            "category": "transaction",
            "clause_type": "force_majeure_transaction",
            "risk_level": "low",
            "weight": 2,
            "description": "交易也应约定不可抗力",
            "suggestion": "建议引用民法典条款",
        },

        # --- 37. assignment_prohibition (1 rule) ---
        {
            "rule_name": "转让限制",
            "category": "transaction",
            "clause_type": "assignment_prohibition",
            "risk_level": "medium",
            "weight": 4,
            "description": "未经同意不得转让合同",
            "suggestion": "建议约定合同转让限制",
        },

        # --- 38. entire_agreement (1 rule) ---
        {
            "rule_name": "完整协议条款",
            "category": "transaction",
            "clause_type": "entire_agreement",
            "risk_level": "low",
            "weight": 2,
            "description": "应约定本协议为完整协议",
            "suggestion": "建议添加完整协议声明",
        },

        # --- 39. severability (1 rule) ---
        {
            "rule_name": "可分割性",
            "category": "transaction",
            "clause_type": "severability",
            "risk_level": "low",
            "weight": 1,
            "description": "部分无效不影响其他条款",
            "suggestion": "建议添加可分割性条款",
        },

        # --- 40. governing_law (1 rule) ---
        {
            "rule_name": "适用法律",
            "category": "transaction",
            "clause_type": "governing_law",
            "risk_level": "low",
            "weight": 2,
            "description": "应明确适用中国法律",
            "suggestion": "建议约定中华人民共和国法律",
        },

        # --- 41. amendment_process (1 rule) ---
        {
            "rule_name": "修改程序",
            "category": "transaction",
            "clause_type": "amendment_process",
            "risk_level": "low",
            "weight": 2,
            "description": "合同修改应书面确认",
            "suggestion": "建议约定书面修改程序",
        },

        # --- 42. notice_requirements (1 rule) ---
        {
            "rule_name": "通知送达",
            "category": "transaction",
            "clause_type": "notice_requirements",
            "risk_level": "low",
            "weight": 1,
            "description": "应约定有效通知方式",
            "suggestion": "建议约定邮件/书面通知方式",
        },
    ]

    for r in rules_data:
        db.add(ContractRiskRule(**r))

    db.commit()
