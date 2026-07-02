"""分成协议模型.

Musician v4: Split Sheets — 创作分成协议管理.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Index, JSON

from app.database import Base


def _uid():
    return uuid.uuid4().hex[:32]


class SplitSheet(Base):
    """分成协议表.

    记录音乐发行的词曲/录音版权分成比例.
    """
    __tablename__ = "split_sheets"

    id = Column(String(32), primary_key=True, default=_uid)
    music_release_id = Column(String(32), ForeignKey("music_releases.id"), nullable=False)
    title = Column(String(200), nullable=False)
    splits = Column(JSON, nullable=True)  # [{"name": "张三", "share": 60}, {"name": "李四", "share": 40}]
    publishing_share = Column(Float, nullable=True)  # 词曲版权分成
    master_share = Column(Float, nullable=True)  # 录音版权分成
    status = Column(String(20), default="draft")  # draft/signing/signed/active
    signed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_split_status", "status"),
    )
