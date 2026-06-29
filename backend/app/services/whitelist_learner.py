"""白名单学习服务 (P2.3.12).

基于用户操作模式自动建议白名单规则:
- 跟踪 ignore/whitelist 操作中的域名
- 当某域名被忽略超过阈值次数时自动建议加入白名单
- 解析 URL 提取域名模式
"""

from typing import Optional
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.models.monitor_ext import WhitelistSuggestion


def extract_domain_pattern(url: str) -> str:
    """从 URL 提取域名模式."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path.split("/")[0]
        # 移除 www 前缀
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return url


def record_whitelist_action(
    db: Session,
    url: str,
    pattern_type: str = "domain",
) -> Optional[WhitelistSuggestion]:
    """记录用户忽略/白名单操作并学习模式.

    当同一域名模式被操作超过阈值时，生成白名单建议.

    Args:
        db: 数据库会话
        url: 被操作的 URL
        pattern_type: 模式类型 (domain/url/regex)

    Returns:
        如果生成了新的建议则返回，否则返回 None.
    """
    pattern = extract_domain_pattern(url) if pattern_type == "domain" else url

    # 查找现有建议或创建
    existing = db.query(WhitelistSuggestion).filter(
        WhitelistSuggestion.pattern_url == pattern,
    ).first()

    if existing:
        existing.occurrence_count += 1
        existing.last_seen_at = __import__("datetime").datetime.utcnow()
        db.commit()
        return existing
    else:
        suggestion = WhitelistSuggestion(
            pattern_url=pattern,
            pattern_type=pattern_type,
            occurrence_count=1,
            status="suggested",
        )
        db.add(suggestion)
        db.commit()
        db.refresh(suggestion)
        return suggestion


def get_pending_suggestions(
    db: Session,
    min_occurrence: int = 2,
) -> list[WhitelistSuggestion]:
    """获取待处理的白名单建议.

    Args:
        db: 数据库会话
        min_occurrence: 最小出现次数阈值 (默认 2)

    Returns:
        建议列表.
    """
    return db.query(WhitelistSuggestion).filter(
        WhitelistSuggestion.status == "suggested",
        WhitelistSuggestion.occurrence_count >= min_occurrence,
    ).order_by(WhitelistSuggestion.occurrence_count.desc()).all()


def accept_suggestion(
    db: Session,
    suggestion_id: str,
) -> Optional[WhitelistSuggestion]:
    """接受白名单建议."""
    suggestion = db.query(WhitelistSuggestion).filter(
        WhitelistSuggestion.id == suggestion_id
    ).first()
    if not suggestion:
        return None

    suggestion.status = "accepted"
    db.commit()
    db.refresh(suggestion)
    return suggestion


def decline_suggestion(
    db: Session,
    suggestion_id: str,
) -> Optional[WhitelistSuggestion]:
    """拒绝白名单建议."""
    suggestion = db.query(WhitelistSuggestion).filter(
        WhitelistSuggestion.id == suggestion_id
    ).first()
    if not suggestion:
        return None

    suggestion.status = "declined"
    db.commit()
    db.refresh(suggestion)
    return suggestion
