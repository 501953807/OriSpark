"""合约生命周期管理服务 — 完整状态机 + 审计追踪."""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.contract import ContractInstance
from app.models.system import AuditLog


class ContractStateService:
    """合约状态机服务.

    完整状态流转:
    draft → listed → active → subscribed → escrowed → insured → executing → inspect → completed/dispute → resolved/refunded/cancelled
    """

    # 合法状态流转表
    VALID_TRANSITIONS = {
        "draft": ["listed", "cancelled"],
        "listed": ["active", "cancelled"],
        "active": ["subscribed", "cancelled"],
        "subscribed": ["escrowed", "cancelled"],
        "escrowed": ["insured", "refunded", "cancelled"],
        "insured": ["executing", "cancelled"],
        "executing": ["inspect", "completed", "dispute"],
        "inspect": ["completed", "dispute"],
        "dispute": ["resolved", "refunded", "cancelled"],
        "resolved": ["completed", "cancelled"],
        "refunded": ["cancelled"],
        "completed": [],
        "cancelled": [],
    }

    # 状态显示标签
    STATUS_LABELS = {
        "draft": "草稿",
        "listed": "已挂牌",
        "active": "生效中",
        "subscribed": "已认购",
        "escrowed": "托管中",
        "insured": "已投保",
        "executing": "履约中",
        "inspect": "待验收",
        "completed": "已完成",
        "dispute": "争议中",
        "resolved": "已解决",
        "refunded": "已退款",
        "cancelled": "已取消",
    }

    @staticmethod
    def get_valid_transitions() -> dict:
        """获取所有合法状态流转."""
        return dict(ContractStateService.VALID_TRANSITIONS)

    @staticmethod
    def get_status_labels() -> dict:
        """获取状态显示标签."""
        return dict(ContractStateService.STATUS_LABELS)

    @classmethod
    def can_transition(cls, current_status: str, target_status: str) -> bool:
        """检查状态流转是否合法."""
        allowed = cls.VALID_TRANSITIONS.get(current_status, [])
        return target_status in allowed

    @classmethod
    def validate_transition(
        cls,
        db: Session,
        contract_id: str,
        target_status: str,
        actor_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> ContractInstance:
        """验证并执行状态流转，记录审计日志."""
        contract = db.query(ContractInstance).filter(
            ContractInstance.id == contract_id
        ).first()
        if not contract:
            raise HTTPException(status_code=404, detail="合约不存在")

        old_status = contract.status
        if not cls.can_transition(old_status, target_status):
            raise HTTPException(
                status_code=400,
                detail=f"非法状态流转：{old_status} -> {target_status}",
            )

        contract.status = target_status
        contract.updated_at = datetime.utcnow()

        # 记录审计日志
        audit = AuditLog(
            user_id=actor_id,
            action=f"contract_status_change:{old_status}->{target_status}",
            detail=json.dumps({
                "contract_id": contract_id,
                "from": old_status,
                "to": target_status,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }, ensure_ascii=False),
            module="contract_market",
        )
        db.add(audit)

        try:
            db.commit()
            db.refresh(contract)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"状态流转失败: {str(e)}")

        return contract

    @classmethod
    def create_contract(
        cls,
        db: Session,
        title: str,
        description: str,
        work_id: str,
        contract_type: str,
        total_amount: float,
        currency: str,
        billing_cycle: str,
        scope_usage: str,
        scope_geography: str,
        scope_duration: str,
        creator_id: str,
        split_rules_json: str = "[]",
    ) -> ContractInstance:
        """创建合约草稿."""
        contract = ContractInstance(
            id=uuid.uuid4().hex,
            title=title,
            description=description,
            work_id=work_id,
            contract_type=contract_type,
            total_amount=total_amount,
            currency=currency,
            billing_cycle=billing_cycle,
            scope_usage=scope_usage,
            scope_geography=scope_geography,
            scope_duration=scope_duration,
            creator_id=creator_id,
            split_rules_json=split_rules_json,
            status="draft",
        )
        db.add(contract)

        audit = AuditLog(
            user_id=creator_id,
            action="contract_create",
            detail=json.dumps({
                "contract_id": contract.id,
                "title": title,
                "type": contract_type,
            }, ensure_ascii=False),
            module="contract_market",
        )
        db.add(audit)

        try:
            db.commit()
            db.refresh(contract)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"创建合约失败: {str(e)}")

        return contract

    @classmethod
    def publish_contract(
        cls,
        db: Session,
        contract_id: str,
        actor_id: Optional[str] = None,
    ) -> ContractInstance:
        """发布合约挂牌."""
        contract = cls.validate_transition(db, contract_id, "listed", actor_id)
        contract.published_at = datetime.utcnow()
        contract.verified = "pending"

        try:
            db.commit()
            db.refresh(contract)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="发布合约失败")

        return contract

    @classmethod
    def activate_contract(
        cls,
        db: Session,
        contract_id: str,
        actor_id: Optional[str] = None,
    ) -> ContractInstance:
        """激活合约（平台审核通过）."""
        contract = cls.validate_transition(db, contract_id, "active", actor_id)
        contract.verified = "approved"
        contract.published_at = datetime.utcnow()

        try:
            db.commit()
            db.refresh(contract)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="激活合约失败")

        return contract

    @classmethod
    def subscribe_contract(
        cls,
        db: Session,
        contract_id: str,
        subscriber_id: str,
        actor_id: Optional[str] = None,
    ) -> ContractInstance:
        """认购合约."""
        contract = cls.validate_transition(
            db, contract_id, "subscribed", actor_id
        )
        contract.subscribed_at = datetime.utcnow()
        contract.operator_id = subscriber_id

        try:
            db.commit()
            db.refresh(contract)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="认购合约失败")

        return contract

    @classmethod
    def initiate_escrow(
        cls,
        db: Session,
        contract_id: str,
        provider: str,
        actor_id: Optional[str] = None,
    ) -> ContractInstance:
        """发起资金托管."""
        contract = cls.validate_transition(
            db, contract_id, "escrowed", actor_id
        )
        contract.escrowed_at = datetime.utcnow()
        contract.escrow_provider = provider

        try:
            db.commit()
            db.refresh(contract)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="发起托管失败")

        return contract

    @classmethod
    def confirm_escrow(
        cls,
        db: Session,
        contract_id: str,
        transaction_id: str,
        actor_id: Optional[str] = None,
    ) -> ContractInstance:
        """确认托管到账."""
        contract = db.query(ContractInstance).filter(
            ContractInstance.id == contract_id
        ).first()
        if not contract:
            raise HTTPException(status_code=404, detail="合约不存在")
        if contract.status != "escrowed":
            raise HTTPException(status_code=400, detail="合约未处于托管状态")

        contract.escrow_transaction_id = transaction_id
        contract.updated_at = datetime.utcnow()

        audit = AuditLog(
            user_id=actor_id,
            action="escrow_confirmed",
            detail=json.dumps({
                "contract_id": contract_id,
                "transaction_id": transaction_id,
            }, ensure_ascii=False),
            module="contract_market",
        )
        db.add(audit)

        try:
            db.commit()
            db.refresh(contract)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="确认托管失败")

        return contract

    @classmethod
    def activate_insurance(
        cls,
        db: Session,
        contract_id: str,
        insurance_product_id: Optional[str] = None,
        policy_no: Optional[str] = None,
        premium: Optional[float] = None,
        actor_id: Optional[str] = None,
    ) -> ContractInstance:
        """激活保险."""
        contract = cls.validate_transition(
            db, contract_id, "insured", actor_id
        )
        if insurance_product_id:
            contract.insurance_product_id = insurance_product_id
        if policy_no:
            contract.insurance_policy_no = policy_no
        if premium is not None:
            contract.insurance_premium = premium

        try:
            db.commit()
            db.refresh(contract)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="激活保险失败")

        return contract

    @classmethod
    def start_execution(
        cls,
        db: Session,
        contract_id: str,
        actor_id: Optional[str] = None,
    ) -> ContractInstance:
        """开始履约."""
        contract = cls.validate_transition(
            db, contract_id, "executing", actor_id
        )
        contract.executed_at = datetime.utcnow()

        try:
            db.commit()
            db.refresh(contract)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="开始履约失败")

        return contract

    @classmethod
    def complete_contract(
        cls,
        db: Session,
        contract_id: str,
        actor_id: Optional[str] = None,
    ) -> ContractInstance:
        """完成合约."""
        contract = cls.validate_transition(
            db, contract_id, "completed", actor_id
        )
        contract.completed_at = datetime.utcnow()

        try:
            db.commit()
            db.refresh(contract)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="完成合约失败")

        return contract

    @classmethod
    def reject_inspection(
        cls,
        db: Session,
        contract_id: str,
        reason: str,
        actor_id: Optional[str] = None,
    ) -> ContractInstance:
        """拒绝验货/发起争议."""
        contract = cls.validate_transition(
            db, contract_id, "dispute", actor_id
        )
        contract.review_comment = reason

        try:
            db.commit()
            db.refresh(contract)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="发起争议失败")

        return contract

    @classmethod
    def resolve_dispute(
        cls,
        db: Session,
        contract_id: str,
        resolution: str,
        actor_id: Optional[str] = None,
    ) -> ContractInstance:
        """解决争议（进入 resolved 状态）."""
        contract = cls.validate_transition(
            db, contract_id, "resolved", actor_id
        )
        contract.review_comment = resolution

        try:
            db.commit()
            db.refresh(contract)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="解决争议失败")

        return contract

    @classmethod
    def refund_contract(
        cls,
        db: Session,
        contract_id: str,
        reason: str,
        actor_id: Optional[str] = None,
    ) -> ContractInstance:
        """退款."""
        contract = cls.validate_transition(
            db, contract_id, "refunded", actor_id
        )
        contract.review_comment = reason

        try:
            db.commit()
            db.refresh(contract)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="退款失败")

        return contract

    @classmethod
    def cancel_contract(
        cls,
        db: Session,
        contract_id: str,
        reason: str,
        actor_id: Optional[str] = None,
    ) -> ContractInstance:
        """取消合约."""
        contract = db.query(ContractInstance).filter(
            ContractInstance.id == contract_id
        ).first()
        if not contract:
            raise HTTPException(status_code=404, detail="合约不存在")

        if contract.status not in ("draft", "listed", "active", "subscribed"):
            raise HTTPException(
                status_code=400,
                detail="当前状态不可取消（仅允许在 draft/listed/active/subscribed 阶段取消）",
            )

        old_status = contract.status
        contract.status = "cancelled"
        contract.review_comment = reason
        contract.updated_at = datetime.utcnow()

        audit = AuditLog(
            user_id=actor_id,
            action=f"contract_cancel:{old_status}->cancelled",
            detail=json.dumps({
                "contract_id": contract_id,
                "from": old_status,
                "reason": reason,
            }, ensure_ascii=False),
            module="contract_market",
        )
        db.add(audit)

        try:
            db.commit()
            db.refresh(contract)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="取消合约失败")

        return contract

    @classmethod
    def get_contract_timeline(
        cls,
        db: Session,
        contract_id: str,
    ) -> list[dict]:
        """获取合约时间线（从审计日志 + 字段时间戳合并）."""
        contract = db.query(ContractInstance).filter(
            ContractInstance.id == contract_id
        ).first()
        if not contract:
            raise HTTPException(status_code=404, detail="合约不存在")

        timeline = []

        # 从审计日志获取状态变更事件
        audits = (
            db.query(AuditLog)
            .filter(AuditLog.module == "contract_market")
            .filter(AuditLog.action.like("contract_status_change%"))
            .order_by(AuditLog.created_at.asc())
            .all()
        )
        for audit in audits:
            try:
                detail = json.loads(audit.detail or "{}")
                timeline.append({
                    "timestamp": audit.created_at.isoformat() if audit.created_at else None,
                    "event": f"{detail.get('from', '?')} -> {detail.get('to', '?')}",
                    "label": f"{ContractStateService.STATUS_LABELS.get(detail.get('from', ''), detail.get('from', ''))} → {ContractStateService.STATUS_LABELS.get(detail.get('to', ''), detail.get('to', ''))}",
                    "action": audit.action,
                })
            except (json.JSONDecodeError, AttributeError):
                pass

        # 从模型字段补充时间线
        field_events = [
            ("created_at", "创建"),
            ("published_at", "挂牌"),
            ("subscribed_at", "认购"),
            ("escrowed_at", "托管"),
            ("executed_at", "履约"),
            ("completed_at", "完成"),
        ]
        for field, label in field_events:
            value = getattr(contract, field, None)
            if value:
                timeline.append({
                    "timestamp": value.isoformat() if hasattr(value, "isoformat") else str(value),
                    "event": label,
                    "label": label,
                    "action": f"field_{field}",
                })

        # 按时间排序
        timeline.sort(key=lambda x: x.get("timestamp") or "")
        return timeline

    @classmethod
    def get_contract_status_summary(
        cls,
        db: Session,
        contract_id: str,
    ) -> dict:
        """获取合约状态摘要."""
        contract = db.query(ContractInstance).filter(
            ContractInstance.id == contract_id
        ).first()
        if not contract:
            raise HTTPException(status_code=404, detail="合约不存在")

        next_statuses = cls.VALID_TRANSITIONS.get(contract.status, [])
        return {
            "id": contract.id,
            "title": contract.title,
            "status": contract.status,
            "status_label": cls.STATUS_LABELS.get(contract.status, contract.status),
            "next_possible": [
                {"status": s, "label": cls.STATUS_LABELS.get(s, s)}
                for s in next_statuses
            ],
            "verified": contract.verified,
            "created_at": contract.created_at.isoformat() if contract.created_at else None,
            "updated_at": contract.updated_at.isoformat() if contract.updated_at else None,
        }
