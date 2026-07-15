"""AI 生成 API 的 Pydantic schemas — re-exported from the router."""

from typing import Optional

from pydantic import BaseModel, Field


class AutoTagRequest(BaseModel):
    work_id: str


class AutoTagResponse(BaseModel):
    tags: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class AutoDescriptionRequest(BaseModel):
    work_id: str


class AutoDescriptionResponse(BaseModel):
    description: str = ""


class ArticleDraftRequest(BaseModel):
    prompt: str
    tone: str = "professional"
    max_words: int = 2000


class ProductDescRequest(BaseModel):
    product_name: str
    materials: list[str] = Field(default_factory=list)
    techniques: list[str] = Field(default_factory=list)


class MusicDescRequest(BaseModel):
    title: str
    genre: str
    mood: str
    bpm: int


class ModerateRequest(BaseModel):
    text: str


class ModerateResponse(BaseModel):
    safe: bool = True
    categories: dict[str, bool] = Field(default_factory=dict)
    reason: str = ""


class AIConfigResponse(BaseModel):
    configured: bool
    provider: str = "openai"
