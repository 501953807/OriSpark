"""品牌监测模块 — 品牌 Watch CRUD + 扫描."""

import logging
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.monitor_ext import BrandWatch, BrandScanResult
from app.schemas.monitor import (
    BrandWatchCreate, BrandWatchUpdate, BrandWatchResponse,
    BrandScanResultResponse,
)
from app.schemas.common import ApiResponse
from app.services.logo_detector import generate_mock_ecommerce_results

logger = logging.getLogger(__name__)


class BrandWatchModule:
    """品牌监测模块."""

    def __init__(self, db: Session):
        self.db = db

    def create_watch(self, data: BrandWatchCreate) -> ApiResponse:
        """创建品牌监测."""
        brand = BrandWatch(
            brand_name=data.brand_name,
            brand_logo_path=data.brand_logo_path,
            keywords=data.keywords,
            platforms=data.platforms,
            notes=data.notes,
        )
        self.db.add(brand)
        try:
            self.db.commit()
            self.db.refresh(brand)
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(data=BrandWatchResponse.model_validate(brand))

    def list_watches(self, is_active: Optional[bool] = None) -> ApiResponse:
        """获取品牌监测列表."""
        query = self.db.query(BrandWatch)
        if is_active is not None:
            query = query.filter(BrandWatch.is_active == is_active)
        watches = query.order_by(BrandWatch.created_at.desc()).all()
        return ApiResponse(data=[BrandWatchResponse.model_validate(w) for w in watches])

    def get_watch(self, brand_id: str) -> ApiResponse:
        """获取单个品牌监测."""
        brand = self.db.query(BrandWatch).filter(BrandWatch.id == brand_id).first()
        if not brand:
            raise HTTPException(status_code=404, detail="品牌监测不存在")
        return ApiResponse(data=BrandWatchResponse.model_validate(brand))

    def update_watch(self, brand_id: str, data: BrandWatchUpdate) -> ApiResponse:
        """更新品牌监测."""
        brand = self.db.query(BrandWatch).filter(BrandWatch.id == brand_id).first()
        if not brand:
            raise HTTPException(status_code=404, detail="品牌监测不存在")
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(brand, key, value)
        try:
            self.db.commit()
            self.db.refresh(brand)
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(data=BrandWatchResponse.model_validate(brand))

    def delete_watch(self, brand_id: str) -> ApiResponse:
        """删除品牌监测."""
        brand = self.db.query(BrandWatch).filter(BrandWatch.id == brand_id).first()
        if not brand:
            raise HTTPException(status_code=404, detail="品牌监测不存在")
        self.db.delete(brand)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(message="品牌监测已删除")

    def trigger_scan(self, brand_id: str) -> ApiResponse:
        """触发品牌扫描."""
        brand = self.db.query(BrandWatch).filter(BrandWatch.id == brand_id).first()
        if not brand:
            raise HTTPException(status_code=404, detail="品牌监测不存在")
        platforms = brand.platforms or ["taobao", "jd", "pinduoduo"]
        mock_results = generate_mock_ecommerce_results(brand.brand_name, platforms)
        new_scans = []
        for mr in mock_results:
            existing = self.db.query(BrandScanResult).filter(
                BrandScanResult.brand_id == brand_id,
                BrandScanResult.item_url == mr["item_url"],
            ).first()
            if existing:
                continue
            new_scans.append(BrandScanResult(
                brand_id=brand_id,
                item_url=mr["item_url"],
                item_title=mr["item_title"],
                similarity=mr["similarity"],
                platform=mr["platform"],
                status="pending_review",
                notes="[MOCK DATA] This is a simulated result for testing",
            ))
        self.db.add_all(new_scans)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(
            message=f"Brand scan completed: found {len(new_scans)} new results",
            data={
                "results_count": len(new_scans),
                "is_mock_data": True,
                "new_scans": len(new_scans),
            },
        )

    def get_scan_results(self, brand_id: str, status: Optional[str] = None) -> ApiResponse:
        """获取品牌扫描结果."""
        query = self.db.query(BrandScanResult).filter(
            BrandScanResult.brand_id == brand_id
        )
        if status:
            query = query.filter(BrandScanResult.status == status)
        results = query.order_by(BrandScanResult.found_at.desc()).all()
        return ApiResponse(data=[BrandScanResultResponse.model_validate(r) for r in results])
