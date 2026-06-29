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
    """在测试 session 范围内建一次表."""
    from app.models.base import target_metadata
    target_metadata.create_all(bind=_engine)

    # P3.5.2: Disable rate limiting globally for tests
    from app.middleware.rate_limit import RateLimitMiddleware
    RateLimitMiddleware._test_disable = True

    yield
    RateLimitMiddleware._test_disable = False
    target_metadata.drop_all(bind=_engine)
    _db_file.close()


@pytest.fixture
def client():
    """FastAPI 测试客户端."""
    from app.main import app
    from app.database import get_db

    def _override():
        db = _TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
