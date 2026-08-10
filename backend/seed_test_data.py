"""Seed script to create test data for all 9 roles and business workflows."""
import sys
import hashlib
from datetime import datetime, timezone, date

sys.path.insert(0, '/Users/tangxiaochuan/AIWorkspace/ClaudeWorkspace/OriSpark/backend')

from app.database import SessionLocal
from app.models.system import User
from app.models.work import Work
from app.models.ipr import IPRegistration
from app.models.enforcement import EnforcementAction
from app.models.monitor import MonitorResult, MonitorTask
from app.models.supply import Partner, Order
from app.models.matchmaking import MatchRequest
from app.models.contract import ContractInstance
from app.services.auth_service import _hash_password

# 9 roles to create
ROLES = [
    ('creator', '创作者', 'illustrator'),
    ('operator', '运营方', 'photographer'),
    ('legal_rep', '法务代表', 'video_creator'),
    ('tax_agent', '税务代理', 'craftsman'),
    ('logistics', '物流方', 'musician'),
    ('insurer', '保险方', 'writer'),
    ('trader', '采购方', 'illustrator'),
    ('payment_provider', '支付托管方', 'photographer'),
    ('platform', '平台方', 'video_creator'),
]

def seed_users(db):
    """Create 9 test users with different roles."""
    print("\n=== Creating 9 role users ===")
    users = {}
    for role_key, role_name, creator_type in ROLES:
        email = f'{role_key}@test.oristudio.com'
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f'  [SKIP] {role_key} already exists')
            users[role_key] = existing
            continue

        user_id = hashlib.md5(email.encode()).hexdigest()[:16]
        user = User(
            id=user_id,
            username=role_name,
            email=email,
            password_hash=_hash_password('Test1234!'),
            role='user',
            status='active',
            creator_type=creator_type,
            participant_roles=[role_key],
        )
        db.add(user)
        users[role_key] = user
        print(f'  [OK] Created {role_key} ({role_name}) - {email}')
    return users

def seed_works(db, creator_user):
    """Create test works for the creator."""
    print("\n=== Creating test works ===")
    works = []
    work_data = [
        ('测试插画作品 001', 'image', 'jpg', 'image/jpeg', 'illustrator'),
        ('测试摄影作品 002', 'image', 'png', 'image/png', 'photographer'),
        ('测试视频作品 003', 'video', 'mp4', 'video/mp4', 'video_creator'),
        ('测试音乐作品 004', 'audio', 'mp3', 'audio/mpeg', 'musician'),
        ('测试文学作品 005', 'document', 'docx', 'application/docx', 'writer'),
    ]

    for i, (title, ftype, ext, mime, ctype) in enumerate(work_data, 1):
        existing = db.query(Work).filter(Work.title == title).first()
        if existing:
            print(f'  [SKIP] Work "{title}" already exists')
            works.append(existing)
            continue

        work = Work(
            id=hashlib.md5(f'work_{i}_{title}'.encode()).hexdigest()[:32],
            title=title,
            file_path=f'/data/works/{title}.{ext}',
            file_name=f'{title}.{ext}',
            file_size=1024 * 1024 * (i + 1),  # 2MB, 3MB, etc.
            file_type=ftype,
            file_extension=ext,
            mime_type=mime,
            sha256=hashlib.sha256(f'test_hash_{i}'.encode()).hexdigest(),
            md5=hashlib.md5(f'test_md5_{i}'.encode()).hexdigest(),
            creator_id=creator_user.id,
            status='active',
            is_verified=False,
            import_mode='full',
            current_stage='created',
            license_type='CC BY 4.0',
        )
        db.add(work)
        works.append(work)
        print(f'  [OK] Created work: {title}')

    db.commit()
    return works

