"""发票与自动续费服务."""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.invoice import Invoice, SubscriptionAutoRenewal


def generate_invoice_number(db: Session) -> str:
    """生成发票编号 INV/YYYY/MM/XXXX."""
    now = datetime.utcnow()
    prefix = f"INV/{now.year:04d}/{now.month:02d}"
    existing = db.query(Invoice).filter(Invoice.invoice_number.like(f"{prefix}%")).all()
    seq = len(existing) + 1
    return f"{prefix}/{seq:04d}"


def create_invoice(user_id: str, amount_yuan: float, tax_rate: float = 0.11, description: str | None = None, payment_method: str | None = None, due_date: datetime | None = None, is_auto_renewal: bool = False, db: Session | None = None) -> dict:
    """创建发票."""
    subtotal = round(amount_yuan / (1 + tax_rate), 2) if tax_rate else amount_yuan
    tax = round(amount_yuan - subtotal, 2)
    invoice = Invoice(
        user_id=user_id,
        invoice_number=generate_invoice_number(db) if db else "INV/TEMP/0001",
        amount_yuan=float(amount_yuan),
        tax_rate=float(tax_rate),
        subtotal_yuan=subtotal,
        tax_amount_yuan=tax,
        total_yuan=float(amount_yuan),
        status="pending",
        due_date=due_date or datetime.utcnow() + timedelta(days=30),
        description=description,
        payment_method=payment_method,
        is_auto_renewal=is_auto_renewal,
    )
    if db:
        db.add(invoice)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        db.refresh(invoice)
    return _invoice_to_dict(invoice)


def list_invoices(user_id: str, status: str | None = None, limit: int = 20, offset: int = 0, db: Session | None = None) -> list[dict]:
    """获取用户发票列表."""
    q = db.query(Invoice).filter(Invoice.user_id == user_id)
    if status:
        q = q.filter(Invoice.status == status)
    invoices = q.order_by(Invoice.created_at.desc()).offset(offset).limit(limit).all()
    return [_invoice_to_dict(i) for i in invoices]


def mark_invoice_paid(invoice_id: str, db: Session) -> dict:
    """标记发票已支付."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise ValueError("发票不存在")
    invoice.status = "paid"
    invoice.paid_at = datetime.utcnow()
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(invoice)
    return _invoice_to_dict(invoice)


def update_auto_renewal(subscriber_id: str, enabled: bool, db: Session) -> dict:
    """更新自动续费配置."""
    renewal = db.query(SubscriptionAutoRenewal).filter(
        SubscriptionAutoRenewal.subscriber_id == subscriber_id
    ).first()
    if not renewal:
        renewal = SubscriptionAutoRenewal(
            subscriber_id=subscriber_id,
            enabled=enabled,
        )
        db.add(renewal)
    else:
        renewal.enabled = enabled
        renewal.updated_at = datetime.utcnow()
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(renewal)
    return {
        "id": renewal.id,
        "subscriber_id": renewal.subscriber_id,
        "enabled": renewal.enabled,
        "last_renewal_attempt": renewal.last_renewal_attempt.isoformat() if renewal.last_renewal_attempt else None,
        "next_renewal_date": renewal.next_renewal_date.isoformat() if renewal.next_renewal_date else None,
        "failed_attempts": renewal.failed_attempts,
        "max_failed_attempts": renewal.max_failed_attempts,
        "created_at": renewal.created_at.isoformat() if renewal.created_at else None,
        "updated_at": renewal.updated_at.isoformat() if renewal.updated_at else None,
    }


def get_auto_renewal(subscriber_id: str, db: Session) -> dict | None:
    """获取自动续费配置."""
    renewal = db.query(SubscriptionAutoRenewal).filter(
        SubscriptionAutoRenewal.subscriber_id == subscriber_id
    ).first()
    if not renewal:
        return None
    return {
        "id": renewal.id,
        "subscriber_id": renewal.subscriber_id,
        "enabled": renewal.enabled,
        "last_renewal_attempt": renewal.last_renewal_attempt.isoformat() if renewal.last_renewal_attempt else None,
        "next_renewal_date": renewal.next_renewal_date.isoformat() if renewal.next_renewal_date else None,
        "failed_attempts": renewal.failed_attempts,
        "max_failed_attempts": renewal.max_failed_attempts,
        "created_at": renewal.created_at.isoformat() if renewal.created_at else None,
        "updated_at": renewal.updated_at.isoformat() if renewal.updated_at else None,
    }


def process_renewal_attempt(subscriber_id: str, success: bool, db: Session) -> dict:
    """处理续费扣款尝试."""
    renewal = db.query(SubscriptionAutoRenewal).filter(
        SubscriptionAutoRenewal.subscriber_id == subscriber_id
    ).first()
    if not renewal:
        return {"status": "not_found"}

    renewal.last_renewal_attempt = datetime.utcnow()
    if success:
        renewal.failed_attempts = 0
        renewal.next_renewal_date = datetime.utcnow() + timedelta(days=30)
        status = "success"
    else:
        renewal.failed_attempts += 1
        status = "failed"
        if renewal.failed_attempts >= renewal.max_failed_attempts:
            renewal.enabled = False

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(renewal)
    return {"status": status, "failed_attempts": renewal.failed_attempts, "enabled": renewal.enabled}


def _invoice_to_dict(i: Invoice) -> dict:
    return {
        "id": i.id,
        "user_id": i.user_id,
        "invoice_number": i.invoice_number,
        "amount_yuan": i.amount_yuan,
        "tax_rate": i.tax_rate,
        "subtotal_yuan": i.subtotal_yuan,
        "tax_amount_yuan": i.tax_amount_yuan,
        "total_yuan": i.total_yuan,
        "status": i.status,
        "due_date": i.due_date.isoformat() if i.due_date else None,
        "paid_at": i.paid_at.isoformat() if i.paid_at else None,
        "description": i.description,
        "payment_method": i.payment_method,
        "payment_proof_path": i.payment_proof_path,
        "is_auto_renewal": i.is_auto_renewal,
        "created_at": i.created_at.isoformat() if i.created_at else None,
        "updated_at": i.updated_at.isoformat() if i.updated_at else None,
    }
