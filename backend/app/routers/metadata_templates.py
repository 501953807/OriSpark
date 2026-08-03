"""元数据模板 API 路由 — 对应: docs/modules-v5/01-creative-assets.md
Phase 2: 摄影师批量元数据模板
端点: 9 (metadata_templates)

业务逻辑已提取至 metadata_template_service.py.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import ApiResponse
from app.deps import require_auth
from app.services.metadata_template_service import (
    list_templates, create_template, update_template, delete_template,
    list_fields, add_field, update_field, delete_field, apply_template,
    get_template, seed_default_templates,
)

router = APIRouter()


class CreateTemplatePayload(BaseModel):
    name: str
    description: str = None
    fields: list = None
    is_default: bool = False


class UpdateTemplatePayload(BaseModel):
    name: str = None
    description: str = None
    fields: list = None
    is_default: bool = None


class AddFieldPayload(BaseModel):
    field_key: str
    label: str
    field_type: str = "string"
    required: bool = False
    default_value: str = None
    choices: list = None
    sort_order: int = 0


class UpdateFieldPayload(BaseModel):
    field_key: str = None
    label: str = None
    field_type: str = None
    required: bool = None
    default_value: str = None
    choices: list = None
    sort_order: int = None


class ApplyTemplatePayload(BaseModel):
    work_id: str


# ============================================================================
# 模板 CRUD
# ============================================================================


@router.get("/metadata-templates", response_model=ApiResponse)
def list_templates_endpoint(is_default: bool = False, db: Session = Depends(get_db)):
    """获取所有元数据模板列表."""
    return ApiResponse(data=list_templates(db, is_default))


@router.post("/metadata-templates", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def create_template_endpoint(payload: CreateTemplatePayload, db: Session = Depends(get_db)):
    """创建元数据模板."""
    data = payload.model_dump(exclude_unset=True)
    result = create_template(db, **data)
    return ApiResponse(data=result, message="模板创建成功")


@router.put("/metadata-templates/{template_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def update_template_endpoint(template_id: str, payload: UpdateTemplatePayload, db: Session = Depends(get_db)):
    """更新元数据模板."""
    result = update_template(db, template_id, payload.model_dump(exclude_unset=True))
    if not result:
        raise HTTPException(status_code=404, detail="模板不存在")
    return ApiResponse(data=result, message="模板更新成功")


@router.delete("/metadata-templates/{template_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_template_endpoint(template_id: str, db: Session = Depends(get_db)):
    """删除元数据模板."""
    deleted = delete_template(db, template_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="模板不存在")
    return ApiResponse(data={"success": True}, message="模板已删除")


# ============================================================================
# 字段 CRUD
# ============================================================================


@router.get("/metadata-templates/{template_id}/fields", response_model=ApiResponse)
def list_fields_endpoint(template_id: str, db: Session = Depends(get_db)):
    """获取模板字段列表."""
    result = list_fields(db, template_id)
    if result is None:
        raise HTTPException(status_code=404, detail="模板不存在")
    return ApiResponse(data=result)


@router.post("/metadata-templates/{template_id}/fields", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def add_field_endpoint(template_id: str, payload: AddFieldPayload, db: Session = Depends(get_db)):
    """向模板添加字段."""
    result = add_field(db, template_id, payload.model_dump(exclude_unset=True))
    if not result:
        raise HTTPException(status_code=404, detail="模板不存在")
    return ApiResponse(data=result, message="字段添加成功")


@router.put("/metadata-templates/{template_id}/fields/{field_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def update_field_endpoint(template_id: str, field_id: str, payload: UpdateFieldPayload, db: Session = Depends(get_db)):
    """更新模板字段."""
    result = update_field(db, field_id, payload.model_dump(exclude_unset=True))
    if not result:
        raise HTTPException(status_code=404, detail="字段不存在")
    return ApiResponse(data=result, message="字段更新成功")


@router.delete("/metadata-templates/{template_id}/fields/{field_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_field_endpoint(template_id: str, field_id: str, db: Session = Depends(get_db)):
    """删除模板字段."""
    deleted = delete_field(db, field_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="字段不存在")
    return ApiResponse(data={"success": True}, message="字段已删除")


# ============================================================================
# 应用模板到作品
# ============================================================================


@router.post("/metadata-templates/{template_id}/apply", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def apply_template_endpoint(template_id: str, payload: ApplyTemplatePayload, db: Session = Depends(get_db)):
    """将模板应用到作品."""
    if not payload.work_id:
        raise HTTPException(status_code=400, detail="work_id is required")
    result = apply_template(db, template_id, payload.work_id)
    if not result:
        raise HTTPException(status_code=404, detail="模板不存在")
    return ApiResponse(data=result, message="模板已应用")


# ============================================================================
# Seed
# ============================================================================


@router.post("/metadata-templates/seed", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def seed_endpoint(db: Session = Depends(get_db)):
    """初始化默认模板种子."""
    seed_default_templates(db)
    return ApiResponse(message="默认模板已初始化")
