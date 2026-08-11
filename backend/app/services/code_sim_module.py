"""代码相似度检测模块."""

import logging
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.schemas.monitor import CodeSimilarityRequest, CodeSimilarityResponse
from app.schemas.common import ApiResponse
from app.services.code_similarity import compare_code_snippets

logger = logging.getLogger(__name__)


class CodeSimModule:
    """代码相似度检测模块."""

    def __init__(self, db: Session):
        self.db = db

    def compare(self, data: CodeSimilarityRequest) -> ApiResponse:
        """比较代码相似度."""
        result = compare_code_snippets(data.code_a, data.code_b)
        return ApiResponse(
            data=CodeSimilarityResponse(
                similarity=result["similarity"],
                match_type=result["match_type"],
                details=result["details"],
            )
        )
