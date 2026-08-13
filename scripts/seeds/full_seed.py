"""简化的种子数据生成器 - 使用本地生成的媒体文件."""

import sys
import uuid
import random
import math
import struct
from pathlib import Path
from datetime import datetime, timedelta, timezone
import os

# 添加路径 - 正确解析项目根目录和backend目录
# 脚本位置: .../scripts/seeds/full_seed.py
script_dir = Path(__file__).parent.parent.parent  # OriSpark/ 项目根目录
backend_dir = script_dir / "backend"  # backend/ 目录

sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(script_dir))

# 确保当前目录是 backend
os.chdir(backend_dir)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import event

from app.database import Base
from app.models.system import User
from app.models.work import Work
from app.models.book import Book
from app.models.manuscript import Manuscript
from app.models.article import Article
from app.models.writing_v4 import Chapter, ChapterComment, ChapterRevision
from app.models.contract import ContractInstance, SplitRule
from app.models.notary import NotaryRecord
from app.models.certification import CertificationRecord
from app.models.monitor import MonitorTask, MonitorResult
from app.models.insurance import InsuranceProvider, InsuranceProduct, InsurancePolicy
from app.models.invoice import Invoice
from app.models.commission import CommissionProject
from app.models.supply import Partner
from app.models.logistics import LogisticsProvider, LogisticsShipment
from app.models.content_pipeline import PlatformAccount, MultiPlatformSchedule
from app.models.innocence_proof import InnocenceProof
from app.models.ai_session import AiCreationSession
from app.models.credit import CreditRating, CreditBehavior


DB_PATH = backend_dir / "data" / "oristudio.db"
MEDIA_DIR = script_dir / "test_media"

for d in [MEDIA_DIR, MEDIA_DIR / "images", MEDIA_DIR / "audio", MEDIA_DIR / "video"]:
    d.mkdir(parents=True, exist_ok=True)


def gen_id():
    return uuid.uuid4().hex[:16]


def now():
    return datetime.now(timezone.utc)


def past(days=30):
    return now() - timedelta(days=days)


def generate_test_image(path: Path, width: int = 800, height: int = 600):
    """生成测试图片."""
    from PIL import Image
    import random
    img = Image.new('RGB', (width, height), color=(
        random.randint(50, 200), random.randint(50, 200), random.randint(50, 200)
    ))
    img.save(path)
    return str(path)


def generate_test_audio(path: Path, duration_sec: int = 5):
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


def generate_test_pdf(path: Path, title: str = "测试书籍"):
    """生成测试PDF."""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        c = canvas.Canvas(str(path), pagesize=A4)
        c.drawString(100, 750, title)
        for i in range(20):
            c.drawString(100, 700 - i * 20, f"第{i+1}行测试内容 - Lorem ipsum dolor sit amet.")
        c.showPage()
        c.save()
        return str(path)
    except Exception as e:
        print(f"PDF生成失败: {e}")
        return ""


def seed_users(db):
    """创建用户."""
    print("\n=== 1. 创建用户 ===")

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
            user = User(
                id=uid,
                username=f"{label}_{i+1}",
                email=f"{label}_{i+1}@test.orispark.com",
                password_hash="pbkdf2:sha256:260000$test$test",
                role="creator",
                status="active",
                creator_type=creator_type,
                login_platform="web",
                created_at=past(random.randint(1, 365)),
            )
            db.add(user)
            users.append((uid, user))

    # 其他角色
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
            user = User(
                id=uid,
                username=f"{label}_{i+1}",
                email=f"{label}_{i+1}@test.orispark.com",
                password_hash="pbkdf2:sha256:260000$test$test",
                role="user",
                status="active",
                bio=f"测试{label}角色#{i+1}",
                created_at=past(random.randint(1, 365)),
            )
            db.add(user)
            users.append((uid, user))

    db.flush()
    print(f"  ✓ 创建 {len(users)} 个用户")
    return users


