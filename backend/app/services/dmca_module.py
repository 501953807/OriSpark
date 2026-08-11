"""DMCA 维权模块 — 证据包生成 + 模板填充."""

import logging
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.monitor import EvidencePackage
from app.schemas.monitor import EvidencePackageCreate
from app.schemas.common import ApiResponse
from app.services.dmca_template import fill_dmca_template_from_work

logger = logging.getLogger(__name__)


class DmcaModule:
    """DMCA 维权模块."""

    def __init__(self, db: Session):
        self.db = db

    def get_template(self, work_id: str) -> ApiResponse:
        """获取 DMCA 模板."""
        return ApiResponse(data={"template": "DMCA takedown notice template"})

    def generate_evidence_package(self, result_id: str, data: EvidencePackageCreate) -> ApiResponse:
        """生成维权证据包."""
        result = self.db.query(EvidencePackage).filter(
            EvidencePackage.id == result_id
        ).first()
        if not result:
            raise HTTPException(status_code=404, detail="结果不存在")
        evidence = EvidencePackage(
            work_id=data.work_id,
            related_result_ids=data.result_ids,
            package_path=f"data/certificates/evidence_{result_id}.zip",
            package_type=data.package_type,
            notes=data.notes,
        )
        self.db.add(evidence)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(
            message="证据包生成任务已创建",
            data={"package_id": evidence.id},
        )

    def list_evidence_packages(self, work_id: Optional[str] = None, package_type: Optional[str] = None) -> ApiResponse:
        """获取证据包列表."""
        q = self.db.query(EvidencePackage)
        if work_id:
            q = q.filter(EvidencePackage.work_id == work_id)
        if package_type:
            q = q.filter(EvidencePackage.package_type == package_type)
        packages = q.order_by(EvidencePackage.created_at.desc()).all()
        return ApiResponse(data=[
            {
                "id": p.id,
                "work_id": p.work_id,
                "related_result_ids": p.related_result_ids,
                "package_path": p.package_path,
                "package_type": p.package_type,
                "notes": p.notes,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in packages
        ])

    def get_evidence_package(self, package_id: str) -> ApiResponse:
        """获取单个证据包详情."""
        pkg = self.db.query(EvidencePackage).filter(EvidencePackage.id == package_id).first()
        if not pkg:
            raise HTTPException(status_code=404, detail="证据包不存在")
        return ApiResponse(data={
            "id": pkg.id,
            "work_id": pkg.work_id,
            "related_result_ids": pkg.related_result_ids,
            "package_path": pkg.package_path,
            "package_type": pkg.package_type,
            "notes": pkg.notes,
            "created_at": pkg.created_at.isoformat() if pkg.created_at else None,
        })
