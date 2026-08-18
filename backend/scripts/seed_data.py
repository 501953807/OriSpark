"""数据库种子数据填充脚本（幂等）."""

import sys
from pathlib import Path
from datetime import datetime, timezone
import uuid

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import event

from app.database import Base
from app.models.system import User


def make_test_engine():
    """创建测试用内存引擎."""
    db_path = Path(__file__).parent.parent / "data" / "oristudio.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        import sqlite3
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def ensure_columns(db):
    """确保users表包含所有缺失列."""
    missing = [
        ("bio", "TEXT"),
        ("login_platform", "VARCHAR(20)"),
        ("participant_roles", "JSON"),
        ("is_platform_operator", "BOOLEAN DEFAULT 0"),
        ("is_payment_provider", "BOOLEAN DEFAULT 0"),
        ("is_insurer", "BOOLEAN DEFAULT 0"),
        ("is_logistics", "BOOLEAN DEFAULT 0"),
        ("company_name", "VARCHAR(200)"),
        ("company_license_no", "VARCHAR(100)"),
        ("company_address", "TEXT"),
        ("company_contact", "VARCHAR(100)"),
        ("company_phone", "VARCHAR(50)"),
        ("company_email", "VARCHAR(200)"),
        ("qualification_verified", "BOOLEAN DEFAULT 0"),
        ("qualification_verified_at", "DATETIME"),
    ]
    for col, ctype in missing:
        try:
            db.execute(text(f"ALTER TABLE users ADD COLUMN {col} {ctype}"))
            print(f"  Added column: users.{col}")
        except Exception:
            pass  # already exists
    db.commit()


def seed_basic_data(db):
    """填充基础数据（幂等，按 email 检查）。"""
    ensure_columns(db)
    from app.models.system import User

    required_emails = {"local@oristudio", "operator@oristudio", "demo@orispark"}
    existing = {u.email for u in db.query(User).filter(User.email.in_(required_emails)).all()}

    created_users = []
    for email, username, role in [
        ("local@oristudio", "演示用户", "creator"),
        ("operator@oristudio", "运营方", "operator"),
        ("demo@orispark", "Demo用户", "local"),
    ]:
        if email not in existing:
            db.add(User(
                email=email,
                username=username,
                password_hash="pbkdf2:sha256:260000$test$test",
                role=role,
                status="active",
            ))
            created_users.append(email)

    if created_users:
        db.commit()
        print(f"Created users: {created_users}")
    else:
        print("All required users already exist, skipping")


def seed_insurance_data(db):
    """填充保险市场数据（幂等）。"""
    from app.models.insurance import InsuranceProvider, InsuranceProduct

    if db.query(InsuranceProduct).count() >= 15:
        print("Insurance products already exist, skipping")
        return

    # Create providers with deterministic IDs to avoid FK issues
    provider_ids = []
    for i, (name_zh, license_no) in enumerate([
        ("测试保险公司A", "TEST001"),
        ("测试保险公司B", "TEST002"),
    ]):
        pid = f"prov{i+1:02d}" * 16  # 32-char ID
        existing = db.query(InsuranceProvider).filter(InsuranceProvider.name_zh == name_zh).first()
        if not existing:
            p = InsuranceProvider(
                id=pid,
                name_zh=name_zh,
                license_no=license_no,
                is_active=True,
            )
            db.add(p)
            provider_ids.append(pid)
        else:
            provider_ids.append(existing.id)

    db.commit()
    print(f"Created {len(provider_ids)} insurance providers")

    if db.query(InsuranceProduct).count() > 0:
        return

    # Generate products
    products = []
    categories = ["copyright", "enforcement", "performance"]
    tiers = ["basic", "advanced", "pro"]

    for provider_id in provider_ids:
        for category in categories:
            for tier in tiers:
                products.append(InsuranceProduct(
                    product_key=f"{provider_id[:8]}_{category}_{tier}",
                    provider_id=provider_id,
                    category=category,
                    tier=tier,
                    name_zh=f"{category}保险-{tier}档",
                    annual_min_yuan=100.0 if tier == "basic" else 500.0 if tier == "advanced" else 2000.0,
                    annual_max_yuan=5000.0 if tier == "basic" else 20000.0 if tier == "advanced" else 100000.0,
                ))

    for p in products:
        db.add(p)
    db.commit()
    print(f"Created {len(products)} insurance products")


