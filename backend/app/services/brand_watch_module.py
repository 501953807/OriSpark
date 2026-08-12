"""品牌监测模块 — 品牌 Watch CRUD + 扫描."""

import asyncio
import logging
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.gateway.baidu_vision import BaiduVisionGateway
from app.gateway.google_vision import GoogleVisionGateway
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
        """触发品牌扫描（支持真实网关 / 降级到 mock）."""
        brand = self.db.query(BrandWatch).filter(BrandWatch.id == brand_id).first()
        if not brand:
            raise HTTPException(status_code=404, detail="品牌监测不存在")

        platforms = brand.platforms or ["taobao", "jd", "pinduoduo"]
        logo_path = brand.brand_logo_path or ""

        # 选择扫描网关
        is_mock = True
        real_results: list[dict] = []

        # 尝试百度识图
        if settings.BAIDU_VISION_API_KEY and logo_path:
            baidu = BaiduVisionGateway()
            loop = asyncio.new_event_loop()
            try:
                baidu_results = loop.run_until_complete(baidu.search_image(logo_path))
                real_results.extend([
                    {
                        "item_url": r.url,
                        "item_title": r.title or brand.brand_name,
                        "similarity": r.similarity,
                        "platform": "baidu",
                        "notes": "",
                    }
                    for r in baidu_results
                ])
                is_mock = False
            finally:
                loop.close()

        # 尝试 Google Vision
        if settings.GOOGLE_VISION_API_KEY and logo_path:
            google = GoogleVisionGateway()
            loop = asyncio.new_event_loop()
            try:
                google_results = loop.run_until_complete(google.search_image(logo_path))
                real_results.extend([
                    {
                        "item_url": r.url,
                        "item_title": r.title or brand.brand_name,
                        "similarity": r.similarity,
                        "platform": "google",
                        "notes": "",
                    }
                    for r in google_results
                ])
                is_mock = False
            finally:
                loop.close()

        # 降级到 mock
        if is_mock:
            mock_results = generate_mock_ecommerce_results(brand.brand_name, platforms)
        else:
            mock_results = real_results

        # 写入数据库（去重）
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
                platform=mr.get("platform", "unknown"),
                status="pending_review",
                notes=mr.get("notes", "") if not is_mock else "[MOCK DATA]",
            ))

        self.db.add_all(new_scans)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        engine = "baidu" if (not is_mock and any(r.get("platform") == "baidu" for r in mock_results)) else (
            "google" if not is_mock else "mock"
        )
        return ApiResponse(
            message=f"扫描完成: 发现 {len(new_scans)} 条新结果",
            data={
                "results_count": len(new_scans),
                "is_mock_data": is_mock,
                "new_scans": len(new_scans),
                "scan_engine": engine,
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