def seed_ipr(db, works):
    """Create test IPR registrations."""
    print("\n=== Creating IPR registrations ===")
    for work in works[:3]:
        existing = db.query(IPRegistration).filter(IPRegistration.work_id == work.id).first()
        if existing:
            print(f'  [SKIP] IPR for work "{work.title}" already exists')
            continue

        ipr = IPRegistration(
            id=hashlib.md5(f'ipr_{work.id}'.encode()).hexdigest()[:32],
            work_id=work.id,
            ip_type='copyright',
            jurisdiction='cn',
            application_no=f'CN2024CP{hashlib.md5(work.id.encode()).hexdigest()[:8].upper()}',
            status='registered',
            registration_date=date(2024, 1, 15),
            expiration_date=date(2034, 1, 15),
            official_fee=300.0,
            total_cost=500.0,
            agent_name='测试代理机构',
            agent_fee=200.0,
            lawyer_consulted='A',
            disclaimer_accepted_at=datetime.now(timezone.utc),
        )
        db.add(ipr)
        print(f'  [OK] Created IPR for work: {work.title}')

    db.commit()

def seed_monitor(db, works):
    """Create test monitoring results."""
    print("\n=== Creating monitor results ===")
    monitors = []
    for i, work in enumerate(works[:2]):
        task_id = hashlib.md5(f'task_{work.id}_{i}'.encode()).hexdigest()[:32]
        task = MonitorTask(
            id=task_id,
            work_id=work.id,
            search_type='image',
            platform='google',
            status='active',
        )
        db.add(task)

        existing = db.query(MonitorResult).filter(MonitorResult.task_id == task_id).first()
        if existing:
            print(f'  [SKIP] Monitor result for work "{work.title}" already exists')
            monitors.append(existing)
            continue

        monitor = MonitorResult(
            id=hashlib.md5(f'monitor_{work.id}_{i}'.encode()).hexdigest()[:32],
            task_id=task_id,
            matched_url=f'https://example.com/infringement/{hashlib.md5(work.id.encode()).hexdigest()[:8]}',
            matched_title='Infringing Content',
            similarity=95.0,
            status='infringing',
            action_taken='generate_complaint',
            match_type='image_similarity',
            confidence=90.0,
            is_mock=1,
        )
        db.add(monitor)
        monitors.append(monitor)
        print(f'  [OK] Created monitor result for work: {work.title}')

    db.commit()
    return monitors

def seed_enforcement(db, monitors):
    """Create test enforcement actions."""
    print("\n=== Creating enforcement actions ===")
    for monitor in monitors[:2]:
        existing = db.query(EnforcementAction).filter(
            EnforcementAction.monitor_result_id == monitor.id
        ).first()
        if existing:
            print(f'  [SKIP] Enforcement for monitor "{monitor.id}" already exists')
            continue

        action = EnforcementAction(
            id=hashlib.md5(f'enforce_{monitor.id}'.encode()).hexdigest()[:32],
            monitor_result_id=monitor.id,
            action_type='platform_complaint',
            platform='taobao',
            status='evidence_gathered',
            complaint_text='侵权投诉：该作品未经授权使用，请求下架。',
            template_used='taobao_copyright',
            notes='已收集侵权证据，等待平台处理',
        )
        db.add(action)
        print(f'  [OK] Created enforcement action for monitor: {monitor.id}')

    db.commit()

def seed_supply(db):
    """Create test supply chain data."""
    print("\n=== Creating supply chain data ===")

    # Create partners
    partners = []
    partner_data = [
        ('测试工厂 A', 'manufacturer', 'Beijing'),
        ('测试供应商 B', 'supplier', 'Shanghai'),
        ('测试 POD 平台 C', 'pod_platform', 'Guangzhou'),
    ]

    for name, ptype, city in partner_data:
        existing = db.query(Partner).filter(Partner.name == name).first()
        if existing:
            print(f'  [SKIP] Partner "{name}" already exists')
            partners.append(existing)
            continue

        partner = Partner(
            id=hashlib.md5(f'partner_{name}'.encode()).hexdigest()[:32],
            name=name,
            company_name=f'{name}有限公司',
            type=ptype,
            contact_person='测试联系人',
            phone='13800138000',
            email=f'{name.lower()}@test.com',
            address=f'{city}测试地址',
            rating=5,
            status='active',
        )
        db.add(partner)
        partners.append(partner)
        print(f'  [OK] Created partner: {name}')

    # Create orders
    for i, partner in enumerate(partners[:2]):
        existing = db.query(Order).filter(Order.partner_id == partner.id).first()
        if existing:
            print(f'  [SKIP] Order for partner "{partner.name}" already exists')
            continue

        order = Order(
            id=hashlib.md5(f'order_{partner.id}'.encode()).hexdigest()[:32],
            order_number=f'ORD2024{i+1:03d}',
            partner_id=partner.id,
            order_type='custom_mfg',
            product_name=f'测试产品 {i+1}',
            product_category='t_shirt',
            status='in_production',
            total_amount=1500.0,
            notes='测试订单',
        )
        db.add(order)
        print(f'  [OK] Created order: {order.order_number}')

    db.commit()
    return partners

