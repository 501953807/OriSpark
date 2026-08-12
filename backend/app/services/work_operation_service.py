"""作品公开可运营状态服务.

v6.0: 创作者可将作品设为「公开可运营」，让运营者在 frontend-nuxt 中发现。
"""

from sqlalchemy.orm import Session

from app.models.work import Work
from app.models.operation_cooperation import OperationCooperation


class WorkOperationService:
    """作品公开可运营状态管理服务."""

    @staticmethod
    def toggle_operation_public(db: Session, work_id: str, user_id: str) -> Work:
        """切换作品的公开可运营状态。

        只有创作者本人可以操作。
        切换为公开时，自动建立 OperationCooperation 记录。
        切换为不公开时，清除 operation_agreement_id。

        Args:
            db: 数据库会话
            work_id: 作品 ID
            user_id: 当前用户 ID（必须是创作者）

        Returns:
            更新后的 Work 对象

        Raises:
            HTTPException: 作品不存在 / 非创作者 / 作品无创作者
        """
        work = db.query(Work).filter(Work.id == work_id).first()
        if not work:
            raise ValueError("作品不存在")

        if not work.creator_id:
            raise ValueError("作品无创作者")

        if work.creator_id != user_id:
            raise ValueError("只有创作者可以操作")

        # 切换状态
        work.work_operation_public = not work.work_operation_public

        if work.work_operation_public:
            # 若已有 pending 合作，关联其 ID；否则清空
            existing = (
                db.query(OperationCooperation)
                .filter(
                    OperationCooperation.work_id == work_id,
                    OperationCooperation.status == "pending",
                )
                .first()
            )
            work.operation_agreement_id = existing.id if existing else None
        else:
            work.operation_agreement_id = None

        db.commit()
        db.refresh(work)
        return work

    @staticmethod
    def list_operation_public_works(
        db: Session,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        """运营者发现公开作品列表.

        只返回 work_operation_public=True 的作品。

        Args:
            db: 数据库会话
            page: 页码（从 1 开始）
            limit: 每页数量

        Returns:
            分页结果
        """
        query = db.query(Work).filter(Work.work_operation_public == True)  # noqa: E712

        total = query.count()
        offset = (page - 1) * limit
        items = query.order_by(Work.created_at.desc()).offset(offset).limit(limit).all()

        total_pages = max(1, (total + limit - 1) // limit)

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": limit,
            "total_pages": total_pages,
        }

    @staticmethod
    def get_operation_public_work(db: Session, work_id: str) -> Work | None:
        """查询单个公开作品（供运营者详情查看）."""
        return (
            db.query(Work)
            .filter(Work.id == work_id, Work.work_operation_public == True)  # noqa: E712
            .first()
        )
