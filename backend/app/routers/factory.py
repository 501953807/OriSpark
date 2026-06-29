"""工厂/RFQ API 路由 — 对应: docs/modules-v3/06-business-management.md
Phase 3: 手工艺人询价单+样品+质检
端点: 9 (factory)"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.factory import RFQRequest, Sample, QualityReport
from app.schemas.common import ApiResponse
from app.deps import require_auth

router = APIRouter()


# ============================================================================
# 11.x 询价请求 CRUD
# ============================================================================


@router.get("/factory/rfq", response_model=ApiResponse[list])
def list_rfqs(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取询价请求列表."""
    q = db.query(RFQRequest)
    if user_id:
        q = q.filter(RFQRequest.user_id == user_id)
    if status:
        q = q.filter(RFQRequest.status == status)
    rfqs = q.order_by(RFQRequest.created_at.desc()).all()
    return ApiResponse(data=[
        {
            "id": r.id,
            "user_id": r.user_id,
            "title": r.title,
            "description": r.description,
            "materials": r.materials or [],
            "quantity": r.quantity,
            "deadline": r.deadline,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        }
        for r in rfqs
    ])


@router.post("/factory/rfq", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_rfq(payload: dict, db: Session = Depends(get_db)):
    """创建询价请求."""
    title = payload.get("title")
    if not title:
        raise HTTPException(status_code=400, detail="title is required")
    rfq = RFQRequest(
        user_id=payload.get("user_id", ""),
        title=title,
        description=payload.get("description"),
        materials=payload.get("materials"),
        quantity=payload.get("quantity"),
        deadline=payload.get("deadline"),
        status=payload.get("status", "draft"),
    )
    db.add(rfq)
    db.commit()
    db.refresh(rfq)
    return ApiResponse(data=_rfq_to_dict(rfq), message="询价请求创建成功")


@router.get("/factory/rfq/{rfq_id}", response_model=ApiResponse[dict])
def get_rfq(rfq_id: str, db: Session = Depends(get_db)):
    """获取单个询价请求详情."""
    rfq = db.query(RFQRequest).filter(RFQRequest.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="询价请求不存在")
    return ApiResponse(data=_rfq_to_dict(rfq))


@router.put("/factory/rfq/{rfq_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def update_rfq(rfq_id: str, payload: dict, db: Session = Depends(get_db)):
    """更新询价请求."""
    rfq = db.query(RFQRequest).filter(RFQRequest.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="询价请求不存在")
    for key in ("title", "description", "materials", "quantity", "deadline", "status"):
        if key in payload:
            setattr(rfq, key, payload[key])
    db.commit()
    db.refresh(rfq)
    return ApiResponse(data=_rfq_to_dict(rfq), message="询价请求更新成功")


@router.delete("/factory/rfq/{rfq_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def delete_rfq(rfq_id: str, db: Session = Depends(get_db)):
    """删除询价请求."""
    rfq = db.query(RFQRequest).filter(RFQRequest.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="询价请求不存在")
    db.delete(rfq)
    db.commit()
    return ApiResponse(data={"success": True}, message="询价请求已删除")


# ============================================================================
# 11.x 样品管理
# ============================================================================


@router.get("/factory/rfq/{rfq_id}/samples", response_model=ApiResponse[list])
def list_samples(rfq_id: str, status: Optional[str] = None, db: Session = Depends(get_db)):
    """获取询价下的样品列表."""
    q = db.query(Sample).filter(Sample.rfq_id == rfq_id)
    if status:
        q = q.filter(Sample.status == status)
    samples = q.all()
    return ApiResponse(data=[
        {
            "id": s.id,
            "rfq_id": s.rfq_id,
            "status": s.status,
            "shipped_at": s.shipped_at.isoformat() if s.shipped_at else None,
            "received_at": s.received_at.isoformat() if s.received_at else None,
            "notes": s.notes,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in samples
    ])


@router.post("/factory/rfq/{rfq_id}/samples", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_sample(rfq_id: str, payload: dict, db: Session = Depends(get_db)):
    """创建样品记录."""
    rfq = db.query(RFQRequest).filter(RFQRequest.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="询价请求不存在")
    sample = Sample(
        rfq_id=rfq_id,
        status=payload.get("status", "requested"),
        notes=payload.get("notes"),
    )
    db.add(sample)
    db.commit()
    db.refresh(sample)
    return ApiResponse(data=_sample_to_dict(sample), message="样品记录创建成功")


# ============================================================================
# 11.x 质检报告
# ============================================================================


@router.get("/factory/sample/{sample_id}/quality-report", response_model=ApiResponse[dict])
def get_quality_report(sample_id: str, db: Session = Depends(get_db)):
    """获取样品质检报告."""
    report = db.query(QualityReport).filter(QualityReport.sample_id == sample_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="质检报告不存在")
    return ApiResponse(data=_qr_to_dict(report))


@router.post("/factory/sample/{sample_id}/quality-report", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_quality_report(sample_id: str, payload: dict, db: Session = Depends(get_db)):
    """创建质检报告."""
    sample = db.query(Sample).filter(Sample.id == sample_id).first()
    if not sample:
        raise HTTPException(status_code=404, detail="样品不存在")
    qr = QualityReport(
        sample_id=sample_id,
        aql_level=payload.get("aql_level", "S-3"),
        defects=payload.get("defects"),
        passed=payload.get("passed", 0),
        total_inspected=payload.get("total_inspected", 0),
        inspector_notes=payload.get("inspector_notes"),
    )
    db.add(qr)
    db.commit()
    db.refresh(qr)
    return ApiResponse(data=_qr_to_dict(qr), message="质检报告创建成功")


def _rfq_to_dict(r: RFQRequest) -> dict:
    return {
        "id": r.id,
        "user_id": r.user_id,
        "title": r.title,
        "description": r.description,
        "materials": r.materials or [],
        "quantity": r.quantity,
        "deadline": r.deadline,
        "status": r.status,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


def _sample_to_dict(s: Sample) -> dict:
    return {
        "id": s.id,
        "rfq_id": s.rfq_id,
        "status": s.status,
        "shipped_at": s.shipped_at.isoformat() if s.shipped_at else None,
        "received_at": s.received_at.isoformat() if s.received_at else None,
        "notes": s.notes,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


def _qr_to_dict(qr: QualityReport) -> dict:
    return {
        "id": qr.id,
        "sample_id": qr.sample_id,
        "aql_level": qr.aql_level,
        "defects": qr.defects or [],
        "passed": qr.passed,
        "total_inspected": qr.total_inspected,
        "inspector_notes": qr.inspector_notes,
        "created_at": qr.created_at.isoformat() if qr.created_at else None,
    }
