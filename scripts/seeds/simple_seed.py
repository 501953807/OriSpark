"""简化的种子数据注入脚本 - 直接操作数据库."""

import sys
import uuid
import random
import math
import struct
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone

# 设置路径
script_dir = Path(__file__).parent.parent
project_root = script_dir.parent
backend_dir = project_root / "backend"
sys.path.insert(0, str(backend_dir))
os.chdir(backend_dir)

import sqlite3
from PIL import Image

DB_PATH = backend_dir / "data" / "oristudio.db"
MEDIA_DIR = project_root / "test_media"

for d in [MEDIA_DIR, MEDIA_DIR / "images", MEDIA_DIR / "audio", MEDIA_DIR / "video"]:
    d.mkdir(parents=True, exist_ok=True)


def gen_id():
    return uuid.uuid4().hex[:16]


def now():
    return datetime.now(timezone.utc).isoformat()


def past(days=30):
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


def generate_test_image(path: Path, width=800, height=600):
    """生成测试图片."""
    img = Image.new('RGB', (width, height), color=(
        random.randint(50, 200), random.randint(50, 200), random.randint(50, 200)
    ))
    img.save(path)
    return str(path)


def generate_test_audio(path: Path, duration_sec=5):
    """生成测试音频."""
    sample_rate = 44100
    num_samples = sample_rate * duration_sec
    freq = 440

    with open(path, 'wb') as f:
        f.write(b'RIFF')
        f.write(struct.pack('<I', 36 + num_samples * 2))
        f.write(b'WAVE')
        f.write(b'fmt ')
        f.write(struct.pack('<I', 16))
        f.write(struct.pack('<H', 1))
        f.write(struct.pack('<H', 1))
        f.write(struct.pack('<I', sample_rate))
        f.write(struct.pack('<I', sample_rate * 2))
        f.write(struct.pack('<H', 2))
        f.write(struct.pack('<H', 16))
        f.write(b'data')
        f.write(struct.pack('<I', num_samples * 2))

        for i in range(num_samples):
            value = int(32767 * 0.3 * math.sin(2 * math.pi * freq * i / sample_rate))
            f.write(struct.pack('<h', value))

    return str(path)


def ensure_users_table(conn):
    """确保users表有所有需要的列."""
    cursor = conn.cursor()

    # 获取现有列
    cursor.execute("PRAGMA table_info(users)")
    existing_cols = {row[1] for row in cursor.fetchall()}

    # 需要添加的列
    cols_to_add = {
        'bio': 'TEXT',
        'login_platform': "VARCHAR(20) DEFAULT 'web'",
        'participant_roles': 'JSON DEFAULT "[]"',
        'is_platform_operator': 'BOOLEAN DEFAULT 0',
        'is_payment_provider': 'BOOLEAN DEFAULT 0',
        'is_insurer': 'BOOLEAN DEFAULT 0',
        'is_logistics': 'BOOLEAN DEFAULT 0',
        'company_name': 'VARCHAR(500)',
        'company_license_no': 'VARCHAR(200)',
        'company_address': 'TEXT',
        'company_contact': 'VARCHAR(200)',
        'company_phone': 'VARCHAR(50)',
        'company_email': 'VARCHAR(200)',
        'qualification_verified': 'BOOLEAN DEFAULT 0',
        'qualification_verified_at': 'DATETIME',
    }

    for col_name, col_type in cols_to_add.items():
        if col_name not in existing_cols:
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                print(f"  Added column: {col_name}")
            except Exception as e:
                print(f"  Warning adding {col_name}: {e}")

    conn.commit()


