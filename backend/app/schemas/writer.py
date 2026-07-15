"""文字作者 Pydantic schemas (P4: 文章/书籍/手稿)."""

from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field


# ============================================================================
# Article schemas
# ============================================================================


class ArticleCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    subtitle: Optional[str] = Field(None, max_length=300)
    content: Optional[str] = None
    excerpt: Optional[str] = Field(None, max_length=1000)
    author_id: Optional[str] = Field(None, max_length=32)
    work_variant_id: Optional[str] = Field(None, max_length=32)
    category: Optional[str] = Field(None, max_length=50)
    tags: Optional[list[str]] = None
    word_count: Optional[int] = None
    reading_time_minutes: Optional[int] = None
    status: str = Field(default="draft", pattern=r"^(draft|published|archived)$")


class ArticleUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=300)
    subtitle: Optional[str] = Field(None, max_length=300)
    content: Optional[str] = None
    excerpt: Optional[str] = Field(None, max_length=1000)
    author_id: Optional[str] = Field(None, max_length=32)
    work_variant_id: Optional[str] = Field(None, max_length=32)
    category: Optional[str] = Field(None, max_length=50)
    tags: Optional[list[str]] = None
    word_count: Optional[int] = None
    reading_time_minutes: Optional[int] = None
    status: Optional[str] = Field(None, pattern=r"^(draft|published|archived)$")


class ArticleSchema(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    title: str
    subtitle: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    author_id: Optional[str] = None
    work_variant_id: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list[str]] = None
    word_count: Optional[int] = None
    reading_time_minutes: Optional[int] = None
    status: str
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Book schemas
# ============================================================================


class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    author_id: Optional[str] = Field(None, max_length=32)
    cover_path: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    genre: Optional[str] = Field(None, max_length=50)
    publisher: Optional[str] = Field(None, max_length=200)
    isbn: Optional[str] = Field(None, max_length=13)
    total_chapters: Optional[int] = None
    total_word_count: Optional[int] = None
    publication_date: Optional[datetime] = None
    status: str = Field(default="writing", pattern=r"^(writing|published|archived)$")


class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=300)
    author_id: Optional[str] = Field(None, max_length=32)
    cover_path: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    genre: Optional[str] = Field(None, max_length=50)
    publisher: Optional[str] = Field(None, max_length=200)
    isbn: Optional[str] = Field(None, max_length=13)
    total_chapters: Optional[int] = None
    total_word_count: Optional[int] = None
    publication_date: Optional[datetime] = None
    status: Optional[str] = Field(None, pattern=r"^(writing|published|archived)$")


class BookSchema(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    title: str
    author_id: Optional[str] = None
    cover_path: Optional[str] = None
    description: Optional[str] = None
    genre: Optional[str] = None
    publisher: Optional[str] = None
    isbn: Optional[str] = None
    total_chapters: Optional[int] = None
    total_word_count: Optional[int] = None
    publication_date: Optional[datetime] = None
    status: str
    created_at: datetime
    updated_at: datetime


class WriterStatsResponse(BaseModel):
    total_articles: int = 0
    total_books: int = 0
    total_manuscripts: int = 0
    total_words: int = 0
    published_count: int = 0
    draft_count: int = 0
    active_books: int = 0
    monthly_reads: int = 0


# ============================================================================
# Manuscript schemas
# ============================================================================


class ManuscriptCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    book_id: Optional[str] = Field(None, max_length=32)
    chapter_number: Optional[int] = None
    content: Optional[str] = None
    word_count: Optional[int] = None
    status: str = Field(default="draft", pattern=r"^(draft|revising|final)$")
    version: int = Field(default=1, ge=1)


class ManuscriptUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=300)
    book_id: Optional[str] = Field(None, max_length=32)
    chapter_number: Optional[int] = None
    content: Optional[str] = None
    word_count: Optional[int] = None
    status: Optional[str] = Field(None, pattern=r"^(draft|revising|final)$")
    version: Optional[int] = Field(None, ge=1)


class ManuscriptSchema(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    title: str
    book_id: Optional[str] = None
    chapter_number: Optional[int] = None
    content: Optional[str] = None
    word_count: Optional[int] = None
    status: str
    version: int
    created_at: datetime
    updated_at: datetime
