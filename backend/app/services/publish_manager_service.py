# -*- coding: utf-8 -*-
"""内容分发管理服务层 — 封装 publish router 中的所有 DB 操作."""

import csv
import io
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.publish import Product, ProductPublishing, RevenueRecord, PublishSchedule, PublishContent, PublishAnalytics, VerifiedMark
from app.schemas.common import ApiResponse


class PublishManagerService:
    """内容分发业务逻辑服务，封装所有 DB 操作."""

    def __init__(self, db: Session):
        self.db = db

    # ── Products CRUD ─────────────────────────────────────────────────

    def list_products(self) -> list:
        products = self.db.query(Product).order_by(Product.created_at.desc()).all()
        return [
            {
                "id": p.id, "work_id": p.work_id, "title": p.title,
                "description": p.description, "ai_description": p.ai_description,
                "price": p.price, "category": p.category,
                "csv_export_path": p.csv_export_path,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in products
        ]

    def create_product(
        self,
        work_id: Optional[str],
        title: Optional[str],
        description: Optional[str],
        price: float,
        category: Optional[str],
        specifications: Optional[dict],
        images: list,
    ) -> dict:
        product = Product(
            work_id=work_id,
            title=title,
            description=description,
            price=price,
            category=category,
            specifications=specifications,
            images=images,
        )
        try:
            self.db.add(product)
            self.db.commit()
            self.db.refresh(product)
        except Exception:
            self.db.rollback()
            raise
        return {"id": product.id}

    def update_product(self, product_id: str, update_data: dict) -> None:
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="商品不存在")
        for key, value in update_data.items():
            if hasattr(product, key) and key != "id":
                setattr(product, key, value)
        try:
            self.db.commit()
            self.db.refresh(product)
        except Exception:
            self.db.rollback()
            raise

    def delete_product(self, product_id: str) -> None:
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="商品不存在")
        try:
            self.db.delete(product)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def get_product(self, product_id: str) -> Product:
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="商品不存在")
        return product

    # ── AI Description ────────────────────────────────────────────────

    def save_ai_description(self, product_id: str, ai_description: str, style: str) -> None:
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="商品不存在")
        product.ai_description = ai_description
        product.ai_desc_platform = style
        product.ai_desc_generated_at = datetime.now(timezone.utc)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    # ── Export ────────────────────────────────────────────────────────

    def export_product_csv(self, product_id: str, platform: str, template: dict) -> dict:
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="商品不存在")

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=template["fields"], extrasaction='ignore')
        writer.writeheader()

        row = {
            "title": product.title,
            "description": product.ai_description or product.description or "",
            "price": product.price,
            "quantity": 1,
            "stock": 1,
            "sku": product.id[:12],
            "images": ",".join(product.images) if product.images else "",
            "category": product.category or "",
            "tags": "原创,创意",
            "specs": str(product.specifications or ""),
            "vendor": "OriStudio",
        }
        writer.writerow(row)

        csv_dir = Path("data/certificates")
        csv_dir.mkdir(parents=True, exist_ok=True)
        csv_path = csv_dir / f"product_{product_id}_{platform}.csv"

        with open(csv_path, "w", encoding="utf-8-sig") as f:
            f.write(output.getvalue())

        product.csv_export_path = str(csv_path)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return {
            "csv_content": output.getvalue(),
            "file_path": str(csv_path),
            "platform": platform,
        }

    def get_product_feed(self, category: Optional[str] = None) -> list:
        query = self.db.query(Product)
        if category:
            query = query.filter(Product.category == category)
        return query.order_by(Product.created_at.desc()).all()

    # ── Publishing ────────────────────────────────────────────────────

    def publish_product(self, product_id: str, platform: str) -> dict:
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="商品不存在")

        publish = ProductPublishing(
            product_id=product.id,
            platform=platform,
            status="published",
            listing_url=f"https://www.{platform}.com/item/{product.id[:12]}",
            published_at=datetime.now(timezone.utc),
        )
        try:
            self.db.add(publish)
            self.db.commit()
            self.db.refresh(publish)
        except Exception:
            self.db.rollback()
            raise
        return {"publish_id": publish.id, "listing_url": publish.listing_url}

    def save_verified_mark(self, product_id: str, qr_code: str, cert_url: str) -> None:
        existing = self.db.query(VerifiedMark).filter(VerifiedMark.product_id == product_id).first()
        if existing:
            existing.qr_code = qr_code
            existing.cert_url = cert_url
        else:
            mark = VerifiedMark(
                product_id=product_id,
                qr_code=qr_code,
                cert_url=cert_url,
            )
            self.db.add(mark)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def get_verified_mark(self, product_id: str) -> Optional[VerifiedMark]:
        return self.db.query(VerifiedMark).filter(VerifiedMark.product_id == product_id).first()

    # ── Revenue ───────────────────────────────────────────────────────

    def get_revenue_summary(self, records: list, period: str) -> dict:
        now = date.today()
        if period == "month":
            filtered = [r for r in records if r.date and r.date.year == now.year and r.date.month == now.month]
            label = f"{now.year}年{now.month}月"
        elif period == "year":
            filtered = [r for r in records if r.date and r.date.year == now.year]
            label = f"{now.year}年"
        else:
            filtered = records
            label = "全部"

        total_amount = sum(r.amount or 0 for r in filtered)
        total_orders = sum(r.order_count or 0 for r in filtered)
        total_refunds = sum(getattr(r, 'refund_amount', 0) or 0 for r in filtered)

        by_platform: dict = {}
        for r in filtered:
            p = r.platform or "unknown"
            by_platform[p] = by_platform.get(p, 0) + (r.amount or 0)

        by_product: dict = {}
        for r in filtered:
            pid = r.product_id or "unknown"
            if pid not in by_product:
                by_product[pid] = {"product_id": pid, "amount": 0, "order_count": 0}
            by_product[pid]["amount"] += r.amount or 0
            by_product[pid]["order_count"] += r.order_count or 0

        monthly_trend: dict = {}
        for r in records:
            if r.date:
                key = r.date.strftime("%Y-%m")
                monthly_trend[key] = monthly_trend.get(key, 0) + (r.amount or 0)

        return {
            "period": period,
            "label": label,
            "total_amount": round(total_amount, 2),
            "total_orders": total_orders,
            "total_refunds": round(total_refunds, 2),
            "platform_count": len(by_platform),
            "by_platform": by_platform,
            "by_product": sorted(by_product.values(), key=lambda x: x["amount"], reverse=True),
            "monthly_trend": dict(sorted(monthly_trend.items())),
        }

    def import_revenue_records(self, rows: list) -> dict:
        imported = 0
        total_amount = 0.0
        errors = []
        for idx, row_data in enumerate(rows, start=1):
            try:
                record = RevenueRecord(
                    platform=row_data.get("platform", "imported"),
                    amount=row_data.get("amount", 0),
                    date=row_data.get("date"),
                    order_count=row_data.get("order_count", 1),
                    notes=row_data.get("notes", "[CSV导入]"),
                )
                self.db.add(record)
                imported += 1
                total_amount += row_data.get("amount", 0)
            except Exception as e:
                errors.append({"row": idx, "error": str(e)})
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return {"imported": imported, "total_amount": round(total_amount, 2), "errors": errors}

    def list_revenue_records(self) -> list:
        """返回所有 RevenueRecord，供 get_revenue_summary 使用."""
        return self.db.query(RevenueRecord).all()

    def list_revenue(self, platform: Optional[str] = None) -> list:
        query = self.db.query(RevenueRecord)
        if platform:
            query = query.filter(RevenueRecord.platform == platform)
        records = query.order_by(RevenueRecord.date.desc()).all()
        return [
            {
                "id": r.id, "product_id": r.product_id,
                "platform": r.platform, "amount": r.amount,
                "currency": r.currency, "date": r.date.isoformat() if r.date else None,
                "order_count": r.order_count, "notes": r.notes,
            }
            for r in records
        ]

    def add_revenue(
        self,
        product_id: Optional[str],
        platform: Optional[str],
        amount: float,
        date_val: date,
        order_count: int,
        notes: Optional[str],
    ) -> None:
        record = RevenueRecord(
            product_id=product_id,
            platform=platform,
            amount=amount,
            date=date_val,
            order_count=order_count,
            notes=notes,
        )
        self.db.add(record)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    # ── Schedules ─────────────────────────────────────────────────────

    def create_schedule(
        self,
        product_id: Optional[str],
        listing_id: Optional[str],
        work_id: Optional[str],
        platform: str,
        scheduled_time: datetime,
        content_preview: Optional[str],
    ) -> None:
        schedule = PublishSchedule(
            product_id=product_id,
            listing_id=listing_id,
            work_id=work_id,
            platform=platform,
            scheduled_time=scheduled_time,
            content_preview=content_preview,
        )
        self.db.add(schedule)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def list_schedules(self) -> list:
        schedules = self.db.query(PublishSchedule).order_by(
            PublishSchedule.scheduled_time.desc()
        ).all()
        return [
            {
                "id": s.id,
                "platform": s.platform,
                "scheduled_time": s.scheduled_time.isoformat() if s.scheduled_time else None,
                "status": s.status,
                "content_preview": s.content_preview,
                "executed_at": s.executed_at.isoformat() if s.executed_at else None,
            }
            for s in schedules
        ]

    def cancel_schedule(self, schedule_id: str) -> None:
        schedule = self.db.query(PublishSchedule).filter(PublishSchedule.id == schedule_id).first()
        if not schedule:
            raise HTTPException(status_code=404, detail="排期不存在")
        if schedule.status != "scheduled":
            raise HTTPException(status_code=400, detail="只能取消待发布的排期")
        schedule.status = "cancelled"
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    # ── Content ───────────────────────────────────────────────────────

    def list_contents(self) -> list:
        contents = self.db.query(PublishContent).order_by(
            PublishContent.created_at.desc()
        ).all()
        return [
            {
                "id": c.id,
                "title": c.title,
                "content_type": c.content_type,
                "text_content": c.text_content,
                "image_paths": c.image_paths,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in contents
        ]

    def create_content(
        self,
        work_id: Optional[str],
        product_id: Optional[str],
        title: str,
        content_type: str,
        text_content: Optional[str],
        image_paths: Optional[list],
    ) -> None:
        content = PublishContent(
            work_id=work_id,
            product_id=product_id,
            title=title,
            content_type=content_type,
            text_content=text_content,
            image_paths=image_paths,
        )
        self.db.add(content)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    # ── Analytics ─────────────────────────────────────────────────────

    def list_analytics(self, platform: Optional[str] = None) -> list:
        query = self.db.query(PublishAnalytics)
        if platform:
            query = query.filter(PublishAnalytics.platform == platform)
        analytics = query.order_by(PublishAnalytics.date.desc()).all()
        return [
            {
                "id": a.id,
                "platform": a.platform,
                "work_id": a.work_id,
                "product_id": a.product_id,
                "views": a.views,
                "likes": a.likes,
                "comments": a.comments,
                "shares": a.shares,
                "saves": a.saves,
                "date": a.date.isoformat() if a.date else None,
                "notes": a.notes,
            }
            for a in analytics
        ]

    def add_analytics(
        self,
        platform: str,
        work_id: Optional[str],
        product_id: Optional[str],
        views: int,
        likes: int,
        comments: int,
        shares: int,
        saves: int,
        date_val: date,
        notes: Optional[str],
    ) -> None:
        analytics = PublishAnalytics(
            platform=platform,
            work_id=work_id,
            product_id=product_id,
            views=views,
            likes=likes,
            comments=comments,
            shares=shares,
            saves=saves,
            date=date_val,
            notes=notes,
        )
        self.db.add(analytics)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
