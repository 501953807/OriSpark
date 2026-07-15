"""Pydantic 请求/响应模型."""

from app.schemas.work import (
    WorkCreate, WorkUpdate, WorkResponse, WorkListResponse,
    WorkTagCreate, WorkTagResponse, ProjectCreate, ProjectResponse,
)
from app.schemas.notary import (
    NotaryRecordCreate, NotaryRecordResponse, NotaryRecordListResponse,
    CertificateResponse, NotaryPlatformInfo,
)
from app.schemas.monitor import (
    MonitorTaskCreate, MonitorTaskResponse, MonitorResultResponse,
    ScanRequest, ResultUpdateRequest, EvidencePackageCreate,
)
from app.schemas.ipr import (
    IPRegistrationCreate, IPRegistrationUpdate, IPRegistrationResponse,
)
from app.schemas.supply import (
    SupplyPartnerCreate as PartnerCreate,
    SupplyOrderCreate as OrderCreate,
)
from app.schemas.publish import (
    ProductCreate, ProductResponse, PublishRequest, RevenueCreate, RevenueResponse,
)
from app.schemas.common import (
    PaginatedResponse, ApiResponse, DashboardStats,
    ErrorResponse, SuccessResponse, PaginationParams,
)

__all__ = [
    "WorkCreate", "WorkUpdate", "WorkResponse", "WorkListResponse",
    "WorkTagCreate", "WorkTagResponse", "ProjectCreate", "ProjectResponse",
    "NotaryRecordCreate", "NotaryRecordResponse", "NotaryRecordListResponse",
    "CertificateResponse", "NotaryPlatformInfo",
    "MonitorTaskCreate", "MonitorTaskResponse", "MonitorResultResponse",
    "ScanRequest", "ResultUpdateRequest", "EvidencePackageCreate",
    "IPRegistrationCreate", "IPRegistrationUpdate", "IPRegistrationResponse",
    "PartnerCreate", "OrderCreate",
    "ProductCreate", "ProductResponse", "PublishRequest", "RevenueCreate", "RevenueResponse",
    "PaginatedResponse", "ApiResponse", "DashboardStats",
    "ErrorResponse", "SuccessResponse", "PaginationParams",
]
