"""佣金提现数据模型."""

from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Text, Index
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.work import generate_uuid


class WithdrawalRequest(Base):
    """佣金提现申请."""
    __tablename__ = "withdrawal_requests"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    amount_yuan = Column(Numeric(12, 2), nullable=False)
    available_balance_yuan = Column(Numeric(12, 2), nullable=False)  # 申请时快照
    fee_yuan = Column(Numeric(12, 2), default=0)
    net_amount_yuan = Column(Numeric(12, 2), nullable=False)
    method = Column(String(50), nullable=False)  # bank_transfer/wechat/alipay
    account_info = Column(Text, nullable=True)  # JSON string
    status = Column(String(20), default="pending", index=True)  # pending/approved/rejected/settled/cancelled
    approved_by = Column(String(32), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejected_reason = Column(Text, nullable=True)
    settled_at = Column(DateTime, nullable=True)
    transaction_ref = Column(String(100), nullable=True)  # 银行流水号
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_withdraw_user", "user_id"),
        Index("idx_withdraw_status", "status"),
        Index("idx_withdraw_created", "created_at"),
    )
