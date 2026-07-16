"""创作者导航种子数据 — 默认任务配置."""


def seed_navigation_tasks(db):
    """初始化创作者导航默认任务 (12+ 条)."""
    from app.models.navigation import NavigationTask

    existing = db.query(NavigationTask).count()
    if existing > 0:
        return  # 已有任务不重复加载

    tasks_data = [
        # ========== Onboarding 路径 ==========
        {
            "task_key": "complete_profile",
            "category": "onboarding",
            "priority": 1,
            "title": "完善个人资料",
            "description": "上传头像并填写个人简介，让其他用户更好地了解你",
            "check_expression": None,
        },
        {
            "task_key": "upload_work",
            "category": "onboarding",
            "priority": 2,
            "title": "上传第一个作品",
            "description": "上传你的第一个原创作品，开启创作者之旅",
            "check_expression": None,
        },
        {
            "task_key": "set_payment",
            "category": "onboarding",
            "priority": 3,
            "title": "设置收款方式",
            "description": "绑定收款账户，确保收入及时到账",
            "check_expression": None,
        },
        {
            "task_key": "read_terms",
            "category": "onboarding",
            "priority": 4,
            "title": "阅读平台规则",
            "description": "了解平台基本规则和社区准则",
            "check_expression": None,
        },

        # ========== Compliance 路径 ==========
        {
            "task_key": "verify_identity",
            "category": "compliance",
            "priority": 1,
            "title": "完成实名认证",
            "description": "提交身份证明以获得平台认证标识",
            "check_expression": None,
        },
        {
            "task_key": "review_first_contract",
            "category": "compliance",
            "priority": 2,
            "title": "审查第一份合同",
            "description": "使用合约风险评估工具审查你的第一份合同",
            "check_expression": None,
        },
        {
            "task_key": "setup_license",
            "category": "compliance",
            "priority": 3,
            "title": "配置版权授权",
            "description": "为你的作品设置 AI 训练数据授权选项",
            "check_expression": None,
        },

        # ========== Growth 路径 ==========
        {
            "task_key": "create_listing",
            "category": "growth",
            "priority": 1,
            "title": "创建第一个挂牌",
            "description": "将你的作品上架为交易挂牌，等待买家订购",
            "check_expression": None,
        },
        {
            "task_key": "connect_social",
            "category": "growth",
            "priority": 2,
            "title": "绑定社交媒体账号",
            "description": "连接你的 YouTube、Patreon 等社交账号",
            "check_expression": None,
        },
        {
            "task_key": "review_revenue",
            "category": "growth",
            "priority": 3,
            "title": "查看收入分析",
            "description": "使用收入多元化分析工具评估收入健康度",
            "check_expression": None,
        },
        {
            "task_key": "join_community",
            "category": "growth",
            "priority": 4,
            "title": "加入创作者社区",
            "description": "参与社区讨论，与其他创作者交流经验",
            "check_expression": None,
        },
    ]

    for t in tasks_data:
        db.add(NavigationTask(**t))

    db.commit()
