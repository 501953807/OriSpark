#!/usr/bin/env python3
"""Complete data injection for OriStudio - all creator types."""
import sqlite3
import uuid
import random
import math
import struct
import os
from pathlib import Path
from datetime import datetime, timedelta

BASE = Path('/Users/tangxiaochuan/AIWorkspace/ClaudeWorkspace/OriSpark')
DB = BASE / 'backend' / 'data' / 'oristudio.db'
MEDIA = BASE / 'test_media'

def gen_id():
    return uuid.uuid4().hex[:16]

def now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def past(days):
    return (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')

def ensure_cols(conn, table, cols):
    """Add missing columns to table."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table})")
    existing = {row[1] for row in cursor.fetchall()}
    adds = {
        'bio': 'TEXT',
        'login_platform': "VARCHAR(20) DEFAULT 'web'",
        'participant_roles': 'TEXT DEFAULT "[]"',
        'is_platform_operator': 'INTEGER DEFAULT 0',
        'is_payment_provider': 'INTEGER DEFAULT 0',
        'is_insurer': 'INTEGER DEFAULT 0',
        'is_logistics': 'INTEGER DEFAULT 0',
        'company_name': 'VARCHAR(500)',
        'company_license_no': 'VARCHAR(200)',
        'company_address': 'TEXT',
        'company_contact': 'VARCHAR(200)',
        'company_phone': 'VARCHAR(50)',
        'company_email': 'VARCHAR(200)',
        'qualification_verified': 'INTEGER DEFAULT 0',
        'qualification_verified_at': 'DATETIME',
    }
    for col, ctype in adds.items():
        if col not in existing and col in cols.get(table, []):
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {ctype}")
            except:
                pass
    conn.commit()

def seed_users(conn):
    print("\n=== 1. Creating users ===")
    c = conn.cursor()
    users = []

    # Creator users (6 types × 5)
    creator_types = [
        ("illustrator", "插画师"),
        ("photographer", "摄影师"),
        ("video_creator", "视频创作者"),
        ("crafter", "手工艺人"),
        ("musician", "音乐人"),
        ("writer", "文字作者"),
    ]

    for ct, label in creator_types:
        for i in range(5):
            uid = gen_id()
            c.execute("""
                INSERT INTO users (id, username, email, password_hash, role, status,
                    creator_type, login_platform, participant_roles, notification_prefs,
                    created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (uid, f"{label}_{i+1}", f"{label}_{i+1}@test.orispark.com",
                  "pbkdf2:sha256:260000$test$test", "creator", "active",
                  ct, "web", "[]", "{}", past(random.randint(1,365)), now()))
            users.append((uid, ct))

    # Non-creator users (7 roles × 3)
    roles = [("operator", "运营方"), ("legal_rep", "法务代表"), ("tax_agent", "税务代理"),
             ("logistics", "物流方"), ("insurer", "保险方"), ("trader", "采购方"),
             ("platform", "平台方")]
    for role, label in roles:
        for i in range(3):
            uid = gen_id()
            c.execute("""
                INSERT INTO users (id, username, email, password_hash, role, status,
                    creator_type, login_platform, participant_roles, notification_prefs,
                    created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (uid, f"{label}_{i+1}", f"{label}_{i+1}@test.orispark.com",
                  "pbkdf2:sha256:260000$test$test", "user", "active",
                  None, "web", f'["{role}"]', "{}", past(random.randint(1,365)), now()))
            users.append((uid, None))

    conn.commit()
    print(f"  ✓ Created {len(users)} users")
    return users

def seed_works(conn, users):
    print("\n=== 2. Creating works ===")
    c = conn.cursor()
    works = []
    creator_types = ["illustrator", "photographer", "video_creator", "crafter", "musician", "writer"]
    titles = ["星空下的花园", "城市夜景", "梦幻森林", "秋日私语", "晨光中的教堂",
              "夕阳下的海滩", "手工陶瓷花瓶", "春日序曲", "最后的守护者", "星辰大海"]

    for ct in creator_types:
        ct_users = [u for u in users if u[1] == ct]
        for i in range(5):
            wuid = gen_id()
            creator = random.choice(ct_users)
            media_path = f"/Users/tangxiaochuan/AIWorkspace/ClaudeWorkspace/OriSpark/test_media/images/{ct}_{i+1}.jpg"

            c.execute("""
                INSERT INTO works (id, title, file_path, file_name, file_size,
                    file_type, file_extension, mime_type, sha256, thumbnail_path,
                    creator_id, creator_type, description, status, is_verified,
                    import_mode, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (wuid, random.choice(titles), media_path, f"{ct}_{i+1}.jpg",
                  random.randint(100000, 5000000), "image", "jpg", "image/jpeg",
                  uuid.uuid4().hex[:64], media_path,
                  creator[0], ct, f"Test work {i+1} for {ct}",
                  "active", random.choice([True, False]),
                  "full", past(random.randint(1,365)), now()))
            works.append((wuid, creator))

    conn.commit()
    print(f"  ✓ Created {len(works)} works")
    return works

def seed_books(conn, works):
    print("\n=== 3. Creating books ===")
    c = conn.cursor()
    books = []
    writer_works = [w for w in works if w[1][1] == "writer"]

    for i, (wuid, creator) in enumerate(writer_works[:5]):
        bid = gen_id()
        c.execute("""
            INSERT INTO books (id, title, author_id, cover_path, description,
                genre, publisher, isbn, total_chapters, total_word_count, status,
                publication_date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (bid, f"测试书籍 {i+1}", creator[0],
              f"/Users/tangxiaochuan/AIWorkspace/ClaudeWorkspace/OriSpark/test_media/images/book_cover_{i+1}.jpg",
              "Test book description",
              random.choice(["小说", "散文", "诗歌", "学术"]),
              "测试出版社", f"978-7-{random.randint(10000,99999)}-{random.randint(1,9)}-X",
              random.randint(10,30), random.randint(50000,300000),
              random.choice(["writing", "published"]),
              past(random.randint(0,365)), now(), now()))
        books.append((bid, creator))

        # Create chapters
        for ch in range(1, 6):
            c.execute("""
                INSERT INTO chapters (id, work_id, title, chapter_number, body,
                    word_count, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (gen_id(), wuid, f"第{ch}章", ch,
                  "Chapter content..." * 10, random.randint(2000,5000),
                  "published" if ch <= 3 else "draft", now(), now()))

        # Create manuscripts
        for v in range(1, 4):
            c.execute("""
                INSERT INTO manuscripts (id, title, book_id, chapter_number,
                    content, word_count, status, version, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (gen_id(), f"手稿v{v}", bid, 1, "Manuscript content...",
                  random.randint(2000,5000), "final" if v==3 else "draft", v, now(), now()))

    conn.commit()
    print(f"  ✓ Created {len(books)} books")
    return books

def seed_articles(conn, users):
    print("\n=== 4. Creating articles ===")
    c = conn.cursor()
    for i in range(20):
        creator = random.choice(users)
        c.execute("""
            INSERT INTO articles (id, title, subtitle, content, excerpt,
                author_id, category, tags, word_count, reading_time_minutes, status,
                published_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (gen_id(), f"测试文章 {i+1}", "",
              "Article content..." * 20, "Excerpt...",
              creator[0], random.choice(["科技", "文学", "艺术"]),
              "[]", random.randint(1000,3000), random.randint(3,10),
              random.choice(["draft", "published"]),
              past(random.randint(0,180)) if random.random()>0.3 else None,
              now(), now()))
    conn.commit()
    print("  ✓ Created 20 articles")

def main():
    print("=" * 60)
    print("OriStudio Data Injection")
    print("=" * 60)

    conn = sqlite3.connect(str(DB))
    conn.execute("PRAGMA foreign_keys=ON")

    try:
        users = seed_users(conn)
        works = seed_works(conn, users)
        books = seed_books(conn, works)
        seed_articles(conn, users)

        # Verify
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users")
        print(f"\nUsers: {c.fetchone()[0]}")
        c.execute("SELECT COUNT(*) FROM works")
        print(f"Works: {c.fetchone()[0]}")
        c.execute("SELECT COUNT(*) FROM books")
        print(f"Books: {c.fetchone()[0]}")
        c.execute("SELECT COUNT(*) FROM articles")
        print(f"Articles: {c.fetchone()[0]}")
        c.execute("SELECT COUNT(*) FROM chapters")
        print(f"Chapters: {c.fetchone()[0]}")

        # Media stats
        img_count = len(list((MEDIA/'images').glob('*')))
        audio_count = len(list((MEDIA/'audio').glob('*')))
        print(f"\nMedia: {img_count} images, {audio_count} audio files")

    finally:
        conn.close()

if __name__ == "__main__":
    main()
