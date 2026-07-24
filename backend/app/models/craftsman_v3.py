"""手工艺人 (v3) 预留数据模型.

Reserved for future craft creator type.
v1: 建表+字段注释 "v3激活".
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship

from app.database import Base


def _uid():
    return uuid.uuid4().hex[:32]


# =============================================================================
# physical_products — 物理原件产品模型 (15.3.1)
# =============================================================================


class PhysicalProduct(Base):
    """物理原件产品表.

    手绘原作/雕塑/纺织品等不可复制的物理商品.
    v3 激活.
    """
    __tablename__ = "physical_products"

    id = Column(String(32), primary_key=True, default=_uid)
    user_id = Column(String(32), nullable=False)
    work_id = Column(String(32), ForeignKey("works.id"), nullable=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)  # painting/sculpture/textile
    dimensions = Column(JSON, nullable=True)  # {"width_cm": 30, "height_cm": 40}
    weight_g = Column(Integer, nullable=True)
    price = Column(Float, nullable=False)
    currency = Column(String(10), default="CNY")
    stock_quantity = Column(Integer, default=1)  # 原作通常=1
    shipping_regions = Column(JSON, nullable=True)  # ["CN","US","JP"]
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_pp_user", "user_id"),
        Index("idx_pp_active", "is_active"),
    )


# =============================================================================
# materials_inventory — 原料库存管理 (15.3.2)
# =============================================================================


class MaterialInventory(Base):
    """原料库存表.

    手工艺人的原材料入库/出库/盘点.
    v3 激活.
    """
    __tablename__ = "materials_inventory"

    id = Column(String(32), primary_key=True, default=_uid)
    user_id = Column(String(32), nullable=False)
    material_name = Column(String(200), nullable=False)
    material_category = Column(String(50), nullable=True)  # fabric/wood/paint
    unit = Column(String(20), nullable=False)  # meter/gram/piece
    quantity_on_hand = Column(Float, default=0.0)
    quantity_reserved = Column(Float, default=0.0)
    reorder_level = Column(Float, nullable=True)
    unit_cost = Column(Float, nullable=True)
    location = Column(String(200), nullable=True)  # 仓库位置
    last_counted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_mi_user", "user_id"),)


class MaterialTransaction(Base):
    """材料出入库流水表.

    记录每次材料的采购/领用/报废.
    v3 激活.
    """
    __tablename__ = "material_transactions"

    id = Column(String(32), primary_key=True, default=_uid)
    material_id = Column(String(32), ForeignKey("materials_inventory.id"), nullable=False)
    transaction_type = Column(String(20), nullable=False)  # purchase/consume/scrap
    quantity = Column(Float, nullable=False)
    reference_type = Column(String(50), nullable=True)  # production_batch/order
    reference_id = Column(String(32), nullable=True)
    operator_id = Column(String(32), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_mt_material", "material_id"),)


# =============================================================================
# production_batches — 生产批次管理 (15.3.3)
# =============================================================================


class ProductionBatch(Base):
    """生产批次表.

    一批次相同作品的印刷/制作任务.
    v3 激活.
    """
    __tablename__ = "production_batches"

    id = Column(String(32), primary_key=True, default=_uid)
    user_id = Column(String(32), nullable=False)
    work_id = Column(String(32), ForeignKey("works.id"), nullable=True)
    title = Column(String(500), nullable=False)
    planned_quantity = Column(Integer, nullable=False)
    produced_quantity = Column(Integer, default=0)
    sold_quantity = Column(Integer, default=0)
    status = Column(String(20), default="planned")  # planned/in_production/done/shipped
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_pb_user", "user_id"),
        Index("idx_pb_status", "status"),
    )
