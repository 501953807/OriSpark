"""摄影师 (v2) 预留数据模型.

Reserved for future photographer creator type.
v1: 建表+字段注释 "v2激活".
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship

from app.database import Base


def _uid():
    return uuid.uuid4().hex[:32]


# =============================================================================
# raw_formats — 原始文件格式记录 (12.1.1)
# =============================================================================


class RawFormat(Base):
    """RAW格式文件记录表.

    存储摄影师导入的RAW/CRF/ARW等原始文件元信息.
    v2 激活.
    """
    __tablename__ = "raw_formats"

    id = Column(String(32), primary_key=True, default=_uid)
    work_id = Column(String(32), ForeignKey("works.id"), nullable=False)
    file_extension = Column(String(10), nullable=False)  # ARW, CR2, DNG, NEF
    file_size_bytes = Column(Integer, nullable=True)
    sensor_width = Column(Integer, nullable=True)  # 传感器分辨率
    sensor_height = Column(Integer, nullable=True)
    color_space = Column(String(50), nullable=True)  # AdobeRGB/sRGB/ProPhoto
    created_at = Column(DateTime, default=datetime.utcnow)

    work = relationship("Work")

    __table_args__ = (
        Index("idx_raw_work", "work_id"),
        Index("idx_raw_ext", "file_extension"),
    )


# =============================================================================
# stock_channels — 图库销售渠道 (15.1.1)
# =============================================================================


class StockChannel(Base):
    """图库销售渠道配置表.

    对接Shutterstock/Adobe Stock/Getty等平台的API凭证与映射.
    v2 激活.
    """
    __tablename__ = "stock_channels"

    id = Column(String(32), primary_key=True, default=_uid)
    user_id = Column(String(32), nullable=False)
    channel_name = Column(String(100), nullable=False)  # shutterstock/adobe/Getty
    api_key = Column(String(255), nullable=False)  # encrypted
    api_secret = Column(String(255), nullable=True)
    account_id = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_stock_user", "user_id"),
        Index("idx_stock_channel", "channel_name"),
    )


class StockUpload(Base):
    """图库上传记录表.

    记录每次向图库平台上传作品的状态.
    v2 激活.
    """
    __tablename__ = "stock_uploads"

    id = Column(String(32), primary_key=True, default=_uid)
    channel_id = Column(String(32), ForeignKey("stock_channels.id"), nullable=False)
    work_id = Column(String(32), ForeignKey("works.id"), nullable=False)
    remote_id = Column(String(255), nullable=True)  # 平台侧作品ID
    status = Column(String(20), default="pending")  # pending/approved/rejected
    rejection_reason = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_stock_upload_channel", "channel_id"),
        Index("idx_stock_upload_work", "work_id"),
    )


class StockSale(Base):
    """图库销售记录表.

    从平台回调或拉取的销售数据.
    v2 激活.
    """
    __tablename__ = "stock_sales"

    id = Column(String(32), primary_key=True, default=_uid)
    upload_id = Column(String(32), ForeignKey("stock_uploads.id"), nullable=True)
    license_type = Column(String(50), nullable=True)  # royalty_free/extended
    sale_amount = Column(Float, nullable=True)
    currency = Column(String(10), default="USD")
    buyer_country = Column(String(10), nullable=True)
    sale_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_stock_sale_upload", "upload_id"),
        Index("idx_stock_sale_date", "sale_date"),
    )


# =============================================================================
# digital_downloads — 数字预设包 (15.1.2)
# =============================================================================


class DigitalDownload(Base):
    """数字预设包表.

    Lightroom预设/达芬奇LUT/动作等可下载的数字商品.
    v2 激活.
    """
    __tablename__ = "digital_downloads"

    id = Column(String(32), primary_key=True, default=_uid)
    work_id = Column(String(32), ForeignKey("works.id"), nullable=False)
    product_id = Column(String(32), nullable=True)  # 关联supply.products
    download_url = Column(String(2000), nullable=True)  # presigned URL
    max_downloads = Column(Integer, nullable=True)  # None=不限
    download_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_dd_work", "work_id"),)


# =============================================================================
# fine_art_print_configs — 艺术微喷配置 (15.1.3)
# =============================================================================


class FineArtPrintConfig(Base):
    """艺术微喷产品配置表.

    定义画布尺寸/纸张类型/装框选项等.
    v2 激活.
    """
    __tablename__ = "fine_art_print_configs"

    id = Column(String(32), primary_key=True, default=_uid)
    work_id = Column(String(32), ForeignKey("works.id"), nullable=False)
    paper_type = Column(String(50), nullable=False)  # cotton_rice/glossy/matte
    max_width_cm = Column(Float, nullable=True)
    max_height_cm = Column(Float, nullable=True)
    framing_available = Column(Boolean, default=False)
    price_multiplier = Column(Float, default=1.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_fap_work", "work_id"),)
