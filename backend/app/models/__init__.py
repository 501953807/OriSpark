"""SQLAlchemy ORM 模型."""

from app.database import Base
from app.models.work import Work, WorkTag, WorkVersion, Project
from app.models.notary import NotaryRecord, Certificate, C2PARecord, NotaryAuditTrail
from app.models.monitor import MonitorTask, MonitorResult, EvidencePackage, ScanSchedule
from app.models.ipr import (
    IPRegistration, TrademarkClass, CopyrightRegistration,
    TrademarkRegistration, TrademarkMonitoring,
    ApplicationTemplate, NiceClassification,
)
from app.models.supply import (
    Partner, PartnerQualification, Order, OrderPayment,
    OrderCommunication, Reminder,
)
from app.models.publish import (
    Product, ProductPublishing, VerifiedMark, RevenueRecord,
    PublishSchedule, PublishContent, PublishAnalytics,
)
from app.models.system import (
    SystemSetting, AuditLog, BackupRecord,
    DictionaryGroup, DictionaryItem,
    Notification, Plugin, EmailVerification, PasswordReset,
    User, UserLoginHistory, Disclaimer, DisclaimerAcceptance,
)

from app.models.metadata_template import MetadataTemplate, TemplateField
from app.models.watermark import WatermarkPreset
from app.models.commission import (
    CommissionProject, CommissionOrder, CommissionMessage,
    CommissionMilestone, CommissionPayment, CommissionRevision,
)

# v2-v4 预留模型
from app.models.subtitle import Subtitle, ProjectFileFormat
from app.models.video_fingerprint import VideoFingerprintConfig, VideoFrameFingerprint
from app.models.work_variant import WorkVariantGroup, WorkVariant
from app.models.factory import (
    RFQRequest, Sample, QualityReport, Factory, CraftProduct, RFQ,
)
from app.models.risk_warning import RiskWarning, TaxDeadline, HealthMetric
from app.models.ai_session import AiCreationSession
from app.models.achievement import AchievementBadge, UserAchievement, LeaderboardEntry
from app.models.invoice import Invoice, SubscriptionAutoRenewal
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
from app.models.enforcement_roi import (
    EnforcementCase, CaseReference, DefenseBudgetTier,
)

from app.models.album import Album
from app.models.music_release import MusicRelease
from app.models.split_sheet import SplitSheet

# 合约市场核心模型 (v5.0)
from app.models.contract import (
    ContractInstance, SplitRule, SplitExecutionLog, ContractMatching,
)

# P2 变现引擎模型
from app.models.listings import DesignListing, DesignTemplateCompatibility
from app.models.monetization import (
    ProductTemplate, MonetizationChannel, Campaign, License,
)
from app.models.subscription import SubscriptionTier, SubscriptionSubscriber
from app.models.private_traffic import SubscriptionLink, FanCommunity, ConversionFunnel
from app.models.listing import Listing

# 保险市场
from app.models.insurance import (
    InsuranceProvider, InsuranceProduct, InsurancePolicy, InsuranceClaim,
)

# 信用体系
from app.models.credit import CreditRating, CreditBehavior

# 合同风险评估
from app.models.contract_risk import ContractRiskRule, ContractReview, ContractClause

# AI 训练许可
from app.models.ai_training_license import AITrainingLicense

# 能力成长
from app.models.capability import CapabilityDimension, CreatorAssessment, LearningPath
from app.models.growth_stage import CreatorGrowthStage, GrowthTask
from app.models.ip_commercialization import IPAsset

# 认证与证据
from app.models.certification import CertificationRecord

# 匹配引擎
from app.models.matchmaking import MatchRequest, MatchTransaction
from app.models.matching_engine import AuctionRecord, Bid, LicensingMatch

# 多市场扩展
from app.models.multi_market import MarketInfo, ExpansionPlan, TaxGuide

# 导航任务
from app.models.navigation import NavigationTask, CreatorNavigation

# 交易谈判
from app.models.negotiation import TradeNegotiation

# 风控系统
from app.models.risk_control import RiskRule, RiskAssessment, BlacklistEntry

# 交易费用
from app.models.trading_fee import TransactionFee, CommissionRule

# 提现
from app.models.withdrawal import WithdrawalRequest

# POD 结算
from app.models.pod_settlement import PodSettlement, PodSettlementItem

# 监控扩展
from app.models.monitor_ext import (
    LocalFingerprint, BrandWatch, BrandScanResult, DomainWatch, WhitelistSuggestion,
)

