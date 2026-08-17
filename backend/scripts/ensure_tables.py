"""补全缺失表结构的迁移脚本."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.database import Base, engine


def get_existing_tables():
    """获取数据库中已存在的表名."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name != 'alembic_version'"))
        return {row[0] for row in result.fetchall()}


def get_model_tables():
    """从所有模型中获取表名."""
    import os
    import re
    tables = set()
    models_dir = Path(__file__).parent.parent / "app" / "models"
    for f in models_dir.glob("*.py"):
        if f.name.startswith("__"):
            continue
        content = f.read_text(encoding="utf-8")
        for match in re.findall(r'__tablename__\s*=\s*["\'](\w+)["\']', content):
            tables.add(match)
    return tables


def create_missing_tables():
    """创建缺失的表."""
    existing = get_existing_tables()
    model_tables = get_model_tables()
    missing = sorted(model_tables - existing)

    print(f"Existing tables: {len(existing)}")
    print(f"Model tables: {len(model_tables)}")
    print(f"Missing tables: {len(missing)}")

    if not missing:
        print("No missing tables found.")
        return

    # Import all models to register them with Base.metadata
    models_dir = Path(__file__).parent.parent / "app" / "models"
    for f in models_dir.glob("*.py"):
        if f.name.startswith("__"):
            continue
        mod_name = f.stem
        try:
            __import__(f"app.models.{mod_name}", fromlist=["Base"])
        except Exception as e:
            print(f"Warning: Failed to import {mod_name}: {e}")

    # Create all missing tables
    Base.metadata.create_all(bind=engine, tables=[
        table for table in Base.metadata.sorted_tables
        if table.name in missing
    ])

    print(f"Created {len(missing)} tables successfully.")


if __name__ == "__main__":
    create_missing_tables()
