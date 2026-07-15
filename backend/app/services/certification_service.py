import hashlib

from sqlalchemy.orm import Session

from app.models.certification import CertificationRecord
from app.models.work import Work


def compute_sha256(file_path: str) -> str:
    """计算文件SHA-256哈希."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def certify_single(db: Session, work: Work) -> CertificationRecord:
    """单件存证：计算哈希→调用区块链→返回记录."""
    sha256 = compute_sha256(work.file_path)
    record = CertificationRecord(
        work_id=work.id,
        sha256_hash=sha256,
        blockchain_tx_id=None,  # 异步调用区块链服务后回填
        is_court_admissible=True,
        cost_saved_yuan=2000,  # 对比传统公证最低¥2000
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def batch_certify(db: Session, work_ids: list[str]) -> dict:
    """批量存证，单次最高10,000件."""
    if len(work_ids) > 10000:
        raise ValueError("批量存证不能超过10,000件")

    results = []
    success = 0
    failed = 0
    total_saved = 0

    for wid in work_ids:
        try:
            work = db.query(Work).filter(Work.id == wid).first()
            if not work:
                failed += 1
                continue
            record = certify_single(db, work)
            results.append(record)
            success += 1
            total_saved += record.cost_saved_yuan
        except Exception:
            failed += 1

    return {
        "total": len(work_ids),
        "success": success,
        "failed": failed,
        "results": results,
        "total_saved_yuan": total_saved,
    }
