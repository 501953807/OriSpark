"""导入所有模型，确保 Alembic 可以检测."""

from app.database import Base
from app.models.work import Work, WorkTag, WorkVersion, Project
from app.models.notary import NotaryRecord, Certificate, C2PARecord, NotaryAuditTrail
from app.models.monitor import MonitorTask, MonitorResult, EvidencePackage, ScanSchedule
from app.models.monitor_ext import (
    LocalFingerprint, BrandWatch, BrandScanResult,
    DomainWatch, WhitelistSuggestion,
)
from app.models.ipr import (
    IPRegistration, TrademarkClass, CopyrightRegistration,
    TrademarkRegistration, TrademarkMonitoring,
    ApplicationTemplate, NiceClassification,
)
from app.models.supply import (
    Partner, PartnerQualification, Order, OrderPayment,
    OrderCommunication, Reminder,
)
from app.models.publish import Product, ProductPublishing, VerifiedMark, RevenueRecord
from app.models.monetization import (
    ProductTemplate, MonetizationChannel, Campaign, License,
)
from app.models.system import (
    SystemSetting, AuditLog, BackupRecord,
    DictionaryGroup, DictionaryItem, User, UserLoginHistory, Notification,
    Plugin, EmailVerification, PasswordReset,
)
from app.models.subtitle import Subtitle, ProjectFileFormat
from app.models.video_fingerprint import VideoFingerprintConfig, VideoFrameFingerprint
from app.models.work_variant import WorkVariantGroup
from app.models.factory import RFQRequest, Sample, QualityReport

# 摄影师 v2 预留
from app.models.reserved_photographer import (
    RawFormat, StockChannel, StockUpload, StockSale,
    DigitalDownload, FineArtPrintConfig,
)

# 视频 v3 预留
from app.models.reserved_video import (
    BrandCampaign, BrandTask, BrandMessage,
    PlatformGoal, PlatformEarning,
)

# 手工 v3 预留
from app.models.reserved_crafts import (
    PhysicalProduct, MaterialInventory, MaterialTransaction,
    ProductionBatch,
)
from app.models.quality_inspection import QualityInspection

# 音乐 v4 预留
from app.models.reserved_music import (
    Album, AlbumTrack,
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
