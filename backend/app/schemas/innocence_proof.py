"""无罪证明 Pydantic 模型。"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class InnocenceProofCreate(BaseModel):
    """创建无罪证明请求体."""
    work_id: str = Field(..., min_length=1, max_length=32, description="作品ID")
    evidence_document_url: Optional[str] = Field(None, max_length=2000, description="证据文档存储URL")
    summary_text: Optional[str] = Field(None, description="证明摘要内容")
    status: Optional[str] = Field("pending", enum=("pending", "completed", "reviewed"), description="证明状态：待处理/已完成/已审核，默认为 pending")


class InnocenceProofResponse(BaseModel):
    """无罪证明响应模型."""
    id: str
    work_id: str
    evidence_document_url: Optional[str] = None
    summary_text: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class InnocenceProofListResponse(BaseModel):
    """无罪证明列表响应."""
    items: list[InnocenceProofResponse]
    total: int
    page: int
    page_size: int