def seed_works(db, users):
    """创建作品."""
    print("\n=== 2. 创建作品 ===")

    works = []
    creator_types = ["illustrator", "photographer", "video_creator", "crafter", "musician", "writer"]

    for ct in creator_types:
        creator_users = [u for u in users if u[1].creator_type == ct]
        for i in range(5):
            creator = random.choice(creator_users)
            wuid = gen_id()

            if ct == "illustrator":
                file_type, ext = "image", "jpg"
                mime_type = "image/jpeg"
                thumbnail = generate_test_image(MEDIA_DIR / "images" / f"ill_{i+1}.jpg", 800, 600)
                title = random.choice(["星空下的花园", "城市夜景", "梦幻森林", "秋日私语"])
            elif ct == "photographer":
                file_type, ext = "image", "jpg"
                mime_type = "image/jpeg"
                thumbnail = generate_test_image(MEDIA_DIR / "images" / f"photo_{i+1}.jpg", 1200, 800)
                title = random.choice(["晨光中的教堂", "夕阳下的海滩", "城市街拍", "自然风光"])
            elif ct == "video_creator":
                file_type, ext = "video", "mp4"
                mime_type = "video/mp4"
                thumbnail = generate_test_image(MEDIA_DIR / "images" / f"video_{i+1}.jpg", 640, 360)
                title = random.choice(["产品宣传片", "旅行Vlog", "教程视频", "生活记录"])
            elif ct == "crafter":
                file_type, ext = "image", "jpg"
                mime_type = "image/jpeg"
                thumbnail = generate_test_image(MEDIA_DIR / "images" / f"crafter_{i+1}.jpg", 600, 600)
                title = random.choice(["手工陶瓷花瓶", "编织毛线帽", "木雕摆件", "皮革钱包"])
            elif ct == "musician":
                file_type, ext = "audio", "mp3"
                mime_type = "audio/mpeg"
                thumbnail = generate_test_image(MEDIA_DIR / "images" / f"music_{i+1}.jpg", 400, 400)
                audio_path = generate_test_audio(MEDIA_DIR / "audio" / f"music_{i+1}.mp3", 15)
                title = random.choice(["春日序曲", "深夜爵士", "电子梦境", "民谣故事"])
            else:
                file_type, ext = "document", "pdf"
                mime_type = "application/pdf"
                thumbnail = generate_test_image(MEDIA_DIR / "images" / f"writer_{i+1}.jpg", 400, 600)
                pdf_path = generate_test_pdf(MEDIA_DIR / "images" / f"writer_{i+1}.pdf", f"《{random.choice(['星辰', '月光', '海浪'])}》")
                title = random.choice(["星辰大海的旅程", "时光倒流的五分钟", "最后的守护者"])

            work = Work(
                id=wuid,
                title=title,
                file_path=thumbnail,
                file_name=f"{ct}_{i+1}.{ext}",
                file_size=random.randint(100000, 5000000),
                file_type=file_type,
                file_extension=ext,
                mime_type=mime_type,
                sha256=uuid.uuid4().hex[:64],
                thumbnail_path=thumbnail,
                creator_id=creator[0],
                creator_type=ct,
                description=f"这是{ct}创作者的测试作品{i+1}",
                status="active",
                is_verified=random.choice([True, False]),
                created_at=past(random.randint(1, 365)),
            )
            db.add(work)
            works.append((wuid, work, creator))

    db.flush()
    print(f"  ✓ 创建 {len(works)} 个作品")
    return works


