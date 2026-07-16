"""版权保险市场路由."""

from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import date
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.insurance import (
    InsuranceProductSchema,
    InsuranceEstimateRequest,
    InsuranceEstimateResponse,
    PolicyPurchaseRequest,
    InsurancePolicySchema,
    ClaimCreateRequest,
    InsuranceClaimSchema,
    InsuranceProviderSchema,
)
from app.services.insurance_service import (
    estimate_premium,
    create_policy,
    get_user_policies,
    submit_claim,
    get_claim_status,
)

router = APIRouter(prefix="/api/insurance", tags=["copyright-insurance"])


@router.get("/products", response_model=list[InsuranceProductSchema])
def list_products(category: str | None = None, tier: str | None = None, db: Session = Depends(get_db)):
    """获取保险产品列表."""
    query = db.query(InsuranceProduct).filter(InsuranceProduct.is_active == True)
    if category:
        query = query.filter(InsuranceProduct.category == category)
    if tier:
        query = query.filter(InsuranceProduct.tier == tier)
    return query.all()


@router.get("/products/{product_id}", response_model=InsuranceProductSchema)
def get_product(product_id: str, db: Session = Depends(get_db)):
    """获取单个产品详情."""
    product = db.query(InsuranceProduct).filter(
        InsuranceProduct.id == product_id,
        InsuranceProduct.is_active == True,
    ).first()
    if not product:
        raise HTTPException(404, "Product not found")
    return product


@router.post("/estimate", response_model=InsuranceEstimateResponse)
def post_estimate(req: InsuranceEstimateRequest, db: Session = Depends(get_db)):
    """保费估算接口."""
    result = estimate_premium(
        db,
        creator_type=req.creator_type,
        work_count=req.work_count,
        risk_level=req.risk_level,
        categories=req.categories,
    )
    return InsuranceEstimateResponse(**result)


@router.post("/policies/{product_id}/purchase", response_model=dict)
def purchase_policy(product_id: str, req: PolicyPurchaseRequest, db: Session = Depends(get_db)):
    """一键投保."""
    from datetime import date
    result = create_policy(db, "current_user", product_id, req.start_date, req.duration_months)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result


@router.get("/policies", response_model=list[InsurancePolicySchema])
def list_policies(db: Session = Depends(get_db)):
    """获取当前用户所有保单."""
    return get_user_policies(db, "current_user")


@router.post("/claims", response_model=dict)
def post_claim(req: ClaimCreateRequest, db: Session = Depends(get_db)):
    """提交理赔申请."""
    result = submit_claim(
        db, req.policy_id, req.claim_type,
        req.description, req.evidence_urls, req.claimed_amount_yuan,
    )
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result


@router.get("/claims/{claim_id}", response_model=dict)
def get_claim(claim_id: str, db: Session = Depends(get_db)):
    """查询理赔状态."""
    result = get_claim_status(db, claim_id)
    if not result:
        raise HTTPException(404, "Claim not found")
    return result


@router.get("/providers", response_model=list[InsuranceProviderSchema])
def list_providers(db: Session = Depends(get_db)):
    """获取合作保险公司列表."""
    return db.query(InsuranceProvider).filter(
        InsuranceProvider.is_active == True
    ).all()
