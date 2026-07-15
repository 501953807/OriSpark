from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class CertificationRequest(BaseModel):
    work_id: str
    batch: Optional[list[str]] = None  # 批量存证的work_ids列表


class CertificationResponse(BaseModel):
    id: str
    work_id: str
    sha256_hash: str
    blockchain_tx_id: Optional[str]
    timestamp: datetime
    is_court_admissible: bool
    certificate_url: Optional[str]
    cost_saved_yuan: int


class BatchCertificationResponse(BaseModel):
    total: int
    success: int
    failed: int
    results: list[CertificationResponse]
    total_saved_yuan: int
