"""合约实例数据模型."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Index, Text, DECIMAL
from sqlalchemy.orm import relationship

from app.database import Base


class ContractInstance(Base):
    """合约实例表 — v5.0 合约市场核心交易标的."""

    __tablename__ = "contract_instances"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)

    # 基础信息
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    work_id = Column(String(32), ForeignKey("works.id", ondelete="SET NULL"), nullable=True)
    contract_type = Column(
        String(50),
        nullable=False,
        default="non_exclusive_license",
    )
    # copyright_transfer / product_license / exclusive_license / non_exclusive_license

    # 价格与货币
    total_amount = Column(DECIMAL(12, 2), nullable=False)
    currency = Column(String(10), default="CNY")
    billing_cycle = Column(String(20), default="monthly")
    # one_time / monthly / quarterly / yearly / revenue_share

    # 授权范围
    scope_usage = Column(String(50), default="commercial")  # personal/commercial/resale/modify
    scope_geography = Column(String(50), default="china")  # local/national/global/china/eu/us/jp
    scope_duration = Column(String(50), nullable=True)  # 1year / 3years / perpetual
    scope_medium = Column(String(50), nullable=True)  # digital/print/web/social_merchandise
    scope_print_limit = Column(Integer, nullable=True)
    scope_revenue_cap = Column(DECIMAL(12, 2), nullable=True)

    # 状态机
    status = Column(String(30), default="draft")
    # draft/listed/active/subscribed/escrowed/insured/executing/inspect/completed/dispute/cancelled/resolved/refunded

    # 分润规则 (JSON 锁定)
    split_rules_json = Column(Text, nullable=False, default="[]")

    # 时间线
    published_at = Column(DateTime, nullable=True)
    subscribed_at = Column(DateTime, nullable=True)
    escrowed_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    # 保险
    insurance_product_id = Column(String(32), nullable=True)
    insurance_policy_no = Column(String(100), nullable=True)
    insurance_premium = Column(DECIMAL(10, 2), nullable=True)

    # 支付托管
    escrow_provider = Column(String(30), nullable=True)  # stripe / paypal / worldfirst
    escrow_transaction_id = Column(String(100), nullable=True)

    # 关联
    creator_id = Column(String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    operator_id = Column(String(32), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    trader_id = Column(String(32), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # 审核与标记
    verified = Column(String(30), default="pending")  # pending/approved/rejected
    review_comment = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_contract_status", "status"),
        Index("idx_contract_creator", "creator_id"),
        Index("idx_contract_work", "work_id"),
        Index("idx_contract_published", "published_at"),
        Index("idx_contract_verified", "verified"),
    )

    # Relationships
    work = relationship("Work", foreign_keys=[work_id])
    creator = relationship("User", foreign_keys=[creator_id], backref="created_contracts")
    operator = relationship("User", foreign_keys=[operator_id])
    trader = relationship("User", foreign_keys=[trader_id])


class SplitRule(Base):
    """分润规则历史表 — 记录每次分润比例变更."""

    __tablename__ = "split_rules"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    contract_id = Column(
        String(32),
        ForeignKey("contract_instances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    participant_id = Column(String(32), nullable=False)
    role = Column(String(30), nullable=False)  # creator/operator/legal_rep/tax_agent/logistics/insurer/platform
    percentage = Column(Float, nullable=False)  # 0.0 - 1.0
    quote_amount = Column(DECIMAL(12, 2), nullable=True)
    quoted_at = Column(DateTime, nullable=False)
    locked_at = Column(DateTime, nullable=True)
    changed_at = Column(DateTime, nullable=True)
    change_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_split_rule_contract", "contract_id"),
        Index("idx_split_rule_participant", "participant_id"),
    )


class SplitExecutionLog(Base):
    """分润执行记录表."""

    __tablename__ = "split_execution_logs"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    contract_id = Column(
        String(32),
        ForeignKey("contract_instances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    execution_batch = Column(String(50), nullable=False)  # e.g. '2026-08-01_monthly'
    total_amount = Column(DECIMAL(12, 2), nullable=False)
    platform_fee = Column(DECIMAL(12, 2), nullable=True)  # 平台 3‰
    executor = Column(String(30), nullable=True)  # stripe_transfer / manual
    executed_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="pending")  # pending/success/failed/refunded
    error_message = Column(Text, nullable=True)
    detail_json = Column(Text, nullable=True)  # 各方分润明细 JSON
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_split_exec_contract", "contract_id"),
        Index("idx_split_exec_batch", "execution_batch"),
    )


class ContractMatching(Base):
    """合约撮合记录表."""

    __tablename__ = "contract_matchings"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    contract_id = Column(
        String(32),
        ForeignKey("contract_instances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    participant_type = Column(String(30), nullable=False)  # operator/trader/buyer
    participant_id = Column(String(32), nullable=False)
    match_score = Column(Float, nullable=True)  # 0.0 - 1.0
    match_reason = Column(Text, nullable=True)
    pushed_at = Column(DateTime, default=datetime.utcnow)
    viewed_at = Column(DateTime, nullable=True)
    responded_at = Column(DateTime, nullable=True)
    response = Column(String(30), nullable=True)  # accepted/declined/counter_offer
    counter_offer_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_contract_matching_contract", "contract_id"),
        Index("idx_contract_matching_participant", "participant_id"),
    )
