"""Migration: add new columns to works table.

Adds synopsis, completion_date, current_stage, copyright_year columns.
SQLite-safe: uses ALTER TABLE ADD COLUMN (no data loss).
"""

import sqlite3
import os
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "oristudio.db")


def get_column_names(conn: sqlite3.Connection, table: str) -> list[str]:
    cursor = conn.execute(f"PRAGMA table_info({table})")
    return [row[1] for row in cursor.fetchall()]


def migrate(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        existing = get_column_names(conn, "works")
        new_columns = {
            "synopsis": "TEXT",
            "completion_date": "DATE",
            "current_stage": "VARCHAR(30)",
            "copyright_year": "INTEGER",
        }
        added = []
        for col, col_type in new_columns.items():
            if col not in existing:
                conn.execute(f"ALTER TABLE works ADD COLUMN {col} {col_type}")
                added.append(col)
                print(f"  Added column: {col} ({col_type})")
            else:
                print(f"  Skipped (exists): {col}")
        conn.commit()
        print(f"\nDone. Added {len(added)} columns.")
    finally:
        conn.close()


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else DB_PATH
    if not os.path.exists(path):
        print(f"Error: database not found at {path}")
        sys.exit(1)
    migrate(path)
