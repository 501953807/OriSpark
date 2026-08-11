"""白名单学习模块."""

import logging
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.monitor_ext import WhitelistSuggestion
from app.schemas.monitor import WhitelistActionRequest
from app.schemas.common import ApiResponse
from app.services.whitelist_learner import (
    record_whitelist_action, get_pending_suggestions,
    accept_suggestion, decline_suggestion,
)

logger = logging.getLogger(__name__)


class WhitelistModule:
    """白名单学习模块."""

    def __init__(self, db: Session):
        self.db = db

    def list_suggestions(self) -> ApiResponse:
        """获取待处理白名单建议."""
        suggestions = get_pending_suggestions(self.db)
        return ApiResponse(data=[
            {
                "id": s.id,
                "matched_url": s.matched_url,
                "pattern_type": s.pattern_type,
                "confidence": s.confidence,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in suggestions
        ])

    def handle_action(self, data: WhitelistActionRequest) -> ApiResponse:
        """处理白名单动作."""
        if data.action == "accept":
            accept_suggestion(self.db, data.suggestion_id)
        elif data.action == "decline":
            decline_suggestion(self.db, data.suggestion_id)
        else:
            raise HTTPException(status_code=400, detail=f"未知动作: {data.action}")
        return ApiResponse(message=f"白名单动作已处理: {data.action}")