def seed_books(db, works, users):
    """创建书籍."""
    print("\n=== 3. 创建书籍 ===")

    books = []
    for wuid, work, creator in works:
        if work.creator_type != "writer":
            continue

        book_uid = gen_id()
        book = Book(
            id=book_uid,
            title=work.title,
            author_id=creator[0],
            cover_path=work.thumbnail_path,
            description=work.description,
            genre=random.choice(["小说", "散文", "诗歌", "学术", "科普"]),
            publisher=random.choice(["测试出版社A", "测试出版社B", "独立出版"]),
            isbn=f"978-7-{random.randint(10000, 99999)}-{random.randint(1, 9)}-X",
            total_chapters=random.randint(10, 30),
            total_word_count=random.randint(50000, 300000),
            status=random.choice(["writing", "published", "archived"]),
            publication_date=past(random.randint(0, 365)),
            created_at=work.created_at,
        )
        db.add(book)
        books.append((book_uid, book, creator))

        # 创建章节
        for ch_num in range(1, min(5, book.total_chapters + 1)):
            chapter = Chapter(
                id=gen_id(),
                work_id=wuid,
                title=f"第{ch_num}章 {random.choice(['启程', '相遇', '冲突', '转折', '高潮', '结局'])}",
                chapter_number=ch_num,
                body=f"这是第{ch_num}章的内容...\n\n" + "\n".join([f"第{j}行测试内容。" for j in range(1, 11)]),
                word_count=random.randint(2000, 5000),
                status="published" if ch_num <= 2 else "draft",
                created_at=past(random.randint(1, 30)),
            )
            db.add(chapter)

        # 创建手稿
        for v in range(1, 3):
            manuscript = Manuscript(
                id=gen_id(),
                title=f"{book.title} - 手稿v{v}",
                book_id=book_uid,
                chapter_number=1,
                content=f"手稿版本{v}的内容...",
                word_count=random.randint(2000, 5000),
                status="final" if v == 2 else "draft",
                version=v,
                created_at=past(random.randint(1, 30)),
            )
            db.add(manuscript)

    db.flush()
    print(f"  ✓ 创建 {len(books)} 本书籍")
    return books


def seed_articles(db, works, users):
    """创建文章."""
    print("\n=== 4. 创建文章 ===")

    articles = []
    for i in range(20):
        creator = random.choice(users)
        article_title = f"测试文章 #{i+1}: {random.choice(['创作心得', '技巧分享', '作品解析'])}"
        article = Article(
            id=gen_id(),
            title=article_title,
            subtitle="",
            content=f"# {article_title}\n\n这是文章的正文内容...\n\n" + "\n".join([f"第{j}段测试内容。" for j in range(1, 6)]),
            excerpt=f"这是文章的摘要内容...",
            author_id=creator[0],
            category=random.choice(["科技", "文学", "历史", "艺术", "生活"]),
            tags=random.sample(["Python", "AI", "教程", "设计", "摄影"], k=2),
            word_count=random.randint(1000, 3000),
            reading_time_minutes=random.randint(3, 10),
            status=random.choice(["draft", "published", "archived"]),
            published_at=past(random.randint(0, 180)) if random.random() > 0.3 else None,
            created_at=past(random.randint(1, 365)),
        )
        db.add(article)
        articles.append((article.id, article, creator))

    db.flush()
    print(f"  ✓ 创建 {len(articles)} 篇文章")
    return articles


def seed_contracts(db, works, users):
    """创建合约."""
    print("\n=== 5. 创建合约 ===")

    contracts = []
    contract_types = ["copyright_transfer", "product_license", "exclusive_license", "non_exclusive_license"]
    statuses = ["draft", "listed", "active", "subscribed", "escrowed", "insured", "executing", "completed"]

    for i in range(10):
        work = random.choice(works)
        creator = work[2]
        operator = random.choice([u for u in users if u[1].role == "user" and u[1].creator_type is None])

        contract = ContractInstance(
            id=gen_id(),
            title=f"{work[1].title} - 合约授权",
            description=f"授权{work[1].title}的使用权",
            work_id=work[0],
            contract_type=random.choice(contract_types),
            total_amount=random.uniform(1000, 50000),
            currency="CNY",
            billing_cycle=random.choice(["one_time", "monthly", "yearly"]),
            scope_usage=random.choice(["personal", "commercial", "resale"]),
            scope_geography=random.choice(["local", "national", "global", "china"]),
            scope_duration=random.choice(["1year", "3years", "perpetual"]),
            status=random.choice(statuses),
            split_rules_json='[{"participant_id": "creator", "role": "creator", "percentage": 0.7}]',
            creator_id=creator[0],
            operator_id=operator[0],
            verified="approved",
            published_at=past(random.randint(1, 90)),
            created_at=past(random.randint(1, 180)),
        )
        db.add(contract)
        contracts.append((contract.id, contract, creator))

        # 分润规则
        for pct in [0.7, 0.15, 0.05, 0.05]:
            rule = SplitRule(
                id=gen_id(),
                contract_id=contract.id,
                participant_id=random.choice([u[0] for u in users]),
                role=random.choice(["creator", "operator", "legal_rep", "tax_agent"]),
                percentage=pct,
                created_at=contract.created_at,
            )
            db.add(rule)

    db.flush()
    print(f"  ✓ 创建 {len(contracts)} 个合约")
    return contracts


