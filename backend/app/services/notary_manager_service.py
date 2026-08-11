# -*- coding: utf-8 -*-
"""存证确权管理服务层 — 封装 notary router 中的所有 DB 操作.

重构后结构:
- NotaryManagerService: 公共接口 (CRUD + 编排)
- _AuditSubmodule: 审计追踪
- _VerifySubmodule: 验证
- _CertificateSubmodule: 证书管理
"""

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.work import Work
from app.models.notary import NotaryRecord, Certificate, C2PARecord, NotaryAuditTrail
from app.schemas.notary import (
    NotaryRecordCreate, NotaryRecordResponse, NotaryRecordListResponse,
    CertificateResponse,
    C2PAManifestResponse, C2PAVerifyResponse,
    MerkleBatchResponse, MerkleProofResponse,
    NotaryRecommendResponse,
    AuditTrailItem, AuditTrailResponse,
    NotaryVerifyResponse, EvidenceChainItem,
)
from app.schemas.common import ApiResponse
from app.services.certificate_service import generate_certificate_pdf
from app.services.hasher import compute_sha256
from app.services.local_notary import sign_work, save_signature

logger = logging.getLogger(__name__)


# ============================================================================
# 内部子模块 — 私有实现细节，不暴露给外部调用方
# ============================================================================

class _AuditSubmodule:
    """存证审计追踪子模块."""

    def __init__(self, db: Session):
        self.db = db

    def record_step(
        self,
        record_id: str,
        step: str,
        status: str = "success",
        detail: str = "",
    ) -> None:
        """记录存证审计追踪步骤."""
        trail = NotaryAuditTrail(
            notary_record_id=record_id,
            step=step,
            status=status,
            detail=detail,
        )
        self.db.add(trail)

    def get_trail(self, record_id: str) -> dict:
        """获取审计追踪."""
        record = self.db.query(NotaryRecord).filter(
            NotaryRecord.id == record_id
        ).first()
        if not record:
            raise HTTPException(status_code=404, detail="存证记录不存在")

        trails = (
            self.db.query(NotaryAuditTrail)
            .filter(NotaryAuditTrail.notary_record_id == record_id)
            .order_by(NotaryAuditTrail.created_at.asc())
            .all()
        )
        return {
            "record_id": record_id,
            "status": record.status,
            "steps": [AuditTrailItem.model_validate(t) for t in trails],
        }


class _VerifySubmodule:
    """存证验证子模块."""

    def __init__(self, db: Session):
        self.db = db

    def get_record(self, record_id: str):
        """返回 (record, work) 用于 verify 端点."""
        record = self.db.query(NotaryRecord).filter(
            NotaryRecord.id == record_id
        ).first()
        if not record:
            raise HTTPException(status_code=404, detail="存证记录不存在")
        work = self.db.query(Work).filter(Work.id == record.work_id).first()
        if not work:
            raise HTTPException(status_code=404, detail="关联作品不存在")
        return record, work

    def get_c2pa_record(self, work_id: str) -> Optional[C2PARecord]:
        return self.db.query(C2PARecord).filter(
            C2PARecord.work_id == work_id
        ).first()

    def get_timestamp_record(self, work_id: str):
        return self.db.query(NotaryRecord).filter(
            NotaryRecord.work_id == work_id,
            NotaryRecord.platform == "tts_timestamp",
        ).first()

    def get_trace_audit_work(self, work_id: str) -> Optional[Work]:
        return self.db.query(Work).filter(Work.id == work_id).first()

    def get_c2pa_count(self, work_id: str) -> int:
        return self.db.query(C2PARecord).filter(
            C2PARecord.work_id == work_id,
            C2PARecord.is_active == True,
        ).count()

    def get_notary_record_count(self, work_id: str) -> int:
        return self.db.query(NotaryRecord).filter(
            NotaryRecord.work_id == work_id,
        ).count()

    def get_triple_auth_work(self, work_id: str) -> Optional[Work]:
        return self.db.query(Work).filter(Work.id == work_id).first()


