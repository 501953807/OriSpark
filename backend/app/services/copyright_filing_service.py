"""跨国版权 API 申报网关服务层.

实现 USCO / EUIPO / JPO / DCC 多法区在线申报网关.
采用 Gateway ABC 模式, 支持模拟模式 (默认) 和真实 API 双模式.
模拟模式用于开发和演示, 真实 API 需配置对应的 API Key.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.copyright_guide import GuideRegistration

logger = logging.getLogger(__name__)


# ============================================================================
# Domain types
# ============================================================================


@dataclass
class FilingResult:
    """申报结果."""
    jurisdiction: str          # "USCO" | "EUIPO" | "JPO" | "DCC"
    application_number: str    # 官方申请号
    status: str                # "pending" | "submitted" | "rejected" | "error"
    reference_id: str          # 内部引用 ID
    message: str               # 状态说明
    submitted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error: Optional[str] = None


@dataclass
class JurisdictionInfo:
    """各法区基本信息."""
    code: str
    name_zh: str
    name_en: str
    fee_usd: float
    estimated_days: int
    requires_online_filing: bool


# 预置各法区信息
JURISDICTIONS = {
    "USCO": JurisdictionInfo(
        code="USCO",
        name_zh="美国版权局",
        name_en="U.S. Copyright Office",
        fee_usd=65.0,
        estimated_days=30,
        requires_online_filing=True,
    ),
    "EUIPO": JurisdictionInfo(
        code="EUIPO",
        name_zh="欧盟知识产权局",
        name_en="European Union Intellectual Property Office",
        fee_usd=150.0,
        estimated_days=20,
        requires_online_filing=True,
    ),
    "JPO": JurisdictionInfo(
        code="JPO",
        name_zh="日本特许厅",
        name_en="Japan Patent Office",
        fee_usd=80.0,
        estimated_days=25,
        requires_online_filing=False,
    ),
    "DCC": JurisdictionInfo(
        code="DCC",
        name_zh="数字版权登记中心",
        name_en="Digital Copyright Center",
        fee_usd=50.0,
        estimated_days=7,
        requires_online_filing=True,
    ),
    "WIPO": JurisdictionInfo(
        code="WIPO",
        name_zh="世界知识产权组织",
        name_en="World Intellectual Property Organization",
        fee_usd=200.0,
        estimated_days=60,
        requires_online_filing=True,
    ),
}


# ============================================================================
# Gateway ABC
# ============================================================================


_REGISTRY: dict[str, type["CopyrightFilingGateway"]] = {}


def _gateway_registry(code: str):
    """装饰器, 自动注册法区网关."""
    def wrap(cls):
        cls.jurisdiction_code = code
        _REGISTRY[code] = cls
        return cls
    return wrap


class CopyrightFilingGateway(ABC):
    """跨国版权申报网关基类."""

    jurisdiction_code: str = ""

    def __init__(self, api_key: Optional[str] = None, simulate: bool = True):
        self.api_key = api_key
        self.simulate = simulate

    @abstractmethod
    async def submit_filing(
        self,
        applicant_name: str,
        applicant_email: str,
        work_title: str,
        work_type: str,
        description: str,
        file_url: Optional[str] = None,
    ) -> FilingResult:
        """向法区提交版权申报."""
        ...

    @abstractmethod
    async def get_filing_status(self, application_number: str) -> FilingResult:
        """查询申报状态."""
        ...

    @abstractmethod
    async def get_filing_fee(self, work_type: str) -> float:
        """获取申报费用."""
        ...

    def validate_input(
        self,
        applicant_name: str,
        work_title: str,
        work_type: str,
    ) -> list[str]:
        """校验输入参数, 返回错误列表."""
        errors: list[str] = []
        if not applicant_name or len(applicant_name.strip()) < 2:
            errors.append("申请人姓名不能为空且不少于2个字符")
        if not work_title or len(work_title.strip()) < 1:
            errors.append("作品标题不能为空")
        valid_types = {"illustration", "photo", "music", "writing", "video", "software", "other"}
        if work_type not in valid_types:
            errors.append(f"作品类型不合法, 可选: {', '.join(sorted(valid_types))}")
        return errors


# -- USCO (美国版权局) -------------------------------------------------------


@_gateway_registry("USCO")
class USCOGateway(CopyrightFilingGateway):
    """美国版权局 (USCO) 在线申报网关.

    真实 API: https://copyright.gov/eco/ (Electronic Copyright Office)
    费用: $65/件 (standard), $125/件 (expedited)
    """

    API_BASE = "https://eco.copyright.gov/eapp/handle/submit"

    async def submit_filing(
        self,
        applicant_name: str,
        applicant_email: str,
        work_title: str,
        work_type: str,
        description: str,
        file_url: Optional[str] = None,
    ) -> FilingResult:
        errors = self.validate_input(applicant_name, work_title, work_type)
        if errors:
            return FilingResult(
                jurisdiction="USCO",
                application_number="",
                status="rejected",
                reference_id="",
                message="; ".join(errors),
                error="; ".join(errors),
            )

        if self.simulate:
            app_num = f"TXu-{datetime.now().strftime('%Y')}-{int(time.time()) % 100000:05d}"
            return FilingResult(
                jurisdiction="USCO",
                application_number=app_num,
                status="submitted",
                reference_id=f"USCO-{app_num}",
                message="模拟模式: USCO 申报已提交 (API Base: https://eco.copyright.gov/eapp/handle/submit)",
            )

        # 真实 API 调用 (需配置 API Key 后启用)
        try:
            import httpx
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    self.API_BASE,
                    json={
                        "applicant_name": applicant_name,
                        "applicant_email": applicant_email,
                        "work_title": work_title,
                        "work_type": work_type,
                        "description": description,
                        "file_url": file_url,
                    },
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                resp.raise_for_status()
                data = resp.json()
                return FilingResult(
                    jurisdiction="USCO",
                    application_number=data.get("application_number", ""),
                    status=data.get("status", "submitted"),
                    reference_id=data.get("reference_id", ""),
                    message=data.get("message", "USCO 申报成功"),
                )
        except Exception as exc:
            logger.error("USCO 申报失败: %s", exc)
            return FilingResult(
                jurisdiction="USCO",
                application_number="",
                status="error",
                reference_id="",
                message=f"USCO 申报失败: {exc}",
                error=str(exc),
            )

    async def get_filing_status(self, application_number: str) -> FilingResult:
        if self.simulate:
            return FilingResult(
                jurisdiction="USCO",
                application_number=application_number,
                status="pending",
                reference_id=f"USCO-{application_number}",
                message="模拟模式: USCO 申报状态查询",
            )
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    f"{self.API_BASE}/status/{application_number}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                resp.raise_for_status()
                data = resp.json()
                return FilingResult(
                    jurisdiction="USCO",
                    application_number=application_number,
                    status=data.get("status", "pending"),
                    reference_id=data.get("reference_id", ""),
                    message=data.get("message", "查询成功"),
                )
        except Exception as exc:
            return FilingResult(
                jurisdiction="USCO",
                application_number=application_number,
                status="error",
                reference_id="",
                message=f"查询失败: {exc}",
                error=str(exc),
            )

    async def get_filing_fee(self, work_type: str) -> float:
        return 65.0  # USCO standard fee


# -- EUIPO (欧盟知识产权局) --------------------------------------------------


@_gateway_registry("EUIPO")
class EUIPOGateway(CopyrightFilingGateway):
    """欧盟知识产权局 (EUIPO) 在线申报网关.

    真实 API: https://www.eposeuroperianunion.eu/ (eSearch plus)
    费用: €150/件 (one class)
    """

    API_BASE = "https://euipo.europa.eu/eSearchPlus/"

    async def submit_filing(
        self,
        applicant_name: str,
        applicant_email: str,
        work_title: str,
        work_type: str,
        description: str,
        file_url: Optional[str] = None,
    ) -> FilingResult:
        errors = self.validate_input(applicant_name, work_title, work_type)
        if errors:
            return FilingResult(
                jurisdiction="EUIPO",
                application_number="",
                status="rejected",
                reference_id="",
                message="; ".join(errors),
                error="; ".join(errors),
            )

        if self.simulate:
            app_num = f"EU-{work_type[:3].upper()}-{int(time.time()) % 100000:05d}"
            return FilingResult(
                jurisdiction="EUIPO",
                application_number=app_num,
                status="submitted",
                reference_id=f"EUIPO-{app_num}",
                message="模拟模式: EUIPO 申报已提交 (API Base: https://euipo.europa.eu/eSearchPlus/)",
            )

        try:
            import httpx
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    self.API_BASE + "submit",
                    json={
                        "applicant_name": applicant_name,
                        "applicant_email": applicant_email,
                        "work_title": work_title,
                        "work_type": work_type,
                        "description": description,
                    },
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                resp.raise_for_status()
                data = resp.json()
                return FilingResult(
                    jurisdiction="EUIPO",
                    application_number=data.get("application_number", ""),
                    status=data.get("status", "submitted"),
                    reference_id=data.get("reference_id", ""),
                    message=data.get("message", "EUIPO 申报成功"),
                )
        except Exception as exc:
            logger.error("EUIPO 申报失败: %s", exc)
            return FilingResult(
                jurisdiction="EUIPO",
                application_number="",
                status="error",
                reference_id="",
                message=f"EUIPO 申报失败: {exc}",
                error=str(exc),
            )

    async def get_filing_status(self, application_number: str) -> FilingResult:
        if self.simulate:
            return FilingResult(
                jurisdiction="EUIPO",
                application_number=application_number,
                status="pending",
                reference_id=f"EUIPO-{application_number}",
                message="模拟模式: EUIPO 申报状态查询",
            )
        return FilingResult(
            jurisdiction="EUIPO",
            application_number=application_number,
            status="error",
            reference_id="",
            message="真实 API 模式未配置",
            error="EUIPO_API_KEY not configured",
        )

    async def get_filing_fee(self, work_type: str) -> float:
        return 150.0  # EUIPO one-class fee in EUR


# -- JPO (日本特许厅) --------------------------------------------------------


@_gateway_registry("JPO")
class JPOGateway(CopyrightFilingGateway):
    """日本特许厅 (JPO) 在线申报网关.

    真实 API: https://www.jpo.go.jp/ (在线申请系统)
    费用: ¥10,000/件 (约 $80)
    """

    API_BASE = "https://www.jpo.go.jp/e-chiiki/"

    async def submit_filing(
        self,
        applicant_name: str,
        applicant_email: str,
        work_title: str,
        work_type: str,
        description: str,
        file_url: Optional[str] = None,
    ) -> FilingResult:
        errors = self.validate_input(applicant_name, work_title, work_type)
        if errors:
            return FilingResult(
                jurisdiction="JPO",
                application_number="",
                status="rejected",
                reference_id="",
                message="; ".join(errors),
                error="; ".join(errors),
            )

        if self.simulate:
            app_num = f"JP-{int(time.time()) % 100000:06d}"
            return FilingResult(
                jurisdiction="JPO",
                application_number=app_num,
                status="submitted",
                reference_id=f"JPO-{app_num}",
                message="模拟模式: JPO 申报已提交 (API Base: https://www.jpo.go.jp/e-chiiki/)",
            )

        return FilingResult(
            jurisdiction="JPO",
            application_number="",
            status="error",
            reference_id="",
            message="JPO 暂未开放在线 API, 请通过官网 https://www.jpo.go.jp/ 提交",
            error="JPO online API not available",
        )

    async def get_filing_status(self, application_number: str) -> FilingResult:
        if self.simulate:
            return FilingResult(
                jurisdiction="JPO",
                application_number=application_number,
                status="pending",
                reference_id=f"JPO-{application_number}",
                message="模拟模式: JPO 申报状态查询",
            )
        return FilingResult(
            jurisdiction="JPO",
            application_number=application_number,
            status="error",
            reference_id="",
            message="JPO 暂未开放在线 API",
            error="JPO online API not available",
        )

    async def get_filing_fee(self, work_type: str) -> float:
        return 80.0  # ~¥10,000


# -- DCC (数字版权登记中心) ---------------------------------------------------


@_gateway_registry("DCC")
class DCCGateway(CopyrightFilingGateway):
    """数字版权登记中心 (DCC) 在线申报网关.

    DCC 是平台内部的快速登记通道, 费用较低, 审核周期短.
    真实 API: 平台内部 API (需配置内部服务地址)
    """

    API_BASE = "/api/internal/dcc/filing"  # 内部服务地址

    async def submit_filing(
        self,
        applicant_name: str,
        applicant_email: str,
        work_title: str,
        work_type: str,
        description: str,
        file_url: Optional[str] = None,
    ) -> FilingResult:
        errors = self.validate_input(applicant_name, work_title, work_type)
        if errors:
            return FilingResult(
                jurisdiction="DCC",
                application_number="",
                status="rejected",
                reference_id="",
                message="; ".join(errors),
                error="; ".join(errors),
            )

        if self.simulate:
            app_num = f"DCC-{int(time.time()) % 1000000:06d}"
            return FilingResult(
                jurisdiction="DCC",
                application_number=app_num,
                status="submitted",
                reference_id=f"DCC-{app_num}",
                message="模拟模式: DCC 申报已提交 (内部服务)",
            )

        # 内部服务调用
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    self.API_BASE,
                    json={
                        "applicant_name": applicant_name,
                        "applicant_email": applicant_email,
                        "work_title": work_title,
                        "work_type": work_type,
                        "description": description,
                        "file_url": file_url,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return FilingResult(
                    jurisdiction="DCC",
                    application_number=data.get("application_number", ""),
                    status=data.get("status", "submitted"),
                    reference_id=data.get("reference_id", ""),
                    message=data.get("message", "DCC 申报成功"),
                )
        except Exception as exc:
            logger.error("DCC 申报失败: %s", exc)
            return FilingResult(
                jurisdiction="DCC",
                application_number="",
                status="error",
                reference_id="",
                message=f"DCC 申报失败: {exc}",
                error=str(exc),
            )

    async def get_filing_status(self, application_number: str) -> FilingResult:
        if self.simulate:
            return FilingResult(
                jurisdiction="DCC",
                application_number=application_number,
                status="approved",
                reference_id=f"DCC-{application_number}",
                message="模拟模式: DCC 申报已批准",
            )
        return FilingResult(
            jurisdiction="DCC",
            application_number=application_number,
            status="error",
            reference_id="",
            message="DCC 未配置",
            error="DCC_API_KEY not configured",
        )

    async def get_filing_fee(self, work_type: str) -> float:
        return 50.0  # DCC standard fee


# -- WIPO (世界知识产权组织) -------------------------------------------------


@_gateway_registry("WIPO")
class WIPOGateway(CopyrightFilingGateway):
    """世界知识产权组织 (WIPO) 在线申报网关.

    真实 API: https://www3.wipo.int/brouter/ (Brand/Trademark database)
    费用: $200/件
    """

    API_BASE = "https://www3.wipo.int/brouter/"

    async def submit_filing(
        self,
        applicant_name: str,
        applicant_email: str,
        work_title: str,
        work_type: str,
        description: str,
        file_url: Optional[str] = None,
    ) -> FilingResult:
        if self.simulate:
            app_num = f"WIPO-{int(time.time()) % 100000:05d}"
            return FilingResult(
                jurisdiction="WIPO",
                application_number=app_num,
                status="submitted",
                reference_id=f"WIPO-{app_num}",
                message="模拟模式: WIPO 申报已提交 (API Base: https://www3.wipo.int/brouter/)",
            )
        return FilingResult(
            jurisdiction="WIPO",
            application_number="",
            status="error",
            reference_id="",
            message="WIPO 暂未开放在线 API",
            error="WIPO online API not available",
        )

    async def get_filing_status(self, application_number: str) -> FilingResult:
        return FilingResult(
            jurisdiction="WIPO",
            application_number=application_number,
            status="error",
            reference_id="",
            message="WIPO 暂未开放在线 API",
            error="WIPO online API not available",
        )

    async def get_filing_fee(self, work_type: str) -> float:
        return 200.0  # WIPO standard fee


# ============================================================================
# Factory
# ============================================================================


def get_filing_gateway(jurisdiction: str, simulate: bool = True, api_key: Optional[str] = None) -> CopyrightFilingGateway:
    """获取指定法区的申报网关."""
    cls = _REGISTRY.get(jurisdiction.upper())
    if not cls:
        raise ValueError(
            f"不支持的法区: {jurisdiction}. "
            f"支持: {list(_REGISTRY.keys())}"
        )
    return cls(api_key=api_key, simulate=simulate)


def list_jurisdictions() -> list[dict[str, Any]]:
    """返回所有支持的法区信息."""
    return [
        {
            "code": info.code,
            "name_zh": info.name_zh,
            "name_en": info.name_en,
            "fee_usd": info.fee_usd,
            "estimated_days": info.estimated_days,
            "requires_online_filing": info.requires_online_filing,
        }
        for info in JURISDICTIONS.values()
    ]


# ============================================================================
# Service layer
# ============================================================================


class CopyrightFilingService:
    """跨国版权申报服务层."""

    def __init__(self, db: Session, simulate: bool = True, api_keys: Optional[dict[str, str]] = None):
        self._db = db
        self._simulate = simulate
        self._api_keys = api_keys or {}

    def submit_filing(
        self,
        user_id: str,
        jurisdiction: str,
        work_title: str,
        work_type: str,
        applicant_name: Optional[str] = None,
        applicant_email: Optional[str] = None,
        description: str = "",
        work_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """提交跨国版权申报."""
        errors = []
        if jurisdiction not in _REGISTRY:
            errors.append(f"不支持的法区: {jurisdiction}")
        if not work_title or len(work_title.strip()) < 1:
            errors.append("作品标题不能为空")
        if errors:
            return {"success": False, "errors": errors, "filing": None}

        gateway = get_filing_gateway(jurisdiction, simulate=self._simulate,
                                      api_key=self._api_keys.get(jurisdiction))

        import asyncio
        result = asyncio.run(gateway.submit_filing(
            applicant_name=applicant_name or user_id,
            applicant_email=applicant_email or f"{user_id}@oristudio.local",
            work_title=work_title,
            work_type=work_type,
            description=description,
        ))

        # 持久化申报记录
        from app.models.copyright_guide import GuideRegistration
        reg = GuideRegistration(
            user_id=user_id,
            work_id=work_id,
            title=work_title,
            work_type=work_type,
            registration_type=jurisdiction.lower(),
            status=result.status,
            application_number=result.application_number,
            fee_yuan=round(result.jurisdiction == "USCO" and 65 or result.jurisdiction == "EUIPO" and 150 or result.jurisdiction == "JPO" and 80 or 50, 2) * 7.14,
            notes=result.message,
        )
        self._db.add(reg)
        self._db.flush()
        self._db.refresh(reg)

        return {
            "success": result.status != "rejected",
            "filing": {
                "id": reg.id,
                "jurisdiction": jurisdiction,
                "application_number": result.application_number,
                "status": result.status,
                "message": result.message,
                "fee_usd": gateway.get_filing_fee(work_type),
                "submitted_at": result.submitted_at.isoformat(),
            },
        }

    def get_filing_status(
        self, user_id: str, reg_id: str,
    ) -> dict[str, Any]:
        """查询申报状态."""
        reg = self._db.query(GuideRegistration).filter(
            GuideRegistration.id == reg_id,
            GuideRegistration.user_id == user_id,
        ).first()
        if not reg:
            return {"success": False, "error": "申报记录不存在"}

        jurisdiction = reg.registration_type.upper()
        try:
            gateway = get_filing_gateway(jurisdiction, simulate=self._simulate,
                                          api_key=self._api_keys.get(jurisdiction))
            result = asyncio.run(gateway.get_filing_status(reg.application_number or ""))
        except Exception as exc:
            result = FilingResult(
                jurisdiction=jurisdiction,
                application_number=reg.application_number or "",
                status="error",
                reference_id="",
                message=f"查询失败: {exc}",
                error=str(exc),
            )

        return {
            "success": True,
            "filing": {
                "id": reg.id,
                "jurisdiction": jurisdiction,
                "application_number": result.application_number,
                "status": result.status,
                "message": result.message,
            },
        }

    def list_registrations(self, user_id: str) -> list[dict[str, Any]]:
        """获取用户的所有申报记录."""
        regs = self._db.query(GuideRegistration).filter(
            GuideRegistration.user_id == user_id,
        ).order_by(GuideRegistration.created_at.desc()).all()
        return [
            {
                "id": r.id,
                "title": r.title,
                "work_type": r.work_type,
                "jurisdiction": r.registration_type,
                "status": r.status,
                "application_number": r.application_number,
                "fee_yuan": r.fee_yuan,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in regs
        ]

    def get_summary(self, user_id: str) -> dict[str, Any]:
        """获取申报概览."""
        regs = self._db.query(GuideRegistration).filter(
            GuideRegistration.user_id == user_id,
        ).all()

        by_status = {}
        by_jurisdiction = {}
        total_fees = 0.0

        for r in regs:
            by_status[r.status] = by_status.get(r.status, 0) + 1
            by_jurisdiction[r.registration_type] = by_jurisdiction.get(r.registration_type, 0) + 1
            total_fees += r.fee_yuan or 0.0

        return {
            "total": len(regs),
            "by_status": by_status,
            "by_jurisdiction": by_jurisdiction,
            "total_fees_yuan": round(total_fees, 2),
        }
