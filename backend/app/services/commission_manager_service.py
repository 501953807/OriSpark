"""委托项目管理业务服务层 — 封装 commission router 中的所有 DB 操作."""

from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
import json
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import extract
from sqlalchemy.orm import Session

from app.models.commission import (
    CommissionProject,
    CommissionOrder,
    CommissionMessage,
    CommissionMilestone,
    CommissionPayment,
    CommissionRevision,
)
from app.schemas.common import ApiResponse, PaginationParams
from app.schemas.commission import (
    MilestoneCreate,
    MilestoneUpdate,
    PaymentCreate,
    PaymentUpdate,
    RevisionCreate,
)


# ── 内部辅助转换函数 ──────────────────────────────────────────────────


def _milestone_to_dict(m: CommissionMilestone) -> dict:
    return {
        "id": m.id,
        "commission_id": m.commission_id,
        "name": m.name,
        "status": m.status,
        "due_date": m.due_date.isoformat() if m.due_date else None,
        "description": m.description,
        "order_index": m.order_index,
        "created_at": m.created_at.isoformat() if m.created_at else None,
        "updated_at": m.updated_at.isoformat() if m.updated_at else None,
    }


def _payment_to_dict(p: CommissionPayment) -> dict:
    return {
        "id": p.id,
        "commission_id": p.commission_id,
        "milestone_id": p.milestone_id,
        "amount": float(p.amount) if isinstance(p.amount, Decimal) else p.amount,
        "method": p.method,
        "status": p.status,
        "paid_at": p.paid_at.isoformat() if p.paid_at else None,
        "notes": p.notes,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


def _revision_to_dict(r: CommissionRevision) -> dict:
    return {
        "id": r.id,
        "commission_id": r.commission_id,
        "description": r.description,
        "client_feedback": r.client_feedback,
        "files": r.files or [],
        "created_by": r.created_by,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def _order_to_dict(o: CommissionOrder) -> dict:
    return {
        "id": o.id,
        "project_id": o.project_id,
        "order_type": o.order_type,
        "amount": o.amount,
        "status": o.status,
        "created_at": o.created_at.isoformat() if o.created_at else None,
    }


def _msg_to_dict(m: CommissionMessage) -> dict:
    return {
        "id": m.id,
        "project_id": m.project_id,
        "sender_id": m.sender_id,
        "content": m.content,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }


def _project_to_dict(p: CommissionProject) -> dict:
    """Convert CommissionProject to dict using ORM relationships."""
    return {
        "id": p.id,
        "user_id": p.user_id,
        "title": p.title,
        "description": p.description,
        "client_name": p.client_name,
        "status": p.status,
        "milestones": [_milestone_to_dict(m) for m in (p.milestones or [])],
        "payment_terms": p.payment_terms or [],
        "orders": [_order_to_dict(o) for o in (p.orders or [])],
        "messages": [_msg_to_dict(m) for m in (p.messages or [])],
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


def _parse_date_value(value: Optional[str]) -> Optional[datetime]:
    """解析日期字符串，支持 ISO 格式和 %Y-%m-%d 格式."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.strptime(value, "%Y-%m-%d")


# ══════════════════════════════════════════════════════════════════════
# CommissionManagerService
# ══════════════════════════════════════════════════════════════════════


class CommissionManagerService:
    """委托项目管理业务逻辑服务，封装所有 DB 操作."""

    def __init__(self, db: Session):
        self.db = db

    # ── 10.x 委托项目 CRUD ────────────────────────────────────────────

    def list_projects(
        self,
        params: PaginationParams,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> ApiResponse:
        """获取委托项目列表 (分页)."""
        q = self.db.query(CommissionProject)
        if user_id:
            q = q.filter(CommissionProject.user_id == user_id)
        if status:
            q = q.filter(CommissionProject.status == status)
        total = q.count()
        projects = (
            q.order_by(CommissionProject.created_at.desc())
            .limit(params.page_size)
            .offset((params.page - 1) * params.page_size)
            .all()
        )
        return ApiResponse(data={
            "items": [
                {
                    "id": p.id,
                    "title": p.title,
                    "description": p.description,
                    "client_name": p.client_name,
                    "status": p.status,
                    "milestones": [_milestone_to_dict(m) for m in (p.milestones or [])],
                    "payment_terms": p.payment_terms or [],
                    "order_count": len(p.orders) if p.orders else 0,
                    "message_count": len(p.messages) if p.messages else 0,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                    "updated_at": p.updated_at.isoformat() if p.updated_at else None,
                }
                for p in projects
            ],
            "total": total,
            "page": params.page,
            "page_size": params.page_size,
            "total_pages": (total + params.page_size - 1) // params.page_size if params.page_size else 0,
        })

    def create_project(
        self,
        title: str,
        user_id: str,
        description: Optional[str] = None,
        client_name: Optional[str] = None,
        status: str = "brief",
        payment_terms: Optional[list] = None,
    ) -> ApiResponse:
        """创建委托项目."""
        project = CommissionProject(
            user_id=user_id,
            title=title,
            description=description,
            client_name=client_name,
            status=status,
            payment_terms=payment_terms or [],
        )
        try:
            self.db.add(project)
            self.db.commit()
            self.db.refresh(project)
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(data=_project_to_dict(project), message="项目创建成功")

    def get_project(self, project_id: str) -> ApiResponse:
        """获取单个委托项目详情."""
        project = self.db.query(CommissionProject).filter(
            CommissionProject.id == project_id
        ).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        return ApiResponse(data=_project_to_dict(project))

    def update_project(
        self,
        project_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        client_name: Optional[str] = None,
        status: Optional[str] = None,
    ) -> ApiResponse:
        """更新委托项目."""
        project = self.db.query(CommissionProject).filter(
            CommissionProject.id == project_id
        ).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        update_data = {k: v for k, v in {
            "title": title,
            "description": description,
            "client_name": client_name,
            "status": status,
        }.items() if v is not None}
        for key, value in update_data.items():
            setattr(project, key, value)
        try:
            self.db.commit()
            self.db.refresh(project)
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(data=_project_to_dict(project), message="项目更新成功")

    def delete_project(self, project_id: str) -> ApiResponse:
        """删除委托项目 (级联删除订单、消息、里程碑、收款、修改记录)."""
        project = self.db.query(CommissionProject).filter(
            CommissionProject.id == project_id
        ).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        try:
            self.db.delete(project)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(data={"success": True}, message="项目已删除")

    # ── 10.x 委托订单 CRUD ────────────────────────────────────────────

    def list_orders(
        self,
        project_id: str,
        status: Optional[str] = None,
    ) -> ApiResponse:
        """获取项目下的订单列表."""
        q = self.db.query(CommissionOrder).filter(
            CommissionOrder.project_id == project_id
        )
        if status:
            q = q.filter(CommissionOrder.status == status)
        orders = q.all()
        return ApiResponse(data=[
            {
                "id": o.id,
                "order_type": o.order_type,
                "amount": o.amount,
                "status": o.status,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in orders
        ])

    def create_order(
        self,
        project_id: str,
        order_type: str,
        amount: float,
        status: str = "pending",
    ) -> ApiResponse:
        """创建委托订单."""
        project = self.db.query(CommissionProject).filter(
            CommissionProject.id == project_id
        ).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        order = CommissionOrder(
            project_id=project_id,
            order_type=order_type,
            amount=amount,
            status=status,
        )
        try:
            self.db.add(order)
            self.db.commit()
            self.db.refresh(order)
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(data=_order_to_dict(order), message="订单创建成功")

    # ── 10.x 委托沟通消息 ─────────────────────────────────────────────

    def list_messages(self, project_id: str) -> ApiResponse:
        """获取项目沟通消息列表."""
        msgs = self.db.query(CommissionMessage).filter(
            CommissionMessage.project_id == project_id
        ).order_by(CommissionMessage.created_at).all()
        return ApiResponse(data=[
            {
                "id": m.id,
                "sender_id": m.sender_id,
                "content": m.content,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in msgs
        ])

    def create_message(
        self,
        project_id: str,
        sender_id: str,
        content: str,
    ) -> ApiResponse:
        """发送沟通消息."""
        project = self.db.query(CommissionProject).filter(
            CommissionProject.id == project_id
        ).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        msg = CommissionMessage(
            project_id=project_id,
            sender_id=sender_id,
            content=content,
        )
        try:
            self.db.add(msg)
            self.db.commit()
            self.db.refresh(msg)
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(data=_msg_to_dict(msg), message="消息发送成功")

    # ── 10.x 里程碑 CRUD ──────────────────────────────────────────────

    def list_milestones(self, id: str) -> ApiResponse:
        """获取项目里程碑列表."""
        project = self.db.query(CommissionProject).filter(
            CommissionProject.id == id
        ).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        milestones = (
            self.db.query(CommissionMilestone)
            .filter(CommissionMilestone.commission_id == id)
            .order_by(CommissionMilestone.order_index)
            .all()
        )
        return ApiResponse(data=[_milestone_to_dict(m) for m in milestones])

    def create_milestone(
        self,
        id: str,
        payload: MilestoneCreate,
    ) -> ApiResponse:
        """创建里程碑."""
        project = self.db.query(CommissionProject).filter(
            CommissionProject.id == id
        ).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        due_date = _parse_date_value(payload.due_date)
        milestone = CommissionMilestone(
            commission_id=id,
            name=payload.name,
            status="pending",
            due_date=due_date,
            description=payload.description,
            order_index=payload.order_index,
        )
        try:
            self.db.add(milestone)
            self.db.commit()
            self.db.refresh(milestone)
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(data=_milestone_to_dict(milestone), message="里程碑创建成功")

    def update_milestone(
        self,
        id: str,
        mid: str,
        payload: MilestoneUpdate,
    ) -> ApiResponse:
        """更新里程碑."""
        milestone = self.db.query(CommissionMilestone).filter(
            CommissionMilestone.id == mid, CommissionMilestone.commission_id == id
        ).first()
        if not milestone:
            raise HTTPException(status_code=404, detail="里程碑不存在")
        update_data = payload.model_dump(exclude_unset=True)
        if "due_date" in update_data and update_data["due_date"]:
            update_data["due_date"] = _parse_date_value(update_data["due_date"])
        for key, value in update_data.items():
            setattr(milestone, key, value)
        try:
            self.db.commit()
            self.db.refresh(milestone)
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(data=_milestone_to_dict(milestone), message="里程碑更新成功")

    def delete_milestone(self, id: str, mid: str) -> ApiResponse:
        """删除里程碑."""
        milestone = self.db.query(CommissionMilestone).filter(
            CommissionMilestone.id == mid, CommissionMilestone.commission_id == id
        ).first()
        if not milestone:
            raise HTTPException(status_code=404, detail="里程碑不存在")
        try:
            self.db.delete(milestone)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(data={"success": True}, message="里程碑已删除")

    # ── 10.x 收款记录 CRUD ────────────────────────────────────────────

    def list_payments(self, id: str) -> ApiResponse:
        """获取项目收款记录列表."""
        project = self.db.query(CommissionProject).filter(
            CommissionProject.id == id
        ).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        payments = (
            self.db.query(CommissionPayment)
            .filter(CommissionPayment.commission_id == id)
            .order_by(CommissionPayment.created_at.desc())
            .all()
        )
        return ApiResponse(data=[_payment_to_dict(p) for p in payments])

    def create_payment(
        self,
        id: str,
        payload: PaymentCreate,
    ) -> ApiResponse:
        """记录收款."""
        project = self.db.query(CommissionProject).filter(
            CommissionProject.id == id
        ).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        payment = CommissionPayment(
            commission_id=id,
            milestone_id=payload.milestone_id,
            amount=Decimal(str(payload.amount)),
            method=payload.method,
            status="pending",
            notes=payload.notes,
        )
        try:
            self.db.add(payment)
            self.db.commit()
            self.db.refresh(payment)
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(data=_payment_to_dict(payment), message="收款记录创建成功")

    def update_payment(
        self,
        id: str,
        pid: str,
        payload: PaymentUpdate,
    ) -> ApiResponse:
        """更新收款记录."""
        payment = self.db.query(CommissionPayment).filter(
            CommissionPayment.id == pid, CommissionPayment.commission_id == id
        ).first()
        if not payment:
            raise HTTPException(status_code=404, detail="收款记录不存在")
        update_data = payload.model_dump(exclude_unset=True)
        if "paid_at" in update_data and update_data["paid_at"]:
            update_data["paid_at"] = _parse_date_value(update_data["paid_at"])
        if "amount" in update_data and update_data["amount"] is not None:
            update_data["amount"] = Decimal(str(update_data["amount"]))
        for key, value in update_data.items():
            setattr(payment, key, value)
        try:
            self.db.commit()
            self.db.refresh(payment)
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(data=_payment_to_dict(payment), message="收款记录更新成功")

    def delete_payment(self, id: str, pid: str) -> ApiResponse:
        """删除收款记录."""
        payment = self.db.query(CommissionPayment).filter(
            CommissionPayment.id == pid, CommissionPayment.commission_id == id
        ).first()
        if not payment:
            raise HTTPException(status_code=404, detail="收款记录不存在")
        try:
            self.db.delete(payment)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(data={"success": True}, message="收款记录已删除")

    # ── 10.x 修改/反馈记录 CRUD ───────────────────────────────────────

    def list_revisions(self, id: str) -> ApiResponse:
        """获取项目修改记录."""
        project = self.db.query(CommissionProject).filter(
            CommissionProject.id == id
        ).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        revisions = (
            self.db.query(CommissionRevision)
            .filter(CommissionRevision.commission_id == id)
            .order_by(CommissionRevision.created_at.desc())
            .all()
        )
        return ApiResponse(data=[_revision_to_dict(r) for r in revisions])

    def create_revision(
        self,
        id: str,
        payload: RevisionCreate,
    ) -> ApiResponse:
        """记录修改."""
        project = self.db.query(CommissionProject).filter(
            CommissionProject.id == id
        ).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        revision = CommissionRevision(
            commission_id=id,
            description=payload.description,
            client_feedback=payload.client_feedback,
            files=payload.files,
            created_by=payload.created_by,
        )
        try:
            self.db.add(revision)
            self.db.commit()
            self.db.refresh(revision)
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(data=_revision_to_dict(revision), message="修改记录创建成功")

    def delete_revision(self, id: str, rid: str) -> ApiResponse:
        """删除修改记录."""
        revision = self.db.query(CommissionRevision).filter(
            CommissionRevision.id == rid, CommissionRevision.commission_id == id
        ).first()
        if not revision:
            raise HTTPException(status_code=404, detail="修改记录不存在")
        try:
            self.db.delete(revision)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(data={"success": True}, message="修改记录已删除")

    # ── 10.x 时间线聚合 ───────────────────────────────────────────────

    def get_timeline(self, id: str) -> ApiResponse:
        """获取项目完整时间线 (里程碑+收款+修改)."""
        project = self.db.query(CommissionProject).filter(
            CommissionProject.id == id
        ).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        events: list[dict] = []

        milestones = (
            self.db.query(CommissionMilestone)
            .filter(CommissionMilestone.commission_id == id)
            .order_by(CommissionMilestone.created_at)
            .all()
        )
        for m in milestones:
            events.append({
                "type": "milestone",
                "id": m.id,
                "title": m.name,
                "description": m.description,
                "date": (m.due_date or m.created_at).isoformat() if (m.due_date or m.created_at) else None,
                "status": m.status,
            })

        payments = (
            self.db.query(CommissionPayment)
            .filter(CommissionPayment.commission_id == id)
            .order_by(CommissionPayment.created_at)
            .all()
        )
        for p in payments:
            events.append({
                "type": "payment",
                "id": p.id,
                "title": f"收款 ¥{float(p.amount)}",
                "description": p.notes,
                "date": (p.paid_at or p.created_at).isoformat() if (p.paid_at or p.created_at) else None,
                "status": p.status,
            })

        revisions = (
            self.db.query(CommissionRevision)
            .filter(CommissionRevision.commission_id == id)
            .order_by(CommissionRevision.created_at)
            .all()
        )
        for r in revisions:
            events.append({
                "type": "revision",
                "id": r.id,
                "title": "修改记录",
                "description": r.description,
                "date": r.created_at.isoformat() if r.created_at else None,
                "status": r.created_by,
            })

        events.sort(key=lambda e: e["date"] or "", reverse=False)
        return ApiResponse(data=events)

    # ── 10.x 约稿日历 ─────────────────────────────────────────────────

    def get_calendar(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> ApiResponse:
        """获取约稿日历事件."""
        start = datetime.strptime(from_date, "%Y-%m-%d").date() if from_date else date.today() - timedelta(days=30)
        end = datetime.strptime(to_date, "%Y-%m-%d").date() if to_date else date.today() + timedelta(days=30)

        projects = self.db.query(CommissionProject).filter(
            CommissionProject.status != "settlement"
        ).all()

        events: list[dict] = []
        for p in projects:
            milestones = (
                self.db.query(CommissionMilestone)
                .filter(CommissionMilestone.commission_id == p.id)
                .all()
            )
            for m in milestones:
                if m.due_date and m.due_date.date() >= start and m.due_date.date() <= end:
                    events.append({
                        "id": m.id,
                        "title": f"{p.title} - {m.name}",
                        "date": m.due_date.isoformat(),
                        "type": "milestone_due",
                    })

            payments = (
                self.db.query(CommissionPayment)
                .filter(CommissionPayment.commission_id == p.id)
                .all()
            )
            for pay in payments:
                if pay.paid_at and pay.paid_at.date() >= start and pay.paid_at.date() <= end:
                    events.append({
                        "id": pay.id,
                        "title": f"{p.title} - 收款 ¥{float(pay.amount)}",
                        "date": pay.paid_at.isoformat(),
                        "type": "payment_received",
                    })

        return ApiResponse(data={"events": events})

    # ── 10.x 仪表盘统计 ───────────────────────────────────────────────

    def get_dashboard(self) -> ApiResponse:
        """获取委托项目仪表盘统计."""
        active_projects = (
            self.db.query(CommissionProject)
            .filter(CommissionProject.status.in_(["proposal", "production", "delivery"]))
            .all()
        )
        active_count = len(active_projects)

        pending_payments = (
            self.db.query(CommissionPayment)
            .filter(CommissionPayment.status.in_(["pending", "partial"]))
            .all()
        )
        pending_payment_count = len(pending_payments)

        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        received = (
            self.db.query(CommissionPayment)
            .filter(CommissionPayment.status == "received")
            .all()
        )
        monthly_revenue = sum(float(p.amount) for p in received if p.paid_at and p.paid_at >= month_start)

        total_amount = sum(float(p.amount) for p in received)
        avg_ticket = total_amount / len(received) if received else 0.0

        return ApiResponse(data={
            "active_count": active_count,
            "pending_payment": pending_payment_count,
            "monthly_revenue": round(monthly_revenue, 2),
            "avg_ticket": round(avg_ticket, 2),
        })

    # ── v2: 佣金余额 + 提现 + 对账单 ──────────────────────────────────

    def get_commission_balance(self) -> ApiResponse:
        """获取可用佣金余额."""
        total_earned = sum(
            float(p.amount)
            for p in self.db.query(CommissionPayment).filter(
                CommissionPayment.status == "received"
            ).all()
        )
        frozen = sum(
            float(p.amount)
            for p in self.db.query(CommissionPayment).filter(
                CommissionPayment.status == "frozen"
            ).all()
        )
        return ApiResponse(data={
            "available_yuan": round(total_earned - frozen, 2),
            "frozen_yuan": round(frozen, 2),
            "total_earned_yuan": round(total_earned, 2),
        })

    def withdraw(
        self,
        user_id: str,
        amount_yuan: float,
        method: str = "bank_transfer",
        account_info: Optional[dict] = None,
    ) -> ApiResponse:
        """申请佣金提现."""
        from app.models.withdrawal import WithdrawalRequest

        amount = Decimal(str(amount_yuan))
        if amount <= 0:
            raise HTTPException(status_code=400, detail="提现金额必须 > 0")

        # 手续费 1%
        fee_rate = Decimal("0.01")
        fee = (amount * fee_rate).quantize(Decimal("0.01"))
        net_amount = amount - fee

        if net_amount < 10:
            raise HTTPException(status_code=400, detail="提现后净额不足 10 元")

        withdrawal = WithdrawalRequest(
            user_id=user_id,
            amount_yuan=amount,
            available_balance_yuan=amount,
            fee_yuan=fee,
            net_amount_yuan=net_amount,
            method=method,
            account_info=json.dumps(account_info or {}),
            status="pending",
        )
        self.db.add(withdrawal)
        self.db.commit()
        self.db.refresh(withdrawal)

        return ApiResponse(data={
            "id": withdrawal.id,
            "amount_yuan": float(withdrawal.amount_yuan),
            "net_amount_yuan": float(withdrawal.net_amount_yuan),
            "status": withdrawal.status,
        }, message="提现申请已提交")

    def get_withdrawals(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> ApiResponse:
        """提现记录列表."""
        from app.models.withdrawal import WithdrawalRequest
        query = self.db.query(WithdrawalRequest).filter(
            WithdrawalRequest.user_id == user_id
        )
        if status:
            query = query.filter(WithdrawalRequest.status == status)
        withdrawals = query.order_by(WithdrawalRequest.created_at.desc()).limit(limit).all()
        return ApiResponse(data=[{
            "id": w.id,
            "amount_yuan": float(w.amount_yuan),
            "net_amount_yuan": float(w.net_amount_yuan),
            "status": w.status,
            "method": w.method,
            "created_at": w.created_at.isoformat() if w.created_at else None,
        } for w in withdrawals])

    def get_monthly_stats(
        self,
        user_id: str,
        year: Optional[int] = None,
    ) -> ApiResponse:
        """月度佣金汇总（对账单）."""
        query = self.db.query(CommissionPayment).filter(
            CommissionPayment.status == "received"
        )
        if year:
            query = query.filter(extract('year', CommissionPayment.paid_at) == year)

        records = query.all()
        monthly = {}
        for r in records:
            month = r.paid_at.strftime("%Y-%m") if r.paid_at and hasattr(r, 'paid_at') else "unknown"
            if month not in monthly:
                monthly[month] = {"total": 0, "record_count": 0}
            monthly[month]["total"] += float(r.amount or 0)
            monthly[month]["record_count"] += 1

        return ApiResponse(data={"monthly": monthly, "records": len(records)})

    def get_yearly_stats(
        self,
        user_id: str,
        year: Optional[int] = None,
    ) -> ApiResponse:
        """年度佣金汇总."""
        query = self.db.query(CommissionPayment).filter(
            CommissionPayment.status == "received"
        )
        if year:
            query = query.filter(extract('year', CommissionPayment.paid_at) == year)

        records = query.all()
        total = sum(float(r.amount or 0) for r in records)
        return ApiResponse(data={
            "year": year or datetime.now().year,
            "total_commission": round(total, 2),
            "record_count": len(records),
        })
