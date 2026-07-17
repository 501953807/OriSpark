"""维权服务层 — 证据包构建、投诉信生成、状态机流转."""

import json
import os
import shutil
import zipfile
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.enforcement import EnforcementAction, EnforcementTemplate
from app.models.work import Work
from app.models.notary import NotaryRecord, C2PARecord
from app.models.ai_session import AiCreationSession
from app.models.work import WorkVersion
from app.models.monitor import MonitorTask, MonitorResult
from fastapi import HTTPException


# ── 维权行动状态机 ──────────────────────────────────────────────

VALID_TRANSITIONS: Dict[str, set] = {
    "pending_review": {"confirmed", "pending_review"},
    "confirmed": {"evidence_gathered", "pending_review"},
    "evidence_gathered": {"complaint_filed", "confirmed"},
    "complaint_filed": {"resolved"},
    "resolved": set(),  # 终态
}


# ── 1. build_evidence_package ───────────────────────────────────

def build_evidence_package(db: Session, work_id: str) -> dict:
    """聚合指定作品的所有维权证据数据."""

    # works
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")

    work_info = {
        "id": work.id,
        "title": work.title,
        "file_type": work.file_type,
        "sha256": work.sha256 or "",
        "file_path": work.file_path,
        "file_name": work.file_name,
        "file_size": work.file_size,
        "status": work.status,
        "is_verified": work.is_verified,
        "custom_metadata": work.custom_metadata or {},
        "created_at": work.created_at.isoformat() if work.created_at else None,
    }

    # notary_records
    notary_records = [
        {
            "platform": r.platform,
            "transaction_hash": r.transaction_hash or "",
            "confirmed_at": r.confirmed_at.isoformat() if r.confirmed_at else None,
            "status": r.status,
            "certificate_id": r.certificate_id or "",
            "blockchain": r.blockchain or "",
        }
        for r in db.query(NotaryRecord).filter(NotaryRecord.work_id == work_id).all()
    ]

    # c2pa_records
    c2pa_manifests = [
        {
            "manifest_json": r.manifest_json or {},
            "embedded_at": r.embedded_at.isoformat() if r.embedded_at else None,
            "is_active": r.is_active,
        }
        for r in db.query(C2PARecord).filter(C2PARecord.work_id == work_id).all()
    ]

    # ai_creation_sessions
    ai_sessions = [
        {
            "prompt": r.prompt or "",
            "tools_used": r.parameters or {},
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "tool_name": r.tool_name or "",
            "model_name": r.model_name or "",
        }
        for r in db.query(AiCreationSession).filter(AiCreationSession.work_id == work_id).all()
    ]

    # work_versions
    work_versions = [
        {
            "version_num": v.version_num,
            "file_path": v.file_path,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in db.query(WorkVersion).filter(WorkVersion.work_id == work_id).all()
    ]

    # infringement evidence: monitor_results joined via monitor_tasks
    task_ids = [
        t.id for t in db.query(MonitorTask.id).filter(
            MonitorTask.work_id == work_id,
        ).all()
    ]
    infringement_evidence = []
    if task_ids:
        results = (
            db.query(MonitorResult)
            .filter(
                MonitorResult.task_id.in_(task_ids),
                MonitorResult.status.in_(["infringing", "pending_review"]),
            )
            .all()
        )
        infringement_evidence = [
            {
                "matched_url": r.matched_url,
                "similarity": r.similarity or 0.0,
                "screenshot_path": r.screenshot_path or "",
                "matched_title": r.matched_title or "",
                "status": r.status,
                "found_at": r.found_at.isoformat() if r.found_at else None,
            }
            for r in results
        ]

    return {
        "work_info": work_info,
        "sha256": work_info["sha256"],
        "notary_records": notary_records,
        "c2pa_manifests": c2pa_manifests,
        "ai_sessions": ai_sessions,
        "work_versions": work_versions,
        "infringement_evidence": infringement_evidence,
    }


# ── 2. generate_pdf_package ─────────────────────────────────────

def generate_pdf_package(evidence: dict, output_dir: str = "data/enforcement") -> str:
    """将证据聚合结果打包为 ZIP 归档.

    Returns:
        ZIP 文件路径
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    zip_path = os.path.join(output_dir, f"evidence_{timestamp}.zip")

    # 准备文本摘要
    summary_lines = [
        "=" * 60,
        "EVIDENCE SUMMARY",
        "=" * 60,
        "",
        f"Work Title:      {evidence['work_info'].get('title', 'N/A')}",
        f"File Type:       {evidence['work_info'].get('file_type', 'N/A')}",
        f"SHA256:          {evidence.get('sha256', 'N/A')}",
        f"Verified:        {evidence['work_info'].get('is_verified', False)}",
        "",
        "--- Infringement Evidence ---",
    ]
    for item in evidence.get("infringement_evidence", []):
        summary_lines.append(
            f"  URL: {item.get('matched_url', 'N/A')}  "
            f"Similarity: {item.get('similarity', 0):.1f}%  "
            f"Status: {item.get('status', 'N/A')}"
        )
    summary_lines.extend(["", "--- Notary Records ---"])
    for nr in evidence.get("notary_records", []):
        summary_lines.append(
            f"  Platform: {nr.get('platform', 'N/A')}  "
            f"Hash: {nr.get('transaction_hash', 'N/A')[:16]}...  "
            f"Status: {nr.get('status', 'N/A')}"
        )
    summary_lines.append("")

    summary_text = "\n".join(summary_lines)

    # 写入临时目录结构再打包
    staging_dir = os.path.join(output_dir, f"_staging_{timestamp}")
    os.makedirs(staging_dir, exist_ok=True)
    os.makedirs(os.path.join(staging_dir, "infringement_evidence"), exist_ok=True)

    # 文本文件
    with open(os.path.join(staging_dir, "evidence_summary.txt"), "w", encoding="utf-8") as f:
        f.write(summary_text)

    # JSON 文件
    json_files = {
        "work_metadata.json": evidence.get("work_info", {}),
        "notary_records.json": evidence.get("notary_records", []),
        "c2pa_manifests.json": evidence.get("c2pa_manifests", []),
        "ai_sessions.json": evidence.get("ai_sessions", []),
        "work_versions.json": evidence.get("work_versions", []),
    }
    for fname, data in json_files.items():
        with open(os.path.join(staging_dir, fname), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    # 截图副本
    for item in evidence.get("infringement_evidence", []):
        screenshot = item.get("screenshot_path", "")
        if screenshot and os.path.isfile(screenshot):
            dest = os.path.join(
                staging_dir, "infringement_evidence",
                os.path.basename(screenshot),
            )
            shutil.copy2(screenshot, dest)

    # 创建 ZIP
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(staging_dir):
            for fname in files:
                full = os.path.join(root, fname)
                arcname = os.path.relpath(full, staging_dir)
                zf.write(full, arcname)

    # 清理临时目录
    shutil.rmtree(staging_dir, ignore_errors=True)

    return zip_path


# ── 3. resolve_template_variables ───────────────────────────────

def resolve_template_variables(body_template: str, variables: dict) -> str:
    """替换 {{key}} 占位符为变量值.

    缺失的 key 保留原占位符不报错.
    """
    result = body_template
    for key, value in variables.items():
        placeholder = "{{" + key + "}}"
        if placeholder in result:
            result = result.replace(placeholder, str(value))
    return result


# ── 4. generate_complaint_letter ────────────────────────────────

def generate_complaint_letter(template_body: str, work_info: dict, evidence: dict) -> str:
    """根据作品信息和证据数据生成投诉信正文."""

    infringement_list = evidence.get("infringement_evidence", [])
    first_url = ""
    if infringement_list:
        first_url = infringement_list[0].get("matched_url", "")

    notary_count = len(evidence.get("notary_records", []))
    c2pa_count = len(evidence.get("c2pa_manifests", []))
    ai_count = len(evidence.get("ai_sessions", []))

    custom_meta = work_info.get("custom_metadata", {})
    if isinstance(custom_meta, str):
        try:
            custom_meta = json.loads(custom_meta)
        except (json.JSONDecodeError, TypeError):
            custom_meta = {}

    if not isinstance(custom_meta, dict):
        custom_meta = {}

    author = custom_meta.get("author", "OriStudio Creator")
    if not author:
        author = "OriStudio Creator"

    variables = {
        "work_title": work_info.get("title", "Unknown Work"),
        "author": author,
        "sha256": work_info.get("sha256", ""),
        "infringement_url": first_url,
        "platform": "generic",
        "date": date.today().isoformat(),
        "evidence_count": notary_count + c2pa_count + ai_count,
        "work_file_type": work_info.get("file_type", "image"),
    }

    return resolve_template_variables(template_body, variables)


# ── 5. update_action_status ─────────────────────────────────────

def update_action_status(
    db: Session,
    action_id: str,
    new_status: str,
    **kwargs: Any,
) -> EnforcementAction:
    """按状态机规则更新维权行动状态.

    Raises:
        HTTPException(400): 状态转换不合法
    """
    action = db.query(EnforcementAction).filter(
        EnforcementAction.id == action_id,
    ).first()
    if not action:
        raise HTTPException(status_code=404, detail="Enforcement action not found")

    current_status = action.status
    allowed = VALID_TRANSITIONS.get(current_status, set())

    if new_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid status transition from '{current_status}' to '{new_status}'. "
                f"Allowed transitions: {sorted(allowed) or ['none (terminal state)']}"
            ),
        )

    for field, value in kwargs.items():
        if hasattr(action, field):
            setattr(action, field, value)

    action.status = new_status
    action.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(action)
    return action
