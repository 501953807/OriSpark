"""维权证据包服务."""

import shutil
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.database import SessionLocal
from app.models.work import Work
from app.models.monitor import MonitorResult, EvidencePackage
from app.models.notary import NotaryRecord


def generate_evidence_package(
    work_id: str,
    result_ids: list[str],
    package_type: str = "complaint",
    output_dir: str = "data/certificates",
) -> Optional[str]:
    """生成维权证据包 ZIP 文件."""
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
    """生成投诉函模板."""
    letter = f"""投诉函

致: [平台名称/侵权方名称]

投诉人: [创作者姓名]
联系方式: [联系方式]

投诉事由: 侵犯著作权

侵权事实与理由:

本人是原创作品《{work.title}》的著作权人，该作品已于{work.created_at.strftime('%Y年%m月%d日') if work.created_at else '[日期]'}创作完成。"""

    if notary_info:
        letter += f"""
该作品已通过{notary_info.platform}平台进行区块链存证确认，
存证哈希: {notary_info.evidence_hash or work.sha256 or ''}
存证时间: {notary_info.confirmed_at.strftime('%Y-%m-%d %H:%M:%S') if notary_info.confirmed_at else ''}"""

    letter += """

近日发现以下平台/用户存在未经授权使用本人作品的行为, 具体如下:

"""
    for i, r in enumerate(results, 1):
        letter += f"""{i}. 侵权链接: {r.matched_url}
   相似度: {r.similarity:.1f}%
   发现时间: {r.found_at.strftime('%Y-%m-%d %H:%M:%S') if r.found_at else ''}

"""

    letter += """投诉请求:

1. 立即删除上述侵权内容;
2. 对侵权方进行处罚;
3. 保留追究法律责任的权利。

随函附上:
- 原创作品信息及哈希值
- 区块链存证记录
- 侵权截图/链接清单

此致

[署名]
[日期]
"""
    return letter


def generate_lawyer_letter(
    work: Work,
    results: list[MonitorResult],
    notary_info: Optional[NotaryRecord] = None,
) -> str:
    """生成律师函模板."""
    return f"""律师函

(XXXX) XX律函字第[编号]号

致: [侵权方名称]

XX律师事务所（以下简称"本所"）接受《{work.title}》著作权人[委托人姓名]（以下简称"委托人"）的委托，就贵方侵犯委托人著作权的行为，致函如下：

一、基本事实

委托人于{work.created_at.strftime('%Y年%m月%d日') if work.created_at else '[日期]'}创作完成作品《{work.title}》，对该作品享有完整的著作权。

{chr(10).join(f'{i+1}. 侵权链接: {r.matched_url} (相似度: {r.similarity:.1f}%)' for i, r in enumerate(results, 1))}

二、法律依据

根据《中华人民共和国著作权法》第四十七条，未经著作权人许可，复制、发行、信息网络传播其作品的，应当承担停止侵害、消除影响、赔礼道歉、赔偿损失等民事责任。

三、律师函告

1. 收到本函后 7 日内立即删除所有侵权内容；
2. 书面向委托人致歉并承诺不再侵权；
3. 赔偿委托人经济损失[金额]元。

如逾期未履行，本所将依法通过行政投诉、民事诉讼等途径维护委托人合法权益。

XX律师事务所
律师: [律师姓名]
日期: {datetime.now(timezone.utc).strftime('%Y年%m月%d日')}

附件: 原创作品证明、存证记录、侵权证据
"""
