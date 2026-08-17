"""补全数据库缺失列."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
from app.database import engine


MISSING_COLS = [
    ("users", "bio", "TEXT"),
    ("users", "login_platform", "VARCHAR(20)"),
    ("users", "participant_roles", "JSON"),
    ("users", "is_platform_operator", "BOOLEAN DEFAULT 0"),
    ("users", "is_payment_provider", "BOOLEAN DEFAULT 0"),
    ("users", "is_insurer", "BOOLEAN DEFAULT 0"),
    ("users", "is_logistics", "BOOLEAN DEFAULT 0"),
    ("users", "company_name", "VARCHAR(200)"),
    ("users", "company_license_no", "VARCHAR(100)"),
    ("users", "company_address", "TEXT"),
    ("users", "company_contact", "VARCHAR(100)"),
    ("users", "company_phone", "VARCHAR(50)"),
    ("users", "company_email", "VARCHAR(200)"),
    ("users", "qualification_verified", "BOOLEAN DEFAULT 0"),
    ("users", "qualification_verified_at", "DATETIME"),
]


def check_and_add_columns():
    """检查并补齐缺失列."""
    with engine.connect() as conn:
        for table, col, col_type in MISSING_COLS:
            try:
                result = conn.execute(text(
                    f"PRAGMA table_info({table})"
                ))
                existing_cols = {row[1] for row in result.fetchall()}
                if col not in existing_cols:
                    conn.execute(text(
                        f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"
                    ))
                    print(f"  Added column: {table}.{col}")
                else:
                    print(f"  OK: {table}.{col} exists")
            except Exception as e:
                print(f"  SKIP {table}.{col}: {e}")
        conn.commit()
    print("Column migration complete.")


if __name__ == "__main__":
    check_and_add_columns()