def seed_certifications(db, works):
    """创建区块链存证."""
    print("\n=== 6. 创建区块链存证 ===")

    count = 0
    for wuid, work, creator in works:
        if work.is_verified:
            cert = CertificationRecord(
                id=gen_id(),
                work_id=wuid,
                sha256_hash=work.sha256,
                blockchain_tx_id=uuid.uuid4().hex[:32],
                block_height=random.randint(1000000, 9999999),
                is_court_admissible=True,
                certificate_url=f"https://cert.orispark.com/{wuid}",
                cost_saved_yuan=random.randint(200, 1000),
                created_at=past(random.randint(1, 30)),
            )
            db.add(cert)
            count += 1

    print(f"  ✓ 创建 {count} 个区块链存证")
    return count


def seed_monitoring(db, works):
    """创建监测任务."""
    print("\n=== 7. 创建监测任务 ===")

    tasks = []
    platforms = ["baidu", "google", "copyscape", "github"]
    search_types = ["image", "text", "video_fingerprint"]

    for wuid, work, creator in works[:15]:
        task = MonitorTask(
            id=gen_id(),
            work_id=wuid,
            search_type=random.choice(search_types),
            platform=random.choice(platforms),
            interval=random.choice(["manual", "daily", "weekly"]),
            status=random.choice(["active", "paused", "completed"]),
            last_run=past(random.randint(0, 7)),
            next_run=future(random.randint(1, 30)),
            priority_score=random.uniform(0, 100),
            created_at=past(random.randint(1, 90)),
        )
        db.add(task)
        tasks.append((task.id, task, work))

    db.flush()
    print(f"  ✓ 创建 {len(tasks)} 个监测任务")
    return tasks


def seed_monitor_results(db, tasks):
    """创建监测结果."""
    print("\n=== 8. 创建监测结果 ===")

    results = []
    for task_id, task, work in tasks[:10]:
        for j in range(random.randint(1, 3)):
            result = MonitorResult(
                id=gen_id(),
                task_id=task_id,
                matched_url=f"https://example.com/match_{j+1}",
                matched_title=f"疑似侵权内容 #{j+1}",
                similarity=random.uniform(60, 95),
                found_at=past(random.randint(0, 30)),
                status=random.choice(["pending_review", "infringing", "ignored"]),
                action_taken=random.choice(["generate_complaint", "export_evidence", "mark_handled"]),
                is_mock=random.choice([0, 1]),
                match_type=task.search_type,
                confidence=random.uniform(50, 90),
                created_at=past(random.randint(0, 30)),
            )
            db.add(result)
            results.append(result)

    db.flush()
    print(f"  ✓ 创建 {len(results)} 个监测结果")
    return results


