"""维权流水线 Pydantic schemas."""

from typing import Optional, Any
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


# ==============================================================================
# EnforcementAction schemas
# ==============================================================================


class EnforcementActionCreate(BaseModel):
    """创建维权行动请求."""

    monitor_result_id: str = Field(..., description="关联的监测结果 ID")
    action_type: str = Field(
        ..., description="platform_complaint / dmca_notice / lawyer_letter / litigation",
    )
    platform: str = Field(..., description="平台名")
    template_id: Optional[str] = None


class EnforcementActionUpdate(BaseModel):
    """更新维权行动."""

    status: Optional[str] = None
    complaint_text: Optional[str] = None
    template_used: Optional[str] = None
    sent_at: Optional[datetime] = None
    response_text: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_type: Optional[str] = None  # takedown / settlement / dismissed / litigation_started
    compensation_amount: Optional[float] = None
    notes: Optional[str] = None


class EnforcementActionResponse(BaseModel):
    """维权行动响应."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    monitor_result_id: str
    work_id: Optional[str] = None
    action_type: str
    platform: str
    status: str
    complaint_text: Optional[str] = None
    template_used: Optional[str] = None
    sent_at: Optional[datetime] = None
    response_text: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_type: Optional[str] = None
    compensation_amount: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Embedded work info (populated by router)
    work_title: Optional[str] = None
    work_file_type: Optional[str] = None
    infringement_url: Optional[str] = None
    similarity_score: Optional[float] = None


# ==============================================================================
# EnforcementTemplate schemas
# ==============================================================================


class EnforcementTemplateCreate(BaseModel):
    """创建投诉模板."""

    platform: str
    jurisdiction: str = Field(default="global", pattern="^(cn|us|eu|global)$")
    action_type: str = Field(default="copyright", description="dmca / copyright / trademark / design_right")
    title: str = Field(..., max_length=200)
    body_template: str
    required_evidence: Optional[list[str]] = None
    filing_url: Optional[str] = None


class EnforcementTemplateResponse(BaseModel):
    """投诉模板响应."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    platform: str
    jurisdiction: str
    action_type: str
    title: str
    body_template: str
    required_evidence: Optional[list[str]] = None
    filing_url: Optional[str] = None
    created_at: datetime


# ==============================================================================
# ComplaintMaterial schemas
# ==============================================================================


class ComplaintMaterialCreate(BaseModel):
    """创建投诉材料."""

    enforcement_action_id: str
    material_type: str = Field(..., description="pdf_package / prefilled_url / api_config")
    material_path: Optional[str] = None
    variables: Optional[dict[str, Any]] = None


class ComplaintMaterialResponse(BaseModel):
    """投诉材料响应."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    enforcement_action_id: str
    material_type: Optional[str] = None
    material_path: Optional[str] = None
    variables: Optional[dict[str, Any]] = None
    created_at: datetime


# ==============================================================================
# Evidence package schemas
# ==============================================================================


class EvidencePackageData(BaseModel):
    """聚合的证据包数据."""

    work_info: dict[str, Any]
    sha256: str
    notary_records: list[dict[str, Any]]
    c2pa_manifests: list[dict[str, Any]]
    ai_sessions: list[dict[str, Any]]
    work_versions: list[dict[str, Any]]
    infringement_evidence: list[dict[str, Any]]


# ==============================================================================
# Complaint submission schemas
# ==============================================================================


class ComplaintSubmitRequest(BaseModel):
    """一键提交投诉请求."""

    template_id: Optional[str] = None
    action_type: Optional[str] = None


class ComplaintSubmitResponse(BaseModel):
    """投诉提交响应."""

    action_id: str
    complaint_text: str
    material_path: Optional[str] = None
    prefilled_url: Optional[str] = None
    status: str
