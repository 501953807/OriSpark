"""Tests for the writer module router and stats endpoint."""

import uuid

import pytest

from app.models.article import Article
from app.models.book import Book
from app.models.manuscript import Manuscript


def _uid(prefix=""):
    return prefix + uuid.uuid4().hex[:32 - len(prefix)]


@pytest.fixture
def article_factory(db_session):
    def _create(title="Test Article", status="draft", word_count=1000):
        a = Article(
            id=_uid("art_"),
            title=title,
            content="Some content here.",
            category="tech",
            status=status,
            word_count=word_count,
            reading_time_minutes=5,
        )
        db_session.add(a)
        db_session.flush()
        return a
    return _create


@pytest.fixture
def book_factory(db_session):
    def _create(title="Test Book", status="writing", total_word_count=5000):
        b = Book(
            id=_uid("bk_"),
            title=title,
            genre="novel",
            status=status,
            total_word_count=total_word_count,
        )
        db_session.add(b)
        db_session.flush()
        return b
    return _create


@pytest.fixture
def manuscript_factory(db_session):
    def _create(title="Test Chapter", word_count=2000, status="draft"):
        m = Manuscript(
            id=_uid("ms_"),
            title=title,
            chapter_number=1,
            content="Chapter content.",
            word_count=word_count,
            status=status,
            version=1,
        )
        db_session.add(m)
        db_session.flush()
        return m
    return _create


class TestGetWriterStats:
    """Tests for GET /api/writer/stats endpoint."""

    def test_returns_stats_when_empty(self, client):
        """When there are no articles/books/manuscripts, stats should be zero."""
        res = client.get("/api/writer/stats")
        assert res.status_code == 200

        data = res.json()
        assert data["success"] is True
        stats = data["data"]
        assert stats["total_articles"] == 0
        assert stats["total_books"] == 0
        assert stats["total_manuscripts"] == 0
        assert stats["total_words"] == 0
        assert stats["published_count"] == 0
        assert stats["draft_count"] == 0

    def test_returns_correct_counts(self, client, article_factory, book_factory, manuscript_factory, db_session):
        """Stats should reflect actual counts and word totals."""
        # Create articles
        article_factory(title="Draft Art 1", status="draft", word_count=500)
        article_factory(title="Draft Art 2", status="draft", word_count=1500)
        article_factory(title="Published Art 1", status="published", word_count=3000)
        article_factory(title="Archived Art 1", status="archived", word_count=200)

        # Create books
        book_factory(title="Active Book", status="writing", total_word_count=10000)
        book_factory(title="Published Book", status="published", total_word_count=50000)

        # Create manuscripts
        manuscript_factory(title="Ch 1", word_count=2000, status="draft")
        manuscript_factory(title="Ch 2", word_count=3000, status="final")

        db_session.commit()

        res = client.get("/api/writer/stats")
        assert res.status_code == 200

        data = res.json()
        assert data["success"] is True
        stats = data["data"]

        # Article counts
        assert stats["total_articles"] == 4

        # Book counts
        assert stats["total_books"] == 2

        # Manuscript counts
        assert stats["total_manuscripts"] == 2

        # Total words: 500+1500+3000+200 (articles) + 10000+50000 (books) + 2000+3000 (manuscripts)
        assert stats["total_words"] == 70200

        # Published articles: 1 (only 'published' status)
        assert stats["published_count"] == 1

    def test_published_count_only_counts_articles(self, client, article_factory, db_session):
        """published_count should only count articles with status=published."""
        article_factory(title="Pub 1", status="published", word_count=100)
        article_factory(title="Pub 2", status="published", word_count=200)
        article_factory(title="Draft 1", status="draft", word_count=50)

        db_session.commit()

        res = client.get("/api/writer/stats")
        assert res.status_code == 200

        stats = res.json()["data"]
        assert stats["published_count"] == 2


class TestWriterEndpoints:
    """Basic tests for writer CRUD endpoints."""

    def test_create_article(self, client, db_session):
        res = client.post(
            "/api/writer/articles",
            json={
                "title": "New Article",
                "category": "tech",
                "status": "draft",
                "word_count": 100,
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["title"] == "New Article"
        assert data["data"]["status"] == "draft"

    def test_get_articles_list(self, client, article_factory, db_session):
        article_factory(title="List Art 1", status="published", word_count=500)
        article_factory(title="List Art 2", status="draft", word_count=300)
        db_session.commit()

        res = client.get("/api/writer/articles")
        assert res.status_code == 200
        data = res.json()
        assert len(data["data"]) == 2

    def test_get_article_detail(self, client, article_factory, db_session):
        a = article_factory(title="Detail Art", status="published", word_count=1000)
        db_session.commit()

        res = client.get(f"/api/writer/articles/{a.id}")
        assert res.status_code == 200
        assert res.json()["data"]["title"] == "Detail Art"

    def test_get_article_not_found(self, client):
        res = client.get("/api/writer/articles/nonexistent-id")
        assert res.status_code == 404

    def test_update_article(self, client, article_factory, db_session):
        a = article_factory(title="Old Title", status="draft", word_count=100)
        db_session.commit()

        res = client.patch(
            f"/api/writer/articles/{a.id}",
            json={"title": "Updated Title"},
        )
        assert res.status_code == 200
        assert res.json()["data"]["title"] == "Updated Title"

    def test_delete_article(self, client, article_factory, db_session):
        a = article_factory(title="Delete Me", status="draft", word_count=100)
        db_session.commit()

        res = client.delete(f"/api/writer/articles/{a.id}")
        assert res.status_code == 200
        assert res.json()["data"]["success"] is True

        # Verify it's gone
        res2 = client.get(f"/api/writer/articles/{a.id}")
        assert res2.status_code == 404

    def test_create_book(self, client, db_session):
        res = client.post(
            "/api/writer/books",
            json={
                "title": "My Novel",
                "genre": "novel",
                "status": "writing",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["data"]["title"] == "My Novel"

    def test_list_books(self, client, book_factory, db_session):
        book_factory(title="Book A", status="writing", total_word_count=1000)
        book_factory(title="Book B", status="published", total_word_count=5000)
        db_session.commit()

        res = client.get("/api/writer/books")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_create_manuscript(self, client, db_session):
        res = client.post(
            "/api/writer/manuscripts",
            json={
                "title": "Chapter 1",
                "chapter_number": 1,
                "status": "draft",
                "word_count": 2000,
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["data"]["title"] == "Chapter 1"

    def test_list_manuscripts(self, client, manuscript_factory, db_session):
        manuscript_factory(title="Ch 1", word_count=1000, status="draft")
        manuscript_factory(title="Ch 2", word_count=2000, status="final")
        db_session.commit()

        res = client.get("/api/writer/manuscripts")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_update_manuscript(self, client, manuscript_factory, db_session):
        m = manuscript_factory(title="Old Ch", word_count=500, status="draft")
        db_session.commit()

        res = client.patch(
            f"/api/writer/manuscripts/{m.id}",
            json={"title": "New Ch Title", "status": "revising"},
        )
        assert res.status_code == 200
        assert res.json()["data"]["title"] == "New Ch Title"
        assert res.json()["data"]["status"] == "revising"
