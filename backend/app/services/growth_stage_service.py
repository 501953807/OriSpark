"""创作者成长阶段服务层 — 自动评估 + 任务清单 + 进度可视化."""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.growth_stage import CreatorGrowthStage, GrowthTask


# 四阶段定义
STAGE_DEFINITIONS = {
    "beginner": {
        "name_zh": "起步期",
        "min_monthly_revenue": 0,
        "max_monthly_revenue": 10000,
        "min_works": 0,
        "min_certificates": 0,
        "description_zh": "刚起步的创作者，正在探索自己的方向和风格。",
        "unlock_features": ["基础存证", "作品管理", "新手引导"],
    },
    "growing": {
        "name_zh": "成长期",
        "min_monthly_revenue": 10000,
        "max_monthly_revenue": 100000,
        "min_works": 50,
        "min_certificates": 5,
        "description_zh": "已有稳定产出和收入，需要建立品牌辨识度和多渠道分发。",
        "unlock_features": ["合同审查", "侵权监测", "多平台分发", "商业撮合"],
    },
    "scaling": {
        "name_zh": "规模化期",
        "min_monthly_revenue": 100000,
        "max_monthly_revenue": 1000000,
        "min_works": 200,
        "min_certificates": 20,
        "description_zh": "收入规模可观，需要专业化管理和团队化运营。",
        "unlock_features": ["IP授权撮合", "版权保险", "能力评估", "多市场扩展"],
    },
    "ecosystem": {
        "name_zh": "生态期",
        "min_monthly_revenue": 1000000,
        "max_monthly_revenue": float("inf"),
        "min_works": 500,
        "min_certificates": 50,
        "description_zh": "已形成个人品牌生态，可拓展团队、衍生产品和跨领域合作。",
        "unlock_features": ["AI训练数据授权", "全流程IP商业化", "高级风控", "定制服务"],
    },
}

# 各阶段任务清单
STAGE_TASKS = {
    "beginner": [
        {"category": "works", "title": "完成至少 10 件作品上传", "description": "建立作品集基础", "priority": 1},
        {"category": "certification", "title": "为前 5 件作品申请时间戳存证", "description": "保护原创权益的第一步", "priority": 1},
        {"category": "revenue", "title": "了解并设置月收入追踪", "description": "记录每一笔收入来源", "priority": 2},
        {"category": "distribution", "title": "选择 2 个主力平台发布内容", "description": "不要贪多，先做好两个平台", "priority": 2},
        {"category": "community", "title": "建立粉丝联系方式（邮箱/社群）", "description": "开始积累私域流量", "priority": 3},
    ],
    "growing": [
        {"category": "works", "title": "作品数突破 50 件", "description": "形成稳定的内容输出节奏", "priority": 1},
        {"category": "revenue", "title": "月收入稳定在 ¥10K+", "description": "验证变现模式的可持续性", "priority": 1},
        {"category": "certification", "title": "为重要作品申请版权注册", "description": "核心资产正式确权", "priority": 2},
        {"category": "distribution", "title": "扩展到 4+ 个平台分发", "description": "降低单一平台依赖风险", "priority": 2},
        {"category": "community", "title": "建立付费订阅或社群", "description": "发展核心粉丝群体", "priority": 3},
    ],
    "scaling": [
        {"category": "revenue", "title": "月收入突破 ¥100K", "description": "规模化收入里程碑", "priority": 1},
        {"category": "works", "title": "作品数达到 200+", "description": "建立丰富的内容库", "priority": 2},
        {"category": "certification", "title": "完成商标/IP 注册", "description": "品牌资产法律保护", "priority": 1},
        {"category": "distribution", "title": "拓展海外市场", "description": "多市场收入多元化", "priority": 2},
        {"category": "community", "title": "建立品牌合作体系", "description": "系统化对接品牌方", "priority": 3},
    ],
    "ecosystem": [
        {"category": "revenue", "title": "月收入突破 ¥1M", "description": "顶级创作者里程碑", "priority": 1},
        {"category": "works", "title": "作品库 500+ 件", "description": "庞大的数字资产库", "priority": 2},
        {"category": "distribution", "title": "建立衍生产品体系", "description": "POD/周边/联名", "priority": 1},
        {"category": "community", "title": "搭建团队或工作室", "description": "从个人到组织", "priority": 1},
        {"category": "certification", "title": "IP 授权矩阵", "description": "系统化 IP 商业化", "priority": 2},
    ],
}


