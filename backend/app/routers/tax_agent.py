"""税务代理 API 路由."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.tax_settlement import (
    TaxAgentCreate,
    TaxAgentUpdate,
    TaxAgentSchema,
    TaxReportSchema,
)
from app.models.tax_settlement import TaxAgent as TaxAgentModel, TaxReport as TaxReportModel

router = APIRouter()


def _agent_to_dict(a: TaxAgentModel) -> dict:
    return {
        "id": a.id,
        "participant_id": a.participant_id,
        "name": a.name,
        "license_no": a.license_no,
        "service_areas": a.service_areas or [],
        "fee_rate": float(a.fee_rate),
        "avalara_account_id": a.avalara_account_id,
        "status": a.status,
        "rating": float(a.rating) if a.rating else None,
        "review_count": a.review_count,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "approved_at": a.approved_at.isoformat() if a.approved_at else None,
    }


def _report_to_dict(r: TaxReportModel) -> dict:
    return {
        "id": r.id,
        "participant_id": r.participant_id,
        "agent_id": r.agent_id,
        "report_period": r.report_period,
        "total_income": float(r.total_income),
        "total_tax_withheld": float(r.total_tax_withheld),
        "total_tax_owed": float(r.total_tax_owed),
        "currency": r.currency,
        "generated_by": r.generated_by,
        "status": r.status,
        "file_path": r.file_path,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "finalized_at": r.finalized_at.isoformat() if r.finalized_at else None,
    }


@router.post("/tax/agents", response_model=ApiResponse)
def create_agent(body: TaxAgentCreate, db: Session = Depends(get_db)):
    agent = TaxAgentModel(
        participant_id=body.participant_id,
        name=body.name,
        license_no=body.license_no,
        service_areas=body.service_areas,
        fee_rate=body.fee_rate,
        avalara_account_id=body.avalara_account_id,
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return ApiResponse(data=_agent_to_dict(agent), message="税务代理已创建")


@router.get("/tax/agents", response_model=ApiResponse)
def list_agents(status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(TaxAgentModel)
    if status:
        q = q.filter(TaxAgentModel.status == status)
    agents = q.all()
    return ApiResponse(data=[_agent_to_dict(a) for a in agents])


@router.get("/tax/agents/{agent_id}", response_model=ApiResponse)
def get_agent(agent_id: str, db: Session = Depends(get_db)):
    agent = db.query(TaxAgentModel).filter(TaxAgentModel.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="税务代理不存在")
    return ApiResponse(data=_agent_to_dict(agent))


@router.patch("/tax/agents/{agent_id}", response_model=ApiResponse)
def update_agent(agent_id: str, body: TaxAgentUpdate, db: Session = Depends(get_db)):
    agent = db.query(TaxAgentModel).filter(TaxAgentModel.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="税务代理不存在")
    for field in ["status", "rating", "fee_rate"]:
        val = getattr(body, field, None)
        if val is not None:
            setattr(agent, field, val)
    db.commit()
    db.refresh(agent)
    return ApiResponse(data=_agent_to_dict(agent))


@router.get("/tax/reports", response_model=ApiResponse)
def list_reports(participant_id: str, db: Session = Depends(get_db)):
    reports = (
        db.query(TaxReportModel)
        .filter(TaxReportModel.participant_id == participant_id)
        .order_by(TaxReportModel.created_at.desc())
        .all()
    )
    return ApiResponse(data=[_report_to_dict(r) for r in reports])


@router.post("/tax/reports", response_model=ApiResponse)
def create_report(body: dict, db: Session = Depends(get_db)):
    from app.services.settlement_service import generate_tax_report
    report = generate_tax_report(
        db,
        participant_id=body["participant_id"],
        period=body["period"],
        currency=body.get("currency", "CNY"),
    )
    return ApiResponse(data=_report_to_dict(report), message="税务报告已生成")
