"""元数据模板 API 路由 — 对应: docs/modules-v5/01-creative-assets.md
Phase 2: 摄影师批量元数据模板
端点: 9 (metadata_templates)"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.metadata_template import MetadataTemplate, TemplateField
from app.models.work import generate_uuid
from app.schemas.common import ApiResponse
from app.deps import require_auth

router = APIRouter()


class CreateTemplatePayload(BaseModel):
    name: str
    description: Optional[str] = None
    fields: Optional[list] = None
    is_default: bool = False


class UpdateTemplatePayload(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    fields: Optional[list] = None
    is_default: Optional[bool] = None


class AddFieldPayload(BaseModel):
    field_key: str
    label: str
    field_type: str = "string"
    required: bool = False
    default_value: Optional[str] = None
    choices: Optional[list] = None
    sort_order: int = 0


class UpdateFieldPayload(BaseModel):
    field_key: Optional[str] = None
    label: Optional[str] = None
    field_type: Optional[str] = None
    required: Optional[bool] = None
    default_value: Optional[str] = None
    choices: Optional[list] = None
    sort_order: Optional[int] = None


class ApplyTemplatePayload(BaseModel):
    work_id: str

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


@router.get("/metadata-templates", response_model=ApiResponse[list])
def list_templates(
    is_default: bool = False,
    db: Session = Depends(get_db),
):
    """获取所有元数据模板列表."""
    q = db.query(MetadataTemplate)
    if is_default:
        q = q.filter(MetadataTemplate.is_default == True)
    templates = q.order_by(MetadataTemplate.created_at.desc()).all()
    return ApiResponse(data=[
        {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "is_default": t.is_default,
            "created_by": t.created_by,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "field_count": len(t.fields_list) if hasattr(t, "fields_list") else 0,
        }
        for t in templates
    ])


@router.post("/metadata-templates", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_template(payload: CreateTemplatePayload, db: Session = Depends(get_db)):
    """创建元数据模板."""
    template = MetadataTemplate(
        name=payload.name,
        description=payload.description,
        fields=payload.fields,
        is_default=payload.is_default,
    )
    db.add(template)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(template)
    return ApiResponse(data=_template_to_dict(template), message="模板创建成功")


@router.put("/metadata-templates/{template_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def update_template(template_id: str, payload: UpdateTemplatePayload, db: Session = Depends(get_db)):
    """更新元数据模板."""
    template = db.query(MetadataTemplate).filter(MetadataTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(template, key, value)
    template.updated_at = datetime.utcnow()
    template.updated_at = datetime.utcnow()
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(template)
    return ApiResponse(data=_template_to_dict(template), message="模板更新成功")


@router.delete("/metadata-templates/{template_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_template(template_id: str, db: Session = Depends(get_db)):
    """删除元数据模板."""
    template = db.query(MetadataTemplate).filter(MetadataTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    db.delete(template)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data={"success": True}, message="模板已删除")


# ============================================================================
# 字段 CRUD
# ============================================================================


@router.get("/metadata-templates/{template_id}/fields", response_model=ApiResponse[list])
def list_fields(template_id: str, db: Session = Depends(get_db)):
    """获取模板字段列表."""
    if not db.query(MetadataTemplate).filter(MetadataTemplate.id == template_id).first():
        raise HTTPException(status_code=404, detail="模板不存在")
    fields = (
        db.query(TemplateField)
        .filter(TemplateField.template_id == template_id)
        .order_by(TemplateField.sort_order)
        .all()
    )
    return ApiResponse(data=[_field_to_dict(f) for f in fields])


@router.post("/metadata-templates/{template_id}/fields", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def add_field(template_id: str, payload: AddFieldPayload, db: Session = Depends(get_db)):
    """向模板添加字段."""
    if not db.query(MetadataTemplate).filter(MetadataTemplate.id == template_id).first():
        raise HTTPException(status_code=404, detail="模板不存在")
    field = TemplateField(
        template_id=template_id,
        field_key=payload.field_key,
        label=payload.label,
        field_type=payload.field_type,
        required=payload.required,
        default_value=payload.default_value,
        choices=payload.choices,
        sort_order=payload.sort_order,
    )
    db.add(field)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(field)
    return ApiResponse(data=_field_to_dict(field), message="字段添加成功")


@router.put("/metadata-templates/{template_id}/fields/{field_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def update_field(template_id: str, field_id: str, payload: UpdateFieldPayload, db: Session = Depends(get_db)):
    """更新模板字段."""
    field = db.query(TemplateField).filter(TemplateField.id == field_id).first()
    if not field or field.template_id != template_id:
        raise HTTPException(status_code=404, detail="字段不存在")
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(field, key, value)
    field.updated_at = datetime.utcnow()
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(field)
    return ApiResponse(data=_field_to_dict(field), message="字段更新成功")


@router.delete("/metadata-templates/{template_id}/fields/{field_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_field(template_id: str, field_id: str, db: Session = Depends(get_db)):
    """删除模板字段."""
    field = db.query(TemplateField).filter(TemplateField.id == field_id).first()
    if not field or field.template_id != template_id:
        raise HTTPException(status_code=404, detail="字段不存在")
    db.delete(field)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data={"success": True}, message="字段已删除")


# ============================================================================
# 应用模板到作品
# ============================================================================


@router.post("/metadata-templates/{template_id}/apply", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def apply_template(template_id: str, payload: ApplyTemplatePayload, db: Session = Depends(get_db)):
    """将模板应用到作品."""
    work_id = payload.work_id
    if not work_id:
        raise HTTPException(status_code=400, detail="work_id is required")
    template = db.query(MetadataTemplate).filter(MetadataTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return ApiResponse(
        data={
            "template_id": template_id,
            "work_id": work_id,
            "fields": template.fields or [],
        },
        message="模板已应用",
    )


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
        "field_count": len(t.fields_list) if hasattr(t, "fields_list") else 0,
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
