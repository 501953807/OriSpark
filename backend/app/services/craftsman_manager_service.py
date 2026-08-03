# -*- coding: utf-8 -*-
"""手工艺人管理服务层 — 封装 craftsman router 中的所有 DB 操作."""

import uuid
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.factory import Factory, CraftProduct, RFQ
from app.models.craftsman_v3 import PhysicalProduct, MaterialInventory, MaterialTransaction, ProductionBatch
from app.schemas.common import ApiResponse


class CraftsmanManagerService:
    """手工艺人业务逻辑服务，封装所有 DB 操作."""

    def __init__(self, db: Session):
        self.db = db

    # ── CraftProducts CRUD ─────────────────────────────────────────────

    def list_craft_products(
        self,
        craft_type: Optional[str] = None,
        work_variant_id: Optional[str] = None,
    ) -> list:
        q = self.db.query(CraftProduct)
        if craft_type:
            q = q.filter(CraftProduct.craft_type == craft_type)
        if work_variant_id:
            q = q.filter(CraftProduct.work_variant_id == work_variant_id)
        products = q.order_by(CraftProduct.created_at.desc()).all()
        return [self._product_to_dict(p) for p in products]

    def create_craft_product(
        self,
        work_variant_id: Optional[str],
        material: Optional[str],
        dimensions: Optional[str],
        craft_type: Optional[str],
        moq: int,
        unit_price: Optional[float],
        production_time_days: Optional[int],
    ) -> dict:
        product = CraftProduct(
            work_variant_id=work_variant_id,
            material=material,
            dimensions=dimensions,
            craft_type=craft_type,
            moq=moq,
            unit_price=unit_price,
            production_time_days=production_time_days,
        )
        try:
            self.db.add(product)
            self.db.commit()
            self.db.refresh(product)
        except Exception:
            self.db.rollback()
            raise
        return {"id": product.id}

    def get_craft_product(self, product_id: str) -> dict:
        p = self.db.query(CraftProduct).filter(CraftProduct.id == product_id).first()
        if not p:
            raise HTTPException(status_code=404, detail="手工艺品不存在")
        return self._product_to_dict(p)

    def update_craft_product(self, product_id: str, update_data: dict) -> dict:
        p = self.db.query(CraftProduct).filter(CraftProduct.id == product_id).first()
        if not p:
            raise HTTPException(status_code=404, detail="手工艺品不存在")
        for key, value in update_data.items():
            setattr(p, key, value)
        try:
            self.db.commit()
            self.db.refresh(p)
        except Exception:
            self.db.rollback()
            raise
        return self._product_to_dict(p)

    def delete_craft_product(self, product_id: str) -> None:
        p = self.db.query(CraftProduct).filter(CraftProduct.id == product_id).first()
        if not p:
            raise HTTPException(status_code=404, detail="手工艺品不存在")
        try:
            self.db.delete(p)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    # ── Factories CRUD ────────────────────────────────────────────────

    def list_factories(self, rating_min: Optional[float] = None) -> list:
        q = self.db.query(Factory)
        if rating_min is not None:
            q = q.filter(Factory.rating >= rating_min)
        factories = q.order_by(Factory.rating.desc()).all()
        return [self._factory_to_dict(f) for f in factories]

    def create_factory(
        self,
        name: str,
        location: Optional[str],
        contact: Optional[str],
        rating: Optional[float],
        capabilities: Optional[list],
    ) -> dict:
        factory = Factory(
            name=name,
            location=location,
            contact=contact,
            rating=rating,
            capabilities=capabilities,
        )
        try:
            self.db.add(factory)
            self.db.commit()
            self.db.refresh(factory)
        except Exception:
            self.db.rollback()
            raise
        return {"id": factory.id}

    def update_factory(self, factory_id: str, update_data: dict) -> dict:
        factory = self.db.query(Factory).filter(Factory.id == factory_id).first()
        if not factory:
            raise HTTPException(status_code=404, detail="工厂不存在")
        for key, value in update_data.items():
            setattr(factory, key, value)
        try:
            self.db.commit()
            self.db.refresh(factory)
        except Exception:
            self.db.rollback()
            raise
        return self._factory_to_dict(factory)

    def delete_factory(self, factory_id: str) -> None:
        factory = self.db.query(Factory).filter(Factory.id == factory_id).first()
        if not factory:
            raise HTTPException(status_code=404, detail="工厂不存在")
        try:
            self.db.delete(factory)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    # ── RFQs CRUD ─────────────────────────────────────────────────────

    def delete_rfq(self, rfq_id: str) -> None:
        rfq = self.db.query(RFQ).filter(RFQ.id == rfq_id).first()
        if not rfq:
            raise HTTPException(status_code=404, detail="询价单不存在")
        try:
            self.db.delete(rfq)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def list_rfqs(
        self,
        status: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> list:
        q = self.db.query(RFQ)
        if status:
            q = q.filter(RFQ.status == status)
        if created_by:
            q = q.filter(RFQ.created_by == created_by)
        rfqs = q.order_by(RFQ.created_at.desc()).all()
        return [self._rfq_to_dict(r) for r in rfqs]

    def create_rfq(
        self,
        craft_product_id: Optional[str],
        title: str,
        description: Optional[str],
        quantity_needed: Optional[int],
        material_specs: Optional[str],
        target_price: Optional[float],
        status: str,
        quoted_factories: Optional[list],
        created_by: Optional[str],
    ) -> dict:
        rfq = RFQ(
            craft_product_id=craft_product_id,
            title=title,
            description=description,
            quantity_needed=quantity_needed,
            material_specs=material_specs,
            target_price=target_price,
            status=status,
            quoted_factories=quoted_factories,
            created_by=created_by,
        )
        try:
            self.db.add(rfq)
            self.db.commit()
            self.db.refresh(rfq)
        except Exception:
            self.db.rollback()
            raise
        return {"id": rfq.id}

    def update_rfq(self, rfq_id: str, update_data: dict) -> dict:
        rfq = self.db.query(RFQ).filter(RFQ.id == rfq_id).first()
        if not rfq:
            raise HTTPException(status_code=404, detail="询价单不存在")
        for key, value in update_data.items():
            setattr(rfq, key, value)
        try:
            self.db.commit()
            self.db.refresh(rfq)
        except Exception:
            self.db.rollback()
            raise
        return self._rfq_to_dict(rfq)

    # ── Physical Products CRUD ────────────────────────────────────────

    def list_physical_products(self, category: Optional[str] = None) -> list:
        q = self.db.query(PhysicalProduct).filter(PhysicalProduct.is_active == True)
        if category:
            q = q.filter(PhysicalProduct.category == category)
        products = q.order_by(PhysicalProduct.created_at.desc()).all()
        return [self._physical_product_to_dict(p) for p in products]

    def create_physical_product(
        self,
        user_id: str,
        work_id: Optional[str],
        title: str,
        description: Optional[str],
        category: Optional[str],
        dimensions: Optional[dict],
        weight_g: Optional[int],
        price: float,
        currency: str,
        stock_quantity: int,
        shipping_regions: Optional[list],
    ) -> dict:
        product = PhysicalProduct(
            user_id=user_id,
            work_id=work_id,
            title=title,
            description=description,
            category=category,
            dimensions=dimensions,
            weight_g=weight_g,
            price=price,
            currency=currency,
            stock_quantity=stock_quantity,
            shipping_regions=shipping_regions,
        )
        try:
            self.db.add(product)
            self.db.commit()
            self.db.refresh(product)
        except Exception:
            self.db.rollback()
            raise
        return {"id": product.id}

    def update_physical_product(self, product_id: str, update_data: dict) -> None:
        product = self.db.query(PhysicalProduct).filter(PhysicalProduct.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="物理产品不存在")
        for key, value in update_data.items():
            setattr(product, key, value)
        try:
            self.db.commit()
            self.db.refresh(product)
        except Exception:
            self.db.rollback()
            raise

    def delete_physical_product(self, product_id: str) -> None:
        product = self.db.query(PhysicalProduct).filter(PhysicalProduct.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="物理产品不存在")
        try:
            self.db.delete(product)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    # ── Material Inventory CRUD ───────────────────────────────────────

    def list_materials(self) -> list:
        items = self.db.query(MaterialInventory).order_by(MaterialInventory.created_at.desc()).all()
        return [self._material_to_dict(m) for m in items]

    def create_material(
        self,
        user_id: str,
        material_name: str,
        material_category: Optional[str],
        unit: str,
        quantity_on_hand: float,
        quantity_reserved: float,
        reorder_level: Optional[float],
        unit_cost: Optional[float],
        location: Optional[str],
    ) -> dict:
        mat = MaterialInventory(
            user_id=user_id,
            material_name=material_name,
            material_category=material_category,
            unit=unit,
            quantity_on_hand=quantity_on_hand,
            quantity_reserved=quantity_reserved,
            reorder_level=reorder_level,
            unit_cost=unit_cost,
            location=location,
        )
        try:
            self.db.add(mat)
            self.db.commit()
            self.db.refresh(mat)
        except Exception:
            self.db.rollback()
            raise
        return {"id": mat.id}

    def update_material(self, material_id: str, update_data: dict) -> None:
        mat = self.db.query(MaterialInventory).filter(MaterialInventory.id == material_id).first()
        if not mat:
            raise HTTPException(status_code=404, detail="原料不存在")
        for key, value in update_data.items():
            setattr(mat, key, value)
        try:
            self.db.commit()
            self.db.refresh(mat)
        except Exception:
            self.db.rollback()
            raise

    def delete_material(self, material_id: str) -> None:
        mat = self.db.query(MaterialInventory).filter(MaterialInventory.id == material_id).first()
        if not mat:
            raise HTTPException(status_code=404, detail="原料不存在")
        try:
            self.db.delete(mat)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def create_material_transaction(
        self,
        material_id: str,
        transaction_type: str,
        quantity: float,
        reference_type: Optional[str],
        reference_id: Optional[str],
        notes: Optional[str],
    ) -> dict:
        mat = self.db.query(MaterialInventory).filter(MaterialInventory.id == material_id).first()
        if not mat:
            raise HTTPException(status_code=404, detail="原料不存在")

        if transaction_type == "purchase":
            mat.quantity_on_hand += quantity
        elif transaction_type in ("consume", "scrap"):
            mat.quantity_on_hand -= quantity
            if mat.quantity_on_hand < 0:
                self.db.rollback()
                raise HTTPException(status_code=400, detail="库存不足，无法出库或报废")

        txn = MaterialTransaction(
            material_id=material_id,
            transaction_type=transaction_type,
            quantity=quantity,
            reference_type=reference_type,
            reference_id=reference_id,
            notes=notes,
        )
        try:
            self.db.add(txn)
            self.db.commit()
            self.db.refresh(txn)
        except Exception:
            self.db.rollback()
            raise
        return {"id": txn.id}

    def list_material_transactions(
        self,
        material_id: Optional[str] = None,
        limit: int = 50,
    ) -> list:
        q = self.db.query(MaterialTransaction)
        if material_id:
            q = q.filter(MaterialTransaction.material_id == material_id)
        txns = q.order_by(MaterialTransaction.created_at.desc()).limit(limit).all()
        return [self._transaction_to_dict(t) for t in txns]

    # ── Production Batches CRUD ───────────────────────────────────────

    def list_production_batches(self, status: Optional[str] = None) -> list:
        q = self.db.query(ProductionBatch)
        if status:
            q = q.filter(ProductionBatch.status == status)
        batches = q.order_by(ProductionBatch.created_at.desc()).all()
        return [self._batch_to_dict(b) for b in batches]

    def create_production_batch(
        self,
        user_id: str,
        work_id: Optional[str],
        title: str,
        planned_quantity: int,
    ) -> dict:
        batch = ProductionBatch(
            user_id=user_id,
            work_id=work_id,
            title=title,
            planned_quantity=planned_quantity,
        )
        try:
            self.db.add(batch)
            self.db.commit()
            self.db.refresh(batch)
        except Exception:
            self.db.rollback()
            raise
        return {"id": batch.id}

    def update_production_batch(self, batch_id: str, update_data: dict) -> dict:
        batch = self.db.query(ProductionBatch).filter(ProductionBatch.id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="生产批次不存在")
        new_status = update_data.get("status")
        if new_status == "in_production" and not batch.started_at:
            update_data["started_at"] = datetime.now(timezone.utc)
        if new_status == "done" and batch.started_at and not batch.completed_at:
            update_data["completed_at"] = datetime.now(timezone.utc)
        for key, value in update_data.items():
            setattr(batch, key, value)
        try:
            self.db.commit()
            self.db.refresh(batch)
        except Exception:
            self.db.rollback()
            raise
        return {
            "id": batch.id,
            "title": batch.title,
            "status": batch.status,
            "planned_quantity": batch.planned_quantity,
            "produced_quantity": batch.produced_quantity,
            "sold_quantity": batch.sold_quantity,
        }

    def delete_production_batch(self, batch_id: str) -> None:
        batch = self.db.query(ProductionBatch).filter(ProductionBatch.id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="生产批次不存在")
        try:
            self.db.delete(batch)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def list_craft_orders(self) -> list:
        rfqs = self.db.query(RFQ).order_by(RFQ.created_at.desc()).limit(20).all()
        return [
            {
                "id": r.id,
                "title": r.title,
                "status": r.status,
                "quote_count": len(r.quoted_factories or []),
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rfqs
        ]

    # ── Helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _product_to_dict(p: CraftProduct) -> dict:
        return {
            "id": p.id,
            "work_variant_id": p.work_variant_id,
            "material": p.material,
            "dimensions": p.dimensions,
            "craft_type": p.craft_type,
            "moq": p.moq,
            "unit_price": p.unit_price,
            "production_time_days": p.production_time_days,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        }

    @staticmethod
    def _factory_to_dict(f: Factory) -> dict:
        return {
            "id": f.id,
            "name": f.name,
            "location": f.location,
            "contact": f.contact,
            "rating": f.rating,
            "capabilities": f.capabilities or [],
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }

    @staticmethod
    def _rfq_to_dict(r: RFQ) -> dict:
        return {
            "id": r.id,
            "craft_product_id": r.craft_product_id,
            "title": r.title,
            "description": r.description,
            "quantity_needed": r.quantity_needed,
            "material_specs": r.material_specs,
            "target_price": r.target_price,
            "status": r.status,
            "quoted_factories": r.quoted_factories or [],
            "created_by": r.created_by,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        }

    @staticmethod
    def _physical_product_to_dict(p: PhysicalProduct) -> dict:
        return {
            "id": p.id,
            "work_id": p.work_id,
            "title": p.title,
            "description": p.description,
            "category": p.category,
            "dimensions": p.dimensions,
            "weight_g": p.weight_g,
            "price": p.price,
            "currency": p.currency,
            "stock_quantity": p.stock_quantity,
            "shipping_regions": p.shipping_regions or [],
            "is_active": p.is_active,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        }

    @staticmethod
    def _material_to_dict(m: MaterialInventory) -> dict:
        return {
            "id": m.id,
            "material_name": m.material_name,
            "material_category": m.material_category,
            "unit": m.unit,
            "quantity_on_hand": m.quantity_on_hand,
            "quantity_reserved": m.quantity_reserved,
            "available_qty": m.quantity_on_hand - (m.quantity_reserved or 0),
            "reorder_level": m.reorder_level,
            "unit_cost": m.unit_cost,
            "location": m.location,
            "last_counted_at": m.last_counted_at.isoformat() if m.last_counted_at else None,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }

    @staticmethod
    def _transaction_to_dict(t: MaterialTransaction) -> dict:
        return {
            "id": t.id,
            "material_id": t.material_id,
            "transaction_type": t.transaction_type,
            "quantity": t.quantity,
            "reference_type": t.reference_type,
            "reference_id": t.reference_id,
            "notes": t.notes,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }

    @staticmethod
    def _batch_to_dict(b: ProductionBatch) -> dict:
        return {
            "id": b.id,
            "work_id": b.work_id,
            "title": b.title,
            "planned_quantity": b.planned_quantity,
            "produced_quantity": b.produced_quantity,
            "sold_quantity": b.sold_quantity,
            "status": b.status,
            "started_at": b.started_at.isoformat() if b.started_at else None,
            "completed_at": b.completed_at.isoformat() if b.completed_at else None,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        }
