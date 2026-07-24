"""测试配置和共享 fixtures — 每个 test 使用独立事务隔离."""

import pytest
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool


# ── Monkey-patches (must run before any app code imports) ──────────

# Patch Session.commit → flush() so router-level db.commit() doesn't
# commit permanently; the per-test rollback undoes everything.
_original_commit = Session.commit


def _patched_commit(self):
    self.flush()


Session.commit = _patched_commit


# Disable audit/rate-limit middleware to avoid writing to production DB
from app.middleware.audit import AuditMiddleware
AuditMiddleware._test_disable = True
from app.middleware.rate_limit import RateLimitMiddleware
RateLimitMiddleware._test_disable = True


# Patch prod-writers in lifespan so TestClient startup doesn't touch prod DB
import app.services.search_service as _search_svc
_search_svc.setup_fts5 = lambda: None

from app.models.base import target_metadata as _orig_target_metadata
# Save original for use in fixtures
_original_create_all = _orig_target_metadata.create_all

# Patch to no-op for lifespan (tables already created by test_db_engine fixture)
_orig_target_metadata.create_all = lambda *args, **kwargs: None

from app.services import dict_seed as _ds
_original_seed = _ds.seed_dictionaries
def _safe_seed(db):
    try:
        _original_seed(db)
    except Exception:
        pass
_ds.seed_dictionaries = _safe_seed

from app.services import watermark_seed as _ws
_original_ws = _ws.seed_default_presets
def _safe_ws(db):
    try:
        _original_ws(db)
    except Exception:
        pass
_ws.seed_default_presets = _safe_ws

# Patch _migrate_json_users to be safe
from app.routers import auth as _auth_mod
_original_migrate = getattr(_auth_mod, '_migrate_json_users', None)
def _safe_migrate(db):
    try:
        if _original_migrate:
            _original_migrate(db)
    except Exception:
        pass
_auth_mod._migrate_json_users = _safe_migrate


# ── Per-test engine & session factory ─────────────────────────────

def _make_test_engine_and_session():
    """Create a fresh in-memory SQLite engine + sessionmaker for a single test.

    Uses StaticPool so all connections share the SAME in-memory database.
    Without StaticPool, each new connection to sqlite:// creates a separate
    in-memory DB and tables created on one are invisible to others.
    """
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        echo=False,
        poolclass=StaticPool,
    )

    @event.listens_for(test_engine, "connect")
    def _pragma(dbapi_conn, record):
        c = dbapi_conn.cursor()
        c.execute("PRAGMA foreign_keys=ON")
        c.close()

    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    return test_engine, TestSessionLocal


@pytest.fixture()
def test_db_engine():
    """Each test gets a fresh in-memory SQLite engine with all tables created."""
    test_engine, TestSessionLocal = _make_test_engine_and_session()

    # Patch app.database to use this engine BEFORE any imports
    import app.database as _app_db
    _app_db.engine = test_engine
    _app_db.SessionLocal = TestSessionLocal

    # Create all tables using original (unpatched) create_all
    try:
        _original_create_all(bind=test_engine)
    except Exception:
        pass

    yield test_engine

    # Teardown: dispose engine (in-memory DB disappears)
    test_engine.dispose()


@pytest.fixture()
def db_session(test_db_engine):
    """Provide a database session for each test.

    Each test gets a fresh session on a fresh in-memory DB.
    After the test, rollback + close — data is discarded when the engine dies.
    """
    session = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture()
def client(test_db_engine):
    """FastAPI test client backed by the per-test in-memory DB.

    Patches app.database.engine and overrides get_db BEFORE creating TestClient,
    so the lifespan creates tables on the test engine instead of the prod DB.
    """
    from app.main import app
    from app.database import get_db
    from starlette.testclient import TestClient

    # Create a session bound to the test engine
    session = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)()

    def _override_get_db():
        yield session

    # Override get_db BEFORE starting TestClient
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as c:
        yield c

    # Cleanup
    session.rollback()
    session.close()
    if get_db in app.dependency_overrides:
        del app.dependency_overrides[get_db]


@pytest.fixture()
def sample_work_file():
    """Create a temporary file with known content for SHA-256 tests."""
    content = b"hello world for sha256 test"
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".bin") as f:
        f.write(content)
        f.flush()
        yield f.name
    Path(f.name).unlink(missing_ok=True)
