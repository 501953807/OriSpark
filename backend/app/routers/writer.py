"""文字作者 CRUD 路由 (P4: 文章/书籍/手稿).

端点: 15 (writer)
- GET/POST   /writer/articles
- GET/PATCH/DELETE /writer/articles/{id}
- GET/POST/PATCH/DELETE /writer/books/{id}
- GET/POST/PATCH/DELETE /writer/manuscripts/{id}
"""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.article import Article
from app.models.book import Book
from app.models.manuscript import Manuscript
from app.schemas.writer import (
    ArticleCreate, ArticleUpdate, ArticleSchema,
    BookCreate, BookUpdate, BookSchema,
    ManuscriptCreate, ManuscriptUpdate, ManuscriptSchema,
    WriterStatsResponse,
)
from app.schemas.common import ApiResponse, PaginatedResponse, PaginationParams
from app.deps import require_auth

router = APIRouter()


# ============================================================================
# Helpers
# ============================================================================


def _article_to_dict(a: Article) -> dict:
    return {
        "id": a.id,
        "title": a.title,
        "subtitle": a.subtitle,
        "content": a.content,
        "excerpt": a.excerpt,
        "author_id": a.author_id,
        "work_variant_id": a.work_variant_id,
        "category": a.category,
        "tags": a.tags,
        "word_count": a.word_count,
        "reading_time_minutes": a.reading_time_minutes,
        "status": a.status,
        "published_at": a.published_at.isoformat() if a.published_at else None,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
    }


def _book_to_dict(b: Book) -> dict:
    return {
        "id": b.id,
        "title": b.title,
        "author_id": b.author_id,
        "cover_path": b.cover_path,
        "description": b.description,
        "genre": b.genre,
        "publisher": b.publisher,
        "isbn": b.isbn,
        "total_chapters": b.total_chapters,
        "total_word_count": b.total_word_count,
        "publication_date": b.publication_date.isoformat() if b.publication_date else None,
        "status": b.status,
        "created_at": b.created_at.isoformat() if b.created_at else None,
        "updated_at": b.updated_at.isoformat() if b.updated_at else None,
    }


def _manuscript_to_dict(m: Manuscript) -> dict:
    return {
        "id": m.id,
        "title": m.title,
        "book_id": m.book_id,
        "chapter_number": m.chapter_number,
        "content": m.content,
        "word_count": m.word_count,
        "status": m.status,
        "version": m.version,
        "created_at": m.created_at.isoformat() if m.created_at else None,
        "updated_at": m.updated_at.isoformat() if m.updated_at else None,
    }


# ============================================================================
# Article endpoints
# ============================================================================


