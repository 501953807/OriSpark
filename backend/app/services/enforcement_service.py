"""维权工作流编排器 —  orchestrator for enforcement workflow."""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, List

from sqlalchemy.orm import Session

from app.models.enforcement import EnforcementAction, EnforcementTemplate, ComplaintMaterial
from app.models.monitor import MonitorResult
from app.models.work import Work
from app.services.evidence_service import (
    generate_evidence_package,
    generate_complaint_letter,
    generate_lawyer_letter,
)
from app.services.contract_state_service import ContractStateService


class EnforcementWorkflow:
    """维权工作流编排器。

    支持的动作类型：
      - platform_complaint（平台投诉）
      - dmca_notice（DMCA 通知）
      - lawyer_letter（律师函）
      - litigation（诉讼）

    状态流转：
      pending_review → confirmed → evidence_gathered → complaint_filed → resolved
    """

    VALID_TRANSITIONS = {
        "pending_review": {"confirmed"},
        "confirmed": {"evidence_gathered"},
        "evidence_gathered": {"complaint_filed"},
        "complaint_filed": {"resolved"},
        "resolved": set(),  # terminal
    }

    def __init__(self, db: Session):
        self.db = db

    @classmethod
    def create_from_monitor(
        cls,
        db: Session,
        monitor_result_id: str,
        action_type: str = "platform_complaint",
        platform: str = "generic",
        actor_id: Optional[str] = None,
    ) -> "EnforcementWorkflow":
        """从监控结果创建维权行动."""
        # 获取监控结果
        monitor_result = db.query(MonitorResult).filter(
            MonitorResult.id == monitor_result_id
        ).first()
        if not monitor_result:
            raise ValueError(f"Monitor result not found: {monitor_result_id}")

        # 创建工作
        work_id = monitor_result.work_id
        work = db.query(Work).filter(Work.id == work_id).first()
        if not work:
            raise ValueError(f"Work not found: {work_id}")

        # 创建 EnforcementAction
        action_id = str(uuid.uuid4().hex[:32])
        action = EnforcementAction(
            id=action_id,
            monitor_result_id=monitor_result_id,
            action_type=action_type,
            platform=platform,
            status="pending_review",
            title=f"维权行动-{action_id[:8]} - {work.title}",
            created_at=datetime.now(timezone.utc),
        )
        db.add(action)
        db.commit()

        return cls(db, action_id)

    def __init__(self, db: Session, action_id: str):
        self.db = db
        self.action_id = action_id
        self._load_action()

    def _load_action(self) -> None:
        """加载当前维权行动."""
        self.action = self.db.query(EnforcementAction).filter(
            EnforcementAction.id == self.action_id
        ).first()
        if not self.action:
            raise ValueError(f"Enforcement action not found: {self.action_id}")

    def can_transition(self, target_status: str) -> bool:
        """检查是否可以转换到目标状态."""
        allowed = self.VALID_TRANSITIONS.get(self.action.status, [])
        return target_status in allowed

    def transition_to(self, target_status: str, actor_id: Optional[str] = None, reason: str = "") -> None:
        """执行状态转换."""
        if not self.can_transition(target_status):
            raise ValueError(
                f"Invalid transition: {self.action.status} -> {target_status}"
            )

        old_status = self.action.status
        self.action.status = target_status
        self.action.updated_at = datetime.now(timezone.utc)
        self.action.reason = reason

        # 记录审计日志（简化版，实际应使用 AuditLog）
        self.db.commit()

    def confirm_review(self, actor_id: Optional[str] = None, review_note: str = "") -> None:
        """确认复核：pending_review → confirmed."""
        self.transition_to("confirmed", actor_id, review_note)
        self.action.review_note = review_note
        self.db.commit()

    def gather_evidence(
        self,
        evidence_data: Dict,
        actor_id: Optional[str] = None,
        evidence_notes: str = "",
    ) -> None:
        """收集证据：confirmed → evidence_gathered."""
        self.transition_to("evidence_gathered", actor_id, evidence_notes)

        # 关联证据材料
        for evid in evidence_data.get("evidences", []):
            material = ComplaintMaterial(
                id=str(uuid.uuid4().hex)[:32],
                action_id=self.action_id,
                evid_type=evid.get("type"),
                url=evid.get("url"),
                description=evid.get("description"),
                uploaded_at=datetime.now(timezone.utc),
            )
            self.db.add(material)

        # 生成证据包
        if evidence_data.get("work_id"):
            try:
                pkg = generate_evidence_package(self.db, evidence_data["work_id"])
                self.action.evidence_package_id = pkg.get("id")
            except Exception as e:
                self.action.evidence_error = str(e)

        self.db.commit()

    def file_complaint(
        self,
        template_id: Optional[str] = None,
        platform: Optional[str] = None,
        custom_text: Optional[str] = None,
        actor_id: Optional[str] = None,
    ) -> None:
        """提交投诉：evidence_gathered → complaint_filed."""
        self.transition_to("complaint_filed", actor_id, f"Platform: {platform or 'generic'}")

        # 选择模板或自定义文本
        if template_id:
            template = self.db.query(EnforcementTemplate).filter(
                EnforcementTemplate.id == template_id
            ).first()
            if template:
                self.action.template_used = template.title
                # 变量替换
                filled_body = self._fill_template_variables(template.body_template)
                self.action.complaint_text = filled_body
            else:
                raise ValueError(f"Template not found: {template_id}")
        elif custom_text:
            self.action.complaint_text = custom_text
        else:
            raise ValueError("Either template_id or custom_text must be provided")

        # 生成投诉信
        try:
            complaint_letter = generate_complaint_letter(
                work_id=self.action.monitor_result.work_id if hasattr(self.action, 'monitor_result') else None,
                template=self.action.template_used if hasattr(self.action, 'template_used') else None,
                text=self.action.complaint_text,
            )
            self.action.complaint_letter_id = complaint_letter.get("id")
        except Exception as e:
            self.action.complaint_error = str(e)

        self.action.sent_at = datetime.now(timezone.utc)
        self.db.commit()

    def resolve(
        self,
        resolution_type: str,
        compensation_amount: Optional[float] = None,
        resolution_note: str = "",
        actor_id: Optional[str] = None,
    ) -> None:
        """解决纠纷：complaint_filed → resolved."""
        valid_resolutions = ["takedown", "settlement", "dismissed", "litigation_started"]
        if resolution_type not in valid_resolutions:
            raise ValueError(f"Invalid resolution type: {resolution_type}. Must be one of {valid_resolutions}")

        self.transition_to("resolved", actor_id, resolution_note)
        self.action.resolution_type = resolution_type
        self.action.resolved_at = datetime.now(timezone.utc)
        self.action.resolution_note = resolution_note
        if compensation_amount is not None:
            self.action.compensation_amount = compensation_amount

        self.db.commit()

    def _fill_template_variables(self, template_body: str) -> str:
        """填充模板中的变量."""
        work = self.db.query(Work).filter(Work.id == self.action.work_id).first() if hasattr(self, 'action') else None
        variables = {
            "{{work_title}}": work.title if work else "",
            "{{owner_name}}": "创作者",
            "{{infringement_url}}": self.action.infringement_url if hasattr(self.action, 'infringement_url') else "",
            "{{date}}": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        }
        for placeholder, value in variables.items():
            template_body = template_body.replace(placeholder, value)
        return template_body

    def get_status_summary(self) -> Dict:
        """获取当前状态摘要."""
        return {
            "action_id": self.action_id,
            "status": self.action.status,
            "action_type": self.action.action_type,
            "platform": self.action.platform,
            "created_at": self.action.created_at.isoformat() if self.action.created_at else None,
            "updated_at": self.action.updated_at.isoformat() if self.action.updated_at else None,
            "next_possible": list(self.VALID_TRANSITIONS.get(self.action.status, [])),
        }

    def get_all_materials(self) -> List[Dict]:
        """获取所有证据材料."""
        materials = self.db.query(ComplaintMaterial).filter(
            ComplaintMaterial.action_id == self.action_id
        ).all()
        return [
            {
                "id": m.id,
                "type": m.evid_type,
                "url": m.url,
                "description": m.description,
                "uploaded_at": m.uploaded_at.isoformat() if m.uploaded_at else None,
            }
            for m in materials
        ]