def seed_invoices(db, users, contracts):
    """创建发票."""
    print("\n=== 9. 创建发票 ===")

    count = 0
    for i, (cid, contract, creator) in enumerate(contracts[:5]):
        invoice = Invoice(
            id=gen_id(),
            user_id=creator[0],
            invoice_number=f"INV/{now().year}/{now().month:02d}/{i+1:04d}",
            amount_yuan=float(contract.total_amount),
            tax_rate=0.06,
            subtotal_yuan=float(contract.total_amount) / 1.06,
            tax_amount_yuan=float(contract.total_amount) - float(contract.total_amount) / 1.06,
            total_yuan=float(contract.total_amount),
            status=random.choice(["pending", "paid", "cancelled"]),
            due_date=future(random.randint(7, 30)),
            description=f"合约{contract.title[:20]}...的发票",
            payment_method=random.choice(["bank_transfer", "alipay", "wechat"]),
            created_at=past(random.randint(1, 60)),
        )
        db.add(invoice)
        count += 1

    print(f"  ✓ 创建 {count} 个发票")
    return count


def seed_partners(db, users):
    """创建合作伙伴."""
    print("\n=== 10. 创建合作伙伴 ===")

    partners = []
    for i in range(5):
        partner = Partner(
            id=gen_id(),
            name=f"测试合作方{i+1}",
            contact_person=f"联系人{i+1}",
            contact_email=f"contact{i+1}@partner.test",
            contact_phone=f"138{i+1:08d}",
            partner_type=random.choice(["operator", "legal_rep", "tax_agent", "logistics"]),
            status=random.choice(["active", "inactive", "pending"]),
            description=f"这是测试合作方{i+1}的描述信息...",
            created_at=past(random.randint(1, 365)),
        )
        db.add(partner)
        partners.append(partner)

    db.flush()
    print(f"  ✓ 创建 {len(partners)} 个合作伙伴")
    return partners


def seed_platform_accounts(db, users):
    """创建平台账号."""
    print("\n=== 11. 创建平台账号 ===")

    accounts = []
    platforms = ["xiaohongshu", "zcool", "bilibili", "weibo", "instagram", "douyin"]

    for user in users[:10]:
        for platform in random.sample(platforms, k=random.randint(1, 2)):
            account = PlatformAccount(
                id=gen_id(),
                user_id=user[0],
                platform=platform,
                account_name=f"{platform}_creator_{random.randint(1000, 9999)}",
                account_id=f"{platform}_uid_{gen_id()[:8]}",
                follower_count=random.randint(100, 100000),
                is_active=True,
                created_at=past(random.randint(1, 365)),
            )
            db.add(account)
            accounts.append(account)

    db.flush()
    print(f"  ✓ 创建 {len(accounts)} 个平台账号")
    return accounts


def seed_content_pipelines(db, works, users):
    """创建内容分发计划."""
    print("\n=== 12. 创建内容分发计划 ===")

    schedules = []
    for i in range(10):
        work = random.choice(works)
        schedule = MultiPlatformSchedule(
            id=gen_id(),
            user_id=work.creator_id,
            work_id=work.id,
            title=f"定时发布计划 #{i+1}",
            description="自动发布到多个平台的计划",
            platforms='[{"platform": "xiaohongshu", "scheduled": true}]',
            scheduled_at=future(random.randint(1, 30)),
            is_recurring=False,
            status=random.choice(["scheduled", "published", "failed"]),
            created_at=past(random.randint(1, 30)),
        )
        db.add(schedule)
        schedules.append(schedule)

    db.flush()
    print(f"  ✓ 创建 {len(schedules)} 个分发计划")
    return schedules


def seed_notary_records(db, works):
    """创建存证记录."""
    print("\n=== 13. 创建存证记录 ===")

    count = 0
    platforms = ["banquanjia", "antchain", "zhixinchain"]
    for wuid, work, creator in works[:10]:
        record = NotaryRecord(
            id=gen_id(),
            work_id=wuid,
            platform=random.choice(platforms),
            platform_url=f"https://{random.choice(platforms)}.com/record/{wuid}",
            transaction_hash=uuid.uuid4().hex[:64],
            block_height=random.randint(100000, 999999),
            blockchain=random.choice(["Ethereum", "Polygon", "蚂蚁链"]),
            certificate_id=wuid[:16],
            status=random.choice(["confirmed", "pending", "unverified"]),
            fee=random.uniform(0.5, 5.0),
            payment_method=random.choice(["wechat", "alipay"]),
            qr_code_url=f"https://qr.orispark.com/{wuid}.png",
            evidence_hash=work.sha256,
            confirmed_at=past(random.randint(1, 30)),
            created_at=past(random.randint(1, 60)),
        )
        db.add(record)
        count += 1

    print(f"  ✓ 创建 {count} 个存证记录")
    return count


