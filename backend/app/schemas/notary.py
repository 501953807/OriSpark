"""存证确权 Pydantic 模型."""

from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class NotaryRecordCreate(BaseModel):
    work_id: str
    platform: str = Field(..., description="banquanjia/antchain/zhixinchain")
    notes: Optional[str] = None


class NotaryRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    work_id: str
    platform: str
    platform_url: Optional[str] = None
    transaction_hash: Optional[str] = None
    block_height: Optional[str] = None
    blockchain: Optional[str] = None
    certificate_id: Optional[str] = None
    status: str
    fee: float
    payment_status: str
    qr_code_url: Optional[str] = None
    evidence_hash: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    certificates: list["CertificateResponse"] = []


class NotaryRecordListResponse(BaseModel):
    items: list[NotaryRecordResponse]
    total: int
    page: int
    page_size: int


class CertificateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    notary_record_id: str
    cert_path: str
    qr_code: Optional[str] = None
    template_name: str
    issued_at: datetime
    expires_at: Optional[datetime] = None


class NotaryPlatformInfo(BaseModel):
    key: str
    name: str
    description: str
    fee_per_record: float
    legal_level: str
    website: str
    is_available: bool = True


class C2PAManifestResponse(BaseModel):
    work_id: str
    manifest: dict


class C2PAVerifyResponse(BaseModel):
    work_id: str
    status: str
    manifest: Optional[dict] = None
    is_valid: bool = False
    details: Optional[dict] = None


class DIDDocumentResponse(BaseModel):
    did: str
    did_document: dict
    public_key_pem: str


class VCGenerateResponse(BaseModel):
    work_id: str
    did: str
    did_document: dict
    credential: dict


class VCVerifyResponse(BaseModel):
    valid: bool
    checks: list[str] = []
    errors: list[str] = []


# --- P1.2.1: Merkle Tree Batch ---

class MerkleBatchRequest(BaseModel):
    work_ids: list[str] = Field(..., min_length=1, max_length=5000)
    platform: str = "antchain"


class MerkleProofResponse(BaseModel):
    work_id: str
    leaf_hash: str
    leaf_index: int
    root: str
    proof: list[dict]
    tree_depth: int
    total_leaves: int


class MerkleBatchResponse(BaseModel):
    root: str
    total_works: int
    tree_depth: int
    proofs: list[MerkleProofResponse]


# --- P1.2.6: Platform Fee Comparison ---

class PlatformFeeItem(BaseModel):
    key: str
    name: str
    fee_per_record: float
    legal_level: str
    estimated_total: float  # 基于作品数量计算
    pros: list[str] = []
    cons: list[str] = []


class NotaryCompareRequest(BaseModel):
    work_count: int = 1
    work_type: str = "image"  # image/text/audio/video/code
    budget: float = 50.0  # 预算 (元)
    legal_level: str = "commercial"  # commercial/judicial/national
    priority: str = "cost"  # cost/legal/speed


class NotaryCompareResponse(BaseModel):
    work_count: int
    work_type: str
    budget: float
    legal_level: str
    platforms: list[PlatformFeeItem]
    recommended: str  # 推荐平台 key
    reasons: list[str]


class NotaryRecommendResponse(BaseModel):
    work_id: str
    recommended_platform: str
    platform_name: str
    estimated_fee: float
    reasons: list[str]


# --- P1.2.7: Audit Trail ---

class AuditTrailItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    notary_record_id: str
    step: str
    status: str
    detail: Optional[str] = None
    created_at: datetime


class AuditTrailResponse(BaseModel):
    record_id: str
    status: str
    steps: list[AuditTrailItem]


# --- P0: Universal Verify Endpoint ---

class EvidenceChainItem(BaseModel):
    level: str
    type: str
    status: str  # "verified" / "pending" / "failed" / "not_started"
    details: Optional[dict] = None


class NotaryVerifyResponse(BaseModel):
    valid: bool
    record_id: str
    work_id: str
    work_title: str
    sha256: str
    platform: str
    confirmed_at: Optional[datetime] = None
    evidence_chain: list[EvidenceChainItem]