# 手稿/文章/书籍
from app.models.manuscript import Manuscript
from app.models.article import Article
from app.models.book import Book

# 摄影师预留
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
    "NotaryRecord", "Certificate", "C2PARecord", "NotaryAuditTrail",
    "MonitorTask", "MonitorResult", "EvidencePackage", "ScanSchedule",
    "IPRegistration", "TrademarkClass", "CopyrightRegistration",
    "TrademarkRegistration", "TrademarkMonitoring",
    "ApplicationTemplate", "NiceClassification",
    "Partner", "PartnerQualification", "Order", "OrderPayment",
    "OrderCommunication", "Reminder",
    "Product", "ProductPublishing", "VerifiedMark", "RevenueRecord",
    "PublishSchedule", "PublishContent", "PublishAnalytics",
    "SystemSetting", "AuditLog", "BackupRecord",
    "DictionaryGroup", "DictionaryItem",
    "Notification", "Plugin", "EmailVerification", "PasswordReset",
    "User", "UserLoginHistory", "Disclaimer", "DisclaimerAcceptance",
    "WatermarkPreset",
    "CommissionProject", "CommissionOrder", "CommissionMessage",
    "CommissionMilestone", "CommissionPayment", "CommissionRevision",
    "Subtitle", "ProjectFileFormat",
    "VideoFingerprintConfig", "VideoFrameFingerprint",
    "WorkVariantGroup", "WorkVariant",
    "RFQRequest", "Sample", "QualityReport", "Factory", "CraftProduct", "RFQ",
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
    "RiskWarning", "TaxDeadline", "HealthMetric",
    "AiCreationSession",
    # AI增长引擎 v2
    "AchievementBadge", "UserAchievement", "LeaderboardEntry",
    "Invoice", "SubscriptionAutoRenewal",
    # 多平台内容分发流水线
    "PlatformAccount", "ContentTemplate", "MultiPlatformSchedule", "PublishLog",
    # POD 利润计算器
    "PODProduct", "PODDesign", "PODSale",
    # 版权登记指南
    "GuideRegistration", "RegistrationGuide",
    # 维权流水线
    "EnforcementAction", "EnforcementTemplate", "ComplaintMaterial",
    "EnforcementCase", "CaseReference", "DefenseBudgetTier",
    # 合约市场 v5.0
    "ContractInstance", "SplitRule", "SplitExecutionLog", "ContractMatching",
    # P2 变现引擎
    "DesignListing", "DesignTemplateCompatibility",
    "ProductTemplate", "MonetizationChannel", "Campaign", "License",
    "SubscriptionTier", "SubscriptionSubscriber",
    "SubscriptionLink", "FanCommunity", "ConversionFunnel",
    "Listing",
    # 保险
    "InsuranceProvider", "InsuranceProduct", "InsurancePolicy", "InsuranceClaim",
    # 信用
    "CreditRating", "CreditBehavior",
    # 合同风险
    "ContractRiskRule", "ContractReview", "ContractClause",
    # AI 训练
    "AITrainingLicense",
    # 能力成长
    "CapabilityDimension", "CreatorAssessment", "LearningPath",
    # 认证
    "CertificationRecord",
    # 匹配
    "MatchRequest", "MatchTransaction",
    "AuctionRecord", "Bid", "LicensingMatch",
    # 多市场
    "MarketInfo", "ExpansionPlan", "TaxGuide",
    # 导航
    "NavigationTask", "CreatorNavigation",
    # 交易谈判
    "TradeNegotiation",
    # 风控
    "RiskRule", "RiskAssessment", "BlacklistEntry",
    # 交易费用
    "TransactionFee", "CommissionRule",
    # 提现
    "WithdrawalRequest",
    # POD 结算
    "PodSettlement", "PodSettlementItem",
    # 监控扩展
    "LocalFingerprint", "BrandWatch", "BrandScanResult", "DomainWatch", "WhitelistSuggestion",
    # 文章/书籍/手稿
    "Manuscript", "Article", "Book",
    # 音乐 v4
    "Album", "MusicRelease", "SplitSheet", "AlbumTrack",
    "WorkCollaborator", "DistributionRelease", "DistroPlatform", "SampleClearance",
    # 文字 v4
    "Chapter", "ChapterComment", "ChapterRevision",
    "ExportConfig", "EbookProduct", "AudiobookProduction", "AudiobookChapter",
]
