"""版权保险市场路由."""

from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import date
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user_id
from app.models.insurance import InsuranceProduct
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

router = APIRouter(prefix="/insurance", tags=["copyright-insurance"])


@router.get("/products", response_model=list[InsuranceProductSchema])
def list_products(category: str | None = None, tier: str | None = None, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """获取保险产品列表."""
    query = db.query(InsuranceProduct).filter(InsuranceProduct.is_active == True)
    if category:
        query = query.filter(InsuranceProduct.category == category)
    if tier:
        query = query.filter(InsuranceProduct.tier == tier)
    AuditLog.log(db, "list_insurance_products", f"Listed products by {actor_id}", actor_id)
    return query.all()


@router.get("/products/{product_id}", response_model=InsuranceProductSchema)
def get_product(product_id: str, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """获取单个产品详情."""
    product = db.query(InsuranceProduct).filter(
        InsuranceProduct.id == product_id,
        InsuranceProduct.is_active == True,
    ).first()
    if not product:
        raise HTTPException(404, "Product not found")
    AuditLog.log(db, "view保险产品", f"Viewed product {product_id} by {actor_id}", actor_id)
    return product


@router.post("/estimate", response_model=InsuranceEstimateResponse)
def post_estimate(req: InsuranceEstimateRequest, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """保费估算接口."""
    result = estimate_premium(
        db,
        creator_type=req.creator_type,
        work_count=req.work_count,
        risk_level=req.risk_level,
        categories=req.categories,
    )
    AuditLog.log(db, "estimate_premium", f"Estimated premium for {actor_id}", actor_id)
    return InsuranceEstimateResponse(**result)


@router.post("/policies/{product_id}/purchase", response_model=dict)
def purchase_policy(product_id: str, req: PolicyPurchaseRequest, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """一键投保."""
    result = create_policy(db, actor_id, product_id, req.start_date, req.duration_months)
    if "error" in result:
        raise HTTPException(400, result["error"])
    AuditLog.log(db, "purchase_policy", f"Purchased policy {product_id} by {actor_id}", actor_id)
    return result


@router.get("/policies", response_model=list[InsurancePolicySchema])
def list_policies(actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """获取当前用户所有保单."""
    AuditLog.log(db, "list_user_policies", f"Listed policies for user {actor_id}", actor_id)
    return get_user_policies(db, actor_id)


@router.post("/claims", response_model=dict)
def post_claim(req: ClaimCreateRequest, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """提交理赔申请."""
    result = submit_claim(
        db, req.policy_id, req.claim_type,
        req.description, req.evidence_urls, req.claimed_amount_yuan,
    )
    if "error" in result:
        raise HTTPException(400, result["error"])
    AuditLog.log(db, "submit_claim", f"Submitted claim by {actor_id}", actor_id)
    return result


@router.get("/claims/{claim_id}", response_model=dict)
def get_claim(claim_id: str, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """查询理赔状态."""
    result = get_claim_status(db, claim_id)
    if not result:
        raise HTTPException(404, "Claim not found")
    AuditLog.log(db, "check_claim_status", f"Checked claim {claim_id} by {actor_id}", actor_id)
    return result


@router.get("/providers", response_model=list[InsuranceProviderSchema])
def list_providers(actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """获取合作保险公司列表."""
    AuditLog.log(db, "list_insurance_providers", f"Listed providers by {actor_id}", actor_id)
    return db.query(InsuranceProvider).filter(
        InsuranceProvider.is_active == True
    ).all()