@router.get("/writer/articles", response_model=ApiResponse[list])
def list_articles(
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """获取文章列表，支持按分类和状态过滤."""
    q = db.query(Article)
    if category:
        q = q.filter(Article.category == category)
    if status:
        q = q.filter(Article.status == status)
    total = q.count()
    items = (
        q.order_by(Article.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return ApiResponse(data=[_article_to_dict(i) for i in items])


@router.post("/writer/articles", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_article(payload: ArticleCreate, db: Session = Depends(get_db)):
    """创建新文章."""
    article = Article(**payload.model_dump())
    db.add(article)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(article)
    return ApiResponse(data=_article_to_dict(article), message="文章创建成功")


@router.get("/writer/articles/{article_id}", response_model=ApiResponse[dict])
def get_article(article_id: str, db: Session = Depends(get_db)):
    """获取文章详情."""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    return ApiResponse(data=_article_to_dict(article))


@router.patch("/writer/articles/{article_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def update_article(article_id: str, payload: ArticleUpdate, db: Session = Depends(get_db)):
    """更新文章."""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(article, key, value)
    article.updated_at = datetime.utcnow()
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(article)
    return ApiResponse(data=_article_to_dict(article), message="文章更新成功")


@router.delete("/writer/articles/{article_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def delete_article(article_id: str, db: Session = Depends(get_db)):
    """删除文章."""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    db.delete(article)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data={"success": True}, message="文章已删除")


# ============================================================================
# Book endpoints
# ============================================================================


@router.get("/writer/books", response_model=ApiResponse[PaginatedResponse])
def list_books(
    params: PaginationParams = Query(PaginationParams()),
    genre: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """获取书籍列表 (分页)."""
    q = db.query(Book)
    if genre:
        q = q.filter(Book.genre == genre)
    if status:
        q = q.filter(Book.status == status)
    total = q.count()
    items = (
        q.order_by(Book.created_at.desc())
        .limit(params.page_size)
        .offset((params.page - 1) * params.page_size)
        .all()
    )
    return ApiResponse(data={
        "items": [_book_to_dict(i) for i in items],
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
        "total_pages": (total + params.page_size - 1) // params.page_size if params.page_size else 0,
    })


@router.post("/writer/books", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_book(payload: BookCreate, db: Session = Depends(get_db)):
    """创建新书籍."""
    book = Book(**payload.model_dump())
    db.add(book)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(book)
    return ApiResponse(data=_book_to_dict(book), message="书籍创建成功")


@router.patch("/writer/books/{book_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def update_book(book_id: str, payload: BookUpdate, db: Session = Depends(get_db)):
    """更新书籍信息."""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(book, key, value)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(book)
    return ApiResponse(data=_book_to_dict(book), message="书籍更新成功")


@router.delete("/writer/books/{book_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_book(book_id: str, db: Session = Depends(get_db)):
    """删除书籍及其所有手稿."""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    db.query(Manuscript).filter(Manuscript.book_id == book_id).delete(synchronize_session=False)
    db.delete(book)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(message="书籍已删除")


# ============================================================================
# Manuscript endpoints
# ============================================================================


@router.get("/writer/manuscripts", response_model=ApiResponse[PaginatedResponse])
def list_manuscripts(
    params: PaginationParams = Query(PaginationParams()),
    book_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """获取手稿列表 (分页)."""
    q = db.query(Manuscript)
    if book_id:
        q = q.filter(Manuscript.book_id == book_id)
    if status:
        q = q.filter(Manuscript.status == status)
    total = q.count()
    items = (
        q.order_by(Manuscript.created_at.desc())
        .limit(params.page_size)
        .offset((params.page - 1) * params.page_size)
        .all()
    )
    return ApiResponse(data={
        "items": [_manuscript_to_dict(i) for i in items],
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
        "total_pages": (total + params.page_size - 1) // params.page_size if params.page_size else 0,
    })


@router.post("/writer/manuscripts", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_manuscript(payload: ManuscriptCreate, db: Session = Depends(get_db)):
    """创建新章节手稿."""
    manuscript = Manuscript(**payload.model_dump())
    db.add(manuscript)
    # Auto-update book totals if linked to a book
    if manuscript.book_id and manuscript.word_count:
        book = db.query(Book).filter(Book.id == manuscript.book_id).first()
        if book:
            existing = book.total_word_count or 0
            book.total_word_count = existing + manuscript.word_count
            if manuscript.chapter_number and (not book.total_chapters or book.total_chapters < manuscript.chapter_number):
                book.total_chapters = manuscript.chapter_number
            try:
                db.commit()
            except Exception:
                db.rollback()
                raise
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(manuscript)
    return ApiResponse(data=_manuscript_to_dict(manuscript), message="手稿创建成功")


@router.patch("/writer/manuscripts/{manuscript_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def update_manuscript(manuscript_id: str, payload: ManuscriptUpdate, db: Session = Depends(get_db)):
    """更新手稿."""
    manuscript = db.query(Manuscript).filter(Manuscript.id == manuscript_id).first()
    if not manuscript:
        raise HTTPException(status_code=404, detail="手稿不存在")
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(manuscript, key, value)
    manuscript.updated_at = datetime.utcnow()
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(manuscript)
    return ApiResponse(data=_manuscript_to_dict(manuscript), message="手稿更新成功")


@router.delete("/writer/manuscripts/{manuscript_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_manuscript(manuscript_id: str, db: Session = Depends(get_db)):
    """删除手稿."""
    manuscript = db.query(Manuscript).filter(Manuscript.id == manuscript_id).first()
    if not manuscript:
        raise HTTPException(status_code=404, detail="手稿不存在")
    # Update book totals
    if manuscript.book_id:
        book = db.query(Book).filter(Book.id == manuscript.book_id).first()
        if book:
            book.total_word_count = max(0, (book.total_word_count or 0) - (manuscript.word_count or 0))
            book.total_chapters = max(0, (book.total_chapters or 0) - 1)
            try:
                db.commit()
            except Exception:
                db.rollback()
                raise
    db.delete(manuscript)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(message="手稿已删除")


# ============================================================================
# Stats endpoint
# ============================================================================


@router.get("/writer/stats", response_model=ApiResponse[WriterStatsResponse])
def get_writer_stats(db: Session = Depends(get_db)):
    """获取写作统计 (文章/书籍/手稿计数与字数汇总)."""
    articles_count = db.query(func.count(Article.id)).scalar() or 0
    books_count = db.query(func.count(Book.id)).scalar() or 0
    manuscripts_count = db.query(func.count(Manuscript.id)).scalar() or 0

    articles_words = db.query(func.coalesce(func.sum(Article.word_count), 0)).scalar() or 0
    books_words = db.query(func.coalesce(func.sum(Book.total_word_count), 0)).scalar() or 0
    manuscripts_words = db.query(func.coalesce(func.sum(Manuscript.word_count), 0)).scalar() or 0

    published_count = (
        db.query(func.count(Article.id))
        .filter(Article.status == "published")
        .scalar() or 0
    )
    draft_count = (
        db.query(func.count(Article.id))
        .filter(Article.status == "draft")
        .scalar() or 0
    )
    draft_count += (
        db.query(func.count(Article.id))
        .filter(Article.status == "archived")
        .scalar() or 0
    )
    # Count non-published books + manuscripts
    writing_books = (
        db.query(func.count(Book.id))
        .filter(Book.status != "published")
        .scalar() or 0
    )
    draft_manuscripts = (
        db.query(func.count(Manuscript.id))
        .filter(Manuscript.status != "final")
        .scalar() or 0
    )

    total_words = int(articles_words) + int(books_words) + int(manuscripts_words)

    return ApiResponse(
        data=WriterStatsResponse(
            total_articles=int(articles_count),
            total_books=int(books_count),
            total_manuscripts=int(manuscripts_count),
            total_words=total_words,
            published_count=int(published_count),
            draft_count=int(draft_count) + int(writing_books) + int(draft_manuscripts),
        )
    )
