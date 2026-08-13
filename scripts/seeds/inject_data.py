#!/usr/bin/env python3
"""Data injection script for OriStudio."""
import sqlite3
import uuid
import random
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path('/Users/tangxiaochuan/AIWorkspace/ClaudeWorkspace/OriSpark')
DB_PATH = BASE / 'backend' / 'data' / 'oristudio.db'
MEDIA_PATH = BASE / 'test_media'

def gen_id():
    return uuid.uuid4().hex[:16]

def now_str():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def past_days(days):
    return (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')

def main():
    print("=" * 60)
    print("OriStudio Data Injection")
    print("=" * 60)

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Seed users
    print("\n[1/6] Creating users...")
    users = []
    creator_types = [
        ("illustrator", "插画师"),
        ("photographer", "摄影师"),
        ("video_creator", "视频创作者"),
        ("crafter", "手工艺人"),
        ("musician", "音乐人"),
        ("writer", "文字作者"),
    ]

    for creator_type, label in creator_types:
        for i in range(5):
            uid = gen_id()
            cursor.execute(
                "INSERT INTO users (id, username, email, password_hash, role, status, creator_type, login_platform, participant_roles, notification_prefs, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (uid, f"{label}_{i+1}", f"{label}_{i+1}@test.orispark.com",
                 "pbkdf2:sha256:260000$test$test", "creator", "active",
                 creator_type, "web", "[]", "{}",
                 past_days(random.randint(1, 365)), now_str())
            )
            users.append((uid, creator_type))

    roles = [
        ("operator", "运营方"), ("legal_rep", "法务代表"),
        ("tax_agent", "税务代理"), ("logistics", "物流方"),
        ("insurer", "保险方"), ("trader", "采购方"), ("platform", "平台方")
    ]
    for role, label in roles:
        for i in range(3):
            uid = gen_id()
            cursor.execute(
                "INSERT INTO users (id, username, email, password_hash, role, status, creator_type, login_platform, participant_roles, notification_prefs, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (uid, f"{label}_{i+1}", f"{label}_{i+1}@test.orispark.com",
                 "pbkdf2:sha256:260000$test$test", "user", "active",
                 None, "web", f'["{role}"]', "{}",
                 past_days(random.randint(1, 365)), now_str())
            )
            users.append((uid, None))

    conn.commit()
    print(f"  ✓ {len(users)} users created")

    # Seed works
    print("\n[2/6] Creating works...")
    works = []
    titles = ["星空下的花园", "城市夜景", "梦幻森林", "秋日私语", "晨光中的教堂",
              "夕阳下的海滩", "手工陶瓷花瓶", "春日序曲", "最后的守护者", "星辰大海"]

    for ct in ["illustrator", "photographer", "video_creator", "crafter", "musician", "writer"]:
        ct_users = [u for u in users if u[1] == ct]
        for i in range(5):
            wuid = gen_id()
            creator = random.choice(ct_users)
            media_path = str(MEDIA_PATH / "images" / f"{ct}_{i+1}.jpg")
            cursor.execute(
                """INSERT INTO works (id, title, file_path, file_name, file_size,
                   file_type, file_extension, mime_type, sha256, thumbnail_path,
                   creator_id, creator_type, description, status, is_verified,
                   import_mode, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (wuid, random.choice(titles), media_path, f"{ct}_{i+1}.jpg",
                 random.randint(100000, 5000000), "image", "jpg", "image/jpeg",
                 uuid.uuid4().hex[:64], media_path, creator[0], ct,
                 f"Test work {i+1} for {ct}", "active", random.choice([True, False]),
                 "full", past_days(random.randint(1, 365)), now_str())
            )
            works.append((wuid, creator))

    conn.commit()
    print(f"  ✓ {len(works)} works created")

    # Seed books
    print("\n[3/6] Creating books...")
    books = []
    writer_works = [w for w in works if w[1][1] == "writer"]
    for i, (wuid, creator) in enumerate(writer_works[:5]):
        bid = gen_id()
        cover_path = str(MEDIA_PATH / "images" / f"book_cover_{i+1}.jpg")
        cursor.execute(
            """INSERT INTO books (id, title, author_id, cover_path, description,
               genre, publisher, isbn, total_chapters, total_word_count, status,
               publication_date, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (bid, f"测试书籍 {i+1}", creator[0], cover_path, "Test book description",
             random.choice(["小说", "散文", "诗歌", "学术"]), "测试出版社",
             f"978-7-{random.randint(10000, 99999)}-{random.randint(1, 9)}-X",
             random.randint(10, 30), random.randint(50000, 300000),
             random.choice(["writing", "published"]), past_days(random.randint(0, 365)),
             now_str(), now_str())
        )
        books.append((bid, creator))

        # Chapters
        for ch_num in range(1, 6):
            cursor.execute(
                """INSERT INTO chapters (id, work_id, title, chapter_number, body,
                   word_count, status, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (gen_id(), wuid, f"第{ch_num}章", ch_num,
                 "Chapter content..." * 10, random.randint(2000, 5000),
                 "published" if ch_num <= 3 else "draft", now_str(), now_str())
            )

        # Manuscripts
        for version in range(1, 4):
            cursor.execute(
                """INSERT INTO manuscripts (id, title, book_id, chapter_number,
                   content, word_count, status, version, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (gen_id(), f"手稿v{version}", bid, 1,
                 "Manuscript content...", random.randint(2000, 5000),
                 "final" if version == 3 else "draft", version, now_str(), now_str())
            )

    conn.commit()
    print(f"  ✓ {len(books)} books created")

    # Seed articles
    print("\n[4/6] Creating articles...")
    for i in range(20):
        creator = random.choice(users)
        cursor.execute(
            """INSERT INTO articles (id, title, subtitle, content, excerpt,
               author_id, category, tags, word_count, reading_time_minutes,
               status, published_at, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (gen_id(), f"测试文章 {i+1}", "", "Article content..." * 20,
             "Excerpt...", creator[0],
             random.choice(["科技", "文学", "历史", "艺术", "生活"]),
             "[]", random.randint(1000, 3000), random.randint(3, 10),
             random.choice(["draft", "published"]),
             past_days(random.randint(0, 180)) if random.random() > 0.3 else None,
             now_str(), now_str())
        )
    conn.commit()
    print("  ✓ 20 articles created")

    # Verify
    print("\n" + "=" * 60)
    print("DATA SUMMARY")
    print("=" * 60)
    for table in ['users', 'works', 'books', 'articles', 'chapters', 'manuscripts']:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table:12s}: {count}")

    img_count = len(list((MEDIA_PATH / "images").glob("*")))
    audio_count = len(list((MEDIA_PATH / "audio").glob("*")))
    print(f"\n  media/images : {img_count}")
    print(f"  media/audio  : {audio_count}")

    conn.close()
    print("\n✓ Data injection complete!")

if __name__ == "__main__":
    main()
