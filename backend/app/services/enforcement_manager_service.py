"""维权管理服务层 — 封装 enforcement router 中的所有 DB 操作."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.enforcement import EnforcementAction, EnforcementTemplate, ComplaintMaterial
from app.models.monitor import MonitorResult, MonitorTask
from app.models.work import Work
from app.schemas.enforcement import (
    ComplaintSubmitRequest,
    ComplaintSubmitResponse,
    EnforcementActionCreate,
    EnforcementActionResponse,
    EnforcementActionUpdate,
    TransitionRequest,
    ConfirmRequest,
    EvidenceGatherRequest,
    ResolveRequest,
    WorkflowStatusResponse,
)
from app.services.enforcement import (
    build_evidence_package,
    generate_complaint_letter,
    generate_pdf_package,
    resolve_template_variables,
    create_action_from_work as service_create_action_from_work,
)
from app.utils.audit import AuditLog

# 状态机合法转换规则
VALID_TRANSITIONS = {
    "pending_review": {"confirmed"},
    "confirmed": {"evidence_gathered"},
    "evidence_gathered": {"complaint_filed"},
    "complaint_filed": {"resolved"},
    "resolved": set(),
}


class EnforcementManagerService:
    """维权管理业务逻辑服务，封装所有 DB 操作."""

    def __init__(self, db: Session):
        self.db = db

    def _enrich_action_response(self, action: EnforcementAction) -> EnforcementActionResponse:
        """填充维权行动响应，嵌入作品与监测信息."""
        result = EnforcementActionResponse.model_validate(action)

        mr = (
            self.db.query(MonitorResult)
            .filter(MonitorResult.id == action.monitor_result_id)
            .first()
        )
        if mr:
            mt = (
                self.db.query(MonitorTask)
                .filter(MonitorTask.id == mr.task_id)
                .first()
            )
            if mt:
                w = self.db.query(Work).filter(Work.id == mt.work_id).first()
                if w:
                    result.work_id = w.id
                    result.work_title = w.title
                    result.work_file_type = w.file_type
            result.infringement_url = mr.matched_url or ""
            result.similarity_score = mr.similarity

        return result

    def _check_access(self, action: EnforcementAction, actor_id: str, is_admin_fn) -> None:
        """检查用户对维权行动的访问权限."""
        if action.operator_id != actor_id and not is_admin_fn(actor_id):
            raise HTTPException(403, "Forbidden: You do not have access to this enforcement action")

    # ── 1. POST /actions ──────────────────────────────────────────────

    def create_action(
        self, payload: EnforcementActionCreate, actor_id: str,
    ) -> EnforcementActionResponse:
        """从监测结果创建维权行动."""
        mr = (
            self.db.query(MonitorResult)
            .filter(MonitorResult.id == payload.monitor_result_id)
            .first()
        )
        if not mr:
            raise HTTPException(status_code=404, detail="MonitorResult not found")

        action_id = str(uuid.uuid4().hex[:32])
        action = EnforcementAction(
            id=action_id,
            monitor_result_id=payload.monitor_result_id,
            action_type=payload.action_type,
            platform=payload.platform,
            status="pending_review",
            operator_id=actor_id,
            created_at=datetime.now(timezone.utc),
        )

        if payload.template_id:
            tpl = (
                self.db.query(EnforcementTemplate)
                .filter(EnforcementTemplate.id == payload.template_id)
                .first()
            )
            if not tpl:
                raise HTTPException(status_code=404, detail="Template not found")
            action.template_used = tpl.title

        self.db.add(action)
        self.db.commit()
        self.db.refresh(action)

        AuditLog.log(
            self.db, "create_enforcement_action",
            f"Created action {action_id} for monitor result {payload.monitor_result_id}",
            actor_id,
        )
        return self._enrich_action_response(action)

    # ── 2. GET /actions ────────────────────────────────────────────────

    def list_actions(
        self,
        status: Optional[str] = None,
        action_type: Optional[str] = None,
        platform: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list:
        """获取维权行动列表."""
        q = self.db.query(EnforcementAction)
        if status:
            q = q.filter(EnforcementAction.status == status)
        if action_type:
            q = q.filter(EnforcementAction.action_type == action_type)
        if platform:
            q = q.filter(EnforcementAction.platform == platform)
        actions = (
            q.order_by(EnforcementAction.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return [self._enrich_action_response(a) for a in actions]

    # ── 3. GET /actions/{action_id} ────────────────────────────────────

    def get_action(
        self, action_id: str, actor_id: str, is_admin_fn,
    ) -> EnforcementActionResponse:
        """获取维权行动详情."""
        action = (
            self.db.query(EnforcementAction)
            .filter(EnforcementAction.id == action_id)
            .first()
        )
        if not action:
            raise HTTPException(status_code=404, detail="Enforcement action not found")

        self._check_access(action, actor_id, is_admin_fn)
        AuditLog.log(self.db, "view_enforcement_action", f"Viewed action {action_id}", actor_id)
        return self._enrich_action_response(action)

    # ── 4. PATCH /actions/{action_id} ──────────────────────────────────

    def update_action(
        self, action_id: str, payload: EnforcementActionUpdate, actor_id: str, is_admin_fn,
    ) -> EnforcementActionResponse:
        """更新维权行动 (状态机约束)."""
        action = (
            self.db.query(EnforcementAction)
            .filter(EnforcementAction.id == action_id)
            .first()
        )
        if not action:
            raise HTTPException(status_code=404, detail="Enforcement action not found")

        self._check_access(action, actor_id, is_admin_fn)

        if payload.status:
            allowed = VALID_TRANSITIONS.get(action.status, set())
            if payload.status not in allowed:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Invalid status transition from '{action.status}' to '{payload.status}'. "
                        f"Allowed transitions: {sorted(allowed) or ['none (terminal state)']}"
                    ),
                )
            action.status = payload.status
            if payload.status == "complaint_filed":
                action.sent_at = datetime.now(timezone.utc)
            elif payload.status == "resolved":
                action.resolved_at = datetime.now(timezone.utc)

        for field in ["complaint_text", "template_used", "response_text", "resolution_type",
                      "compensation_amount", "notes"]:
            value = getattr(payload, field, None)
            if value is not None:
                setattr(action, field, value)

        action.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(action)

        AuditLog.log(
            self.db, "update_enforcement_action",
            f"Updated action {action_id} status={payload.status}", actor_id,
        )
        return self._enrich_action_response(action)

    # ── 5. POST /actions/{action_id}/gather-evidence ───────────────────

    def gather_evidence(self, action_id: str, actor_id: str, is_admin_fn) -> dict:
        """收集证据包并创建投诉材料."""
        action = (
            self.db.query(EnforcementAction)
            .filter(EnforcementAction.id == action_id)
            .first()
        )
        if not action:
            raise HTTPException(status_code=404, detail="Enforcement action not found")

        self._check_access(action, actor_id, is_admin_fn)

        mr = (
            self.db.query(MonitorResult)
            .filter(MonitorResult.id == action.monitor_result_id)
            .first()
        )
        if not mr:
            raise HTTPException(status_code=404, detail="MonitorResult not found")

        mt = (
            self.db.query(MonitorTask)
            .filter(MonitorTask.id == mr.task_id)
            .first()
        )
        if not mt:
            raise HTTPException(status_code=404, detail="MonitorTask not found")

        evidence = build_evidence_package(self.db, mt.work_id)
        zip_path = generate_pdf_package(evidence)

        material = ComplaintMaterial(
            enforcement_action_id=action_id,
            material_type="pdf_package",
            material_path=zip_path,
        )
        self.db.add(material)

        action.status = "evidence_gathered"
        action.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(action)

        AuditLog.log(self.db, "gather_evidence", f"Gathered evidence for action {action_id}", actor_id)

        return {
            "status": "evidence_gathered",
            "material_path": zip_path,
            "evidence": evidence,
        }

    # ── 6. POST /actions/{action_id}/submit-complaint ──────────────────

    def submit_complaint(
        self, action_id: str, payload: ComplaintSubmitRequest, actor_id: str, is_admin_fn,
    ) -> ComplaintSubmitResponse:
        """使用模板变量提交投诉."""
        action = (
            self.db.query(EnforcementAction)
            .filter(EnforcementAction.id == action_id)
            .first()
        )
        if not action:
            raise HTTPException(status_code=404, detail="Enforcement action not found")

        self._check_access(action, actor_id, is_admin_fn)

        mr = (
            self.db.query(MonitorResult)
            .filter(MonitorResult.id == action.monitor_result_id)
            .first()
        )
        if not mr:
            raise HTTPException(status_code=404, detail="MonitorResult not found")

        mt = (
            self.db.query(MonitorTask)
            .filter(MonitorTask.id == mr.task_id)
            .first()
        )
        if not mt:
            raise HTTPException(status_code=404, detail="MonitorTask not found")

        work = self.db.query(Work).filter(Work.id == mt.work_id).first()
        if not work:
            raise HTTPException(status_code=404, detail="Work not found")

        evidence = build_evidence_package(self.db, mt.work_id)

        template_body = ""
        prefilled_url = None
        if action.template_used:
            tpl = (
                self.db.query(EnforcementTemplate)
                .filter(EnforcementTemplate.title == action.template_used)
                .first()
            )
            if tpl:
                template_body = tpl.body_template
                prefilled_url = tpl.filing_url

        if not template_body:
            template_body = (
                "To Whom It May Concern,\n\n"
                "I have a good faith belief that the use of the material '{{work_title}}' "
                "on your platform constitutes copyright infringement.\n\n"
                "Work Details:\n"
                "- Title: {{work_title}}\n"
                "- Hash: {{sha256}}\n"
                "- File Type: {{work_file_type}}\n"
                "- Date: {{date}}\n\n"
                "Infringing URL: {{infringement_url}}\n\n"
                "Sincerely,\n{{author}}"
            )

        complaint_text = generate_complaint_letter(
            template_body, evidence.get("work_info", {}), evidence,
        )

        variables = resolve_template_variables(template_body, evidence.get("work_info", {}))
        material = ComplaintMaterial(
            enforcement_action_id=action_id,
            material_type="prefilled_url",
            material_path=prefilled_url or "",
            variables={"complaint_text": complaint_text},
        )
        self.db.add(material)

        action.status = "complaint_filed"
        action.sent_at = datetime.now(timezone.utc)
        action.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(action)

        AuditLog.log(self.db, "submit_complaint", f"Submitted complaint for action {action_id}", actor_id)

        return ComplaintSubmitResponse(
            action_id=action_id,
            complaint_text=complaint_text,
            material_path=material.material_path,
            prefilled_url=prefilled_url,
            status=action.status,
        )

    # ── 7. POST /actions/{action_id}/transition ────────────────────────

    def transition_action(
        self, action_id: str, request: TransitionRequest, actor_id: str, is_admin_fn,
    ) -> dict:
        """通过工作流步骤转换维权行动状态."""
        if request.actor_id != actor_id:
            raise HTTPException(400, "actor_id does not match authenticated user")

        action = (
            self.db.query(EnforcementAction)
            .filter(EnforcementAction.id == action_id)
            .first()
        )
        if not action:
            raise HTTPException(status_code=404, detail="Enforcement action not found")

        allowed = VALID_TRANSITIONS.get(action.status, set())
        if request.target_status not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot transition to {request.target_status} from current status",
            )

        self._check_access(action, actor_id, is_admin_fn)

        action.status = request.target_status
        action.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(action)

        AuditLog.log(
            self.db, "transition_action",
            f"Transitioned action {action_id} to {request.target_status}", actor_id,
        )
        return {"status": action.status, "message": f"Transitioned to {request.target_status}"}

    # ── 8. POST /actions/{action_id}/confirm ───────────────────────────

    def confirm_action(
        self, action_id: str, request: ConfirmRequest, actor_id: str, is_admin_fn,
    ) -> dict:
        """确认复核步骤 (pending_review → confirmed)."""
        if request.actor_id != actor_id:
            raise HTTPException(400, "actor_id does not match authenticated user")

        action = (
            self.db.query(EnforcementAction)
            .filter(EnforcementAction.id == action_id)
            .first()
        )
        if not action:
            raise HTTPException(status_code=404, detail="Enforcement action not found")

        self._check_access(action, actor_id, is_admin_fn)

        action.status = "confirmed"
        action.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(action)

        AuditLog.log(self.db, "confirm_action", f"Confirmed action {action_id}", actor_id)
        return {"status": action.status, "message": "Review confirmed"}

    # ── 9. POST /actions/{action_id}/gather-evidence/step ──────────────

    def gather_action_evidence(
        self, action_id: str, request: EvidenceGatherRequest, actor_id: str, is_admin_fn,
    ) -> dict:
        """收集证据并转换到 evidence_gathered 阶段."""
        if request.actor_id != actor_id:
            raise HTTPException(400, "actor_id does not match authenticated user")

        action = (
            self.db.query(EnforcementAction)
            .filter(EnforcementAction.id == action_id)
            .first()
        )
        if not action:
            raise HTTPException(status_code=404, detail="Enforcement action not found")

        self._check_access(action, actor_id, is_admin_fn)

        action.status = "evidence_gathered"
        action.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(action)

        AuditLog.log(self.db, "gather_evidence", f"Gathered evidence for action {action_id}", actor_id)
        return {"status": action.status, "message": "Evidence gathered"}

    # ── 10. POST /actions/{action_id}/resolve ──────────────────────────

    def resolve_action(
        self, action_id: str, request: ResolveRequest, actor_id: str, is_admin_fn,
    ) -> dict:
        """解决维权行动."""
        valid_resolutions = ["takedown", "settlement", "dismissed", "litigation_started"]
        if request.resolution_type not in valid_resolutions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid resolution type. Must be one of {valid_resolutions}",
            )

        if request.actor_id != actor_id:
            raise HTTPException(400, "actor_id does not match authenticated user")

        action = (
            self.db.query(EnforcementAction)
            .filter(EnforcementAction.id == action_id)
            .first()
        )
        if not action:
            raise HTTPException(status_code=404, detail="Enforcement action not found")

        self._check_access(action, actor_id, is_admin_fn)

        action.status = "resolved"
        action.resolution_type = request.resolution_type
        action.resolved_at = datetime.now(timezone.utc)
        if request.compensation_amount is not None:
            action.compensation_amount = request.compensation_amount
        action.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(action)

        AuditLog.log(
            self.db, "resolve_action",
            f"Resolved action {action_id} with type {request.resolution_type}", actor_id,
        )
        return {
            "status": action.status,
            "message": f"Action resolved with type {request.resolution_type}",
        }

    # ── 11. GET /actions/{action_id}/workflow-status ───────────────────

    def get_workflow_status(
        self, action_id: str, actor_id: str, is_admin_fn,
    ) -> WorkflowStatusResponse:
        """获取当前工作流状态和可能的下一步操作."""
        action = (
            self.db.query(EnforcementAction)
            .filter(EnforcementAction.id == action_id)
            .first()
        )
        if not action:
            raise HTTPException(status_code=404, detail="Enforcement action not found")

        self._check_access(action, actor_id, is_admin_fn)

        NEXT_POSSIBLE = {
            "pending_review": ["confirmed"],
            "confirmed": ["evidence_gathered"],
            "evidence_gathered": ["complaint_filed"],
            "complaint_filed": ["resolved"],
            "resolved": [],
        }

        materials = self.db.query(ComplaintMaterial).filter(
            ComplaintMaterial.enforcement_action_id == action_id,
        ).all()

        result = {
            "action_id": action.id,
            "status": action.status,
            "action_type": action.action_type,
            "platform": action.platform,
            "created_at": action.created_at.isoformat(),
            "updated_at": action.updated_at.isoformat(),
            "next_possible": NEXT_POSSIBLE.get(action.status, []),
            "all_materials": [
                {
                    "id": m.id,
                    "type": m.material_type,
                    "url": m.material_path,
                    "description": "",
                    "uploaded_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in materials
            ],
        }

        AuditLog.log(
            self.db, "check_workflow_status", f"Checked workflow status for action {action_id}", actor_id,
        )
        return WorkflowStatusResponse.model_validate(result)

    # ── 12. GET /actions/work/{work_id} ────────────────────────────────

    def list_actions_by_work(self, work_id: str, actor_id: str) -> list:
        """列出与指定作品相关的所有维权行动."""
        AuditLog.log(self.db, "list_actions_by_work", f"Listed actions for work {work_id}", actor_id)

        task_ids = [t.id for t in self.db.query(MonitorTask).filter(MonitorTask.work_id == work_id).all()]
        result_ids = [
            mr.id for mr in self.db.query(MonitorResult).filter(MonitorResult.task_id.in_(task_ids)).all()
        ]

        if not result_ids:
            return []

        actions = (
            self.db.query(EnforcementAction)
            .filter(EnforcementAction.monitor_result_id.in_(result_ids))
            .order_by(EnforcementAction.created_at.desc())
            .all()
        )
        return [self._enrich_action_response(a) for a in actions]

    # ── 13. GET /templates ─────────────────────────────────────────────

    def list_templates(self, platform: Optional[str], jurisdiction: Optional[str], actor_id: str) -> list:
        """列出维权模板，支持可选过滤."""
        AuditLog.log(
            self.db, "list_templates",
            f"Listed templates (platform={platform}, jurisdiction={jurisdiction})", actor_id,
        )

        q = self.db.query(EnforcementTemplate)
        if platform:
            q = q.filter(EnforcementTemplate.platform == platform)
        if jurisdiction:
            q = q.filter(EnforcementTemplate.jurisdiction == jurisdiction)
        return q.all()

    # ── 14. POST /templates/seed ───────────────────────────────────────

    def seed_templates(self, actor_id: str, is_admin_fn) -> dict:
        """若模板为空，填充 3 个默认维权模板."""
        if not is_admin_fn(actor_id):
            raise HTTPException(403, "Forbidden: Only admin can seed templates")

        existing = self.db.query(EnforcementTemplate).count()
        if existing > 0:
            return {"status": "skipped", "message": "Templates already seeded", "count": existing}

        templates_data = [
            {
                "platform": "generic",
                "jurisdiction": "us",
                "action_type": "dmca",
                "title": "DMCA Takedown Notice",
                "body_template": (
                    "To Whom It May Concern,\n\n"
                    "I have a good faith belief that the use of the material '{{work_title}}' "
                    "on your platform constitutes copyright infringement.\n\n"
                    "Work Details:\n"
                    "- Title: {{work_title}}\n"
                    "- Hash: {{sha256}}\n"
                    "- File Type: {{work_file_type}}\n"
                    "- Date: {{date}}\n\n"
                    "Infringing URL: {{infringement_url}}\n\n"
                    "This work was created by and is owned by the undersigned. "
                    "The information provided is accurate and I consent to penalties for perjury.\n\n"
                    "Sincerely,\n{{author}}"
                ),
                "required_evidence": ["work_ownership_proof", "infringement_url", "identity_verification"],
                "filing_url": "https://www.copyright.gov/online/notice.html",
            },
            {
                "platform": "xiaohongshu",
                "jurisdiction": "cn",
                "action_type": "copyright",
                "title": "网络著作权侵权投诉通知书",
                "body_template": (
                    "贵平台您好，\n\n"
                    "本人系作品《{{work_title}}》的著作权人，"
                    "该作品的哈希值为 {{sha256}}，"
                    "文件类型为 {{work_file_type}}。\n\n"
                    "发现贵平台存在以下侵权行为：\n"
                    "侵权链接：{{infringement_url}}\n\n"
                    "根据《中华人民共和国著作权法"
                    "及相关法规，请贵平台在收到本通知"
                    "后及时删除或屏蔽侵权内容。\n\n"
                    "权属证明：已随本通知附上\n"
                    "身份证明：已随本通知附上\n"
                    "证据数量：{{evidence_count}}\n\n"
                    "此致\n"
                    "{{author}}\n"
                    "{{date}}"
                ),
                "required_evidence": ["身份证明", "权属证明", "侵权链接"],
                "filing_url": "",
            },
            {
                "platform": "instagram",
                "jurisdiction": "us",
                "action_type": "copyright",
                "title": "Instagram Copyright Report",
                "body_template": (
                    "I have a good faith belief that the use of the material '{{work_title}}' "
                    "on Instagram infringes my copyright.\n\n"
                    "Work Details:\n"
                    "- Title: {{work_title}}\n"
                    "- Hash: {{sha256}}\n"
                    "- File Type: {{work_file_type}}\n"
                    "- Date: {{date}}\n\n"
                    "Infringing Content URL: {{infringement_url}}\n\n"
                    "I am the exclusive rights holder of the copyrighted work.\n\n"
                    "Sincerely,\n{{author}}"
                ),
                "required_evidence": ["work_ownership_proof", "infringing_url"],
                "filing_url": "https://www.facebook.com/help/contact/260749600972847",
            },
        ]

        for td in templates_data:
            tpl = EnforcementTemplate(**td)
            self.db.add(tpl)

        self.db.commit()
        count = self.db.query(EnforcementTemplate).count()

        AuditLog.log(self.db, "seed_templates", f"Seeded {count} enforcement templates", actor_id)
        return {"status": "seeded", "message": f"Seeded {count} templates", "count": count}

    # ── Bridge: POST /actions/from-work/{work_id} ─────────────────────

    def create_action_from_work(self, work_id: str, actor_id: str) -> dict:
        """从作品直接启动维权流程的桥接端点."""
        AuditLog.log(
            self.db, "create_action_from_work", f"Created enforcement action for work {work_id}", actor_id,
        )
        return service_create_action_from_work(self.db, work_id, actor_id)
