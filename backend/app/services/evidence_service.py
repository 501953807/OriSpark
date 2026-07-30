"""维权证据包服务."""

import shutil
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
import html  # 用于HTML转义，防止模板注入

from app.database import SessionLocal
from app.models.work import Work
from app.models.monitor import MonitorResult, EvidencePackage
from app.models.notary import NotaryRecord


def _sanitize_output_dir(output_dir: str) -> Path:
    """验证输出目录是否在允许的基目录下，防止路径遍历."""
    base = Path("data/certificates").resolve()
    target = Path(output_dir).resolve()

    if not str(target).startswith(str(base) + os.sep):
        raise ValueError(f"Output directory must be under {base}")

    return target


def generate_evidence_package(
    work_id: str,
    result_ids: list[str],
    package_type: str = "complaint",
    output_dir: str = "data/certificates",
) -> Optional[str]:
    """生成维权证据包 ZIP 文件."""
    # Validate output directory to prevent path traversal
    try:
        pkg_dir_base = _sanitize_output_dir(output_dir)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    db = SessionLocal()
    try:
        work = db.query(Work).filter(Work.id == work_id).first()
        if not work:
            return None

        results = db.query(MonitorResult).filter(
            MonitorResult.id.in_(result_ids)
        ).all()

        notary = db.query(NotaryRecord).filter(
            NotaryRecord.work_id == work_id,
            NotaryRecord.status == "confirmed",
        ).first()

        # 创建证据包目录
        pkg_dir = Path(output_dir) / f"evidence_{work_id}_{int(datetime.now(timezone.utc).timestamp())}"
        pkg_dir.mkdir(parents=True, exist_ok=True)

        # 1. 作品信息
        work_info = {
            "id": work.id,
            "title": work.title,
            "sha256": work.sha256,
            "file_name": work.file_name,
            "file_size": work.file_size,
            "created_at": work.created_at.isoformat() if work.created_at else None,
        }
        (pkg_dir / "work_info.json").write_text(json.dumps(work_info, ensure_ascii=False, indent=2))

        # 2. 侵权结果
        infringement_data = []
        for r in results:
            infringement_data.append({
                "url": r.matched_url,
                "title": r.matched_title,
                "similarity": r.similarity,
                "found_at": r.found_at.isoformat() if r.found_at else None,
                "status": r.status,
            })

        (pkg_dir / "infringement_results.json").write_text(
            json.dumps(infringement_data, ensure_ascii=False, indent=2)
        )

        # 3. 存证信息
        if notary:
            cert_data = {
                "platform": notary.platform,
                "evidence_hash": notary.evidence_hash,
                "transaction_hash": notary.transaction_hash,
                "confirmed_at": notary.confirmed_at.isoformat() if notary.confirmed_at else None,
                "certificate_id": notary.certificate_id,
            }
            (pkg_dir / "notary_record.json").write_text(
                json.dumps(cert_data, ensure_ascii=False, indent=2)
            )

        # 4. 生成投诉函模板 (TXT)
        complaint_template = generate_complaint_letter(work, results, notary)
        (pkg_dir / "complaint_letter.txt").write_text(complaint_template)

        # 5. 生成律师函模板 (TXT)
        lawyer_template = generate_lawyer_letter(work, results, notary)
        (pkg_dir / "lawyer_letter.txt").write_text(lawyer_template)

        # 6. 打包成 ZIP
        zip_path = str(pkg_dir) + ".zip"
        shutil.make_archive(str(pkg_dir), "zip", str(pkg_dir.parent), pkg_dir.name)

        # 清理临时目录
        shutil.rmtree(pkg_dir)

        return zip_path

    finally:
        db.close()


