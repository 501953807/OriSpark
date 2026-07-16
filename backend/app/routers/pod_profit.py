"""POD 利润计算路由."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.pod_profit import (
    ProductConfigCreate, PricingSimulation, SaleRecord,
    ProfitResult, DesignSummary, PodOverview,
)
from app.services.pod_profit_service import (
    get_or_create_product, simulate_pricing, log_sale,
    get_design_profit_summary, get_pod_overview,
)

router = APIRouter(prefix="/api/pod-profit", tags=["pod-profit"])


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
