"""POD 利润计算路由."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_auth
from app.schemas.pod_profit import (
    ProductConfigCreate, PricingSimulation, SaleRecord,
    ProfitResult, DesignSummary, PodOverview,
)
from app.services.pod_profit_service import (
    get_or_create_product, simulate_pricing, log_sale,
    get_design_profit_summary, get_pod_overview,
)

router = APIRouter(prefix="/pod-profit", tags=["pod-profit"])


@router.post("/product-config")
def create_product_config(data: ProductConfigCreate, db: Session = Depends(get_db)):
    """创建/更新 POD 产品配置."""
    product = get_or_create_product(
        db, "current_user", data.platform, data.product_type, data.markup_rate,
    )
    return {
        "id": product.id,
        "platform": product.platform,
        "product_type": product.product_type,
        "base_cost_usd": product.base_cost_usd,
        "markup_rate": product.markup_rate,
    }


@router.post("/simulate-pricing", response_model=list[PricingSimulation])
def simulate(data: ProductConfigCreate):
    """模拟不同加价率下的定价和利润."""
    results = simulate_pricing(
        data.platform, data.product_type, [0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5],
    )
    return results


@router.post("/log-sale", response_model=ProfitResult)
def record_sale(data: SaleRecord, db: Session = Depends(get_db)):
    """记录一笔 POD 销售."""
    result = log_sale(
        db, "current_user", None,
        platform=data.platform,
        product_type=data.product_type,
        sale_price_usd=data.sale_price_usd,
        base_cost_usd=data.base_cost_usd,
        shipping_cost_usd=data.shipping_cost_usd,
        platform_fee_pct=data.platform_fee_pct,
        exchange_rate=data.exchange_rate,
    )
    return result


@router.get("/designs-summary", response_model=list[DesignSummary])
def designs_summary(db: Session = Depends(get_db)):
    """获取各设计作品的利润汇总."""
    return get_design_profit_summary(db, "current_user")


@router.get("/overview", response_model=PodOverview)
def overview(db: Session = Depends(get_db)):
    """获取 POD 整体概览."""
    return get_pod_overview(db, "current_user")


# ============================================================================
# v2: POD 结算 + 统计
# ============================================================================


@router.get("/my-settlements")
def get_my_settlements(user_id: str = Depends(require_auth),
                       period: str = None, status: str = None,
                       db: Session = Depends(get_db)):
    """我的结算单列表."""
    from app.services.pod_settlement_service import list_settlements
    settlements = list_settlements(db, user_id, period, status)
    return [{
        "id": s.id, "period": s.period, "status": s.status,
        "total_sales_yuan": float(s.total_sales_yuan),
        "creator_earnings_yuan": float(s.creator_earnings_yuan),
        "confirmed_at": s.confirmed_at.isoformat() if s.confirmed_at else None,
    } for s in settlements]


@router.post("/settlements/generate")
def post_generate_settlement(period: str, user_id: str = Depends(require_auth),
                             db: Session = Depends(get_db)):
    """手动触发月度结算生成."""
    from app.services.pod_settlement_service import generate_monthly_settlement
    settlement = generate_monthly_settlement(db, user_id, period)
    return {"id": settlement.id, "period": settlement.period, "status": settlement.status}


@router.post("/settlements/{settlement_id}/confirm")
def post_confirm_settlement(settlement_id: str, user_id: str = Depends(require_auth),
                            db: Session = Depends(get_db)):
    """确认结算单."""
    from app.services.pod_settlement_service import confirm_settlement
    try:
        settlement = confirm_settlement(db, settlement_id, user_id)
        return {"id": settlement.id, "status": settlement.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sales/statistics")
def get_sales_statistics(user_id: str = Depends(require_auth),
                         start_date: str = None, end_date: str = None,
                         db: Session = Depends(get_db)):
    """POD 销售统计."""
    from app.services.pod_settlement_service import get_sales_statistics as _get_stats
    return _get_stats(db, user_id, start_date, end_date)