def seed_matchmaking(db, creator_user):
    """Create test matchmaking data."""
    print("\n=== Creating matchmaking data ===")

    trader_email = 'trader@test.oristudio.com'
    trader = db.query(User).filter(User.email == trader_email).first()
    if not trader:
        print('  [WARN] Trader user not found, skipping matchmaking')
        return

    for i in range(2):
        existing = db.query(MatchRequest).filter(
            MatchRequest.buyer_id == trader.id,
        ).first()
        if existing:
            print(f'  [SKIP] Match request {i+1} already exists')
            continue

        match = MatchRequest(
            id=hashlib.md5(f'match_{trader.id}_{i}'.encode()).hexdigest()[:32],
            buyer_id=trader.id,
            title=f'测试采购需求 {i+1}',
            description='需要创作类内容',
            category='illustration',
            status='pending',
            budget_min_yuan=1000.0,
            budget_max_yuan=5000.0,
            notes='测试商业撮合数据',
        )
        db.add(match)
        print(f'  [OK] Created matchmaking request {i+1}')

    db.commit()

def seed_contracts(db, creator_user, trader_user):
    """Create test contract data."""
    print("\n=== Creating contract data ===")

    for i in range(2):
        existing = db.query(ContractInstance).filter(
            ContractInstance.contract_number == f'CT2024{i+1:03d}'
        ).first()
        if existing:
            print(f'  [SKIP] Contract CT2024{i+1:03d} already exists')
            continue

        contract = ContractInstance(
            id=hashlib.md5(f'contract_{i}'.encode()).hexdigest()[:32],
            contract_number=f'CT2024{i+1:03d}',
            title=f'测试授权合同 {i+1}',
            contract_type='non_exclusive_license',
            status='draft',
            creator_id=creator_user.id,
            trader_id=trader_user.id if trader_user else None,
            total_amount=10000.0,
            currency='CNY',
            billing_cycle='monthly',
            scope_usage='commercial',
            scope_geography='china',
            scope_duration='1year',
            split_rules_json='[{"role": "creator", "percentage": 0.7}, {"role": "operator", "percentage": 0.3}]',
            verified='pending',
            notes='测试合约市场数据',
        )
        db.add(contract)
        print(f'  [OK] Created contract: CT2024{i+1:03d}')

    db.commit()

def main():
    db = SessionLocal()
    try:
        # Create users
        users = seed_users(db)

        # Get creator user
        creator = users.get('creator')
        if not creator:
            print('Error: Creator user not found')
            return

        # Create works
        works = seed_works(db, creator)

        # Create IPR registrations
        seed_ipr(db, works)

        # Create monitor results
        monitors = seed_monitor(db, works)

        # Create enforcement actions
        seed_enforcement(db, monitors)

        # Create supply chain data
        partners = seed_supply(db)

        # Create matchmaking data
        trader = users.get('trader')
        seed_matchmaking(db, creator)

        # Create contract data
        seed_contracts(db, creator, trader)

        print("\n" + "="*50)
        print("✅ All test data seeded successfully!")
        print("="*50)
        print("\nTest accounts (email / password):")
        for role_key, role_name, _ in ROLES:
            email = f'{role_key}@test.oristudio.com'
            print(f'  {role_name} ({role_key}): {email} / Test1234!')

    except Exception as e:
        db.rollback()
        print(f'\n❌ Error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    main()
