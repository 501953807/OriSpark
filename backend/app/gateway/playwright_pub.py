"""Playwright 浏览器自动化发布适配器."""

import json
from pathlib import Path
from typing import Optional

from app.config import settings


class PlaywrightPublisher:
    """Playwright 自动化发布 — 小红书/抖音/淘宝."""

    def __init__(self, headless: bool = False):
        self.headless = headless
        self._session_dir = Path("data/config")
        self._session_dir.mkdir(parents=True, exist_ok=True)

    async def connect_oauth(self, platform: str, auth_code: str) -> dict:
        """模拟 OAuth 连接流程."""
        # 实际实现: 启动 Playwright 浏览器, 打开平台登录页
        # 用户完成扫码/密码登录, 保存 session
        session_file = self._session_dir / f"{platform}_session.json"
        session_data = {
            "platform": platform,
            "auth_code": auth_code,
            "connected_at": str(Path(session_file).stat().st_mtime) if session_file.exists() else None,
        }
        # 加密保存 session
        with open(session_file, "w") as f:
            json.dump(session_data, f)

        return {"status": "connected", "platform": platform}

    async def publish_product(
        self,
        platform: str,
        product_data: dict,
        images: list[str],
    ) -> dict:
        """发布商品到平台."""
        # 实际实现: 启动/复用 Playwright 浏览器
        # 1. 打开平台发布页
        # 2. 自动填写: title, description, price, category
        # 3. 上传图片
        # 4. 提交发布

        # 模拟发布成功
        return {
            "status": "published",
            "platform": platform,
            "listing_url": self._mock_listing_url(platform, product_data.get("id", "")),
            "publish_id": f"pub_{hash(str(product_data))}",
        }

    async def check_publish_status(self, publish_id: str) -> str:
        """查询发布状态."""
        return "published"

    def _mock_listing_url(self, platform: str, product_id: str) -> str:
        """生成模拟 listing URL."""
        urls = {
            "taobao": f"https://item.taobao.com/item.htm?id={product_id}",
            "xiaohongshu": f"https://www.xiaohongshu.com/explore/{product_id}",
            "douyin": f"https://www.douyin.com/video/{product_id}",
            "shopify": f"https://shop.myshopify.com/products/{product_id}",
        }
        return urls.get(platform, f"https://{platform}.com/item/{product_id}")