def main():
    """主函数."""
    print("=" * 60)
    print("OriSpark 全类型创作者种子数据注入")
    print("=" * 60)

    # 连接数据库
    engine = create_engine(
        f"sqlite:///{DB_PATH}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _pragma(dbapi_conn, record):
        c = dbapi_conn.cursor()
        c.execute("PRAGMA foreign_keys=ON")
        c.close()

    # 确保所有表已创建
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    db = Session()

    # 清空现有数据
    print("\n清空现有数据...")
    for model in [
        ContractInstance, SplitRule, CertificationRecord, NotaryRecord,
        MonitorTask, MonitorResult, Invoice, Partner, PlatformAccount,
        MultiPlatformSchedule, Book, Manuscript, Article, Chapter, Work, User,
    ]:
        try:
            db.query(model).delete()
        except Exception as e:
            print(f"  清理 {model.__tablename__} 失败: {e}")

    db.commit()
    print("  ✓ 数据已清空")

    # 执行种子
    print("\n开始种子数据注入...")

    users = seed_users(db)
    works = seed_works(db, users)
    books = seed_books(db, works, users)
    articles = seed_articles(db, works, users)
    contracts = seed_contracts(db, works, users)
    seed_certifications(db, works)
    tasks = seed_monitoring(db, works)
    seed_monitor_results(db, tasks)
    seed_invoices(db, users, contracts)
    partners = seed_partners(db, users)
    accounts = seed_platform_accounts(db, users)
    schedules = seed_content_pipelines(db, works, users)
    seed_notary_records(db, works)

    db.commit()

    # 统计
    print("\n" + "=" * 60)
    print("种子数据注入完成!")
    print("=" * 60)
    print(f"  用户: {db.query(User).count()}")
    print(f"  作品: {db.query(Work).count()}")
    print(f"  书籍: {db.query(Book).count()}")
    print(f"  文章: {db.query(Article).count()}")
    print(f"  合约: {db.query(ContractInstance).count()}")
    print(f"  存证: {db.query(CertificationRecord).count()}")
    print(f"  监测任务: {db.query(MonitorTask).count()}")
    print(f"  监测结果: {db.query(MonitorResult).count()}")
    print(f"  发票: {db.query(Invoice).count()}")
    print(f"  合作伙伴: {db.query(Partner).count()}")
    print(f"  平台账号: {db.query(PlatformAccount).count()}")
    print(f"  分发计划: {db.query(MultiPlatformSchedule).count()}")
    print(f"  存证记录: {db.query(NotaryRecord).count()}")

    # 按创作者类型统计
    print("\n按创作者类型统计:")
    for ct in ["illustrator", "photographer", "video_creator", "crafter", "musician", "writer"]:
        count = db.query(User).filter(User.creator_type == ct).count()
        work_count = db.query(Work).filter(Work.creator_type == ct).count()
        print(f"  {ct}: {count} 用户, {work_count} 作品")

    # 媒体文件统计
    print("\n媒体文件统计:")
    print(f"  图片: {len(list(MEDIA_DIR.glob('images/**'), recursive=True))}")
    print(f"  音频: {len(list(MEDIA_DIR.glob('audio/**'), recursive=True))}")
    print(f"  视频: {len(list(MEDIA_DIR.glob('video/**'), recursive=True))}")

    db.close()


if __name__ == "__main__":
    main()
