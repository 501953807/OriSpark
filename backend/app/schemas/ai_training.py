from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.ai_training_license import CCProtocol


class AILicenseUpdate(BaseModel):
    work_id: str
    enabled: bool
    cc_protocol: Optional[CCProtocol] = None
    price_per_use_cents: Optional[int] = None


class AILicenseResponse(BaseModel):
    id: str
    work_id: str
    enabled: bool
    cc_protocol: CCProtocol
    price_per_use_cents: int
    total_uses: int
    total_revenue_cents: int
    exclude_ai_training_clause: Optional[str]
