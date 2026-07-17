"""SQLAlchemy ORM 模型."""

from app.database import Base
from app.models.work import Work, WorkTag, WorkVersion, Project
from app.models.notary import NotaryRecord, Certificate, C2PARecord
from app.models.monitor import MonitorTask, MonitorResult, EvidencePackage, ScanSchedule
from app.models.ipr import (
    IPRegistration, TrademarkClass, CopyrightRegistration,
    TrademarkRegistration, TrademarkMonitoring,
)
from app.models.supply import (
    Partner, PartnerQualification, Order, OrderPayment,
    OrderCommunication, Reminder,
)
from app.models.publish import Product, ProductPublishing, VerifiedMark, RevenueRecord
from app.models.system import (
    SystemSetting, AuditLog, BackupRecord,
    DictionaryGroup, DictionaryItem,
    Notification, Plugin, EmailVerification, PasswordReset,
)

from app.models.metadata_template import MetadataTemplate, TemplateField
from app.models.watermark import WatermarkPreset
from app.models.commission import CommissionProject, CommissionOrder, CommissionMessage

# v2-v4 预留模型
from app.models.subtitle import Subtitle
from app.models.video_fingerprint import VideoFingerprintConfig, VideoFrameFingerprint
from app.models.work_variant import WorkVariantGroup, WorkVariant
from app.models.factory import RFQRequest, Sample, QualityReport
from app.models.subtitle import Subtitle, ProjectFileFormat

# 摄影师 v2 预留
from app.models.reserved_photographer import (
    RawFormat,
    StockChannel, StockUpload, StockSale,
    DigitalDownload,
    FineArtPrintConfig,
)

# 视频 v3 预留
from app.models.reserved_video import (
    BrandCampaign, BrandTask, BrandMessage,
    PlatformGoal, PlatformEarning,
)

# 手工 v3 预留
from app.models.reserved_crafts import (
    PhysicalProduct,
    MaterialInventory, MaterialTransaction,
    ProductionBatch,
)
from app.models.quality_inspection import QualityInspection
from app.models.etsy import EtsyListing, EtsyOrder, EtsyShop
from app.models.risk_warning import RiskWarning
from app.models.ai_session import AiCreationSession
from app.models.content_pipeline import (
    PlatformAccount, ContentTemplate, MultiPlatformSchedule, PublishLog,
)
from app.models.pod_profit import PODProduct, PODDesign, PODSale
from app.models.case_study import CaseStudy, CaseTag
from app.models.copyright_guide import GuideRegistration, RegistrationGuide

# 维权流水线
from app.models.enforcement import (
    EnforcementAction, EnforcementTemplate, ComplaintMaterial,
)

from app.models.album import Album
from app.models.music_release import MusicRelease
from app.models.split_sheet import SplitSheet

# 音乐 v4 预留
from app.models.reserved_music import (
    AlbumTrack,
    WorkCollaborator,
    DistributionRelease, DistroPlatform,
    SampleClearance,
)

# 文字 v4 预留
from app.models.reserved_writing import (
    Chapter, ChapterComment, ChapterRevision,
    ExportConfig,
    EbookProduct,
    AudiobookProduction, AudiobookChapter,
)

# Alembic 迁移需要
target_metadata = Base.metadata

__all__ = [
    # v1 core
    "Work", "WorkTag", "WorkVersion", "Project",
    "MetadataTemplate", "TemplateField",
    "NotaryRecord", "Certificate", "C2PARecord",
    "MonitorTask", "MonitorResult", "EvidencePackage", "ScanSchedule",
    "IPRegistration", "TrademarkClass", "CopyrightRegistration",
    "TrademarkRegistration", "TrademarkMonitoring",
    "Partner", "PartnerQualification", "Order", "OrderPayment",
    "OrderCommunication", "Reminder",
    "Product", "ProductPublishing", "VerifiedMark", "RevenueRecord",
    "SystemSetting", "AuditLog", "BackupRecord",
    "DictionaryGroup", "DictionaryItem",
    "Notification", "Plugin", "EmailVerification", "PasswordReset",
    "WatermarkPreset",
    "CommissionProject", "CommissionOrder", "CommissionMessage",
    "Subtitle", "ProjectFileFormat",
    "VideoFingerprintConfig", "VideoFrameFingerprint",
    "WorkVariantGroup",
    "WorkVariant",
    "RFQRequest", "Sample", "QualityReport",
    # 摄影师 v2
    "RawFormat",
    "StockChannel", "StockUpload", "StockSale",
    "DigitalDownload",
    "FineArtPrintConfig",
    # 视频 v3
    "BrandCampaign", "BrandTask", "BrandMessage",
    "PlatformGoal", "PlatformEarning",
    # 手工 v3
    "PhysicalProduct",
    "MaterialInventory", "MaterialTransaction",
    "ProductionBatch",
    "QualityInspection",
    "EtsyListing", "EtsyOrder", "EtsyShop",
    "RiskWarning",
    "AiCreationSession",
    # 多平台内容分发流水线
    "PlatformAccount", "ContentTemplate", "MultiPlatformSchedule", "PublishLog",
    # POD 利润计算器
    "PODProduct", "PODDesign", "PODSale",
    # 音乐 v4
    "Album", "MusicRelease", "SplitSheet", "AlbumTrack",
    "WorkCollaborator",
    "DistributionRelease", "DistroPlatform",
    "SampleClearance",
    # 文字 v4
    "Chapter", "ChapterComment", "ChapterRevision",
    "ExportConfig",
    "EbookProduct",
    "AudiobookProduction", "AudiobookChapter",
    # 版权登记指南
    "GuideRegistration", "RegistrationGuide",
    # 维权流水线
    "EnforcementAction", "EnforcementTemplate", "ComplaintMaterial",
]
