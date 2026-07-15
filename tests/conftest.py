import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.work import Work


# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def db_session():
    """Create a fresh database session with all tables."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="session")
def sample_work(db_session):
    """Create a sample work file and Work record for testing."""
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp.write(b"test image content for hashing")
    tmp.close()

    work = Work(
        id="sample_work_001",
        title="Sample Test Work",
        file_path=tmp.name,
        file_name="test_image.png",
        file_size=os.path.getsize(tmp.name),
        file_type="image",
        file_extension="png",
        sha256="dummy_hash_for_test",
        status="active",
    )
    db_session.add(work)
    db_session.commit()
    db_session.refresh(work)
    yield work

    # Cleanup temp file after test
    os.unlink(tmp.name)


@pytest.fixture
def sample_work_file():
    """Return a path to a temp file with known content."""
    tmp = tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w")
    tmp.write("hello world for sha256 test")
    tmp.close()
    yield tmp.name
    os.unlink(tmp.name)
