"""合约到期提醒和报告生成任务."""

import logging
from datetime import datetime, timedelta, timezone

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
def check_contract_expirations():
    """检查合约到期提醒 (7天/3天/1天)."""
    from app.database import SessionLocal
    from app.models.contract import ContractInstance
    from app.utils.audit import AuditLog

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        reminders = []

        for days_offset, label in [(7, "7天"), (3, "3天"), (1, "1天")]:
            target = now + timedelta(days=days_offset)
            contracts = db.query(ContractInstance).filter(
                ContractInstance.status == "active",
                ContractInstance.expires_at >= target - timedelta(hours=12),
                ContractInstance.expires_at < target + timedelta(hours=12),
            ).all()

            for contract in contracts:
                # 检查是否已发送过提醒
                existing = db.query(AuditLog).filter(
                    AuditLog.action == f"contract_expire_reminder_{days_offset}d",
                    AuditLog.detail.like(f"%{contract.id}%"),
                ).first()
                if existing:
                    continue

                reminders.append({
                    "contract_id": contract.id,
                    "title": contract.title,
                    "days": days_offset,
                    "expires_at": contract.expires_at.isoformat(),
                })
                # 记录提醒
                AuditLog.log(
                    db,
                    f"contract_expire_reminder_{days_offset}d",
                    f"Contract {contract.id} expires in {days_offset} days",
                    contract.creator_id or "system",
                )

        db.commit()
        logger.info(f"Contract expiration check: {len(reminders)} reminders sent")
        return {"status": "completed", "reminders_count": len(reminders)}
    except Exception as e:
        db.rollback()
        logger.error(f"Contract expiration check failed: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@celery_app.task
def generate_weekly_report():
    """生成周报."""
    from app.database import SessionLocal
    from app.models.system import Report
    from app.utils.audit import AuditLog

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        week_start = now - timedelta(days=now.weekday() + 7)
        week_end = week_start + timedelta(days=7)

        report = Report(
            type="weekly",
            period_start=week_start.isoformat(),
            period_end=week_end.isoformat(),
            status="draft",
        )
        db.add(report)
        db.commit()

        AuditLog.log(db, "generate_weekly_report", f"Weekly report generated: {report.id}")
        logger.info(f"Weekly report generated: {report.id}")
        return {"status": "completed", "report_id": report.id}
    except Exception as e:
        db.rollback()
        logger.error(f"Weekly report generation failed: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@celery_app.task
def generate_monthly_report():
    """生成月报."""
    from app.database import SessionLocal
    from app.models.system import Report
    from app.utils.audit import AuditLog

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        report = Report(
            type="monthly",
            period_start=month_start.isoformat(),
            period_end=month_end.isoformat(),
            status="draft",
        )
        db.add(report)
        db.commit()

        AuditLog.log(db, "generate_monthly_report", f"Monthly report generated: {report.id}")
        logger.info(f"Monthly report generated: {report.id}")
        return {"status": "completed", "report_id": report.id}
    except Exception as e:
        db.rollback()
        logger.error(f"Monthly report generation failed: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()
