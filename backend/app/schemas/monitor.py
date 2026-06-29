"""侵权监测 Pydantic 模型."""

from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class MonitorTaskCreate(BaseModel):
    work_id: str
    search_type: str = Field(default="image")
    platform: str = Field(default="baidu")
    interval: str = Field(default="manual")


class MonitorTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    work_id: str
    search_type: str
    platform: str
    interval: str
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    status: str
    quota_used_today: int = 0
    priority_score: float = 0.0  # P1.3.7
    created_at: datetime
    updated_at: datetime


class ScanRequest(BaseModel):
    work_ids: list[str] = Field(..., min_length=1, max_length=50)
    platform: str = "baidu"


class MonitorResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    task_id: str
    matched_url: str
    matched_title: Optional[str] = None
    similarity: float
    matched_thumbnail_url: Optional[str] = None
    screenshot_path: Optional[str] = None
    found_at: datetime
    status: str
    action_taken: Optional[str] = None
    ignore_reason: Optional[str] = None
    notes: Optional[str] = None


class ResultUpdateRequest(BaseModel):
    status: Optional[str] = None
    action_taken: Optional[str] = None
    ignore_reason: Optional[str] = None
    notes: Optional[str] = None


class EvidencePackageCreate(BaseModel):
    work_id: str
    result_ids: list[str]
    package_type: str = "complaint"
    notes: Optional[str] = None


# --- P2.3 新增 Schemas ---


class FingerprintRequest(BaseModel):
    """计算并存储指纹请求."""
    work_id: str
    hash_types: list[str] = Field(
        default=["dhash", "phash", "whash", "average_hash"]
    )


class FingerprintResponse(BaseModel):
    work_id: str
    fingerprints: dict[str, str]  # {hash_type: hash_value}


class FingerprintCompareRequest(BaseModel):
    """指纹比对请求."""
    work_id_a: str
    work_id_b: str
    hash_type: str = "dhash"


class FingerprintCompareResponse(BaseModel):
    work_id_a: str
    work_id_b: str
    hash_type: str
    hamming_distance: int
    similarity: float  # 0-100


class BrandWatchCreate(BaseModel):
    """注册品牌监测."""
    brand_name: str = Field(..., min_length=1, max_length=200)
    brand_logo_path: Optional[str] = None
    keywords: list[str] = []
    platforms: list[str] = Field(
        default=["taobao", "jd", "pinduoduo"]
    )
    notes: Optional[str] = None


class BrandWatchUpdate(BaseModel):
    brand_name: Optional[str] = None
    brand_logo_path: Optional[str] = None
    keywords: Optional[list[str]] = None
    platforms: Optional[list[str]] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class BrandWatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    brand_name: str
    brand_logo_path: Optional[str] = None
    keywords: Optional[list] = None
    platforms: Optional[list] = None
    is_active: bool = True
    last_scan_at: Optional[datetime] = None
    total_matches: int = 0
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class BrandScanResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    brand_id: str
    platform: str
    item_url: str
    item_title: Optional[str] = None
    similarity: float = 0.0
    thumbnail_url: Optional[str] = None
    found_at: datetime
    status: str
    notes: Optional[str] = None


class DomainWatchCreate(BaseModel):
    """注册域名监测."""
    domain: str = Field(..., min_length=1, max_length=500)
    target_brand: Optional[str] = None
    watch_type: str = "whois"  # whois/typo/phishing


class DomainWatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    domain: str
    target_brand: Optional[str] = None
    watch_type: str = "whois"
    is_active: bool = True
    last_checked_at: Optional[datetime] = None
    registrar: Optional[str] = None
    creation_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    status_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DmcaTemplateResponse(BaseModel):
    """DMCA 通知模板."""
    work_id: str
    work_title: str
    template_type: str = "dmca_takedown"
    filled_template: str
    usage_guide: str