def evaluate_stage(monthly_revenue: float, total_works: int, total_certificates: int, credit_score: float) -> dict:
    """
    根据指标自动评估创作者所处阶段。
    返回当前阶段信息和距下一阶段的进度。
    """
    stages_sorted = sorted(STAGE_DEFINITIONS.items(), key=lambda x: x[1]["min_monthly_revenue"])

    current_stage = stages_sorted[0][0]
    current_info = stages_sorted[0][1]

    for key, info in reversed(stages_sorted):
        if (monthly_revenue >= info["min_monthly_revenue"] and
                total_works >= info["min_works"] and
                total_certificates >= info["min_certificates"]):
            current_stage = key
            current_info = info
            break

    # 计算当前阶段内进度（基于收入占比）
    min_rev = current_info["min_monthly_revenue"]
    max_rev = current_info["max_monthly_revenue"]
    if max_rev == float("inf"):
        # 最高阶段，进度 100%
        stage_progress = 100.0
        next_stage = None
    else:
        stage_progress = min(((monthly_revenue - min_rev) / max(max_rev - min_rev, 1)) * 100, 100)
        # 找下一阶段
        idx = [s[0] for s in stages_sorted].index(current_stage)
        next_stage = stages_sorted[idx + 1][1] if idx + 1 < len(stages_sorted) else None

    # 距下一阶段进度
    next_progress = 0.0
    if next_stage:
        next_min_rev = next_stage["min_monthly_revenue"]
        next_max_rev = next_stage["max_monthly_revenue"]
        if next_max_rev == float("inf"):
            next_progress = min(monthly_revenue / max(next_min_rev, 1) * 100, 100)
        else:
            next_progress = min(((monthly_revenue - next_min_rev) / (next_max_rev - next_min_rev)) * 100, 100)
        next_progress = max(0, next_progress)

    return {
        "stage_key": current_stage,
        "stage_name_zh": current_info["name_zh"],
        "stage_progress": round(stage_progress, 1),
        "next_stage": next_stage,
        "next_stage_progress": round(next_progress, 1),
        "unlock_features": current_info["unlock_features"],
    }


def get_progress_dashboard(db: Session, user_id: str) -> dict:
    """获取成长进度仪表盘."""
    # 查找最近一次评估
    latest = db.query(CreatorGrowthStage).filter(
        CreatorGrowthStage.user_id == user_id,
    ).order_by(CreatorGrowthStage.evaluated_at.desc()).first()

    if latest:
        monthly_revenue = latest.monthly_revenue_yuan
        total_works = latest.total_works
        total_certs = latest.total_certificates
    else:
        monthly_revenue = 0
        total_works = 0
        total_certs = 0

    evaluation = evaluate_stage(monthly_revenue, total_works, total_certs, latest.credit_score if latest else 50)

    # 获取当前阶段任务
    tasks = STAGE_TASKS.get(evaluation["stage_key"], [])
    completed_count = 0
    if latest:
        completed_count = latest.total_works  # placeholder: would query GrowthTask table

    total_task_count = len(tasks)

    return {
        "current_stage": {
            "key": evaluation["stage_key"],
            "name_zh": evaluation["stage_name_zh"],
            **evaluation.get("next_stage", {}),
            "unlock_features": evaluation["unlock_features"],
        },
        "progress_percent": evaluation["stage_progress"],
        "next_stage": {
            "key": evaluation["next_stage"]["name_zh"] if evaluation["next_stage"] else "",
            "name_zh": evaluation["next_stage"]["name_zh"] if evaluation["next_stage"] else None,
        } if evaluation["next_stage"] else None,
        "remaining_to_next": {
            "monthly_revenue_gap": max(0, evaluation["next_stage"]["min_monthly_revenue"] - monthly_revenue) if evaluation["next_stage"] else 0,
            "works_needed": max(0, evaluation["next_stage"]["min_works"] - total_works) if evaluation["next_stage"] else 0,
            "certs_needed": max(0, evaluation["next_stage"]["min_certificates"] - total_certs) if evaluation["next_stage"] else 0,
        },
        "completed_tasks": completed_count,
        "total_tasks": total_task_count,
        "tasks": tasks,
    }


def update_growth_stage(db: Session, user_id: str, data: dict) -> dict:
    """手动更新成长阶段指标."""
    existing = db.query(CreatorGrowthStage).filter(
        CreatorGrowthStage.user_id == user_id,
    ).first()

    if existing:
        existing.monthly_revenue_yuan = data.get("monthly_revenue_yuan", existing.monthly_revenue_yuan)
        existing.total_works = data.get("total_works", existing.total_works)
        existing.total_certificates = data.get("total_certificates", existing.total_certificates)
        existing.credit_score = data.get("credit_score", existing.credit_score)
        existing.evaluated_at = datetime.utcnow()
    else:
        existing = CreatorGrowthStage(
            user_id=user_id,
            monthly_revenue_yuan=data.get("monthly_revenue_yuan", 0),
            total_works=data.get("total_works", 0),
            total_certificates=data.get("total_certificates", 0),
            credit_score=data.get("credit_score", 50),
        )
        db.add(existing)

    db.commit()
    db.refresh(existing)

    evaluation = evaluate_stage(
        existing.monthly_revenue_yuan,
        existing.total_works,
        existing.total_certificates,
        existing.credit_score,
    )

    return {
        "id": existing.id,
        "stage_key": evaluation["stage_key"],
        "stage_name_zh": evaluation["stage_name_zh"],
        "progress_percent": evaluation["stage_progress"],
        "next_stage_progress": evaluation["next_stage_progress"],
    }


def complete_task(db: Session, user_id: str, task_id: str) -> dict:
    """标记任务完成."""
    task = db.query(GrowthTask).filter(
        GrowthTask.id == task_id,
        GrowthTask.user_id == user_id,
    ).first()
    if not task:
        raise ValueError("Task not found")
    task.is_completed = True
    task.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    return {
        "id": task.id,
        "is_completed": task.is_completed,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }
