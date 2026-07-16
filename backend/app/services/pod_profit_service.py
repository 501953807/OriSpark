"""POD 利润计算器服务层."""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.pod_profit import PODProduct, PODDesign, PODSale


# 各平台/产品类型基础成本 (USD)
BASE_COSTS = {
    "t-shirt": {"redbubble": 8.5, "printful": 7.2, "printify": 6.5},
    "phone_case": {"redbubble": 12.0, "printful": 10.5, "printify": 9.0},
    "poster": {"redbubble": 10.0, "printful": 8.5, "printify": 7.0},
    "mug": {"redbubble": 13.0, "printful": 11.0, "printify": 9.5},
    "sticker": {"redbubble": 2.5, "printful": 2.0, "printify": 1.5},
    "tapestry": {"redbubble": 22.0, "printful": 18.0, "printify": 16.0},
}

PLATFORM_FEES = {
    "redbubble": 0.20,  # 20% platform margin built into pricing
    "printful": 0.0,   # no extra fee, just base cost
    "printify": 0.0,   # no extra fee, just base cost
}

EXCHANGE_RATE = 7.2


def get_or_create_product(
    db: Session, user_id: str, platform: str, product_type: str,
    markup_rate: float = 0.2,
) -> PODProduct:
    """获取或创建 POD 产品配置."""
    existing = db.query(PODProduct).filter(
        PODProduct.user_id == user_id,
        PODProduct.platform == platform,
        PODProduct.product_type == product_type,
        PODProduct.is_active == True,
    ).first()

    if existing:
        existing.markup_rate = markup_rate
        db.flush()
        return existing

    base_cost = BASE_COSTS.get(product_type, {}).get(platform, 10.0)

    pod = PODProduct(
        user_id=user_id,
        platform=platform,
        product_type=product_type,
        base_cost_usd=base_cost,
        base_cost_cny=round(base_cost * EXCHANGE_RATE, 2),
        markup_rate=markup_rate,
    )
    db.add(pod)
    db.flush()
    return pod


def calculate_profit(
    sale_price_usd: float, base_cost_usd: float, shipping_cost_usd: float,
    platform_fee_pct: float, exchange_rate: float = EXCHANGE_RATE,
) -> dict:
    """计算单次销售的利润."""
    platform_fee = sale_price_usd * platform_fee_pct
    total_cost = base_cost_usd + shipping_cost_usd + platform_fee
    profit_usd = sale_price_usd - total_cost
    profit_cny = round(profit_usd * exchange_rate, 2)

    return {
        "sale_price_usd": round(sale_price_usd, 2),
        "sale_price_cny": round(sale_price_usd * exchange_rate, 2),
        "base_cost_usd": round(base_cost_usd, 2),
        "shipping_cost_usd": round(shipping_cost_usd, 2),
        "platform_fee_usd": round(platform_fee, 2),
        "profit_usd": round(profit_usd, 2),
        "profit_cny": profit_cny,
        "margin_pct": round((profit_usd / sale_price_usd * 100) if sale_price_usd > 0 else 0, 1),
        "exchange_rate": exchange_rate,
    }


def simulate_pricing(
    platform: str, product_type: str, markup_rates: list[float],
) -> list[dict]:
    """模拟不同加价率下的定价和利润."""
    base_cost = BASE_COSTS.get(product_type, {}).get(platform, 10.0)
    fee_pct = PLATFORM_FEES.get(platform, 0.0)
    results = []

    for markup in markup_rates:
        # Redbubble 等平台的定价机制: 卖家设置加价 = 基础价格 * (1 + markup)
        if platform == "redbubble":
            sale_price = base_cost * (1 + markup)
        else:
            # Printful/Printify: 卖家自己定价，这里假设基于成本加价
            sale_price = base_cost * (1 + markup)

        profit_info = calculate_profit(sale_price, base_cost, 0, fee_pct)
        results.append({
            "markup_pct": int(markup * 100),
            "sale_price_usd": profit_info["sale_price_usd"],
            "sale_price_cny": profit_info["sale_price_cny"],
            "profit_usd": profit_info["profit_usd"],
            "profit_cny": profit_info["profit_cny"],
            "margin_pct": profit_info["margin_pct"],
        })

    return results


