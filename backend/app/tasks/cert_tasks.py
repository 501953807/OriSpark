"""证书生成异步任务."""

from pathlib import Path

from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, max_retries=2)
def generate_certificate_async(self, notary_record_id: str):
    """异步生成存证 PDF 证书."""
    from app.database import SessionLocal
    from app.models.notary import NotaryRecord, Certificate
    from app.models.work import Work
    from app.services.certificate_service import generate_certificate_pdf

    db = SessionLocal()
    try:
        record = db.query(NotaryRecord).filter(
            NotaryRecord.id == notary_record_id
        ).first()

        if not record:
            return {"status": "not_found"}

        work = db.query(Work).filter(Work.id == record.work_id).first()

        cert_dir = Path("data/certificates")
        cert_dir.mkdir(parents=True, exist_ok=True)

        cert_path = generate_certificate_pdf(
            work=work,
            notary_record=record,
            output_dir=str(cert_dir),
        )

        # 创建证书记录
        certificate = Certificate(
            notary_record_id=record.id,
            cert_path=cert_path,
            qr_code=record.qr_code_url,
            template_name="default",
            expires_at=record.expires_at,
        )
        db.add(certificate)

        # 更新作品状态
        work.is_verified = True

        db.commit()
        return {
            "status": "completed",
            "cert_path": cert_path,
        }
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=30)
    finally:
        db.close()


@celery_app.task
def batch_generate_certificates(record_ids: list[str]) -> dict:
    """批量生成证书."""
    results = {}
    for rid in record_ids:
        task = generate_certificate_async.delay(rid)
        results[rid] = task.id
    return {"task_ids": results}
