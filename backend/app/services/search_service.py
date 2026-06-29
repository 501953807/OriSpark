"""FTS5 全文搜索服务."""

from app.database import SessionLocal, engine, Base
from app.services.cache import cached


FTS5_SETUP_SQL = """
-- 创建 FTS5 虚拟表 (外部内容表模式)
CREATE VIRTUAL TABLE IF NOT EXISTS works_fts USING fts5(
    title,
    description,
    tags,
    content='works',
    content_rowid='rowid'
);

-- 触发器: INSERT
CREATE TRIGGER IF NOT EXISTS works_fts_insert AFTER INSERT ON works BEGIN
    INSERT INTO works_fts(rowid, title, description, tags)
    VALUES (
        new.rowid,
        COALESCE(new.title, ''),
        COALESCE(new.description, ''),
        (SELECT GROUP_CONCAT(tag, ' ') FROM work_tags WHERE work_id = new.id)
    );
END;

-- 触发器: DELETE
CREATE TRIGGER IF NOT EXISTS works_fts_delete AFTER DELETE ON works BEGIN
    INSERT INTO works_fts(works_fts, rowid, title, description, tags)
    VALUES ('delete', old.rowid, COALESCE(old.title, ''), COALESCE(old.description, ''), '');
END;

-- 触发器: UPDATE
CREATE TRIGGER IF NOT EXISTS works_fts_update AFTER UPDATE ON works BEGIN
    INSERT INTO works_fts(works_fts, rowid, title, description, tags)
    VALUES ('delete', old.rowid, COALESCE(old.title, ''), COALESCE(old.description, ''), '');
    INSERT INTO works_fts(rowid, title, description, tags)
    VALUES (
        new.rowid,
        COALESCE(new.title, ''),
        COALESCE(new.description, ''),
        (SELECT GROUP_CONCAT(tag, ' ') FROM work_tags WHERE work_id = new.id)
    );
END;
"""


def setup_fts5():
    """初始化 FTS5 全文搜索."""
    import sqlite3

    db_path = "data/oristudio.db"
    conn = sqlite3.connect(db_path)

    try:
        conn.execute("BEGIN")
        for stmt in FTS5_SETUP_SQL.split(";"):
            stmt = stmt.strip()
            if stmt and not stmt.startswith("--"):
                try:
                    conn.execute(stmt)
                except sqlite3.OperationalError as e:
                    err = str(e).lower()
                    if "already exists" not in err and "duplicate" not in err:
                        pass  # 静默跳过
        conn.commit()
    finally:
        conn.close()


@cached(ttl=30, key_prefix="fts_search")
def search_works_fts(query: str, limit: int = 50, offset: int = 0) -> list[str]:
    """FTS5 全文搜索，返回匹配的 work ID 列表."""
    import sqlite3

    db_path = "data/oristudio.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        # 检查 FTS5 表是否存在
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='works_fts'"
        )
        if not cursor.fetchone():
            return []

        # FTS5 查询 (使用 simple 分词器)
        fts_query = query.replace("'", "''")
        rows = conn.execute(
            "SELECT rowid FROM works_fts WHERE works_fts MATCH ? ORDER BY rank LIMIT ? OFFSET ?",
            (fts_query, limit, offset),
        ).fetchall()

        return [str(r["rowid"]) for r in rows]
    finally:
        conn.close()
