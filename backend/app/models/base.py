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
from app.models.album import Album
from app.models.music_release import MusicRelease
from app.models.split_sheet import SplitSheet
from app.models.video_fingerprint import VideoFingerprintConfig, VideoFrameFingerprint
from app.models.work_variant import WorkVariantGroup, WorkVariant
from app.models.factory import RFQRequest, Sample, QualityReport, Factory, CraftProduct, RFQ

# 摄影师 v2 预留
from app.models.photographer_v2 import (
    RawFormat, StockChannel, StockUpload, StockSale,
    DigitalDownload, FineArtPrintConfig,
)

# 视频 v3 预留
from app.models.video_v3 import (
    BrandCampaign, BrandTask, BrandMessage,
    PlatformGoal, PlatformEarning,
)

# 手工 v3 预留
from app.models.craftsman_v3 import (
    PhysicalProduct, MaterialInventory, MaterialTransaction,
    ProductionBatch,
)
from app.models.etsy import EtsyListing, EtsyOrder, EtsyShop
from app.models.quality_inspection import QualityInspection

# 文字作者 (P4)
from app.models.article import Article
from app.models.book import Book
from app.models.manuscript import Manuscript

# Commission 委托管理
from app.models.commission import (
    CommissionProject, CommissionOrder, CommissionMessage,
    CommissionMilestone, CommissionPayment, CommissionRevision,
)

# 音乐 v4 预留
from app.models.music_v4 import (
    WorkCollaborator,
    DistributionRelease, DistroPlatform,
    SampleClearance,
    AlbumTrack,
)

# 文字 v4 预留
from app.models.writing_v4 import (
    Chapter, ChapterComment, ChapterRevision,
    ExportConfig,
    EbookProduct,
    AudiobookProduction, AudiobookChapter,
)

# Enforcement workflow (维权流水线)
from app.models.enforcement import EnforcementAction, EnforcementTemplate, ComplaintMaterial

# Contract market (v5.0)
from app.models.contract import ContractInstance, SplitRule, SplitExecutionLog, ContractMatching

# Contract risk assessment
from app.models.contract_risk import ContractRiskRule, ContractReview, ContractClause

# Alembic 迁移需要
target_metadata = Base.metadata
