# -*- coding: utf-8 -*-
"""元数据模板服务层 — 从 metadata_templates.py 提取的业务逻辑."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.metadata_template import MetadataTemplate, TemplateField
from app.schemas.common import ApiResponse

# 默认模板种子
_DEFAULT_TEMPLATES = [
    {
        "name": "IPTC Core",
        "description": "标准 IPTC 元数据字段",
        "is_default": True,
        "fields": [
            {"field_key": "title", "label": "标题", "field_type": "string", "required": True},
            {"field_key": "creator", "label": "创作者", "field_type": "string", "required": True},
            {"field_key": "copyright", "label": "版权信息", "field_type": "string", "required": False},
            {"field_key": "description", "label": "描述", "field_type": "text", "required": False},
            {"field_key": "keywords", "label": "关键词", "field_type": "string", "required": False},
        ],
    },
    {
        "name": "EXIF Camera",
        "description": "相机拍摄参数",
        "is_default": True,
        "fields": [
            {"field_key": "camera_make", "label": "相机品牌", "field_type": "string", "required": False},
            {"field_key": "camera_model", "label": "相机型号", "field_type": "string", "required": False},
            {"field_key": "lens", "label": "镜头", "field_type": "string", "required": False},
            {"field_key": "focal_length", "label": "焦距", "field_type": "string", "required": False},
            {"field_key": "aperture", "label": "光圈", "field_type": "string", "required": False},
            {"field_key": "shutter_speed", "label": "快门速度", "field_type": "string", "required": False},
            {"field_key": "iso", "label": "ISO", "field_type": "string", "required": False},
            {"field_key": "exposure_time", "label": "曝光时间", "field_type": "string", "required": False},
        ],
    },
    {
        "name": "Creative Commons",
        "description": "创作共享许可信息",
        "is_default": True,
        "fields": [
            {"field_key": "license", "label": "许可证", "field_type": "choice", "required": True,
             "choices": ["CC BY 4.0", "CC BY-SA 4.0", "CC BY-NC 4.0", "CC BY-NC-SA 4.0", "CC BY-ND 4.0", "CC BY-NC-ND 4.0", "Public Domain"]},
            {"field_key": "author", "label": "作者", "field_type": "string", "required": True},
            {"field_key": "source", "label": "来源", "field_type": "string", "required": False},
            {"field_key": "attribution", "label": "署名要求", "field_type": "text", "required": False},
        ],
    },
]


def seed_default_templates(db: Session) -> None:
    """初始化默认模板. 幂等: 已存在同名模板则跳过."""
    for tpl_data in _DEFAULT_TEMPLATES:
        existing = db.query(MetadataTemplate).filter(
            MetadataTemplate.name == tpl_data["name"]
        ).first()
        if existing:
            continue
        template = MetadataTemplate(
            name=tpl_data["name"],
            description=tpl_data["description"],
            is_default=tpl_data["is_default"],
            fields=tpl_data["fields"],
        )
        db.add(template)
        db.flush()
        for i, f_data in enumerate(tpl_data["fields"]):
            field = TemplateField(
                template_id=template.id,
                field_key=f_data["field_key"],
                label=f_data["label"],
                field_type=f_data["field_type"],
                required=f_data.get("required", False),
                default_value=f_data.get("default_value"),
                choices=f_data.get("choices"),
                sort_order=i,
            )
            db.add(field)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


# ============================================================================
# 模板 CRUD
# ============================================================================


def list_templates(db: Session, is_default: bool = False):
    """获取所有元数据模板列表."""
    q = db.query(MetadataTemplate)
    if is_default:
        q = q.filter(MetadataTemplate.is_default == True)
    templates = q.order_by(MetadataTemplate.created_at.desc()).all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "is_default": t.is_default,
            "created_by": t.created_by,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "field_count": len(t.fields) if t.fields else 0,
        }
        for t in templates
    ]


def create_template(db: Session, name: str, description: Optional[str],
                    fields: Optional[list], is_default: bool = False):
    """创建元数据模板."""
    template = MetadataTemplate(
        name=name,
        description=description,
        fields=fields,
        is_default=is_default,
    )
    db.add(template)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(template)
    return _template_to_dict(template)


def update_template(db: Session, template_id: str, payload: dict) -> Optional[dict]:
    """更新元数据模板."""
    template = db.query(MetadataTemplate).filter(MetadataTemplate.id == template_id).first()
    if not template:
        return None
    for key, value in payload.items():
        setattr(template, key, value)
    template.updated_at = datetime.now(timezone.utc)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(template)
    return _template_to_dict(template)


def delete_template(db: Session, template_id: str) -> bool:
    """删除元数据模板."""
    template = db.query(MetadataTemplate).filter(MetadataTemplate.id == template_id).first()
    if not template:
        return False
    db.delete(template)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return True


def get_template(db: Session, template_id: str) -> Optional[dict]:
    """获取单个模板详情."""
    template = db.query(MetadataTemplate).filter(MetadataTemplate.id == template_id).first()
    if not template:
        return None
    return _template_to_dict(template)


def list_fields(db: Session, template_id: str) -> list:
    """获取模板字段列表."""
    if not db.query(MetadataTemplate).filter(MetadataTemplate.id == template_id).first():
        return None
    fields = (
        db.query(TemplateField)
        .filter(TemplateField.template_id == template_id)
        .order_by(TemplateField.sort_order)
        .all()
    )
    return [_field_to_dict(f) for f in fields]


def add_field(db: Session, template_id: str, payload: dict) -> Optional[dict]:
    """向模板添加字段."""
    if not db.query(MetadataTemplate).filter(MetadataTemplate.id == template_id).first():
        return None
    field = TemplateField(
        template_id=template_id,
        field_key=payload["field_key"],
        label=payload["label"],
        field_type=payload["field_type"],
        required=payload.get("required", False),
        default_value=payload.get("default_value"),
        choices=payload.get("choices"),
        sort_order=payload.get("sort_order", 0),
    )
    db.add(field)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(field)
    return _field_to_dict(field)


def update_field(db: Session, field_id: str, payload: dict) -> Optional[dict]:
    """更新模板字段."""
    field = db.query(TemplateField).filter(TemplateField.id == field_id).first()
    if not field:
        return None
    for key, value in payload.items():
        setattr(field, key, value)
    field.updated_at = datetime.now(timezone.utc)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(field)
    return _field_to_dict(field)


def delete_field(db: Session, field_id: str) -> bool:
    """删除模板字段."""
    field = db.query(TemplateField).filter(TemplateField.id == field_id).first()
    if not field:
        return False
    db.delete(field)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return True


def apply_template(db: Session, template_id: str, work_id: str) -> Optional[dict]:
    """将模板应用到作品（返回模板字段，前端用于表单填充）."""
    template = db.query(MetadataTemplate).filter(MetadataTemplate.id == template_id).first()
    if not template:
        return None
    return {
        "template_id": template_id,
        "work_id": work_id,
        "fields": template.fields or [],
    }


# ============================================================================
# 辅助函数
# ============================================================================


def _template_to_dict(t: MetadataTemplate) -> dict:
    return {
        "id": t.id,
        "name": t.name,
        "description": t.description,
        "is_default": t.is_default,
        "created_by": t.created_by,
        "fields": t.fields or [],
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        "field_count": len(t.fields) if t.fields else 0,
    }


def _field_to_dict(f: TemplateField) -> dict:
    return {
        "id": f.id,
        "template_id": f.template_id,
        "field_key": f.field_key,
        "label": f.label,
        "field_type": f.field_type,
        "required": f.required,
        "default_value": f.default_value,
        "choices": f.choices,
        "sort_order": f.sort_order,
        "created_at": f.created_at.isoformat() if f.created_at else None,
        "updated_at": f.updated_at.isoformat() if f.updated_at else None,
    }
