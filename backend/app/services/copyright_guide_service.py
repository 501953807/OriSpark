"""版权登记指南服务层."""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.copyright_guide import CopyrightRegistration, RegistrationGuide


# 预置各作品类型的登记指南
DEFAULT_GUIDES = [
    {
        "work_type": "illustration",
        "title_zh": "美术/插画作品登记",
        "steps": [
            {"step": 1, "title": "准备作品原稿", "description": "提供清晰的作品扫描件或电子文件 (PNG/JPG, 300dpi+)", "required_files": ["作品原稿"]},
            {"step": 2, "title": "填写申请表", "description": "在版权保护中心网站填写作品名称、创作完成时间、首次发表日期", "required_files": ["申请表"]},
            {"step": 3, "title": "提交身份证明", "description": "身份证/营业执照复印件", "required_files": ["身份证明"]},
            {"step": 4, "title": "缴纳费用", "description": "个人登记 ¥200/件, 单位登记 ¥500/件", "required_files": []},
            {"step": 5, "title": "等待审核", "description": "通常 30-60 个工作日完成审核", "required_files": []},
        ],
        "estimated_days": 45,
        "estimated_fee_yuan": 200,
    },
    {
        "work_type": "photo",
        "title_zh": "摄影作品登记",
        "steps": [
            {"step": 1, "title": "准备原始照片文件", "description": "提供 RAW 格式或高质量 JPG，包含 EXIF 信息", "required_files": ["原始照片"]},
            {"step": 2, "title": "填写申请表", "description": "注明拍摄时间、地点、设备信息", "required_files": ["申请表"]},
            {"step": 3, "title": "提交身份证明", "description": "身份证复印件", "required_files": ["身份证明"]},
            {"step": 4, "title": "缴纳费用", "description": "个人登记 ¥200/件", "required_files": []},
            {"step": 5, "title": "等待审核", "description": "通常 30-60 个工作日", "required_files": []},
        ],
        "estimated_days": 45,
        "estimated_fee_yuan": 200,
    },
    {
        "work_type": "music",
        "title_zh": "音乐作品登记",
        "steps": [
            {"step": 1, "title": "准备乐谱和音频", "description": "提供完整乐谱 (PDF) 和音频文件 (WAV/MP3)", "required_files": ["乐谱", "音频文件"]},
            {"step": 2, "title": "填写申请表", "description": "注明词曲作者、演奏者、录制时间", "required_files": ["申请表"]},
            {"step": 3, "title": "提交合作者声明", "description": "如有多位创作者，需提供合作者同意书", "required_files": ["合作者声明"]},
            {"step": 4, "title": "缴纳费用", "description": "¥200/件", "required_files": []},
            {"step": 5, "title": "等待审核", "description": "音乐作品审核时间可能较长，约 60-90 天", "required_files": []},
        ],
        "estimated_days": 75,
        "estimated_fee_yuan": 200,
    },
    {
        "work_type": "writing",
        "title_zh": "文字作品登记",
        "steps": [
            {"step": 1, "title": "准备稿件", "description": "提供完整或节选稿件 PDF 文档", "required_files": ["稿件"]},
            {"step": 2, "title": "填写申请表", "description": "注明作品字数、创作时间、体裁类型", "required_files": ["申请表"]},
            {"step": 3, "title": "提交身份证明", "description": "身份证复印件", "required_files": ["身份证明"]},
            {"step": 4, "title": "缴纳费用", "description": "¥200/件", "required_files": []},
            {"step": 5, "title": "等待审核", "description": "通常 30-60 个工作日", "required_files": []},
        ],
        "estimated_days": 45,
        "estimated_fee_yuan": 200,
    },
]


def get_or_create_guides(db: Session) -> list[RegistrationGuide]:
    """初始化预置的登记指南."""
    for guide_data in DEFAULT_GUIDES:
        existing = db.query(RegistrationGuide).filter(
            RegistrationGuide.work_type == guide_data["work_type"],
        ).first()
        if not existing:
            guide = RegistrationGuide(
                work_type=guide_data["work_type"],
                title_zh=guide_data["title_zh"],
                steps=guide_data["steps"],
                estimated_days=guide_data["estimated_days"],
                estimated_fee_yuan=guide_data["estimated_fee_yuan"],
            )
            db.add(guide)
    db.commit()
    return db.query(RegistrationGuide).filter(RegistrationGuide.is_active == True).all()


def get_guide(db: Session, work_type: str) -> Optional[RegistrationGuide]:
    """获取特定作品类型的登记指南."""
    return db.query(RegistrationGuide).filter(
        RegistrationGuide.work_type == work_type,
        RegistrationGuide.is_active == True,
    ).first()


def create_registration(
    db: Session, user_id: str, title: str, work_type: str,
    registration_type: str = "domestic",
) -> dict:
    """创建新的版权登记申请."""
    reg = CopyrightRegistration(
        user_id=user_id,
        title=title,
        work_type=work_type,
        registration_type=registration_type,
    )
    db.add(reg)
    db.flush()
    return {"id": reg.id, "status": reg.status}


def update_registration(
    db: Session, user_id: str, reg_id: str, data: dict,
) -> bool:
    """更新登记申请状态."""
    reg = db.query(CopyrightRegistration).filter(
        CopyrightRegistration.id == reg_id,
        CopyrightRegistration.user_id == user_id,
    ).first()
    if not reg:
        return False
    for key in ("status", "application_number", "registration_date", "fee_yuan", "notes", "certificate_url"):
        if key in data and data[key] is not None:
            setattr(reg, key, data[key])
    db.flush()
    return True


def list_registrations(db: Session, user_id: str) -> list[CopyrightRegistration]:
    """获取用户的版权登记记录."""
    return db.query(CopyrightRegistration).filter(
        CopyrightRegistration.user_id == user_id,
    ).order_by(CopyrightRegistration.created_at.desc()).all()


def get_registration_summary(db: Session, user_id: str) -> dict:
    """获取登记概览: 按状态/类型分布."""
    regs = db.query(CopyrightRegistration).filter(
        CopyrightRegistration.user_id == user_id,
    ).all()

    by_status = {}
    by_type = {}
    total_fees = 0

    for r in regs:
        by_status[r.status] = by_status.get(r.status, 0) + 1
        by_type[r.work_type] = by_type.get(r.work_type, 0) + 1
        total_fees += r.fee_yuan or 0

    return {
        "total": len(regs),
        "by_status": by_status,
        "by_type": by_type,
        "total_fees_yuan": total_fees,
    }