def log_sale(
    db: Session, user_id: str, design_id: Optional[str],
    platform: str, product_type: str, sale_price_usd: float,
    base_cost_usd: float, shipping_cost_usd: float = 0,
    platform_fee_pct: float = 0, exchange_rate: float = EXCHANGE_RATE,
) -> dict:
    """记录一笔 POD 销售."""
    profit_info = calculate_profit(sale_price_usd, base_cost_usd, shipping_cost_usd, platform_fee_pct, exchange_rate)

    sale = PODSale(
        user_id=user_id,
        design_id=design_id,
        platform=platform,
        product_type=product_type,
        sale_price_usd=sale_price_usd,
        base_cost_usd=base_cost_usd,
        shipping_cost_usd=shipping_cost_usd,
        platform_fee_pct=platform_fee_pct,
        profit_usd=profit_info["profit_usd"],
        profit_cny=profit_info["profit_cny"],
        exchange_rate=exchange_rate,
    )
    db.add(sale)
    db.flush()

    return {
        "id": sale.id,
        **profit_info,
    }


def get_design_profit_summary(db: Session, user_id: str) -> list[dict]:
    """获取每个设计作品的利润汇总."""
    designs = db.query(PODDesign).filter(
        PODDesign.user_id == user_id,
    ).all()

    results = []
    for d in designs:
        sales = db.query(PODSale).filter(
            PODSale.design_id == d.id,
        ).all()

        total_revenue = sum(s.sale_price_usd for s in sales)
        total_cost = sum(s.base_cost_usd + s.shipping_cost_usd for s in sales)
        total_profit = sum(s.profit_usd for s in sales)

        results.append({
            "id": d.id,
            "title": d.title,
            "status": d.status,
            "total_sales": len(sales),
            "total_revenue_cny": round(total_revenue * EXCHANGE_RATE, 2),
            "total_profit_cny": round(total_profit * EXCHANGE_RATE, 2),
            "avg_margin_pct": round((total_profit / total_revenue * 100) if total_revenue > 0 else 0, 1),
        })

    return results


def get_pod_overview(db: Session, user_id: str) -> dict:
    """获取 POD 整体概览: 总收入、总利润、平均利润率."""
    sales = db.query(PODSale).filter(PODSale.user_id == user_id).all()

    total_revenue = sum(s.sale_price_usd for s in sales)
    total_cost = sum(s.base_cost_usd + s.shipping_cost_usd for s in sales)
    total_profit = sum(s.profit_usd for s in sales)
    total_sales_count = len(sales)

    # 按平台统计
    by_platform = {}
    for s in sales:
        if s.platform not in by_platform:
            by_platform[s.platform] = {"sales": 0, "revenue": 0, "profit": 0}
        by_platform[s.platform]["sales"] += 1
        by_platform[s.platform]["revenue"] += s.sale_price_usd
        by_platform[s.platform]["profit"] += s.profit_usd

    platform_stats = {}
    for plat, data in by_platform.items():
        platform_stats[plat] = {
            "sales": data["sales"],
            "revenue_cny": round(data["revenue"] * EXCHANGE_RATE, 2),
            "profit_cny": round(data["profit"] * EXCHANGE_RATE, 2),
            "margin_pct": round((data["profit"] / data["revenue"] * 100) if data["revenue"] > 0 else 0, 1),
        }

    return {
        "total_sales": total_sales_count,
        "total_revenue_cny": round(total_revenue * EXCHANGE_RATE, 2),
        "total_cost_cny": round(total_cost * EXCHANGE_RATE, 2),
        "total_profit_cny": round(total_profit * EXCHANGE_RATE, 2),
        "overall_margin_pct": round((total_profit / total_revenue * 100) if total_revenue > 0 else 0, 1),
        "by_platform": platform_stats,
    }