def seed_users(conn):
    """创建用户."""
    print("\n=== 1. 创建用户 ===")

    cursor = conn.cursor()
    users = []

    creator_types = [
        ("illustrator", "插画师"),
        ("photographer", "摄影师"),
        ("video_creator", "视频创作者"),
        ("crafter", "手工艺人"),
        ("musician", "音乐人"),
        ("writer", "文字作者"),
    ]

    # 创作者用户
    for creator_type, label in creator_types:
        for i in range(5):
            uid = gen_id()
            cursor.execute("""
                INSERT OR REPLACE INTO users (id, username, email, password_hash, role, status,
                    creator_type, login_platform, participant_roles, notification_prefs,
                    created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                uid, f"{label}_{i+1}",
                f"{label}_{i+1}@test.orispark.com",
                "pbkdf2:sha256:260000$test$test",
                "creator", "active", creator_type, "web", "[]",
                "{}", past(random.randint(1, 365)), now()
            ))
            users.append((uid, creator_type))

    # 其他角色用户
    other_roles = [
        ("operator", "运营方"),
        ("legal_rep", "法务代表"),
        ("tax_agent", "税务代理"),
        ("logistics", "物流方"),
        ("insurer", "保险方"),
        ("trader", "采购方"),
    ]

    for role, label in other_roles:
        for i in range(3):
            uid = gen_id()
            cursor.execute("""
                INSERT OR REPLACE INTO users (id, username, email, password_hash, role, status,
                    creator_type, login_platform, participant_roles, notification_prefs,
                    created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                uid, f"{label}_{i+1}",
                f"{label}_{i+1}@test.orispark.com",
                "pbkdf2:sha256:260000$test$test",
                "user", "active", None, "web", f'["{role}"]',
                "{}", past(random.randint(1, 365)), now()
            ))
            users.append((uid, None))

    print(f"  ✓ 创建 {len(users)} 个用户")
    return users


def seed_works(conn, users):
    """创建作品."""
    print("\n=== 2. 创建作品 ===")

    cursor = conn.cursor()
    works = []
    creator_types = ["illustrator", "photographer", "video_creator", "crafter", "musician", "writer"]

    for ct in creator_types:
        creator_users = [u for u in users if u[1] == ct]
        for i in range(5):
            creator = random.choice(creator_users)
            wuid = gen_id()

            # 生成媒体文件
            if ct in ["illustrator", "photographer", "crafter"]:
                file_type, ext = "image", "jpg"
                mime_type = "image/jpeg"
                media_path = generate_test_image(MEDIA_DIR / "images" / f"{ct}_{i+1}.jpg", 800, 600)
            elif ct == "video_creator":
                file_type, ext = "video", "mp4"
                mime_type = "video/mp4"
                media_path = generate_test_image(MEDIA_DIR / "images" / f"video_{i+1}.jpg", 640, 360)
            elif ct == "musician":
                file_type, ext = "audio", "mp3"
                mime_type = "audio/mpeg"
                audio_path = generate_test_audio(MEDIA_DIR / "audio" / f"music_{i+1}.mp3", 10)
                media_path = generate_test_image(MEDIA_DIR / "images" / f"music_{i+1}.jpg", 400, 400)
            else:  # writer
                file_type, ext = "document", "pdf"
                mime_type = "application/pdf"
                media_path = generate_test_image(MEDIA_DIR / "images" / f"writer_{i+1}.jpg", 400, 600)

            title = random.choice([
                "星空下的花园", "城市夜景", "梦幻森林", "秋日私语",
                "海底世界", "未来城市", "田园风光", "雪山日出",
                "晨光中的教堂", "夕阳下的海滩", "手工陶瓷花瓶", "春日序曲"
            ])

            cursor.execute("""
                INSERT OR REPLACE INTO works (id, title, file_path, file_name, file_size,
                    file_type, file_extension, mime_type, sha256, thumbnail_path,
                    creator_id, creator_type, description, status, is_verified,
                    created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                wuid, title, media_path, f"{ct}_{i+1}.{ext}",
                random.randint(100000, 5000000),
                file_type, ext, mime_type,
                uuid.uuid4().hex[:64], media_path,
                creator[0], ct, f"这是{ct}创作者的测试作品{i+1}",
                "active", random.choice([True, False]),
                past(random.randint(1, 365)), now()
            ))
            works.append((wuid, creator))

    print(f"  ✓ 创建 {len(works)} 个作品")
    return works


def seed_books(conn, works, users):
    """创建书籍."""
    print("\n=== 3. 创建书籍 ===")

    cursor = conn.cursor()
    books = []

    writer_works = [w for w in works if w[1][1] == "writer"]
    for i, (wuid, creator) in enumerate(writer_works[:5]):
        book_uid = gen_id()
        cursor.execute("""
            INSERT OR REPLACE INTO books (id, title, author_id, cover_path, description,
                genre, publisher, isbn, total_chapters, total_word_count, status,
                publication_date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            book_uid, f"测试书籍 {i+1}", creator[0],
            generate_test_image(MEDIA_DIR / "images" / f"book_cover_{i+1}.jpg", 400, 600),
            "这是测试书籍的描述",
            random.choice(["小说", "散文", "诗歌", "学术"]),
            random.choice(["测试出版社A", "测试出版社B"]),
            f"978-7-{random.randint(10000, 99999)}-{random.randint(1, 9)}-X",
            random.randint(10, 30), random.randint(50000, 300000),
            random.choice(["writing", "published", "archived"]),
            past(random.randint(0, 365)), now(), now()
        ))
        books.append((book_uid, creator))

        # 创建章节
        for ch_num in range(1, 4):
            cursor.execute("""
                INSERT OR REPLACE INTO chapters (id, work_id, title, chapter_number, body,
                    word_count, status, published_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                gen_id(), wuid,
                f"第{ch_num}章 {random.choice(['启程', '相遇', '冲突'])}",
                ch_num,
                f"这是第{ch_num}章的内容...\n" + "\n".join([f"第{j}行测试内容。" for j in range(1, 11)]),
                random.randint(2000, 5000),
                "published" if ch_num <= 2 else "draft",
                past(random.randint(1, 30)), now(), now()
            ))

    print(f"  ✓ 创建 {len(books)} 本书籍")
    return books


def seed_articles(conn, users):
    """创建文章."""
    print("\n=== 4. 创建文章 ===")

    cursor = conn.cursor()
    articles = []

    for i in range(20):
        creator = random.choice(users)
        cursor.execute("""
            INSERT OR REPLACE INTO articles (id, title, subtitle, content, excerpt,
                author_id, category, tags, word_count, reading_time_minutes, status,
                published_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            gen_id(),
            f"测试文章 #{i+1}: {random.choice(['创作心得', '技巧分享', '作品解析'])}",
            "",
            f"# 测试文章\n\n这是文章的正文内容...\n\n" + "\n".join([f"第{j}段测试内容。" for j in range(1, 6)]),
            "这是文章的摘要内容...",
            creator[0],
            random.choice(["科技", "文学", "历史", "艺术", "生活"]),
            "[]",
            random.randint(1000, 3000),
            random.randint(3, 10),
            random.choice(["draft", "published", "archived"]),
            past(random.randint(0, 180)) if random.random() > 0.3 else None,
            now(), now()
        ))
        articles.append(gen_id())

    print(f"  ✓ 创建 {len(articles)} 篇文章")
    return articles