class _CertificateSubmodule:
    """证书管理子模块."""

    def __init__(self, db: Session):
        self.db = db

    def get_certificate(self, cert_id: str) -> CertificateResponse:
        cert = self.db.query(Certificate).filter(
            Certificate.id == cert_id
        ).first()
        if not cert:
            raise HTTPException(status_code=404, detail="证书不存在")
        return CertificateResponse.model_validate(cert)

    def get_certificate_record(self, cert_id: str):
        """返回证书 ORM 对象（供 download 端点检查路径用）."""
        cert = self.db.query(Certificate).filter(
            Certificate.id == cert_id
        ).first()
        if not cert:
            raise HTTPException(status_code=404, detail="证书不存在")
        return cert


# ============================================================================
# 公共接口 — NotaryManagerService
# ============================================================================

class NotaryManagerService:
    """存证确权业务逻辑服务，封装所有 DB 操作.

    内部通过子模块组织职责:
    - _AuditSubmodule: 审计追踪
    - _VerifySubmodule: 验证
    - _CertificateSubmodule: 证书管理
    """

    def __init__(self, db: Session):
        self.db = db
        self._audit = _AuditSubmodule(db)
        self._verify = _VerifySubmodule(db)
        self._certificate = _CertificateSubmodule(db)

    # ── 公共接口 (向后兼容，router 无需修改) ──────────────────────────

    def list_notary_records(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        platform: Optional[str] = None,
        work_id: Optional[str] = None,
    ) -> dict:
        query = self.db.query(NotaryRecord)

        if status:
            query = query.filter(NotaryRecord.status == status)
        if platform:
            query = query.filter(NotaryRecord.platform == platform)
        if work_id:
            query = query.filter(NotaryRecord.work_id == work_id)

        total = query.count()
        records = query.order_by(NotaryRecord.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        total_pages = (total + page_size - 1) // page_size

        return {
            "items": [NotaryRecordResponse.model_validate(r) for r in records],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def create_notary_record(
        self,
        data: NotaryRecordCreate,
        platform_info,
        work: Work,
    ) -> NotaryRecordResponse:
        qr_data = f"oristudio:notary:{data.work_id}:{data.platform}:{work.sha256[:16]}"

        record = NotaryRecord(
            work_id=data.work_id,
            platform=data.platform,
            status="pending",
            fee=platform_info.fee_per_record,
            payment_status="unpaid",
            qr_code_url=qr_data,
            evidence_hash=work.sha256,
            notes=data.notes,
            expires_at=datetime.now(timezone.utc) + timedelta(days=365 * 3),
        )

        try:
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
        except Exception as e:
            self.db.rollback()
            logger.exception("Failed to create notary record: %s", str(e))
            raise HTTPException(status_code=500, detail="创建存证记录失败")

        self._audit.record_step(record.id, "create", "success",
                               f"Created notary record for work {data.work_id} on {data.platform}")

        # ECDSA L1 本地签名
        try:
            sig_data = sign_work(work.sha256)
            sig_path = save_signature(record.id, sig_data)
            signature_ref = {"l1_signature": sig_path, "algorithm": sig_data["algorithm"]}
            record.notes = (record.notes or "") + f"\n[L1 Signature: {sig_path}]"
            try:
                self.db.commit()
                self.db.refresh(record)
            except Exception as e:
                self.db.rollback()
                logger.exception("Failed to update L1 signature: %s", str(e))
            self._audit.record_step(record.id, "pending", "success",
                                   f"ECDSA L1 signature completed, sig_path={sig_path}")
        except Exception as e:
            self._audit.record_step(record.id, "pending", "failure",
                                   f"ECDSA L1 signature failed: {str(e)}")

        return NotaryRecordResponse.model_validate(record)

    def get_notary_record(self, record_id: str) -> NotaryRecordResponse:
        record = self.db.query(NotaryRecord).filter(
            NotaryRecord.id == record_id
        ).first()
        if not record:
            raise HTTPException(status_code=404, detail="存证记录不存在")
        return NotaryRecordResponse.model_validate(record)

    def confirm_notary_record(
        self,
        record_id: str,
        transaction_hash: Optional[str],
        block_height: Optional[str],
        platform_url: Optional[str],
        work: Work,
    ) -> NotaryRecordResponse:
        record = self.db.query(NotaryRecord).filter(
            NotaryRecord.id == record_id
        ).first()
        if not record:
            raise HTTPException(status_code=404, detail="存证记录不存在")

        record.status = "confirmed"
        record.payment_status = "paid"
        record.confirmed_at = datetime.now(timezone.utc)
        if transaction_hash:
            record.transaction_hash = transaction_hash
        if block_height:
            record.block_height = block_height
        if platform_url:
            record.platform_url = platform_url

        cert_dir = Path("data/certificates")
        cert_dir.mkdir(parents=True, exist_ok=True)

        cert_path = generate_certificate_pdf(
            work=work,
            notary_record=record,
            output_dir=str(cert_dir),
        )

        certificate = Certificate(
            notary_record_id=record.id,
            cert_path=cert_path,
            qr_code=record.qr_code_url,
            template_name="default",
            expires_at=record.expires_at,
        )

        work.is_verified = True

        try:
            self.db.add(certificate)
            self.db.commit()
            self.db.refresh(record)
        except Exception as e:
            self.db.rollback()
            logger.exception("Failed to save certificate: %s", str(e))
            raise HTTPException(status_code=500, detail="保存证书失败")

        self._audit.record_step(record.id, "confirm", "success",
                               f"Notary confirmed with tx={transaction_hash or 'N/A'}, block={block_height or 'N/A'}")
        self._audit.record_step(record.id, "cert_generate", "success",
                               f"Certificate PDF generated at {cert_path}")
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.exception("Failed to commit audit trail: %s", str(e))

        return NotaryRecordResponse.model_validate(record)

    def batch_notarize(self, work_ids: list, platform: str, platform_info) -> int:
        records = []
        for work_id in work_ids:
            work = self.db.query(Work).filter(Work.id == work_id).first()
            if not work:
                continue

            if not work.sha256 and os.path.exists(work.file_path):
                work.sha256 = compute_sha256(work.file_path)

            record = NotaryRecord(
                work_id=work_id,
                platform=platform,
                status="pending",
                fee=platform_info.fee_per_record,
                payment_status="unpaid",
                evidence_hash=work.sha256,
                expires_at=datetime.now(timezone.utc) + timedelta(days=365 * 3),
            )
            records.append(record)

        try:
            self.db.add_all(records)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.exception("Failed to batch notarize records: %s", str(e))
            raise HTTPException(status_code=500, detail="批量存证失败")

        return len(records)

    # ── 委托到子模块 ──────────────────────────────────────────────────

    def get_certificate(self, cert_id: str) -> CertificateResponse:
        return self._certificate.get_certificate(cert_id)

    def get_certificate_record(self, cert_id: str):
        return self._certificate.get_certificate_record(cert_id)

    def generate_c2pa_for_work(
        self,
        work: Work,
        manifest,
    ) -> C2PAManifestResponse:
        c2pa_record = C2PARecord(
            work_id=work.id,
            manifest_json=manifest,
            is_active=True,
            validator_url=str(Path("data/certificates/signatures") / f"{work.id}_c2pa_key.json"),
        )
        self.db.add(c2pa_record)
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.exception("Failed to save C2PA record: %s", str(e))
            raise HTTPException(status_code=500, detail="保存 C2PA 记录失败")
        return C2PAManifestResponse(work_id=work.id, manifest=manifest)

    def collect_work_hashes(self, work_ids: list) -> tuple:
        """收集所有作品哈希，返回 (work_hashes, work_map)."""
        work_hashes = []
        work_map = {}
        for work_id in work_ids:
            work = self.db.query(Work).filter(Work.id == work_id).first()
            if not work:
                continue
            if not work.sha256 and os.path.exists(work.file_path):
                work.sha256 = compute_sha256(work.file_path)
                try:
                    self.db.commit()
                except Exception:
                    self.db.rollback()
                    logger.exception("Failed to update merkle work sha256")
            if work.sha256:
                work_hashes.append(work.sha256)
                work_map[work.sha256] = work
        return work_hashes, work_map

    def get_work_for_recommend(self, work_id: str) -> Optional[Work]:
        return self.db.query(Work).filter(Work.id == work_id).first()

    def get_notary_audit_trail(self, record_id: str) -> dict:
        return self._audit.get_trail(record_id)

    def create_polygon_record(self, work_id: str, anchor) -> NotaryRecord:
        record = NotaryRecord(
            work_id=work_id,
            platform="polygon",
            status="confirmed",
            transaction_hash=anchor.tx_hash,
            blockchain=anchor.chain,
            fee=0.0,
        )
        try:
            self.db.add(record)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.exception("Failed to anchor to polygon: %s", str(e))
            raise HTTPException(status_code=500, detail="Polygon 锚定失败")
        return record

    def get_or_create_timestamp_record(self, work_id: str, ts_path) -> None:
        record = self.db.query(NotaryRecord).filter(
            NotaryRecord.work_id == work_id, NotaryRecord.platform == "tts_timestamp"
        ).first()
        try:
            if record:
                record.notes = (record.notes or "") + f"\nTimestamp: {ts_path}"
            else:
                record = NotaryRecord(
                    work_id=work_id,
                    platform="tts_timestamp",
                    status="confirmed",
                    notes=f"RFC 3161 timestamp: {ts_path}",
                    fee=0.15,
                )
                self.db.add(record)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.exception("Failed to save timestamp: %s", str(e))
            raise HTTPException(status_code=500, detail="时间戳保存失败")

    def get_verify_record(self, record_id: str):
        return self._verify.get_record(record_id)

    def get_c2pa_record(self, work_id: str) -> Optional[C2PARecord]:
        return self._verify.get_c2pa_record(work_id)

    def get_timestamp_record(self, work_id: str):
        return self._verify.get_timestamp_record(work_id)

    def get_trace_audit_work(self, work_id: str) -> Optional[Work]:
        return self._verify.get_trace_audit_work(work_id)

    def get_c2pa_count(self, work_id: str) -> int:
        return self._verify.get_c2pa_count(work_id)

    def get_notary_record_count(self, work_id: str) -> int:
        return self._verify.get_notary_record_count(work_id)

    def get_triple_auth_work(self, work_id: str) -> Optional[Work]:
        return self._verify.get_triple_auth_work(work_id)

    def get_work(self, work_id: str) -> Optional[Work]:
        """查询作品，缺失 sha256 时自动计算并保存."""
        work = self.db.query(Work).filter(Work.id == work_id).first()
        if not work:
            return None
        if not work.sha256 and os.path.exists(work.file_path):
            work.sha256 = compute_sha256(work.file_path)
            try:
                self.db.commit()
            except Exception:
                self.db.rollback()
                logger.exception("Failed to update work sha256")
        return work

    def confirm_notary_record_with_all_ops(
        self,
        record_id: str,
        transaction_hash: Optional[str],
        block_height: Optional[str],
        platform_url: Optional[str],
    ) -> NotaryRecordResponse:
        """确认存证完成、生成证书、更新审计追踪（完整事务）."""
        record = self.db.query(NotaryRecord).filter(
            NotaryRecord.id == record_id
        ).first()
        if not record:
            raise HTTPException(status_code=404, detail="存证记录不存在")

        work = self.get_work(record.work_id)
        if not work:
            raise HTTPException(status_code=404, detail="关联作品不存在")

        record.status = "confirmed"
        record.payment_status = "paid"
        record.confirmed_at = datetime.now(timezone.utc)
        if transaction_hash:
            record.transaction_hash = transaction_hash
        if block_height:
            record.block_height = block_height
        if platform_url:
            record.platform_url = platform_url

        cert_dir = Path("data/certificates")
        cert_dir.mkdir(parents=True, exist_ok=True)

        cert_path = generate_certificate_pdf(
            work=work,
            notary_record=record,
            output_dir=str(cert_dir),
        )

        certificate = Certificate(
            notary_record_id=record.id,
            cert_path=cert_path,
            qr_code=record.qr_code_url,
            template_name="default",
            expires_at=record.expires_at,
        )

        work.is_verified = True

        try:
            self.db.add(certificate)
            self.db.commit()
            self.db.refresh(record)
        except Exception as e:
            self.db.rollback()
            logger.exception("Failed to save certificate: %s", str(e))
            raise HTTPException(status_code=500, detail="保存证书失败")

        self._audit.record_step(record.id, "confirm", "success",
                               f"Notary confirmed with tx={transaction_hash or 'N/A'}, block={block_height or 'N/A'}")
        self._audit.record_step(record.id, "cert_generate", "success",
                               f"Certificate PDF generated at {cert_path}")
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.exception("Failed to commit audit trail: %s", str(e))

        return NotaryRecordResponse.model_validate(record)
