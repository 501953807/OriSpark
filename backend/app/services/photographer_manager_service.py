# -*- coding: utf-8 -*-
"""摄影师管理服务层 — 封装 photographer router 中的所有 DB 操作."""

import uuid
from datetime import datetime, timezone
from math import radians, sin, cos, sqrt, atan2
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.work_variant import WorkVariant
from app.models.photographer_v2 import (
    RawFormat, DigitalDownload, FineArtPrintConfig,
    StockUpload, StockSale, StockChannel,
)
from app.schemas.photographer import (
    ShotResponse, ShotListResponse, ShotStatusUpdate,
    GPSPoint, GPSMapResponse, StockChannelInfo, StockUploadResult,
    StockSalesResponse, PhotographerStatsResponse, ShotStats,
    RawFormatSchema, DigitalDownloadSchema, FineArtPrintConfigSchema,
)


class PhotographerManagerService:
    """摄影师业务逻辑服务，封装所有 DB 操作."""

    def __init__(self, db: Session):
        self.db = db

    # ── Shots ─────────────────────────────────────────────────────────

    def list_shots(
        self,
        shot_status: Optional[str] = None,
        camera_model: Optional[str] = None,
        group_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        q = self.db.query(WorkVariant)
        if shot_status:
            q = q.filter(WorkVariant.shot_status == shot_status)
        if camera_model:
            q = q.filter(WorkVariant.camera_model == camera_model)
        if group_id:
            q = q.filter(WorkVariant.group_id == group_id)

        total = q.count()
        items = (
            q.order_by(WorkVariant.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        total_pages = max(1, (total + page_size - 1) // page_size)
        return {
            "items": [self._variant_to_dict(v) for v in items],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def update_shot_status(self, variant_id: str, payload: ShotStatusUpdate) -> dict:
        variant = self.db.query(WorkVariant).filter(WorkVariant.id == variant_id).first()
        if not variant:
            raise HTTPException(status_code=404, detail="作品变体不存在")

        variant.shot_status = payload.shot_status
        if payload.shot_notes is not None:
            variant.shot_notes = payload.shot_notes
        variant.updated_at = datetime.now(timezone.utc)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(variant)
        return self._variant_to_dict(variant)

    # ── EXIF Search ───────────────────────────────────────────────────

    def search_exif(
        self,
        camera_model: Optional[str] = None,
        lens: Optional[str] = None,
        iso_min: Optional[int] = None,
        iso_max: Optional[int] = None,
        aperture: Optional[str] = None,
        shutter_speed: Optional[str] = None,
        focal_length: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        q = self.db.query(WorkVariant).filter(WorkVariant.camera_model.isnot(None))

        if camera_model:
            q = q.filter(WorkVariant.camera_model.ilike(f"%{camera_model}%"))
        if lens:
            q = q.filter(WorkVariant.lens.ilike(f"%{lens}%"))
        if iso_min is not None:
            q = q.filter(WorkVariant.iso >= iso_min)
        if iso_max is not None:
            q = q.filter(WorkVariant.iso <= iso_max)
        if aperture:
            q = q.filter(WorkVariant.aperture == aperture)
        if shutter_speed:
            q = q.filter(WorkVariant.shutter_speed == shutter_speed)
        if focal_length:
            q = q.filter(WorkVariant.focal_length == focal_length)

        total = q.count()
        items = (
            q.order_by(WorkVariant.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        total_pages = max(1, (total + page_size - 1) // page_size)
        return {
            "items": [self._variant_to_dict(v) for v in items],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    # ── GPS Map ───────────────────────────────────────────────────────

    def get_gps_map(self, group_id: Optional[str] = None) -> list:
        q = self.db.query(WorkVariant).filter(
            WorkVariant.gps_latitude.isnot(None),
            WorkVariant.gps_longitude.isnot(None),
        )
        if group_id:
            q = q.filter(WorkVariant.group_id == group_id)
        points = [
            GPSPoint(
                id=v.id,
                name=v.name,
                latitude=v.gps_latitude,
                longitude=v.gps_longitude,
                altitude=v.gps_altitude,
                camera_model=v.camera_model,
            )
            for v in q.order_by(WorkVariant.created_at.desc()).all()
        ]
        return {"points": points, "total": len(points)}

    # ── Stock Channels ────────────────────────────────────────────────

    def add_stock_channel(self, variant_id: str, channel: str, status: str, remote_id: str) -> dict:
        variant = self.db.query(WorkVariant).filter(WorkVariant.id == variant_id).first()
        if not variant:
            raise HTTPException(status_code=404, detail="作品变体不存在")

        channels = variant.stock_channels or []
        existing_idx = next(
            (i for i, c in enumerate(channels) if c.get("channel") == channel),
            None,
        )
        channel_entry = {
            "channel": channel,
            "status": status,
            "remote_id": remote_id,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if existing_idx is not None:
            channels[existing_idx] = channel_entry
        else:
            channels.append(channel_entry)

        variant.stock_channels = channels
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(variant)

        return {
            "channel": channel,
            "status": status,
            "remote_id": remote_id,
            "updated_at": datetime.fromisoformat(channel_entry["updated_at"]),
        }

    def remove_stock_channel(self, variant_id: str, channel: str) -> None:
        variant = self.db.query(WorkVariant).filter(WorkVariant.id == variant_id).first()
        if not variant:
            raise HTTPException(status_code=404, detail="作品变体不存在")

        channels = variant.stock_channels or []
        updated_channels = [c for c in channels if c.get("channel") != channel]

        if len(updated_channels) == len(channels):
            raise HTTPException(status_code=404, detail=f"渠道 {channel} 未找到")

        variant.stock_channels = updated_channels
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    # ── Stats ─────────────────────────────────────────────────────────

    def get_photographer_stats(self, group_id: Optional[str] = None) -> dict:
        q = self.db.query(WorkVariant)
        if group_id:
            q = q.filter(WorkVariant.group_id == group_id)

        total = q.count()
        pass_count = self.db.query(func.count(WorkVariant.id)).filter(
            WorkVariant.shot_status == "pass",
        ).count()
        hold_count = self.db.query(func.count(WorkVariant.id)).filter(
            WorkVariant.shot_status == "hold",
        ).count()
        reject_count = self.db.query(func.count(WorkVariant.id)).filter(
            WorkVariant.shot_status == "reject",
        ).count()
        shortlist_count = self.db.query(func.count(WorkVariant.id)).filter(
            WorkVariant.shot_status == "shortlist",
        ).count()
        unreviewed_count = self.db.query(func.count(WorkVariant.id)).filter(
            WorkVariant.shot_status == "unreviewed",
        ).count()
        raw_file_count = self.db.query(func.count(WorkVariant.id)).filter(
            WorkVariant.raw_file_path.isnot(None),
        ).count()
        stock_channel_count = self.db.query(func.count(WorkVariant.id)).filter(
            WorkVariant.stock_channels.isnot(None),
        ).count()
        gps_tracked_count = self.db.query(func.count(WorkVariant.id)).filter(
            WorkVariant.gps_latitude.isnot(None),
            WorkVariant.gps_longitude.isnot(None),
        ).count()

        recent = (
            self.db.query(WorkVariant)
            .order_by(WorkVariant.created_at.desc())
            .limit(10)
            .all()
        )
        recent_activity = [
            {
                "id": v.id,
                "name": v.name,
                "shot_status": v.shot_status,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in recent
        ]

        return {
            "stats": ShotStats(
                total_variants=total,
                pass_count=pass_count,
                hold_count=hold_count,
                reject_count=reject_count,
                shortlist_count=shortlist_count,
                unreviewed_count=unreviewed_count,
                raw_file_count=raw_file_count,
                stock_channel_count=stock_channel_count,
                gps_tracked_count=gps_tracked_count,
            ),
            "recent_activity": recent_activity,
        }

    # ── Stock Uploads ─────────────────────────────────────────────────

    def list_stock_uploads(
        self,
        channel_id: Optional[str] = None,
        status: Optional[str] = None,
        work_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        q = self.db.query(StockUpload)
        if channel_id:
            q = q.filter(StockUpload.channel_id == channel_id)
        if status:
            q = q.filter(StockUpload.status == status)
        if work_id:
            q = q.filter(StockUpload.work_id == work_id)

        total = q.count()
        items = (
            q.order_by(StockUpload.uploaded_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        total_pages = max(1, (total + page_size - 1) // page_size)
        return {
            "items": [
                StockUploadResult(
                    id=i.id,
                    channel_id=i.channel_id,
                    work_id=i.work_id,
                    remote_id=i.remote_id or "",
                    status=i.status,
                    uploaded_at=i.uploaded_at.isoformat() if i.uploaded_at else None,
                )
                for i in items
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def get_stock_sales(
        self,
        channel_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        ch = self.db.query(StockChannel).filter(StockChannel.id == channel_id).first()
        if not ch:
            raise HTTPException(status_code=404, detail=f"Channel {channel_id} not found")

        q = self.db.query(StockSale).filter(
            StockSale.sale_amount.isnot(None),
        )

        if start_date:
            q = q.filter(StockSale.sale_date >= datetime.fromisoformat(start_date))
        if end_date:
            q = q.filter(StockSale.sale_date <= datetime.fromisoformat(end_date))

        total_sales = q.count()
        total_rev = q.with_entities(func.coalesce(func.sum(StockSale.sale_amount))).scalar() or 0.0
        currency = q.with_entities(func.coalesce(func.max(StockSale.currency))).scalar() or "USD"

        records = q.order_by(StockSale.sale_date.desc()).limit(50).all()

        return {
            "channel_name": ch.channel_name,
            "total_sales": total_sales,
            "total_revenue": round(total_rev, 2),
            "currency": currency,
            "records": [
                {
                    "id": r.id,
                    "sale_amount": r.sale_amount,
                    "license_type": r.license_type,
                    "sale_date": r.sale_date.isoformat() if r.sale_date else None,
                }
                for r in records
            ],
        }

    def sync_sales_summary(self, channel_id: str, sd, ed) -> dict:
        ch = self.db.query(StockChannel).filter(StockChannel.id == channel_id).first()
        if not ch:
            raise HTTPException(status_code=404, detail=f"Channel {channel_id} not found")

        total_sales = self.db.query(func.count(StockSale.id)).filter(
            StockSale.sale_amount.isnot(None),
            StockSale.sale_date >= sd,
            StockSale.sale_date <= ed,
        ).scalar() or 0
        total_rev = self.db.query(func.coalesce(func.sum(StockSale.sale_amount))).filter(
            StockSale.sale_date >= sd, StockSale.sale_date <= ed,
        ).scalar() or 0.0

        return {
            "channel_name": ch.channel_name,
            "total_sales": total_sales,
            "total_revenue": round(float(total_rev), 2),
            "records": [],
        }

    def validate_stock_file(self, work_id: str) -> dict:
        v = self.db.query(WorkVariant).filter(WorkVariant.id == work_id).first()
        if not v:
            raise HTTPException(status_code=404, detail="Work variant not found")
        return {"variant_id": v.id}

    def get_variant_with_file_path(self, work_id: str) -> tuple:
        """查询作品变体及其文件路径，供 validate 端点使用."""
        from app.models.work_variant import WorkVariant
        from app.models.work import Work
        v = self.db.query(WorkVariant).filter(WorkVariant.id == work_id).first()
        if not v:
            raise HTTPException(status_code=404, detail="Work variant not found")
        file_path = v.storage_path if hasattr(v, "storage_path") and v.storage_path else None
        if not file_path:
            work_id_for_file = None
            if hasattr(v, "group") and hasattr(v.group, "work_id"):
                work_id_for_file = v.group.work_id
            elif hasattr(v, "work_id"):
                work_id_for_file = v.work_id
            if work_id_for_file:
                w = self.db.query(Work).filter(Work.id == work_id_for_file).first()
                if w and hasattr(w, "file_path") and w.file_path:
                    file_path = w.file_path
        return v, file_path

    # ── RAW Formats CRUD ──────────────────────────────────────────────

    def list_raw_formats(self) -> list:
        items = self.db.query(RawFormat).order_by(RawFormat.created_at.desc()).all()
        return [RawFormatSchema.model_validate(i).model_dump() for i in items]

    def create_raw_format(
        self,
        work_id: str,
        file_extension: str,
        file_size_bytes: Optional[int],
        sensor_width: Optional[int],
        sensor_height: Optional[int],
        color_space: Optional[str],
    ) -> dict:
        raw = RawFormat(
            work_id=work_id,
            file_extension=file_extension,
            file_size_bytes=file_size_bytes,
            sensor_width=sensor_width,
            sensor_height=sensor_height,
            color_space=color_space,
        )
        try:
            self.db.add(raw)
            self.db.commit()
            self.db.refresh(raw)
        except Exception:
            self.db.rollback()
            raise
        return {"id": raw.id}

    def update_raw_format(self, raw_id: str, update_data: dict) -> None:
        raw = self.db.query(RawFormat).filter(RawFormat.id == raw_id).first()
        if not raw:
            raise HTTPException(status_code=404, detail="RAW 记录不存在")
        for key, value in update_data.items():
            setattr(raw, key, value)
        try:
            self.db.commit()
            self.db.refresh(raw)
        except Exception:
            self.db.rollback()
            raise

    def delete_raw_format(self, raw_id: str) -> None:
        raw = self.db.query(RawFormat).filter(RawFormat.id == raw_id).first()
        if not raw:
            raise HTTPException(status_code=404, detail="RAW 记录不存在")
        try:
            self.db.delete(raw)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    # ── Digital Downloads CRUD ────────────────────────────────────────

    def list_digital_downloads(self) -> list:
        items = self.db.query(DigitalDownload).order_by(DigitalDownload.created_at.desc()).all()
        return [DigitalDownloadSchema.model_validate(i).model_dump() for i in items]

    def create_digital_download(
        self,
        work_id: str,
        product_id: str,
        download_url: str,
        max_downloads: Optional[int],
    ) -> dict:
        dd = DigitalDownload(
            work_id=work_id,
            product_id=product_id,
            download_url=download_url,
            max_downloads=max_downloads,
        )
        try:
            self.db.add(dd)
            self.db.commit()
            self.db.refresh(dd)
        except Exception:
            self.db.rollback()
            raise
        return {"id": dd.id}

    def update_digital_download(self, dd_id: str, update_data: dict) -> None:
        dd = self.db.query(DigitalDownload).filter(DigitalDownload.id == dd_id).first()
        if not dd:
            raise HTTPException(status_code=404, detail="数字预设包不存在")
        for key, value in update_data.items():
            setattr(dd, key, value)
        try:
            self.db.commit()
            self.db.refresh(dd)
        except Exception:
            self.db.rollback()
            raise

    def delete_digital_download(self, dd_id: str) -> None:
        dd = self.db.query(DigitalDownload).filter(DigitalDownload.id == dd_id).first()
        if not dd:
            raise HTTPException(status_code=404, detail="数字预设包不存在")
        try:
            self.db.delete(dd)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    # ── Fine Art Prints CRUD ──────────────────────────────────────────

    def list_fine_art_prints(self) -> list:
        items = self.db.query(FineArtPrintConfig).order_by(FineArtPrintConfig.created_at.desc()).all()
        return [FineArtPrintConfigSchema.model_validate(i).model_dump() for i in items]

    def create_fine_art_print(
        self,
        work_id: str,
        paper_type: str,
        max_width_cm: float,
        max_height_cm: float,
        framing_available: bool,
        price_multiplier: float,
    ) -> dict:
        fap = FineArtPrintConfig(
            work_id=work_id,
            paper_type=paper_type,
            max_width_cm=max_width_cm,
            max_height_cm=max_height_cm,
            framing_available=framing_available,
            price_multiplier=price_multiplier,
        )
        try:
            self.db.add(fap)
            self.db.commit()
            self.db.refresh(fap)
        except Exception:
            self.db.rollback()
            raise
        return {"id": fap.id}

    def update_fine_art_print(self, fap_id: str, update_data: dict) -> None:
        fap = self.db.query(FineArtPrintConfig).filter(FineArtPrintConfig.id == fap_id).first()
        if not fap:
            raise HTTPException(status_code=404, detail="艺术微喷配置不存在")
        for key, value in update_data.items():
            setattr(fap, key, value)
        try:
            self.db.commit()
            self.db.refresh(fap)
        except Exception:
            self.db.rollback()
            raise

    def delete_fine_art_print(self, fap_id: str) -> None:
        fap = self.db.query(FineArtPrintConfig).filter(FineArtPrintConfig.id == fap_id).first()
        if not fap:
            raise HTTPException(status_code=404, detail="艺术微喷配置不存在")
        try:
            self.db.delete(fap)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    # ── Helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _variant_to_dict(v: WorkVariant) -> dict:
        return ShotResponse.model_validate(v).model_dump()
