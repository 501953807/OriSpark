"""合约风险评估 API 路由."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user_id
from app.schemas.contract_risk import (
    ContractReviewRequest,
    ContractReviewResponse,
    ContractClauseSchema,
    ContractRiskRuleSchema,
    TransactionCheckRequest,
    TransactionCheckResponse,
)
from app.services.contract_risk_service import review_contract, check_transaction
from app.utils.audit import AuditLog

router = APIRouter(prefix="/contract-risk", tags=["contract-risk"])


@router.post("/review", response_model=ContractReviewResponse)
def post_review(body: ContractReviewRequest, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """提交合同审查."""
    result = review_contract(
        db,
        user_id=actor_id,
        contract_text=body.contract_text,
        review_type=body.review_type,
        target_type=body.target_type,
        target_id=body.target_id,
    )
    # 🔑 Log review
    AuditLog.log(db, "review_contract", f"Reviewed contract by {actor_id}", actor_id)
    return ContractReviewResponse(
        id=result["id"],
        total_score=result["total_score"],
        risk_level=result["risk_level"],
        clauses_found=result["clauses_found"],
        risk_count=result["risk_count"],
        clauses=[ContractClauseSchema(**c) for c in result["clauses"]],
        suggestions=result["suggestions"],
        created_at=result["created_at"],
    )


@router.get("/history/{user_id}")
def get_history(user_id: str, limit: int = 20, page: int = 1, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """获取审查历史."""
    from app.models.contract_risk import ContractReview
    offset = (page - 1) * limit
    reviews = (
        db.query(ContractReview)
        .filter(ContractReview.user_id == user_id)
        .order_by(ContractReview.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    # 🔑 Log history access
    AuditLog.log(db, "view_review_history", f"Accessed history for user {user_id} by {actor_id}", actor_id)
    return {
        "reviews": [
            {
                "id": r.id,
                "review_type": r.review_type,
                "total_score": r.total_score,
                "risk_level": r.risk_level,
                "clauses_found": r.clauses_found,
                "created_at": r.created_at.isoformat(),
            }
            for r in reviews
        ],
        "total": len(reviews),
    }


@router.post("/transaction-check", response_model=TransactionCheckResponse)
def post_transaction_check(body: TransactionCheckRequest, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """交易合约预检."""
    result = check_transaction(
        db,
        user_id=actor_id,
        listing_id=body.listing_id,
        custom_terms=body.custom_terms,
    )
    # 🔑 Log transaction check
    AuditLog.log(db, "check_transaction", f"Checked transaction for user {actor_id}", actor_id)
    return TransactionCheckResponse(**result)


@router.get("/rules", response_model=list[ContractRiskRuleSchema])
def get_rules(category: str = "general", actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """获取风险规则列表."""
    from app.models.contract_risk import ContractRiskRule
    rules = (
        db.query(ContractRiskRule)
        .filter(ContractRiskRule.category == category, ContractRiskRule.is_active == True)
        .all()
    )
    # 🔑 Log rules access
    AuditLog.log(db, "list_risk_rules", f"Listed rules (category={category}) by {actor_id}", actor_id)
    return rules


@router.post("/rules", response_model=ContractRiskRuleSchema)
def create_rule(body: dict, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """添加风险规则（管理员）."""
    from app.models.contract_risk import ContractRiskRule
    rule = ContractRiskRule(
        rule_name=body["rule_name"],
        category=body["category"],
        clause_type=body["clause_type"],
        risk_level=body["risk_level"],
        weight=body.get("weight", 1),
        description=body.get("description"),
        suggestion=body.get("suggestion"),
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    # 🔑 Log rule creation
    AuditLog.log(db, "create_risk_rule", f"Created rule {rule.rule_name} by {actor_id}", actor_id)
    return rule
