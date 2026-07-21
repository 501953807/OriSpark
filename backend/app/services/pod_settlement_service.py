"""POD 月度结算服务."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.pod_settlement import PodSettlement, PodSettlementItem


def generate_monthly_settlement(db: Session, user_id: str, period: str) -> PodSettlement:
    """生成指定月份的 POD 结算单.

    period 格式: "2026-07"
    """
    # 解析月份
    year, month = period.split("-")
    start_date = datetime(int(year), int(month), 1)
    if month == "12":
        end_date = datetime(int(year) + 1, 1, 1)
    else:
        end_date = datetime(int(year), int(month) + 1, 1)

    # 查询该月销售记录
    from app.models.pod_profit import PODSale
    sales = db.query(PODSale).filter(
        PODSale.user_id == user_id,
        PODSale.sold_at >= start_date,
        PODSale.sold_at < end_date,
    ).all()

    total_sales = Decimal("0")
    total_cost = Decimal("0")
    total_creator_earning = Decimal("0")
    total_platform_fee = Decimal("0")

    items = []
    for sale in sales:
        sale_amount = Decimal(str(sale.sale_price_usd * sale.exchange_rate or 0))
        cost = Decimal(str((sale.base_cost_usd + sale.shipping_cost_usd) * sale.exchange_rate or 0))
        creator_earning = Decimal(str(sale.profit_cny or 0))
        platform_fee = Decimal(str(float(sale.platform_fee_pct or 0) * float(sale.sale_price_usd) * sale.exchange_rate / 100))

        total_sales += sale_amount
        total_cost += cost
        total_creator_earning += creator_earning
        total_platform_fee += platform_fee

        items.append(PodSettlementItem(
            sale_id=sale.id,
            product_id=None,  # PODSale 无 product_id，后续可扩展
            sale_amount_yuan=sale_amount,
            cost_yuan=cost,
            creator_earning_yuan=creator_earning,
            platform_fee_yuan=platform_fee,
        ))

    settlement = PodSettlement(
        user_id=user_id,
        period=period,
        total_sales_yuan=total_sales,
        total_cost_yuan=total_cost,
        creator_earnings_yuan=total_creator_earning,
        platform_fee_yuan=total_platform_fee,
        status="pending",
        items=items,
    )
    db.add(settlement)
    db.commit()
    db.refresh(settlement)
    return settlement


def confirm_settlement(db: Session, settlement_id: str, user_id: str) -> PodSettlement:
    """创作者确认结算."""
    settlement = db.query(PodSettlement).filter(
        PodSettlement.id == settlement_id,
        PodSettlement.user_id == user_id,
    ).first()
    if not settlement:
        raise ValueError(f"Settlement {settlement_id} not found")
    if settlement.status != "pending":
        raise ValueError(f"Cannot confirm settlement in status: {settlement.status}")

    settlement.status = "confirmed"
    settlement.confirmed_at = datetime.utcnow()
    db.commit()
    db.refresh(settlement)
    return settlement


def list_settlements(db: Session, user_id: str, period: str = None, status: str = None) -> list[PodSettlement]:
    """获取用户结算单列表."""
    query = db.query(PodSettlement).filter(PodSettlement.user_id == user_id)
    if period:
        query = query.filter(PodSettlement.period == period)
    if status:
        query = query.filter(PodSettlement.status == status)
    return query.order_by(PodSettlement.period.desc()).all()


def get_settlement(db: Session, settlement_id: str) -> PodSettlement | None:
    """获取单个结算单详情."""
    return db.query(PodSettlement).filter(PodSettlement.id == settlement_id).first()


def get_sales_statistics(db: Session, user_id: str, start_date: str = None, end_date: str = None) -> dict:
    """POD 销售统计."""
    from app.models.pod_profit import PODSale

    query = db.query(PODSale).filter(PODSale.user_id == user_id)
    if start_date:
        query = query.filter(PODSale.sold_at >= start_date)
    if end_date:
        query = query.filter(PODSale.sold_at <= end_date)

    sales = query.all()
    stats = {
        "total_sales": sum(float(s.sale_price_usd * s.exchange_rate or 0) for s in sales),
        "total_cost": sum(float((s.base_cost_usd + s.shipping_cost_usd) * s.exchange_rate or 0) for s in sales),
        "total_earnings": sum(float(s.profit_cny or 0) for s in sales),
        "total_fees": sum(float(float(s.platform_fee_pct or 0) * float(s.sale_price_usd) * s.exchange_rate / 100) for s in sales),
        "sale_count": len(sales),
    }
    return stats