class CodeSimilarityRequest(BaseModel):
    """代码相似度检测请求."""
    code_a: str = Field(..., description="源代码片段 A")
    code_b: str = Field(..., description="源代码片段 B")
    language: str = "python"


class CodeSimilarityResponse(BaseModel):
    code_a: str = ""  # 原始内容摘要
    code_b: str = ""
    similarity: float  # 0-100
    structure_similarity: float
    keyword_similarity: float
    is_mock: bool = False
    message: str = ""


class WhitelistSuggestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    pattern_url: str
    pattern_type: str
    occurrence_count: int
    last_seen_at: datetime
    suggested_at: datetime
    status: str


class WhitelistActionRequest(BaseModel):
    """白名单建议操作."""
    suggestion_id: str
    action: str  # accept/decline


# --- P1.3.3: Delta Detection ---

class DeltaDetectionRequest(BaseModel):
    """Delta 检测请求 — 预扫描哈希比对."""
    work_ids: list[str] = Field(..., min_length=1, max_length=50)
    platform: str = "baidu"


class DeltaDetectionResult(BaseModel):
    """单个作品的 delta 检测结果."""
    work_id: str
    work_title: str = ""
    previous_hash: Optional[str] = None
    current_hash: Optional[str] = None
    has_changed: bool = False
    scan_needed: bool = True


class DeltaDetectionResponse(BaseModel):
    results: list[DeltaDetectionResult]
    works_changed: int
    works_unchanged: int
    scans_triggered: int


# --- P1.3.5: Cross-platform Rotation ---

class PlatformRotationStatus(BaseModel):
    """平台轮转状态."""
    platform: str
    daily_limit: int
    used_today: int
    remaining: int
    available: bool
    fallback_platform: Optional[str] = None
    fallback_limit: Optional[int] = None
    fallback_remaining: Optional[int] = None


class QuotaStatusResponse(BaseModel):
    platforms: list[PlatformRotationStatus]
    total_remaining: int
    rotation_enabled: bool = True


# --- P1.3.7: Scan Priority Scoring ---

class PriorityScoreResult(BaseModel):
    work_id: str
    title: str = ""
    age_days: float = 0
    has_notary: bool = False
    previous_infringements: int = 0
    priority_score: float = 0.0
    factors: dict = {}


# --- P3 Video Fingerprint Monitoring ---

class VideoFingerprintMatch(BaseModel):
    """视频帧指纹匹配结果."""
    video_work_id: str
    video_title: str = ""
    frame_number: int = 0
    timestamp: Optional[float] = None
    perceptual_hash: str = ""
    hamming_distance: int = 0
    similarity: float = 0.0
    matched_frames: int = 0
    total_frames: int = 0


class VideoFingerprintScanResponse(BaseModel):
    matches: list[VideoFingerprintMatch]
    total_compared: int
    match_threshold: int = 15


# --- Audio Fingerprint Monitoring ---

class AudioFingerprintGenerateResponse(BaseModel):
    work_id: str
    audio_duration: Optional[float] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    spectral_signature: dict = {}


class AudioMatch(BaseModel):
    matched_work_id: str
    matched_title: str = ""
    spectral_similarity: float = 0.0
    duration_diff: float = 0.0
    confidence: float = 0.0


class AudioScanResponse(BaseModel):
    matches: list[AudioMatch]
    total_compared: int
    work_id: str


# --- Text Plagiarism Detection ---

class TextDocInfo(BaseModel):
    work_id: str
    title: str = ""
    word_count: int = 0
    tfidf_sparse: dict = {}  # {term_index: value}


class TextPlagiarismMatch(BaseModel):
    matched_work_id: str
    matched_title: str = ""
    cosine_similarity: float = 0.0
    shared_terms: int = 0
    match_percentage: float = 0.0


class TextPlagiarismScanResponse(BaseModel):
    matches: list[TextPlagiarismMatch]
    total_compared: int
    top_n: int = 20


# --- P1.3.7: Scan Priority Scoring ---
