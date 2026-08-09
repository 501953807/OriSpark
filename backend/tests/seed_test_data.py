"""端到端测试数据种子脚本.

模拟9种参与角色和6种创作者类型的完整业务链:
- 创作者注册 -> 上传作品 -> 挂牌/竞价 -> 合约签署 -> 维权监测
- 每个角色不少于5条业务记录
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
import uuid

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import event

from app.database import Base
from app.models.system import User
from app.models.work import Work
from app.models.listing import Listing
from app.models.matching_engine import AuctionRecord, Bid, LicensingMatch
from app.models.contract import ContractInstance, SplitRule
from app.models.enforcement import EnforcementAction, EnforcementTemplate
from app.models.monitor import MonitorTask, MonitorResult, EvidencePackage
from app.models.certification import CertificationRecord
from app.models.innocence_proof import InnocenceProof
from app.models.ip_commercialization import IPAsset, IPEvaluationStage
from app.models.insurance import InsuranceProvider, InsuranceProduct, InsurancePolicy
from app.models.credit import CreditRating, CreditBehavior
from app.models.fork_merge import ForkMergeWork, ForkMergeBranch
from app.models.achievement import LeaderboardEntry
from app.models.content_pipeline import MultiPlatformSchedule
from app.models.growth_stage import CreatorGrowthStage
from app.models.notary import NotaryRecord


def make_test_engine():
    """创建测试用内存引擎."""
    from pathlib import Path
    db_path = Path(__file__).parent.parent / "data" / "oristudio.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _pragma(dbapi_conn, record):
        c = dbapi_conn.cursor()
        c.execute("PRAGMA foreign_keys=ON")
        c.close()

    return engine


def gen_id():
    return uuid.uuid4().hex[:16]


def now():
    return datetime.now(timezone.utc)


def future(days=30):
    return now() + timedelta(days=days)


def past(days=30):
    return now() - timedelta(days=days)


def seed_users(db):
    """创建9种参与角色的用户, 每种5个."""
    roles = {
        "creator": "创作者",
        "operator": "运营方",
        "legal_rep": "法务代表",
        "tax_agent": "税务代理",
        "logistics": "物流方",
        "insurer": "保险方",
        "trader": "采购方",
        "payment_provider": "支付托管方",
        "platform": "平台方",
    }

    users = []
    for role, label in roles.items():
        for i in range(5):
            uid = gen_id()
            user = User(
                id=uid,
                username=f"{label}_{i+1}",
                email=f"{label}_{i+1}@test.ori.spark",
                role="user",
                status="active",
                participant_roles=[role],
                bio=f"测试用户: {label}角色#{i+1}",
            )
            db.add(user)
            users.append((uid, user))

    db.flush()
    print(f"  创建 {len(users)} 个用户 (9角色 x 5)")
    return users


def seed_works(db, users):
    """为6种创作者类型创建作品, 每种5个."""
    creator_types = {
        "illustrator": "插画师",
        "photographer": "摄影师",
        "video_creator": "视频创作者",
        "crafter": "手工艺人",
        "musician": "音乐人",
        "writer": "写作者",
    }

    file_types = {
        "illustrator": ("image", "png"),
        "photographer": ("image", "jpg"),
        "video_creator": ("video", "mp4"),
        "crafter": ("image", "jpg"),
        "musician": ("audio", "mp3"),
        "writer": ("document", "pdf"),
    }

    works = []
    creator_users = [u for u in users if "creator" in u[1].participant_roles]

    for ct, label in creator_types.items():
        for i in range(5):
            wuid = gen_id()
            ft, ext = file_types[ct]
            creator = creator_users[i % len(creator_users)]

            work = Work(
                id=wuid,
                title=f"{label}作品 #{i+1}",
                file_path=f"/data/{ct}/work_{i+1}.{ext}",
                file_name=f"work_{i+1}.{ext}",
                file_size=1024 * 1024 * (i + 1),
                file_type=ft,
                file_extension=ext,
                mime_type=f"image/{ext}" if ft == "image" else f"video/{ext}",
                sha256=uuid.uuid4().hex[:64],
                thumbnail_path=f"/thumbnails/{ct}/{wuid}.jpg",
                creator_id=creator[0],
                description=f"这是{label}角色{i+1}的创作作品",
                creator_type=ct,
                status="active",
                is_verified=i % 2 == 0,
            )
            db.add(work)
            works.append((wuid, work, creator))

    db.flush()
    print(f"  创建 {len(works)} 个作品 (6创作者类型 x 5)")
    return works


def seed_certifications(db, works):
    """为已验证作品创建区块链存证."""
    certified = [w for w in works if w[1].is_verified]
    count = 0

    for wuid, work, creator in certified[:10]:
        cert = CertificationRecord(
            id=gen_id(),
            work_id=wuid,
            sha256_hash=work.sha256,
            blockchain_tx_id=uuid.uuid4().hex[:32],
            block_height=1000 + count,
            is_court_admissible=True,
            certificate_url=f"https://cert.ori.spark/{wuid}",
            cost_saved_yuan=500,
        )
        db.add(cert)
        count += 1

    print(f"  创建 {count} 个区块链存证")


def seed_innocence_proofs(db, works):
    """创建清白证明."""
    count = 0
    for wuid, work, creator in works[:8]:
        proof = InnocenceProof(
            id=gen_id(),
            work_id=wuid,
            evidence_document_url=f"https://evidence.ori.spark/{wuid}.pdf",
            summary_text=f"作品{work.title}创作过程完整存证, 时间戳: {past(30).isoformat()}",
            status="completed" if count % 3 != 0 else "pending",
        )
        db.add(proof)
        count += 1

    print(f"  创建 {count} 个清白证明")


def seed_listings(db, works, users):
    """创建挂牌记录."""
    operator_users = [u for u in users if "operator" in u[1].participant_roles]
    listings = []

    for wuid, work, creator in works[:15]:
        op = operator_users[0]
        listing = Listing(
            id=gen_id(),
            work_id=wuid,
            seller_id=creator[0],
            title=f"{work.title} 授权挂牌",
            description=f"授权{work.creator_type}作品用于商业用途",
            asking_price_yuan=5000 + len(listings) * 500,
            original_cost_yuan=1000,
            min_price_yuan=3000,
            quantity_total=10,
            status="active",
            profit_split_percent=70.0,
            platform_fee_rate_bps=200,
            tags=[work.creator_type, "授权", "商业"],
        )
        db.add(listing)
        listings.append(listing)

    db.flush()
    print(f"  创建 {len(listings)} 个挂牌记录")
    return listings


def seed_auctions(db, listings, works, users):
    """创建竞价记录."""
    trader_users = [u for u in users if "trader" in u[1].participant_roles]
    auctions = []

    for listing in listings[:10]:
        auction = AuctionRecord(
            id=gen_id(),
            listing_id=listing.id,
            work_id=listing.work_id,
            seller_id=listing.seller_id,
            title=f"{listing.title} 竞价",
            starting_price_yuan=listing.asking_price_yuan * 0.8,
            current_bid_yuan=listing.asking_price_yuan * 0.85,
            bid_count=0,
            min_increment_yuan=100,
            ends_at=future(7),
            status="active",
        )
        db.add(auction)
        auctions.append(auction)

    # 创建出价
    bids = []
    for auction in auctions[:8]:
        for j in range(3):
            trader = trader_users[j % len(trader_users)]
            bid = Bid(
                id=gen_id(),
                auction_id=auction.id,
                buyer_id=trader[0],
                amount_yuan=auction.current_bid_yuan + (j + 1) * 200,
                status="open",
                notes=f"测试出价 #{j+1}",
            )
            db.add(bid)
            bids.append(bid)
            auction.bid_count += 1
            auction.current_bid_yuan = bid.amount_yuan

    db.flush()
    print(f"  创建 {len(auctions)} 个竞价记录, {len(bids)} 个出价")
    return auctions, bids


def seed_licensing_matches(db, works, users):
    """创建授权撮合."""
    trader_users = [u for u in users if "trader" in u[1].participant_roles]
    matches = []

    for i, (wuid, work, creator) in enumerate(works[:8]):
        trader = trader_users[i % len(trader_users)]
        match = LicensingMatch(
            id=gen_id(),
            work_id=wuid,
            seller_id=creator[0],
            buyer_id=trader[0],
            license_type="exclusive",
            usage_scope="商业广告使用",
            territory="china",
            duration_days=365,
            price_per_use_cents=50000,
            minimum_guarantee_yuan=10000,
            royalty_percent=15.0,
            status="pending" if i % 3 != 0 else "agreed",
            notes="测试授权撮合",
        )
        db.add(match)
        matches.append(match)

    db.flush()
    print(f"  创建 {len(matches)} 个授权撮合")
    return matches


def seed_contracts(db, works, listings, users):
    """创建合约实例."""
    contract_types = [
        "copyright_transfer",
        "product_license",
        "exclusive_license",
        "non_exclusive_license",
    ]

    operator_users = [u for u in users if "operator" in u[1].participant_roles]
    trader_users = [u for u in users if "trader" in u[1].participant_roles]

    contracts = []
    for i, (wuid, work, creator) in enumerate(works[:12]):
        op = operator_users[0]
        trader = trader_users[i % len(trader_users)]
        ct = contract_types[i % len(contract_types)]

        contract = ContractInstance(
            id=gen_id(),
            title=f"{work.title} 商业合约",
            description=f"{ct}合约 - {work.description}",
            work_id=wuid,
            contract_type=ct,
            total_amount=50000 + i * 10000,
            currency="CNY",
            billing_cycle="one_time",
            scope_usage="commercial",
            scope_geography="china",
            scope_duration="1year",
            status="draft" if i % 4 != 0 else "active",
            verified="approved" if i % 3 == 0 else "pending",
            creator_id=creator[0],
            operator_id=op[0],
            trader_id=trader[0],
            split_rules_json='[{"role":"creator","percentage":0.7},{"role":"operator","percentage":0.15},{"role":"platform","percentage":0.05},{"role":"legal_rep","percentage":0.05},{"role":"tax_agent","percentage":0.05}]',
        )
        db.add(contract)
        contracts.append(contract)

        # 创建分润规则
        for j, role in enumerate(["creator", "operator", "platform", "legal_rep", "tax_agent"]):
            split = SplitRule(
                id=gen_id(),
                contract_id=contract.id,
                participant_id=[creator[0], op[0], trader[0], creator[0], op[0]][j],
                role=role,
                percentage=[0.7, 0.15, 0.05, 0.05, 0.05][j],
                quote_amount=contract.total_amount * [0.7, 0.15, 0.05, 0.05, 0.05][j],
                quoted_at=now(),
                locked_at=now() if contract.status == "active" else None,
            )
            db.add(split)

    db.flush()
    print(f"  创建 {len(contracts)} 个合约实例")
    return contracts


def seed_enforcement(db, works, users, results):
    """创建维权行动."""
    legal_users = [u for u in users if "legal_rep" in u[1].participant_roles]
    actions = []

    templates = [
        ("platform_complaint", "taobao"),
        ("dmca_notice", "generic"),
        ("lawyer_letter", "generic"),
        ("platform_complaint", "xiaohongshu"),
        ("platform_complaint", "instagram"),
    ]

    for i, (wuid, work, creator) in enumerate(works[:10]):
        legal = legal_users[i % len(legal_users)]
        atype, platform = templates[i % len(templates)]

        # 使用实际存在的monitor_result_id
        monitor_result_id = results[i * 3].id if i * 3 < len(results) else gen_id()

        action = EnforcementAction(
            id=gen_id(),
            monitor_result_id=monitor_result_id,
            action_type=atype,
            platform=platform,
            status=["pending_review", "confirmed", "evidence_gathered", "resolved"][i % 4],
            complaint_text=f"发现侵权内容: {work.title} 被未经授权使用",
            template_used=f"{atype}_template",
            resolution_type=["takedown", "settlement", "dismissed"][i % 3] if i % 4 == 3 else None,
            compensation_amount=5000 if i % 4 == 3 else None,
            operator_id=legal[0],
        )
        db.add(action)
        actions.append(action)

    db.flush()
    print(f"  创建 {len(actions)} 个维权行动")
    return actions


def seed_monitoring(db, works):
    """创建监测任务和结果."""
    tasks = []
    results = []

    for i, (wuid, work, creator) in enumerate(works[:10]):
        task = MonitorTask(
            id=gen_id(),
            work_id=wuid,
            search_type="image" if work.file_type == "image" else "text",
            platform=["baidu", "google", "xiaohongshu", "github"][i % 4],
            interval=["daily", "weekly", "manual"][i % 3],
            status="active" if i % 3 != 2 else "paused",
            priority_score=50 + i * 5,
        )
        db.add(task)
        tasks.append(task)

        # 创建监测结果
        for j in range(3):
            result = MonitorResult(
                id=gen_id(),
                task_id=task.id,
                matched_url=f"https://example.com/infringement/{i}_{j}.html",
                matched_title=f"侵权内容 {j+1}",
                similarity=60 + j * 15,
                status=["pending_review", "infringing", "ignored"][j],
                match_type="image_similarity",
                confidence=70 + j * 10,
            )
            db.add(result)
            results.append(result)

    db.flush()
    print(f"  创建 {len(tasks)} 个监测任务, {len(results)} 个监测结果")
    return tasks, results


def seed_evidence_packages(db, works):
    """创建维权证据包."""
    packages = []

    for i, (wuid, work, creator) in enumerate(works[:6]):
        pkg = EvidencePackage(
            id=gen_id(),
            work_id=wuid,
            related_result_ids=[gen_id() for _ in range(3)],
            package_path=f"/evidence/pkg_{i+1}.zip",
            notes=f"证据包 #{i+1}",
        )
        db.add(pkg)
        packages.append(pkg)

    print(f"  创建 {len(packages)} 个证据包")


def seed_ip_assets(db, works):
    """创建IP资产."""
    assets = []

    for i, (wuid, work, creator) in enumerate(works[:8]):
        asset = IPAsset(
            id=gen_id(),
            work_id=wuid,
            ip_name=f"{work.title} IP",
            originality_score=80 + i * 2,
            market_demand_score=70 + i * 3,
            competition_density=30 + i * 5,
            monetization_potential=85 + i * 2,
            overall_score=(
                80 + i * 2 + 70 + i * 3 + 30 + i * 5 + 85 + i * 2
            ) / 4,
            current_stage=[
                IPEvaluationStage.ASSESSMENT,
                IPEvaluationStage.CONCEPT,
                IPEvaluationStage.PROTOTYPE,
                IPEvaluationStage.SUPPLY_LOCK,
            ][i % 4],
            derivative_products=["周边", "授权", "影视"][i % 3],
            pod_platforms=["printful", "redbubble"],
            mgr_floor_price=10000 + i * 5000,
            brand_premium_estimate=20 + i * 5,
            trademark_classes=["9", "25", "41"][i % 3],
        )
        db.add(asset)
        assets.append(asset)

    db.flush()
    print(f"  创建 {len(assets)} 个IP资产")
    return assets


def seed_achievements(db, works, users):
    """创建成就排行榜."""
    creator_types = ["illustrator", "photographer", "video_creator", "crafter", "musician", "writer"]
    creator_users = [u for u in users if "creator" in u[1].participant_roles]

    entries = []
    for ct in creator_types:
        for i, user in enumerate(creator_users[:5]):
            entry = LeaderboardEntry(
                id=gen_id(),
                user_id=user[0],
                creator_type=ct,
                period="monthly",
                rank_position=i + 1,
                score=1000 - i * 100,
            )
            db.add(entry)
            entries.append(entry)

    db.flush()
    print(f"  创建 {len(entries)} 个成就记录")


def seed_credits(db, users):
    """创建信用记录."""
    for user in users:
        rating = CreditRating(
            id=gen_id(),
            user_id=user[0],
            user_type="creator" if "creator" in user[1].participant_roles else "merchant",
            total_score=100,
            tier="good",
            notes="测试信用评分",
        )
        db.add(rating)

    db.flush()  # 先刷新所有 rating

    for user in users:
        rating = db.query(CreditRating).filter_by(user_id=user[0]).first()
        if not rating:
            continue
        for i in range(5):
            behavior = CreditBehavior(
                id=gen_id(),
                rating_id=rating.id,
                user_id=user[0],
                behavior_type="transaction_completed" if i % 2 == 0 else "contract_signed",
                score_delta=5 if i % 2 == 0 else 3,
                description=f"测试信用行为 #{i+1}",
            )
            db.add(behavior)

    db.flush()
    ratings_count = db.query(CreditRating).count()
    behaviors_count = db.query(CreditBehavior).count()
    print(f"  创建 {ratings_count} 个信用评分, {behaviors_count} 个行为记录")


def seed_fork_merge(db, works, users):
    """创建Fork/Merge记录."""
    from app.models.fork_merge import ForkMergeWork, ForkMergeBranch, ForkMergeCommit
    creator_users = [u for u in users if "creator" in u[1].participant_roles]
    forks = []
    commits = []
    branches = []

    for i, (wuid, work, creator) in enumerate(works[:6]):
        owner = creator_users[i % len(creator_users)]
        fork = ForkMergeWork(
            id=gen_id(),
            original_work_id=wuid,
            title=f"协同仓库: {work.title}",
            description=f"Fork作品 #{i+1}",
            owner_id=owner[0],
            status="active",
        )
        db.add(fork)
        forks.append((fork, owner[0]))

    db.flush()

    for fork_obj, owner_id in forks:
        commit = ForkMergeCommit(
            id=gen_id(),
            work_id=fork_obj.id,
            author_id=owner_id,
            message=f"初始提交: {fork_obj.title}",
        )
        db.add(commit)
        commits.append(commit)

    db.flush()  # 先提交commits

    for (fork_obj, _), commit in zip(forks, commits):
        branch = ForkMergeBranch(
            id=gen_id(),
            work_id=fork_obj.id,
            name="main",
            commit_id=commit.id,
            is_default=True,
        )
        db.add(branch)
        branches.append(branch)

    db.flush()
    print(f"  创建 {len(forks)} 个Fork仓库, {len(commits)} 个提交, {len(branches)} 个分支")


def seed_content_pipelines(db, works, users):
    """创建内容流水线."""
    creator_users = [u for u in users if "creator" in u[1].participant_roles]
    pipelines = []

    for i, (wuid, work, creator) in enumerate(works[:5]):
        owner = creator_users[i % len(creator_users)]
        schedule = MultiPlatformSchedule(
            id=gen_id(),
            user_id=owner[0],
            work_id=wuid,
            title=f"内容分发: {work.title}",
            platforms=[{"platform": "xiaohongshu", "status": "scheduled"}],
            scheduled_at=future(1),
            is_recurring=False,
            status="scheduled",
        )
        db.add(schedule)
        pipelines.append(schedule)

    print(f"  创建 {len(pipelines)} 个内容流水线")


def seed_growth_stages(db, works, users):
    """创建成长阶段记录."""
    creator_users = [u for u in users if "creator" in u[1].participant_roles]
    stages = []

    for i, (wuid, work, creator) in enumerate(works[:6]):
        owner = creator_users[i % len(creator_users)]
        stage = CreatorGrowthStage(
            id=gen_id(),
            user_id=owner[0],
            stage_key=["beginner", "growing", "scaling", "ecosystem"][i % 4],
            stage_name_zh=["新手", "成长", "规模化", "生态"][i % 4],
            monthly_revenue_yuan=1000 + i * 500,
            total_works=5 + i,
            total_certificates=2 + i % 3,
            credit_score=80 + i * 5,
            overall_progress_percent=60 + i * 10,
        )
        db.add(stage)
        stages.append(stage)

    print(f"  创建 {len(stages)} 个成长阶段记录")


def seed_insurance(db, users):
    """创建保险保单."""
    insurer_users = [u for u in users if "insurer" in u[1].participant_roles]

    # 创建保险公司
    providers = []
    for i in range(3):
        provider = InsuranceProvider(
            id=gen_id(),
            name_zh=f"测试保险公司 {i+1}",
            is_active=True,
        )
        db.add(provider)
        providers.append(provider)

    db.flush()  # 先提交providers

    # 创建保险产品
    products = []
    categories = ["版权侵权", "深度伪造", "作品被盗", "风格抄袭", "其他"]
    tiers = ["basic", "advanced", "pro"]
    for i, cat in enumerate(categories):
        for tier in tiers:
            product = InsuranceProduct(
                id=gen_id(),
                product_key=f"{cat}_{tier}",
                provider_id=providers[i % len(providers)].id,
                category=cat,
                tier=tier,
                name_zh=f"{cat}-{tier}",
                annual_min_yuan=500 if tier == "basic" else (2000 if tier == "advanced" else 5000),
                annual_max_yuan=5000 if tier == "basic" else (20000 if tier == "advanced" else 50000),
                is_active=True,
            )
            db.add(product)
            products.append(product)

    db.flush()  # 先提交products

    # 创建保单
    policies = []
    for i, user in enumerate(users[:10]):
        product = products[i % len(products)]
        policy = InsurancePolicy(
            id=gen_id(),
            user_id=user[0],
            product_id=product.id,
            provider_id=product.provider_id,
            policy_number=f"POL-{i+1:04d}",
            status="active" if i % 3 != 0 else "pending",
            annual_premium_yuan=product.annual_min_yuan + i * 100,
            start_date=datetime.now(timezone.utc).date(),
            end_date=(datetime.now(timezone.utc) + timedelta(days=365)).date(),
        )
        db.add(policy)
        policies.append(policy)

    db.flush()
    print(f"  创建 {len(providers)} 个保险公司, {len(products)} 个产品, {len(policies)} 个保单")


def seed_notary_records(db, works):
    """创建公证记录."""
    records = []

    for i, (wuid, work, creator) in enumerate(works[:4]):
        record = NotaryRecord(
            id=gen_id(),
            work_id=wuid,
            notary_office="北京市公证处",
            certificate_no=f"京公证字第{i+1:04d}号",
            status="completed",
            fee_yuan=200 + i * 100,
        )
        db.add(record)
        records.append(record)

    print(f"  创建 {len(records)} 个公证记录")


def main():
    engine = make_test_engine()
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # 清空现有数据
    db.query(EnforcementAction).delete()
    db.query(MonitorResult).delete()
    db.query(MonitorTask).delete()
    db.query(SplitRule).delete()
    db.query(ContractInstance).delete()
    db.query(LicensingMatch).delete()
    db.query(Bid).delete()
    db.query(AuctionRecord).delete()
    db.query(Listing).delete()
    db.query(InnocenceProof).delete()
    db.query(CertificationRecord).delete()
    db.query(Work).delete()
    db.query(User).delete()
    db.commit()

    print("=== 开始种子数据生成 ===\n")

    print("1. 创建用户...")
    users = seed_users(db)

    print("2. 创建作品...")
    works = seed_works(db, users)

    print("3. 创建区块链存证...")
    seed_certifications(db, works)

    print("4. 创建清白证明...")
    seed_innocence_proofs(db, works)

    print("5. 创建挂牌记录...")
    listings = seed_listings(db, works, users)

    print("6. 创建竞价...")
    auctions, bids = seed_auctions(db, listings, works, users)

    print("7. 创建授权撮合...")
    matches = seed_licensing_matches(db, works, users)

    print("8. 创建合约...")
    contracts = seed_contracts(db, works, listings, users)

    print("9. 创建监测...")
    tasks, results = seed_monitoring(db, works)

    print("10. 创建维权行动...")
    actions = seed_enforcement(db, works, users, results)

    print("11. 创建证据包...")
    seed_evidence_packages(db, works)

    print("12. 创建IP资产...")
    assets = seed_ip_assets(db, works)

    print("13. 创建成就记录...")
    seed_achievements(db, works, users)

    print("  创建信用记录...")
    seed_credits(db, users)

    print("  创建Fork/Merge...")
    seed_fork_merge(db, works, users)

    print("  创建内容流水线...")
    seed_content_pipelines(db, works, users)

    print("  创建成长阶段...")
    seed_growth_stages(db, works, users)

    print("  创建保险...")
    seed_insurance(db, users)

    db.commit()
    print("\n=== 种子数据生成完成 ===")

    # 统计
    print("\n数据统计:")
    print(f"  用户: {db.query(User).count()}")
    print(f"  作品: {db.query(Work).count()}")
    print(f"  挂牌: {db.query(Listing).count()}")
    print(f"  竞价: {db.query(AuctionRecord).count()}")
    print(f"  出价: {db.query(Bid).count()}")
    print(f"  撮合: {db.query(LicensingMatch).count()}")
    print(f"  合约: {db.query(ContractInstance).count()}")
    print(f"  分润: {db.query(SplitRule).count()}")
    print(f"  维权: {db.query(EnforcementAction).count()}")
    print(f"  监测任务: {db.query(MonitorTask).count()}")
    print(f"  监测结果: {db.query(MonitorResult).count()}")
    print(f"  存证: {db.query(CertificationRecord).count()}")
    print(f"  清白证明: {db.query(InnocenceProof).count()}")
    print(f"  IP资产: {db.query(IPAsset).count()}")
    print(f"  成就: {db.query(LeaderboardEntry).count()}")
    print(f"  信用: {db.query(CreditRating).count()}")
    print(f"  保险: {db.query(InsurancePolicy).count()}")


if __name__ == "__main__":
    main()
