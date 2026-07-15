"""测试配置和共享 fixtures."""

import pytest
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker


# 临时文件数据库
_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
DB_URL = f"sqlite:///{_db_file.name}"

_engine = create_engine(DB_URL, connect_args={"check_same_thread": False})


@event.listens_for(_engine, "connect")
def _pragma(dbapi_conn, record):
    c = dbapi_conn.cursor()
    c.execute("PRAGMA foreign_keys=ON")
    c.close()


_TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


@pytest.fixture(autouse=True, scope="session")
def setup_db():
    """在测试 session 范围内建一次表.

    NOTE: Drops ALL tables + indexes from sqlite_master to avoid
    dangling-index errors (e.g. duplicate idx_rfq_status on RFQRequest/RFQ).
    """
    from app.models.base import target_metadata

    with _engine.connect() as conn:
        from sqlalchemy import text
        # Drop all indexes
        for row in conn.execute(text(
            "SELECT name FROM sqlite_master "
            "WHERE type='index' AND name NOT LIKE 'sqlite_%'"
        )).fetchall():
            try:
                conn.execute(text(f"DROP INDEX IF EXISTS [{row[0]}]"))
            except Exception:
                pass
        # Drop all tables
        for row in conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )).fetchall():
            try:
                conn.execute(text(f"DROP TABLE IF EXISTS [{row[0]}]"))
            except Exception:
                pass
        conn.commit()

    try:
        target_metadata.create_all(bind=_engine)
    except Exception:
        pass  # May fail on duplicate indexes; tables are created

    # P3.5.2: Disable rate limiting globally for tests
    from app.middleware.rate_limit import RateLimitMiddleware
    RateLimitMiddleware._test_disable = True

    yield
    RateLimitMiddleware._test_disable = False
    target_metadata.drop_all(bind=_engine)
    _db_file.close()


@pytest.fixture
def client():
    """FastAPI 测试客户端.

    NOTE: The db_session fixture overrides get_db to share the same session.
    Tests that don't use db_session can set their own overrides.
    """
    from app.main import app
    from starlette.testclient import TestClient

    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_session(setup_db, client):
    """Provide a database session backed by the test engine.
    Each test gets its own session; rolled back after each test.
    Also overrides get_db so the test client uses the same session.
    """
    from app.database import get_db
    from app.main import app

    session = _TestingSession()

    def _override():
        yield session

    app.dependency_overrides[get_db] = _override

    try:
        yield session
    finally:
        session.rollback()
        session.close()
        if app.dependency_overrides.get(get_db) == _override:
            del app.dependency_overrides[get_db]


@pytest.fixture(autouse=True)
def _cleanup_writer_tables(db_session):
    """Auto-clear articles/books/manuscripts between tests."""
    from sqlalchemy import text

    yield
    try:
        db_session.execute(text("DELETE FROM manuscripts"))
        db_session.execute(text("DELETE FROM books"))
        db_session.execute(text("DELETE FROM articles"))
        db_session.commit()
    except Exception:
        db_session.rollback()
