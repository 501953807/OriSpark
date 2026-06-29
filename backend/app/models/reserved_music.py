"""音乐人 (v4) 预留数据模型.

Reserved for future music creator type.
v1: 建表+字段注释 "v4激活".
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship

from app.database import Base


def _uid():
    return uuid.uuid4().hex[:32]


# =============================================================================
# albums — 专辑/EP/Single (12.3.2)
# =============================================================================


class Album(Base):
    """专辑表.

    音乐人发布的专辑/EP/单曲集合.
    v4 激活.
    """
    __tablename__ = "albums"

    id = Column(String(32), primary_key=True, default=_uid)
    user_id = Column(String(32), nullable=False)
    title = Column(String(500), nullable=False)
    album_type = Column(String(20), nullable=False)  # album/ep/single
    isrc = Column(String(20), nullable=True)  # 国际标准录音编码
    cover_work_id = Column(String(32), nullable=True)  # 引用works表的封面
    label = Column(String(200), nullable=True)
    release_date = Column(DateTime, nullable=True)
    genre = Column(String(50), nullable=True)
    total_tracks = Column(Integer, default=0)
    duration_seconds = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_album_user", "user_id"),
        Index("idx_album_type", "album_type"),
    )


class AlbumTrack(Base):
    """专辑音轨表.

    专辑中的每首曲目，关联到具体的works录音作品.
    v4 激活.
    """
    __tablename__ = "album_tracks"

    id = Column(String(32), primary_key=True, default=_uid)
    album_id = Column(String(32), ForeignKey("albums.id"), nullable=False)
    work_id = Column(String(32), ForeignKey("works.id"), nullable=False)
    track_number = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    isrc = Column(String(20), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    is_explicit = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_at_album", "album_id"),
        Index("idx_at_work", "work_id"),
    )


# =============================================================================
# work_collaborators — Split Sheets (12.3.3)
# =============================================================================


class WorkCollaborator(Base):
    """作品合作者表.

    记录歌曲的词曲作者/制作人/演奏者及分成比例.
    v4 激活.
    """
    __tablename__ = "work_collaborators"

    id = Column(String(32), primary_key=True, default=_uid)
    work_id = Column(String(32), ForeignKey("works.id"), nullable=False)
    collaborator_name = Column(String(200), nullable=False)
    collaborator_role = Column(String(50), nullable=False)  # composer/lyricist/producer/performer
    share_percentage = Column(Float, nullable=True)  # 0-100
    isrc_share = Column(Float, nullable=True)  # 录音版税分成
    publishing_share = Column(Float, nullable=True)  # 词曲版税分成
    contact_email = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_wc_work", "work_id"),)


# =============================================================================
# distribution_releases — 音乐发行管理 (15.4.1)
# =============================================================================


class DistributionRelease(Base):
    """音乐发行表.

    向Spotify/Apple Music/网易云等平台分发的发行记录.
    v4 激活.
    """
    __tablename__ = "distribution_releases"

    id = Column(String(32), primary_key=True, default=_uid)
    user_id = Column(String(32), nullable=False)
    album_id = Column(String(32), ForeignKey("albums.id"), nullable=True)
    release_type = Column(String(20), nullable=False)  # album/single
    distributor = Column(String(100), nullable=True)  # tunecore/distrokid/cd baby/self
    status = Column(String(20), default="draft")  # draft/pending/released/withdrawn
    planned_date = Column(DateTime, nullable=True)
    released_date = Column(DateTime, nullable=True)
    barcode = Column(String(20), nullable=True)  # UPC/EAN
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_dr_user", "user_id"),
        Index("idx_dr_status", "status"),
    )


class DistroPlatform(Base):
    """分发平台映射表.

    某次发行对应的各音乐平台状态.
    v4 激活.
    """
    __tablename__ = "distro_platforms"

    id = Column(String(32), primary_key=True, default=_uid)
    release_id = Column(String(32), ForeignKey("distribution_releases.id"), nullable=False)
    platform_name = Column(String(50), nullable=False)  # spotify/apple_music/netease/tencent
    platform_track_id = Column(String(255), nullable=True)
    status = Column(String(20), default="pending")  # pending/accepted/rejected
    rejection_reason = Column(Text, nullable=True)
    live_url = Column(String(2000), nullable=True)
    synced_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_dp_release", "release_id"),
        Index("idx_dp_platform", "platform_name"),
    )


# =============================================================================
# sample_clearances — 采样授权 (15.4.2)
# =============================================================================


class SampleClearance(Base):
    """采样授权表.

    记录作品中使用的采样素材的版权 clearance 状态.
    v4 激活.
    """
    __tablename__ = "sample_clearances"

    id = Column(String(32), primary_key=True, default=_uid)
    work_id = Column(String(32), ForeignKey("works.id"), nullable=False)
    source_work_id = Column(String(32), nullable=True)  # 被采样的作品
    sample_description = Column(Text, nullable=True)  # "0.5秒钢琴和弦"
    cleared = Column(Boolean, default=False)
    clearance_type = Column(String(50), nullable=True)  # mechanical/_sync/master
    clearance_fee = Column(Float, nullable=True)
    cleared_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_sc_work", "work_id"),)