def seed_dictionary_data(db):
    """填充字典数据（幂等，按 group_key 检查）。"""
    from app.models.system import DictionaryGroup, DictionaryItem

    # 已有 397+ 条字典条目，跳过全量注入
    if db.query(DictionaryGroup).count() >= 50:
        print("Dictionary data already complete, skipping")
        return

    groups = [
        DictionaryGroup(id=str(uuid.uuid4().hex[:32]), group_key="creator_type", name="创作者类型"),
        DictionaryGroup(id=str(uuid.uuid4().hex[:32]), group_key="contract_status", name="合约状态"),
        DictionaryGroup(id=str(uuid.uuid4().hex[:32]), group_key="work_type", name="作品类型"),
    ]

    items = [
        DictionaryItem(id=str(uuid.uuid4().hex[:32]), group_id=groups[0].id, item_key="illustrator", item_value="插画师"),
        DictionaryItem(id=str(uuid.uuid4().hex[:32]), group_id=groups[0].id, item_key="photographer", item_value="摄影师"),
        DictionaryItem(id=str(uuid.uuid4().hex[:32]), group_id=groups[1].id, item_key="draft", item_value="草稿"),
        DictionaryItem(id=str(uuid.uuid4().hex[:32]), group_id=groups[1].id, item_key="listed", item_value="已挂牌"),
        DictionaryItem(id=str(uuid.uuid4().hex[:32]), group_id=groups[2].id, item_key="image", item_value="图片"),
        DictionaryItem(id=str(uuid.uuid4().hex[:32]), group_id=groups[2].id, item_key="video", item_value="视频"),
    ]

    for obj in groups + items:
        db.add(obj)

    db.commit()
    print(f"Created {len(groups)} groups and {len(items)} items")


def seed_system_settings(db):
    """填充系统设置默认值（幂等）。"""
    from app.models.system import SystemSetting
    defaults = {
        "onboarding_completed": "false",
        "storage_quota_mb": "5120",
        "storage_warn_threshold": "80",
        "backup_schedule_cron": "0 2 * * *",
        "backup_schedule_enabled": "true",
        "backup_schedule_encrypted": "true",
        "default_theme": "light",
        "default_language": "zh-CN",
        "max_file_size_mb": "500",
        "allowed_file_types": "image,audio,video,document,code,design",
        "brand_name": "OriStudio",
        "brand_slogan": "创作者的数字资产管理与版权保护平台",
    }
    for key, value in defaults.items():
        existing = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if not existing:
            db.add(SystemSetting(key=key, value=value))
    db.commit()
    print(f"System settings seeded")


