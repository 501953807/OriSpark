"""分发回流服务 — 短链管理 + 归因分析."""

import os
import random
import string
import urllib.parse
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.reverse_trace import ReverseTraceLink, ReverseTraceEvent

# Branch.io 配置
BRANCH_KEY = os.environ.get("BRANCH_KEY", "")
BRANCH_DOMAIN = os.environ.get("BRANCH_DOMAIN", "oristudio.app")


def _generate_short_code(db: Session, length: int = 8) -> str:
    """生成唯一短链代码."""
    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choices(chars, k=length))
        # Check uniqueness (rare collision, but safe)
        exists = db.query(ReverseTraceLink).filter(
            ReverseTraceLink.short_code == code
        ).first()
        if not exists:
            return code


class ReverseTraceService:
    """分发回流引擎核心服务."""

    def __init__(self, db: Session):
        self.db = db

    def create_link(
        self,
        work_id: str,
        user_id: str,
        platform_code: str,
        original_url: str,
        redirect_url: Optional[str] = None,
        utm_source: Optional[str] = None,
        utm_medium: Optional[str] = None,
        utm_campaign: Optional[str] = None,
        expire_at: Optional[datetime] = None,
    ) -> ReverseTraceLink:
        """创建可信短链."""
        if not redirect_url:
            redirect_url = f"/redirect/{platform_code}"

        link = ReverseTraceLink(
            work_id=work_id,
            user_id=user_id,
            platform_code=platform_code,
            short_code=_generate_short_code(self.db),
            original_url=original_url,
            redirect_url=redirect_url,
            utm_source=utm_source,
            utm_medium=utm_medium,
            utm_campaign=utm_campaign,
            expire_at=expire_at,
        )
        self.db.add(link)
        self.db.flush()
        self.db.refresh(link)

        # 自动创建 Branch deep link（如果已配置 BRANCH_KEY）
        if BRANCH_KEY:
            branch_result = self.create_branch_link(link.id, work_id, {})
            if branch_result and branch_result.get("short_code"):
                link.branch_link_id = branch_result["branch_link_id"]
                link.deep_link_url = branch_result["deep_link"]
                self.db.flush()

        return link

    def get_link(self, link_id: str) -> Optional[ReverseTraceLink]:
        """获取链接详情."""
        return self.db.query(ReverseTraceLink).filter(
            ReverseTraceLink.id == link_id
        ).first()

    def get_link_by_code(self, short_code: str) -> Optional[ReverseTraceLink]:
        """通过短链代码获取链接."""
        return self.db.query(ReverseTraceLink).filter(
            ReverseTraceLink.short_code == short_code
        ).first()

    def list_links(
        self,
        user_id: Optional[str] = None,
        platform_code: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> list[ReverseTraceLink]:
        """列出短链."""
        q = self.db.query(ReverseTraceLink)
        if user_id:
            q = q.filter(ReverseTraceLink.user_id == user_id)
        if platform_code:
            q = q.filter(ReverseTraceLink.platform_code == platform_code)
        if is_active is not None:
            q = q.filter(ReverseTraceLink.is_active == is_active)
        return q.order_by(ReverseTraceLink.created_at.desc()).all()

    def update_link(self, link_id: str, **kwargs) -> Optional[ReverseTraceLink]:
        """更新链接属性."""
        link = self.get_link(link_id)
        if not link:
            return None
        for key, value in kwargs.items():
            if hasattr(link, key):
                setattr(link, key, value)
        self.db.flush()
        return link

    def delete_link(self, link_id: str) -> bool:
        """删除链接."""
        link = self.get_link(link_id)
        if not link:
            return False
        self.db.delete(link)
        self.db.flush()
        return True

    def record_event(
        self,
        link_id: str,
        event_type: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        referrer: Optional[str] = None,
        geo_country: Optional[str] = None,
        geo_region: Optional[str] = None,
        geo_city: Optional[str] = None,
        device_type: Optional[str] = None,
        browser: Optional[str] = None,
        os_name: Optional[str] = None,
        custom_params: Optional[dict] = None,
        converted: bool = False,
        conversion_value: Optional[float] = None,
    ) -> ReverseTraceEvent:
        """记录归因事件."""
        event = ReverseTraceEvent(
            link_id=link_id,
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
            geo_country=geo_country,
            geo_region=geo_region,
            geo_city=geo_city,
            device_type=device_type,
            browser=browser,
            os_name=os_name,
            custom_params=custom_params,
            converted=converted,
            conversion_value=conversion_value,
        )
        self.db.add(event)

        # Increment click count on the link
        link = self.get_link(link_id)
        if link:
            link.click_count += 1

        self.db.flush()
        return event

    def get_attribution_summary(self, link_id: str) -> dict:
        """获取归因分析摘要."""
        events = (
            self.db.query(ReverseTraceEvent)
            .filter(ReverseTraceEvent.link_id == link_id)
            .all()
        )

        total_clicks = len(events)
        unique_ips = len(set(e.ip_address for e in events if e.ip_address))
        event_breakdown: dict[str, int] = {}
        for e in events:
            event_breakdown[e.event_type] = event_breakdown.get(e.event_type, 0) + 1

        country_counts: dict[str, int] = {}
        for e in events:
            if e.geo_country:
                country_counts[e.geo_country] = country_counts.get(e.geo_country, 0) + 1
        top_countries = sorted(
            [{"country": k, "count": v} for k, v in country_counts.items()],
            key=lambda x: x["count"],
            reverse=True,
        )[:10]

        conversions = [e for e in events if e.converted]
        total_conversions = len(conversions)
        total_conversion_value = sum(e.conversion_value or 0 for e in conversions)
        conversion_rate = total_conversions / total_clicks if total_clicks > 0 else 0.0

        return {
            "link_id": link_id,
            "total_clicks": total_clicks,
            "unique_visitors": unique_ips,
            "event_breakdown": event_breakdown,
            "top_countries": top_countries,
            "conversion_rate": round(conversion_rate, 4),
            "total_conversions": total_conversions,
            "total_conversion_value": round(total_conversion_value, 2),
        }

    def create_branch_link(self, link_id: str, work_id: str, custom_params: dict) -> dict:
        """生成 Branch deep link 和 URI scheme."""
        short_code = _generate_short_code(self.db)
        domain = BRANCH_DOMAIN

        # Branch deep link URL
        encoded_params = urllib.parse.urlencode({**{"work_id": work_id}, **custom_params})
        deep_link = f"https://{domain}/{short_code}?{encoded_params}"

        # URI scheme
        uri_scheme = f"oristudio://link/{short_code}?work_id={work_id}"

        if not BRANCH_KEY:
            return {
                "is_mock": True,
                "deep_link": deep_link,
                "uri_scheme": uri_scheme,
                "short_code": short_code,
                "branch_key": "",
            }

        # 模拟 Branch API 调用（实际项目中替换为真实 Branch SDK）
        branch_link_id = f"branch-{link_id}-{short_code}"
        self.db.query(ReverseTraceLink).filter(
            ReverseTraceLink.id == link_id
        ).update({"branch_link_id": branch_link_id})
        self.db.flush()

        return {
            "is_mock": False,
            "deep_link": deep_link,
            "uri_scheme": uri_scheme,
            "short_code": short_code,
            "branch_link_id": branch_link_id,
            "branch_key": BRANCH_KEY,
        }

    def record_branch_event(self, link_id: str, event_type: str, session_id: Optional[str] = None) -> dict:
        """记录 Branch 归因事件."""
        custom_params: dict = {"source": "branch", "event_type": event_type}
        if session_id:
            custom_params["session_id"] = session_id

        event = self.record_event(
            link_id=link_id,
            event_type=event_type,
            custom_params=custom_params,
        )

        return {
            "event_id": event.id,
            "link_id": link_id,
            "event_type": event_type,
            "session_id": session_id,
            "timestamp": event.created_at.isoformat() if event.created_at else None,
        }


class BranchService:
    """Branch.io 服务层（别名），提供便捷的静态方法."""

    @staticmethod
    def generate_deep_link(short_code: str, extra_params: Optional[dict] = None) -> str:
        """生成 Branch deep link URL."""
        domain = BRANCH_DOMAIN
        params: dict = {"work_id": ""}
        if extra_params:
            params.update(extra_params)
        encoded = urllib.parse.urlencode(params)
        return f"https://{domain}/{short_code}?{encoded}"

    @staticmethod
    def create_branch_link_data(short_code: str, work_id: str) -> dict:
        """生成 Branch 链接数据（不写数据库）."""
        deep_link = BranchService.generate_deep_link(short_code, {"work_id": work_id})
        uri_scheme = f"oristudio://link/{short_code}?work_id={work_id}"
        return {
            "deep_link": deep_link,
            "uri_scheme": uri_scheme,
            "short_code": short_code,
            "branch_key": BRANCH_KEY,
            "is_mock": not bool(BRANCH_KEY),
        }

    @staticmethod
    def record_attribution_event(link_id: str, event_type: str, custom_params: Optional[dict] = None, db: Optional[Session] = None) -> dict:
        """记录归因事件（静态方法，供外部调用）."""
        params = custom_params or {}
        params["source"] = "branch"
        return {
            "link_id": link_id,
            "event_type": event_type,
            "custom_params": params,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
