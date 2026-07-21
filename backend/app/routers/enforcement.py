"""维权流水线 API 路由 - actions CRUD, evidence package, complaint submission, templates."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.enforcement import (
    ComplaintMaterial,
    EnforcementAction,
    EnforcementTemplate,
)
from app.models.monitor import MonitorResult, MonitorTask
from app.models.work import Work
from app.schemas.enforcement import (
    ComplaintSubmitRequest,
    ComplaintSubmitResponse,
    EnforcementActionCreate,
    EnforcementActionResponse,
    EnforcementActionUpdate,
    EnforcementTemplateResponse,
)
from app.services.enforcement import (
    build_evidence_package,
    generate_complaint_letter,
    generate_pdf_package,
    resolve_template_variables,
    update_action_status as service_update_action_status,
    create_action_from_work as service_create_action_from_work,
)

router = APIRouter(prefix="/enforcement", tags=["Enforcement"])


# ── helpers ───────────────────────────────────────────────────────


def _enrich_action_response(action: EnforcementAction, db: Session) -> EnforcementActionResponse:
    """Build an EnforcementActionResponse with embedded work + monitor info."""
    result = EnforcementActionResponse.model_validate(action)

    # Resolve work via monitor_result -> monitor_task -> work
    mr = (
        db.query(MonitorResult)
        .filter(MonitorResult.id == action.monitor_result_id)
        .first()
    )
    if mr:
        mt = (
            db.query(MonitorTask)
            .filter(MonitorTask.id == mr.task_id)
            .first()
        )
        if mt:
            w = db.query(Work).filter(Work.id == mt.work_id).first()
            if w:
                result.work_id = w.id
                result.work_title = w.title
                result.work_file_type = w.file_type
        result.infringement_url = mr.matched_url or ""
        result.similarity_score = mr.similarity

    return result


# ── 1. POST /actions ─────────────────────────────────────────────


@router.post("/actions", response_model=EnforcementActionResponse, status_code=201)
async def create_action(
    payload: EnforcementActionCreate,
    db: Session = Depends(get_db),
):
    """Create an enforcement action from a monitor result."""
    mr = db.query(MonitorResult).filter(MonitorResult.id == payload.monitor_result_id).first()
    if not mr:
        raise HTTPException(status_code=404, detail="MonitorResult not found")

    action_id = uuid.uuid4().hex
    action = EnforcementAction(
        id=action_id,
        monitor_result_id=payload.monitor_result_id,
        action_type=payload.action_type,
        platform=payload.platform,
        status="pending_review",
    )

    if payload.template_id:
        tpl = db.query(EnforcementTemplate).filter(
            EnforcementTemplate.id == payload.template_id
        ).first()
        if not tpl:
            raise HTTPException(status_code=404, detail="Template not found")
        action.template_used = tpl.title

    db.add(action)
    db.commit()
    db.refresh(action)

    return _enrich_action_response(action, db)


# ── 2. GET /actions/{action_id} ──────────────────────────────────


@router.get("/actions/{action_id}", response_model=EnforcementActionResponse)
async def get_action(action_id: str, db: Session = Depends(get_db)):
    """Get enforcement action detail with embedded work info."""
    action = db.query(EnforcementAction).filter(EnforcementAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Enforcement action not found")
    return _enrich_action_response(action, db)


# ── 3. PATCH /actions/{action_id} ────────────────────────────────


@router.patch("/actions/{action_id}", response_model=EnforcementActionResponse)
async def update_action(
    action_id: str,
    payload: EnforcementActionUpdate,
    db: Session = Depends(get_db),
):
    """Update enforcement action (state machine enforced)."""
    action = db.query(EnforcementAction).filter(EnforcementAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Enforcement action not found")

    if payload.status:
        kwargs = {}
        if payload.status == "complaint_filed":
            kwargs["sent_at"] = datetime.utcnow()
        elif payload.status == "resolved":
            kwargs["resolved_at"] = datetime.utcnow()

        action = service_update_action_status(db, action_id, new_status=payload.status, **kwargs)

    # Apply non-status fields
    for field in ["complaint_text", "template_used", "response_text", "resolution_type",
                  "compensation_amount", "notes"]:
        value = getattr(payload, field, None)
        if value is not None:
            setattr(action, field, value)

    action.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(action)

    return _enrich_action_response(action, db)


# ── 4. POST /actions/{action_id}/evidence ────────────────────────


@router.post("/actions/{action_id}/evidence")
async def gather_evidence(
    action_id: str,
    db: Session = Depends(get_db),
):
    """Gather evidence package and create complaint material."""
    action = db.query(EnforcementAction).filter(EnforcementAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Enforcement action not found")

    mr = db.query(MonitorResult).filter(MonitorResult.id == action.monitor_result_id).first()
    if not mr:
        raise HTTPException(status_code=404, detail="MonitorResult not found")

    mt = db.query(MonitorTask).filter(MonitorTask.id == mr.task_id).first()
    if not mt:
        raise HTTPException(status_code=404, detail="MonitorTask not found")

    evidence = build_evidence_package(db, mt.work_id)
    zip_path = generate_pdf_package(evidence)

    material = ComplaintMaterial(
        enforcement_action_id=action_id,
        material_type="pdf_package",
        material_path=zip_path,
    )
    db.add(material)

    service_update_action_status(db, action_id, new_status="evidence_gathered")
    db.refresh(action)

    return {
        "status": "evidence_gathered",
        "material_path": zip_path,
        "evidence": evidence,
    }


# ── 5. POST /actions/{action_id}/submit ──────────────────────────


@router.post("/actions/{action_id}/submit", response_model=ComplaintSubmitResponse)
async def submit_complaint(
    action_id: str,
    _payload: ComplaintSubmitRequest = ComplaintSubmitRequest(),
    db: Session = Depends(get_db),
):
    """Submit complaint using template variables."""
    action = db.query(EnforcementAction).filter(EnforcementAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Enforcement action not found")

    mr = db.query(MonitorResult).filter(MonitorResult.id == action.monitor_result_id).first()
    if not mr:
        raise HTTPException(status_code=404, detail="MonitorResult not found")

    mt = db.query(MonitorTask).filter(MonitorTask.id == mr.task_id).first()
    if not mt:
        raise HTTPException(status_code=404, detail="MonitorTask not found")

    work = db.query(Work).filter(Work.id == mt.work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")

    evidence = build_evidence_package(db, mt.work_id)

    # Load template
    template_body = ""
    prefilled_url = None
    if action.template_used:
        tpl = db.query(EnforcementTemplate).filter(
            EnforcementTemplate.title == action.template_used
        ).first()
        if tpl:
            template_body = tpl.body_template
            prefilled_url = tpl.filing_url

    if not template_body:
        # Fallback generic template
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

    complaint_text = generate_complaint_letter(template_body, evidence.get("work_info", {}), evidence)

    # Create complaint material
    variables = resolve_template_variables(template_body, evidence.get("work_info", {}))
    material = ComplaintMaterial(
        enforcement_action_id=action_id,
        material_type="prefilled_url",
        material_path=prefilled_url or "",
        variables={"complaint_text": complaint_text},
    )
    db.add(material)

    service_update_action_status(db, action_id, new_status="complaint_filed", sent_at=datetime.utcnow())
    db.refresh(action)

    return ComplaintSubmitResponse(
        action_id=action_id,
        complaint_text=complaint_text,
        material_path=material.material_path,
        prefilled_url=prefilled_url,
        status=action.status,
    )


# ── 6. GET /templates ────────────────────────────────────────────


@router.get("/templates", response_model=list[EnforcementTemplateResponse])
async def list_templates(
    platform: str | None = Query(None),
    jurisdiction: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """List enforcement templates with optional filters."""
    q = db.query(EnforcementTemplate)
    if platform:
        q = q.filter(EnforcementTemplate.platform == platform)
    if jurisdiction:
        q = q.filter(EnforcementTemplate.jurisdiction == jurisdiction)
    return q.all()


# ── 7. POST /templates/seed ──────────────────────────────────────


@router.post("/templates/seed")
async def seed_templates(db: Session = Depends(get_db)):
    """Seed 3 default enforcement templates if none exist."""
    existing = db.query(EnforcementTemplate).count()
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
                "根据《中华人民共和国著作权法》"
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
        db.add(tpl)

    db.commit()

    count = db.query(EnforcementTemplate).count()
    return {"status": "seeded", "message": f"Seeded {count} templates", "count": count}


# ── 8. POST /actions/from-work/{work_id} ────────────────────────


@router.post("/actions/from-work/{work_id}")
async def create_action_from_work_endpoint(
    work_id: str,
    db: Session = Depends(get_db),
):
    """Bridge endpoint: create enforcement actions directly from a work."""
    result = service_create_action_from_work(db, work_id)
    return result


# ── 9. GET /actions/by-work/{work_id} ──────────────────────────


@router.get("/actions/by-work/{work_id}")
async def list_actions_by_work(
    work_id: str,
    db: Session = Depends(get_db),
):
    """List all enforcement actions linked to a work."""
    task_ids = [
        t.id for t in db.query(MonitorTask.id).filter(
            MonitorTask.work_id == work_id
        ).all()
    ]
    result_ids = [
        mr.id for mr in db.query(MonitorResult.id).filter(
            MonitorResult.task_id.in_(task_ids)
        ).all()
    ]
    if not result_ids:
        return []
    actions = (
        db.query(EnforcementAction)
        .filter(EnforcementAction.monitor_result_id.in_(result_ids))
        .order_by(EnforcementAction.created_at.desc())
        .all()
    )
    return [_enrich_action_response(a, db) for a in actions]
