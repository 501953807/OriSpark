"""音乐人 API Pydantic schemas.

Musician v4: Albums, Music Releases, Split Sheets.
"""

from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field


# ============================================================================
# Album schemas
# ============================================================================


class AlbumCreate(BaseModel):
    """创建专辑请求."""
    title: str = Field(..., min_length=1, max_length=200)
    album_type: str = Field(default="single", pattern="^(single|ep|album|compilation)$")
    release_date: Optional[datetime] = None
    cover_art_path: Optional[str] = Field(None, max_length=500)
    label: Optional[str] = Field(None, max_length=200)
    total_tracks: Optional[int] = None
    duration_seconds: Optional[int] = None


class AlbumUpdate(BaseModel):
    """更新专辑请求."""
    title: Optional[str] = Field(None, max_length=200)
    album_type: Optional[str] = Field(None, pattern="^(single|ep|album|compilation)$")
    release_date: Optional[datetime] = None
    cover_art_path: Optional[str] = Field(None, max_length=500)
    label: Optional[str] = Field(None, max_length=200)
    total_tracks: Optional[int] = None
    duration_seconds: Optional[int] = None


class AlbumSchema(BaseModel):
    """专辑完整响应."""
    model_config = {"from_attributes": True}

    id: str
    title: str
    album_type: str
    release_date: Optional[datetime] = None
    cover_art_path: Optional[str] = None
    label: Optional[str] = None
    total_tracks: Optional[int] = None
    duration_seconds: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============================================================================
# MusicRelease schemas
# ============================================================================


class MusicReleaseCreate(BaseModel):
    """创建音乐发行请求."""
    title: str = Field(..., min_length=1, max_length=200)
    album_id: Optional[str] = None
    work_variant_id: Optional[str] = None
    isrc: Optional[str] = Field(None, max_length=12)
    audio_file_path: Optional[str] = Field(None, max_length=500)
    duration_seconds: Optional[int] = None
    bitrate: Optional[int] = None
    format: str = Field(default="mp3", pattern="^(mp3|flac|wav)$")
    genre: Optional[str] = Field(None, max_length=50)
    mood: Optional[str] = Field(None, max_length=50)
    bpm: Optional[int] = None
    distribution_status: str = Field(default="pending", pattern="^(pending|distributing|distributed)$")


class MusicReleaseUpdate(BaseModel):
    """更新音乐发行请求."""
    title: Optional[str] = Field(None, max_length=200)
    album_id: Optional[str] = None
    work_variant_id: Optional[str] = None
    isrc: Optional[str] = Field(None, max_length=12)
    audio_file_path: Optional[str] = Field(None, max_length=500)
    duration_seconds: Optional[int] = None
    bitrate: Optional[int] = None
    format: Optional[str] = Field(None, pattern="^(mp3|flac|wav)$")
    genre: Optional[str] = Field(None, max_length=50)
    mood: Optional[str] = Field(None, max_length=50)
    bpm: Optional[int] = None
    distribution_status: Optional[str] = Field(None, pattern="^(pending|distributing|distributed)$")


class MusicReleaseSchema(BaseModel):
    """音乐发行完整响应."""
    model_config = {"from_attributes": True}

    id: str
    title: str
    album_id: Optional[str] = None
    work_variant_id: Optional[str] = None
    isrc: Optional[str] = None
    audio_file_path: Optional[str] = None
    duration_seconds: Optional[int] = None
    bitrate: Optional[int] = None
    format: str
    genre: Optional[str] = None
    mood: Optional[str] = None
    bpm: Optional[int] = None
    distribution_status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============================================================================
# SplitSheet schemas
# ============================================================================


class SplitSheetCreate(BaseModel):
    """创建分成协议请求."""
    music_release_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=200)
    splits: Optional[list[dict]] = None
    publishing_share: Optional[float] = None
    master_share: Optional[float] = None
    status: str = Field(default="draft", pattern="^(draft|signing|signed|active)$")


class SplitSheetUpdate(BaseModel):
    """更新分成协议请求."""
    title: Optional[str] = Field(None, max_length=200)
    splits: Optional[list[dict]] = None
    publishing_share: Optional[float] = None
    master_share: Optional[float] = None
    status: Optional[str] = Field(None, pattern="^(draft|signing|signed|active)$")
    signed_at: Optional[datetime] = None


class SplitSheetSchema(BaseModel):
    """分成协议完整响应."""
    model_config = {"from_attributes": True}

    id: str
    music_release_id: str
    title: str
    splits: Optional[list[dict]] = None
    publishing_share: Optional[float] = None
    master_share: Optional[float] = None
    status: str
    signed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
