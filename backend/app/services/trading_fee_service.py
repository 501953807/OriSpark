from sqlalchemy.orm import Session

from app.models.trading_fee import TransactionFee, CommissionRule


# 基础费率档位 (basis points: 200 = 2%)
TIER_RATES = {
    "tier_1": {"max": 10000, "bps": 200},      # ≤ ¥10K → 2%
    "tier_2": {"max": 100000, "bps": 150},     # > ¥10K, ≤ ¥100K → 1.5%
    "tier_3": {"max": 500000, "bps": 100},     # > ¥100K, ≤ ¥500K → 1%
    "tier_4": {"max": float("inf"), "bps": 50}, # > ¥500K → 0.5%
}

# 信用等级折扣 (credit_score × 0.5 bps)
CREDIT_DISCOUNT_BPS = 0.5
MAX_CREDIT_DISCOUNT_BPS = 20  # cap at 0.2%

# 月度交易量阶梯折扣
VOLUME_TIER_BPS = {
    0: 0,        # 0-10K
    10000: -5,   # 10K-100K → -0.05%
    100000: -10, # 100K-500K → -0.1%
    500000: -20, # > 500K → -0.2%
}


def calculate_fee(amount_yuan: float, monthly_volume_yuan: float = 0,
                  credit_score: int = 50, creator_type: str | None = None,
                  category: str | None = None) -> dict:
    """计算交易费用.

    Returns: {amount, rate_bps, fee_amount, tier, is_discounted, discount_reason}
    """
    # Step 1: 根据交易额确定基础档位
    tier_name = "tier_1"
    for name, config in TIER_RATES.items():
        if amount_yuan <= config["max"]:
            tier_name = name
            break

    rate_bps = TIER_RATES[tier_name]["bps"]
    original_bps = rate_bps

    # Step 2: 月度交易量折扣
    vol_thresholds = sorted(VOLUME_TIER_BPS.keys())
    for i in range(len(vol_thresholds) - 1, -1, -1):
        if monthly_volume_yuan >= vol_thresholds[i]:
            vol_discount = VOLUME_TIER_BPS[vol_thresholds[i]]
            rate_bps += vol_discount
            break

    # Step 3: 信用等级折扣
    credit_discount = min(int(credit_score * CREDIT_DISCOUNT_BPS), MAX_CREDIT_DISCOUNT_BPS)
    if credit_discount > 0:
        rate_bps -= credit_discount

    # Step 4: 最终计算
    fee_amount = round(amount_yuan * rate_bps / 10000, 2)
    is_discounted = rate_bps < original_bps

    reason = None
    if is_discounted:
        discounts = []
        if monthly_volume_yuan > 0:
            discounts.append("volume")
        if credit_discount > 0:
            discounts.append("credit")
        reason = ",".join(discounts)

    return {
        "amount_yuan": amount_yuan,
        "rate_bps": rate_bps,
        "fee_amount_yuan": fee_amount,
        "tier": tier_name,
        "is_discounted": is_discounted,
        "discount_reason": reason,
    }


def record_transaction(db: Session, transaction_id: str, amount_yuan: float,
                       seller_work_id: str | None, buyer_id: str | None,
                       calc_result: dict) -> TransactionFee:
    """记录一笔交易费用."""
    fee = TransactionFee(
        transaction_id=transaction_id,
        seller_work_id=seller_work_id,
        buyer_id=buyer_id,
        amount_yuan=amount_yuan,
        fee_rate_bps=calc_result["rate_bps"],
        fee_amount_yuan=calc_result["fee_amount_yuan"],
        tier=calc_result["tier"],
        is_discounted=calc_result["is_discounted"],
        discount_reason=calc_result.get("discount_reason"),
    )
    db.add(fee)
    db.commit()
    db.refresh(fee)
    return fee
