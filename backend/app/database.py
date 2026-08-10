"""数据库引擎和会话管理.

支持 SQLite (开发/MVP) 和 PostgreSQL (生产) 自动切换.
数据库 URL 通过 DATABASE_URL 环境变量或 .env 文件配置.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

from app.config import settings

db_url = settings.DATABASE_URL
is_sqlite = db_url.startswith("sqlite") or db_url.startswith("sqlite+aiosqlite")

if is_sqlite:
    # SQLite: 使用 StaticPool 避免多线程冲突
    sync_url = db_url.replace("sqlite+aiosqlite:///", "sqlite:///")
    engine = create_engine(
        sync_url,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """SQLite PRAGMA 优化."""
        import sqlite3
        if isinstance(dbapi_connection, sqlite3.Connection):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA cache_size=-8000")
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.execute("PRAGMA mmap_size=268435456")
            cursor.close()
else:
    # PostgreSQL: 使用连接池
    engine = create_engine(
        db_url,
        echo=settings.DEBUG,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        pool_recycle=1800,
    )

    @event.listens_for(engine, "connect")
    def set_postgres_init(dbapi_connection, connection_record):
        """PostgreSQL 初始化."""
        cursor = dbapi_connection.cursor()
        cursor.execute("SET search_path TO public")
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
