"""数据库引擎和会话管理."""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

from app.config import settings

# 从 DATABASE_URL 提取 SQLite 路径
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite+aiosqlite:///"):
    sync_url = db_url.replace("sqlite+aiosqlite:///", "sqlite:///")
else:
    sync_url = db_url

# SQLite 使用 StaticPool（单连接），避免多线程冲突
engine = create_engine(
    sync_url,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
    poolclass=StaticPool,
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """设置 SQLite PRAGMA 优化."""
    if dbapi_connection.__class__.__module__ == "sqlite3":
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA cache_size=-8000")  # 8MB 缓存
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA mmap_size=268435456")  # 256MB mmap
        cursor.close()


Base = declarative_base()


def get_db():
    """获取数据库会话 (FastAPI Depends)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