def generate_complaint_letter(
    work: Work,
    results: list[MonitorResult],
    notary_info: Optional[NotaryRecord] = None,
) -> str:
    """生成投诉函模板 — 所有用户可控内容均经过HTML转义，防止模板注入."""

    def esc(s: Any) -> str:
        """HTML实体转义，防止XSS和模板注入."""
        if s is None:
            return ""
        return html.escape(str(s))

    work_title_escaped = esc(work.title)
    created_at_str = work.created_at.strftime('%Y年%m月%d日') if work.created_at else '[日期]'
    created_at_escaped = esc(created_at_str)

    letter_parts = [
        "投诉函",
        "",
        "致: [平台名称/侵权方名称]",
        "",
        "投诉人: [创作者姓名]",
        "联系方式: [联系方式]",
        "",
        "投诉事由: 侵犯著作权",
        "",
        "侵权事实与理由:",
        "",
        f"本人是原创作品《{work_title_escaped}》的著作权人，该作品于{created_at_escaped}创作完成。",
    ]

    if notary_info:
        platform_escaped = esc(notary_info.platform or "")
        hash_escaped = esc(notary_info.evidence_hash or work.sha256 or "")
        confirmed_at_str = notary_info.confirmed_at.strftime('%Y-%m-%d %H:%M:%S') if notary_info.confirmed_at else ""
        confirmed_at_escaped = esc(confirmed_at_str)
        letter_parts.extend([
            "",
            f"该作品已通过{platform_escaped}平台进行区块链存证确认，",
            f"存证哈希: {hash_escaped}",
            f"存证时间: {confirmed_at_escaped}",
        ])

    letter_parts.extend([
        "",
        "近日发现以下平台/用户存在未经授权使用本人作品的行为，具体如下:",
        "",
    ])

    for i, r in enumerate(results, 1):
        url_escaped = esc(r.matched_url or "")
        sim_val = f"{r.similarity:.1f}" if r.similarity is not None else "?"
        sim_escaped = esc(sim_val)
        found_at_str = r.found_at.strftime('%Y-%m-%d %H:%M:%S') if r.found_at else ""
        found_at_escaped = esc(found_at_str)
        letter_parts.extend([
            f"{i}. 侵权链接: {url_escaped}",
            f"   相似度: {sim_escaped}%",
            f"   发现时间: {found_at_escaped}",
            "",
        ])

    letter_parts.extend([
        "",
        "投诉请求:",
        "",
        "1. 立即删除上述侵权内容;",
        "2. 对侵权方进行处罚;",
        "3. 保留追究法律责任的权利。",
        "",
        "随函附上:",
        "- 原创作品信息及哈希值",
        "- 区块链存证记录",
        "- 侵权截图/链接清单",
        "",
        "此致",
        "",
        "[署名]",
        "[日期]",
    ])

    return "\n".join(letter_parts)


def generate_lawyer_letter(
    work: Work,
    results: list[MonitorResult],
    notary_info: Optional[NotaryRecord] = None,
) -> str:
    """生成律师函模板 — 所有用户可控内容均经过HTML转义，防止模板注入."""

    def esc(s: Any) -> str:
        """HTML实体转义，防止XSS和模板注入."""
        if s is None:
            return ""
        return html.escape(str(s))

    work_title_escaped = esc(work.title)
    created_at_str = work.created_at.strftime('%Y年%m月%d日') if work.created_at else '[日期]'
    created_at_escaped = esc(created_at_str)

    # Build infringement list with escaped content
    infringement_lines = []
    for i, r in enumerate(results, 1):
        url_escaped = esc(r.matched_url or "")
        sim_val = f"{r.similarity:.1f}" if r.similarity is not None else "?"
        sim_escaped = esc(sim_val)
        line = f"{i+1}. 侵权链接: {url_escaped} (相似度: {sim_escaped}%)"
        infringement_lines.append(line)

    lines_text = "\n".join(infringement_lines)

    now_str = datetime.now(timezone.utc).strftime('%Y年%m月%d日')
    now_escaped = esc(now_str)

    # Build the letter using string joining to avoid f-string injection risks
    parts = [
        "律师函",
        "",
        "(XXXX) XX律函字第[编号]号",
        "",
        "致: [侵权方名称]",
        "",
        'XX律师事务所（以下简称"本所"）接受《{0}》著作权人[委托人姓名]（以下简称"委托人"）的委托，就贵方侵犯委托人著作权的行为，致函如下：'.format(work_title_escaped),
        "",
        "一、基本事实",
        "",
        f"委托人于{created_at_escaped}创作完成作品《{work_title_escaped}》，对该作品享有完整的著作权。",
        "",
        lines_text,
        "",
        "二、法律依据",
        "",
        "根据《中华人民共和国著作权法》第四十七条，未经著作权人许可，复制、发行、信息网络传播其作品的，应当承担停止侵害、消除影响、赔礼道歉、赔偿损失等民事责任。",
        "",
        "三、律师函告",
        "",
        "1. 收到本函后 7 日内立即删除所有侵权内容；",
        "2. 书面向委托人致歉并承诺不再侵权；",
        "3. 赔偿委托人经济损失[金额]元。",
        "",
        "如逾期未履行，本所将依法通过行政投诉、民事诉讼等途径维护委托人合法权益。",
        "",
        "XX律师事务所",
        "律师: [律师姓名]",
        f"日期: {now_escaped}",
        "",
        "附件: 原创作品证明、存证记录、侵权证据",
    ]

    return "\n".join(parts)