def seed_manuscripts(conn, books):
    """创建手稿."""
    print("\n=== 5. 创建手稿 ===")

    cursor = conn.cursor()
    manuscripts = []

    for book_uid, creator in books:
        for v in range(1, 3):
            cursor.execute("""
                INSERT OR REPLACE INTO manuscripts (id, title, book_id, chapter_number,
                    content, word_count, status, version, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                gen_id(),
                f"《测试书籍》手稿v{v}",
                book_uid, 1,
                f"手稿版本{v}的内容...",
                random.randint(2000, 5000),
                "final" if v == 2 else "draft",
                v, now(), now()
            ))
            manuscripts.append(gen_id())

    print(f"  ✓ 创建 {len(manuscripts)} 个手稿")
    return manuscripts


def main():
    """主函数."""
    print("=" * 60)
    print("OriSpark 种子数据注入 (简化版)")
    print("=" * 60)

    # 连接数据库
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys=ON")

    try:
        # 确保schema正确
        print("\n检查并修复数据库schema...")
        ensure_users_table(conn)

        # 执行种子
        print("\n开始种子数据注入...")

        users = seed_users(conn)
        works = seed_works(conn, users)
        books = seed_books(conn, works, users)
        articles = seed_articles(conn, users)
        manuscripts = seed_manuscripts(conn, books)

        conn.commit()

        # 统计
        print("\n" + "=" * 60)
        print("种子数据注入完成!")
        print("=" * 60)

        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        print(f"  用户: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM works")
        print(f"  作品: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM books")
        print(f"  书籍: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM articles")
        print(f"  文章: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM chapters")
        print(f"  章节: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM manuscripts")
        print(f"  手稿: {cursor.fetchone()[0]}")

        # 按创作者类型统计
        print("\n按创作者类型统计:")
        for ct in ["illustrator", "photographer", "video_creator", "crafter", "musician", "writer"]:
            cursor.execute("SELECT COUNT(*) FROM users WHERE creator_type = ?", (ct,))
            user_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM works WHERE creator_type = ?", (ct,))
            work_count = cursor.fetchone()[0]
            print(f"  {ct}: {user_count} 用户, {work_count} 作品")

        # 媒体文件统计
        print("\n媒体文件统计:")
        print(f"  图片: {len(list(MEDIA_DIR.glob('images/**'), recursive=True))}")
        print(f"  音频: {len(list(MEDIA_DIR.glob('audio/**'), recursive=True))}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
