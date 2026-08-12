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
        # Convert result to dict
        if hasattr(result, 'model_dump'):
            result_dict = result.model_dump()
        elif isinstance(result, dict):
            result_dict = result
        else:
            result_dict = {"similarity": 0, "match_type": "unknown", "details": "", "structure_similarity": 0, "keyword_similarity": 0, "code_a": data.code_a, "code_b": data.code_b, "is_mock": True, "message": "Mock result"}
        return ApiResponse(
            data=CodeSimilarityResponse(
                code_a=data.code_a,
                code_b=data.code_b,
                similarity=result_dict.get("similarity", 0),
                structure_similarity=result_dict.get("structure_similarity", 0),
                keyword_similarity=result_dict.get("keyword_similarity", 0),
                is_mock=result_dict.get("is_mock", True),
                message=result_dict.get("message", ""),
            )
        )
