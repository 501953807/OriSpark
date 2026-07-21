"""多市场扩展路由."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.multi_market import (
    MarketInfoSchema,
    GeoArbitrageRequest,
    GeoArbitrageResponse,
    ExpansionPlanCreate,
    TaxGuideSchema,
)
from app.services.multi_market_service import (
    get_all_markets,
    calculate_geo_arbitrage,
    get_expansion_phases,
    create_expansion_plan,
    get_tax_guide,
)

router = APIRouter(prefix="/multi-market", tags=["multi-market"])


@router.get("/markets", response_model=list[MarketInfoSchema])
def list_markets(db: Session = Depends(get_db)):
    """获取所有市场信息."""
    return get_all_markets(db)


@router.post("/geo-arbitrage", response_model=GeoArbitrageResponse)
def calc_geo_arbitrage(req: GeoArbitrageRequest):
    """地理套利计算器."""
    result = calculate_geo_arbitrage(
        req.current_markets,
        req.monthly_revenue_yuan,
        req.creator_type,
    )
    return GeoArbitrageResponse(**result)


@router.get("/phases")
def list_phases():
    """获取出海三阶段规划."""
    return get_expansion_phases()


@router.post("/plans", response_model=dict)
def create_plan(req: ExpansionPlanCreate, db: Session = Depends(get_db)):
    """创建出海规划."""
    result = create_expansion_plan(
        db, "current_user",
        req.target_markets, req.phase, req.start_date, req.notes,
    )
    return result


@router.get("/tax-guide")
def get_tax(source: str = "cn", target: str = "us", db: Session = Depends(get_db)):
    """获取跨境税务指南."""
    result = get_tax_guide(db, source, target)
    if not result:
        raise HTTPException(404, "Tax guide not found")
    return result
