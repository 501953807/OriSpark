"""Seed data for public API endpoints — only inserts into existing tables."""

import uuid
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models.work import Work
from app.models.system import Notification


def seed_public_api():
    """Insert seed data into public API tables."""
    db = SessionLocal()

    try:
        # Check if already seeded
        existing_works = db.query(Work).count()
        if existing_works > 10:
            print("Already seeded, skipping.")
            return

        now = datetime.now()

        # Seed Works
        works_data = [
            {
                "id": uuid.uuid4().hex[:32],
                "title": "山水意境插画 — 春",
                "description": "中国传统山水风格插画，表现春天万物复苏的意境。采用数字水墨技法，融合现代构图理念。",
                "creator_type": "illustrator",
                "status": "active",
                "thumbnail_path": "/uploads/landscape_spring.png",
                "file_path": "/seed/landscape_spring.png",
                "file_name": "landscape_spring.png",
                "file_size": 0,
                "file_type": "image",
                "file_extension": "png",
                "mime_type": "image/png",
                "sha256": "0" * 64,
                "md5": "0" * 32,
                "import_mode": "full",
                "current_stage": "review",
                "created_at": now - timedelta(days=30),
            },
            {
                "id": uuid.uuid4().hex[:32],
                "title": "城市光影摄影集 — 东京",
                "description": "东京街头摄影系列，捕捉霓虹灯下的都市夜生活与日常人文瞬间。",
                "creator_type": "photographer",
                "status": "active",
                "thumbnail_path": "/uploads/tokyo_night.jpg",
                "file_path": "/seed/tokyo_night.jpg",
                "file_name": "tokyo_night.jpg",
                "file_size": 0,
                "file_type": "image",
                "file_extension": "jpg",
                "mime_type": "image/jpeg",
                "sha256": "0" * 64,
                "md5": "0" * 32,
                "import_mode": "full",
                "current_stage": "review",
                "created_at": now - timedelta(days=25),
            },
            {
                "id": uuid.uuid4().hex[:32],
                "title": "抽象几何装饰画",
                "description": "现代抽象风格装饰画，以几何图形和大胆色彩构建视觉节奏感。",
                "creator_type": "illustrator",
                "status": "active",
                "thumbnail_path": "/uploads/abstract_geometry.png",
                "file_path": "/seed/abstract_geometry.png",
                "file_name": "abstract_geometry.png",
                "file_size": 0,
                "file_type": "image",
                "file_extension": "png",
                "mime_type": "image/png",
                "sha256": "0" * 64,
                "md5": "0" * 32,
                "import_mode": "full",
                "current_stage": "review",
                "created_at": now - timedelta(days=20),
            },
            {
                "id": uuid.uuid4().hex[:32],
                "title": "非遗手工艺记录 — 景德镇陶瓷",
                "description": "景德镇传统制瓷工艺的影像记录，展现匠人精神与千年传承。",
                "creator_type": "video",
                "status": "active",
                "thumbnail_path": "/uploads/jingdezhen.jpg",
                "file_path": "/seed/jingdezhen.jpg",
                "file_name": "jingdezhen.jpg",
                "file_size": 0,
                "file_type": "image",
                "file_extension": "jpg",
                "mime_type": "image/jpeg",
                "sha256": "0" * 64,
                "md5": "0" * 32,
                "import_mode": "full",
                "current_stage": "review",
                "created_at": now - timedelta(days=15),
            },
            {
                "id": uuid.uuid4().hex[:32],
                "title": "儿童绘本系列 — 星空探险",
                "description": "原创儿童绘本，讲述小朋友在星空中的奇幻冒险旅程。",
                "creator_type": "illustrator",
                "status": "active",
                "thumbnail_path": "/uploads/stars_kids.png",
                "file_path": "/seed/stars_kids.png",
                "file_name": "stars_kids.png",
                "file_size": 0,
                "file_type": "image",
                "file_extension": "png",
                "mime_type": "image/png",
                "sha256": "0" * 64,
                "md5": "0" * 32,
                "import_mode": "full",
                "current_stage": "review",
                "created_at": now - timedelta(days=10),
            },
        ]

        for wd in works_data:
            work = Work(**wd)
            db.add(work)

        db.flush()

        # Seed Notifications
        notifications_data = [
            {
                "id": uuid.uuid4().hex[:32],
                "user_id": "all",
                "type": "announcement",
                "title": "平台v5.0更新公告",
                "content": "OriStudio v5.0 全新上线！新增合同市场、税务结算、分发回流等核心功能。",
                "channel": "in_app",
                "is_read": True,
                "created_at": now - timedelta(days=10),
            },
            {
                "id": uuid.uuid4().hex[:32],
                "user_id": "all",
                "type": "system",
                "title": "系统维护通知",
                "content": "计划于本周六凌晨2:00-4:00进行系统维护，届时服务可能短暂不可用。",
                "channel": "in_app",
                "is_read": False,
                "created_at": now - timedelta(days=3),
            },
        ]

        for nd in notifications_data:
            notification = Notification(**nd)
            db.add(notification)

        db.commit()
        print(f"Seeded: {len(works_data)} works, {len(notifications_data)} notifications")

    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_public_api()