def seed_disclaimers(db):
    """填充免责声明种子数据（幂等，由 system_service._seed_disclaimers 也可触发）。"""
    from app.models.system import Disclaimer
    if db.query(Disclaimer).count() >= 7:
        print("Disclaimers already exist, skipping")
        return

    seeds = [
        ("no_attorney_relationship", "不构成律师-客户关系",
         "使用本软件不建立律师-客户特权关系。本软件是信息参考工具，不提供法律代理服务。如需法律意见，请咨询持证律师。",
         "legal", 10, True, "modal", ["ipr"]),
        ("no_legal_advice", "不构成法律建议",
         "IP登记指引、类别推荐、费用计算等信息仅供参考，不构成法律建议。每个案件的具体情况不同，请咨询专业律师获取针对性的法律意见。",
         "legal", 9, True, "modal", ["ipr"]),
        ("no_guarantee", "不保证注册成功",
         "商标/专利/版权注册结果取决于官方审查机构的审查标准和判断。本工具不保证任何注册申请的通过率或成功率。注册费用一旦支付，无论结果如何均不予退还(官方收费)。",
         "legal", 8, True, "banner", ["ipr"]),
        ("pod_ip_warning", "POD平台IP条款警告",
         "在POD平台上传设计前，请仔细阅读平台服务条款中有关知识产权的部分。各平台对侵权内容的处理政策不同。上传他人享有著作权的设计可能导致账户被暂停或永久封禁。",
         "warning", 7, False, "banner", ["supply", "pod_channel"]),
        ("ai_content_label", "AI内容标注要求",
         "建议按各平台规则标注'AI辅助生成'或等效标签。不同平台(小红书/抖音/Instagram/站酷等)的AI内容标注规则不同，请在发布前查阅对应平台的现行政策。",
         "warning", 6, False, "footer", ["publish"]),
        ("monitor_limitation", "侵权监测局限性",
         "本监测功能基于公开搜索引擎的以图搜图能力（百度识图/Google Vision），存在以下局限：1. 不能保证发现所有侵权行为；2. 搜索结果需人工审核判断是否构成侵权；3. 相似度分数仅为参考——高相似度不必然等于侵权，低相似度不必然等于不侵权。",
         "warning", 5, False, "banner", ["monitor"]),
        ("jurisdiction_limitation", "司法管辖区限制",
         "IP登记指引仅覆盖主要司法管辖区(中国/美国/欧盟/WIPO/日本/韩国)。其他辖区的IP法律法规、申请流程、费用标准可能不同。如需在未覆盖辖区进行IP登记，请咨询当地持证代理机构。",
         "legal", 4, False, "banner", ["ipr"]),
    ]
    for dk, title, content, category, priority, is_required, mode, pages in seeds:
        existing = db.query(Disclaimer).filter(Disclaimer.disclaimer_key == dk).first()
        if not existing:
            db.add(Disclaimer(
                disclaimer_key=dk, title=title, content=content,
                category=category, priority=priority,
                is_required=is_required, display_mode=mode, trigger_pages=pages,
            ))
    db.commit()
    print(f"Disclaimers seeded")


def seed_factory_data(db):
    """填充工厂/物流基础数据（幂等）。"""
    from app.models.factory import Factory
    from app.models.logistics import LogisticsProvider
    if db.query(Factory).count() >= 2:
        print("Factory data already exists, skipping")
        return

    factories = [
        ("test_factory_001", "测试印刷工厂A", "深圳", "contact@testfactory.com"),
        ("test_factory_002", "测试印刷工厂B", "杭州", "contact@testfactory2.com"),
    ]
    for fid, name, loc, contact in factories:
        existing = db.query(Factory).filter(Factory.name == name).first()
        if not existing:
            db.add(Factory(id=fid, name=name, location=loc, contact=contact, rating=4.5))

    db.commit()
    print(f"Factory data seeded")

    if db.query(LogisticsProvider).count() >= 2:
        print("Logistics data already exists, skipping")
        return

    companies = [
        ("sf-express", "顺丰速运", "contact@sf-express.com"),
        ("yunda", "韵达快递", "contact@yunda.com"),
    ]
    for lid, name, email in companies:
        existing = db.query(LogisticsProvider).filter(LogisticsProvider.name == name).first()
        if not existing:
            db.add(LogisticsProvider(id=lid, name=name, contact_email=email))

    db.commit()
    print(f"Logistics data seeded")


def main():
    """主入口."""
    engine = make_test_engine()
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        print("Starting seed data...")
        seed_basic_data(db)
        seed_insurance_data(db)
        seed_dictionary_data(db)
        seed_system_settings(db)
        seed_disclaimers(db)
        seed_factory_data(db)
        print("Seed data completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
