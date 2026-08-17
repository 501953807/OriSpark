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
    """填充基础数据（幂等）."""
    ensure_columns(db)
    from app.models.system import User

    existing = db.query(User).filter(
        User.email.in_(["local@oristudio", "operator@oristudio"])
    ).count()
    if existing >= 2:
        print("Users already exist, skipping")
        return

    users = [
        User(
            email="local@oristudio",
            username="演示用户",
            password_hash="pbkdf2:sha256:260000$test$test",
            role="creator",
            status="active",
        ),
        User(
            email="operator@oristudio",
            username="运营方",
            password_hash="pbkdf2:sha256:260000$test$test",
            role="operator",
            status="active",
        ),
    ]
    for user in users:
        db.add(user)
    db.commit()
    print(f"Created {len(users)} users")


def seed_insurance_data(db):
    """填充保险市场数据（幂等）."""
    from app.models.insurance import InsuranceProvider, InsuranceProduct

    if db.query(InsuranceProduct).count() >= 18:
        print("Insurance products already exist, skipping")
        return

    providers = list(db.query(InsuranceProvider).all())
    if len(providers) < 2:
        # Create missing providers
        for i in range(len(providers), 2):
            providers.append(InsuranceProvider(
                id=str(uuid.uuid4().hex[:32]),
                name_zh=f"测试保险公司{chr(65+i)}",
                license_no=f"TEST{i+1}",
                is_active=True,
            ))
        db.commit()
        print(f"Created {len(providers)} providers")

    # Clear any partial products first
    db.query(InsuranceProduct).delete()
    db.commit()

    products = []
    categories = ["copyright", "enforcement", "performance"]
    tiers = ["basic", "advanced", "pro"]

    for provider in providers:
        for category in categories:
            for tier in tiers:
                products.append(InsuranceProduct(
                    id=str(uuid.uuid4().hex[:32]),
                    product_key=f"{provider.id[:8]}_{category}_{tier}",
                    provider_id=provider.id,
                    category=category,
                    tier=tier,
                    name_zh=f"{category}保险-{tier}档",
                    annual_min_yuan=100.0 if tier == "basic" else 500.0 if tier == "advanced" else 2000.0,
                    annual_max_yuan=5000.0 if tier == "basic" else (20000.0 if tier == "advanced" else 100000.0),
                    is_active=True,
                ))

    for p in products:
        db.add(p)
    db.commit()
    print(f"Created {len(products)} products")


def seed_dictionary_data(db):
    """填充字典数据（幂等）."""
    from app.models.system import DictionaryGroup, DictionaryItem

    if db.query(DictionaryGroup).count() >= 3:
        print("Dictionary data already exists, skipping")
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
        print("Seed data completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
