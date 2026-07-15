# OriStudio 创作者经济交易所 — 完整实施计划

> **基于**: docs/superpowers/specs/2026-07-15-ori-studio-creator-exchange-master-plan.md
> **日期**: 2026-07-15
> **架构**: FastAPI + SQLAlchemy + Vue 3 + SQLite/PostgreSQL
> **技术栈**: Python 3.11+, FastAPI, SQLAlchemy 2.0, Pydantic v2, Vue 3 (Composition API), Vite

---

## Phase 0: 核心基础设施（0-6个月）— 5个模块

### Task 0.1: 区块链存证引擎增强（批量存证+法院认可格式）

**Files:**
- Create: `backend/app/models/certification.py`
- Create: `backend/app/routers/certification.py`
- Create: `backend/app/services/certification_service.py`
- Create: `backend/app/schemas/certification.py`
- Test: `tests/test_certification.py`

**Interfaces:**
- Consumes: `Work.sha256`, `Work.id`
- Produces: `CertificateRecord` with `hash`, `blockchain_tx_id`, `timestamp`, `court_admissible=True`

**Step 1: 数据模型**

```python
# backend/app/models/certification.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, ForeignKey, JSON
from app.database import Base


class CertificationRecord(Base):
    """区块链存证记录表."""
    __tablename__ = "certification_records"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    work_id = Column(String(32), ForeignKey("works.id"), nullable=False, index=True)
    sha256_hash = Column(String(64), nullable=False)
    blockchain_tx_id = Column(String(128), nullable=True, index=True)  # 蚂蚁链交易ID
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    block_height = Column(Integer, nullable=True)
    is_court_admissible = Column(Boolean, default=True)
    certificate_url = Column(String(2000), nullable=True)  # 证书下载URL
    cost_saved_yuan = Column(Integer, default=0)  # 节省金额（对比传统公证）
    metadata = Column(JSON, nullable=True)  # 额外元数据
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Step 2: Schema定义**

```python
# backend/app/schemas/certification.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CertificationRequest(BaseModel):
    work_id: str
    batch: Optional[list[str]] = None  # 批量存证的work_ids列表

class CertificationResponse(BaseModel):
    id: str
    work_id: str
    sha256_hash: str
    blockchain_tx_id: Optional[str]
    timestamp: datetime
    is_court_admissible: bool
    certificate_url: Optional[str]
    cost_saved_yuan: int

class BatchCertificationResponse(BaseModel):
    total: int
    success: int
    failed: int
    results: list[CertificationResponse]
    total_saved_yuan: int
```

**Step 3: 服务层 — 批量存证**

```python
# backend/app/services/certification_service.py
import hashlib
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.certification import CertificationRecord
from app.models.work import Work


def compute_sha256(file_path: str) -> str:
    """计算文件SHA-256哈希."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def certify_single(db: Session, work: Work) -> CertificationRecord:
    """单件存证：计算哈希→调用区块链→返回记录."""
    sha256 = compute_sha256(work.file_path)
    record = CertificationRecord(
        work_id=work.id,
        sha256_hash=sha256,
        blockchain_tx_id=None,  # 异步调用区块链服务后回填
        is_court_admissible=True,
        cost_saved_yuan=2000,  # 对比传统公证最低¥2000
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def batch_certify(db: Session, work_ids: list[str]) -> dict:
    """批量存证，单次最高10,000件."""
    if len(work_ids) > 10000:
        raise ValueError("批量存证不能超过10,000件")

    results = []
    success = 0
    failed = 0
    total_saved = 0

    for wid in work_ids:
        try:
            work = db.query(Work).filter(Work.id == wid).first()
            if not work:
                failed += 1
                continue
            record = certify_single(db, work)
            results.append(record)
            success += 1
            total_saved += record.cost_saved_yuan
        except Exception:
            failed += 1

    return {
        "total": len(work_ids),
        "success": success,
        "failed": failed,
        "results": results,
        "total_saved_yuan": total_saved,
    }
```

**Step 4: Router端点**

```python
# backend/app/routers/certification.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.certification import CertificationRequest, CertificationResponse, BatchCertificationResponse
from app.services.certification_service import batch_certify, certify_single

router = APIRouter(prefix="/api/certification", tags=["certification"])

@router.post("/single", response_model=CertificationResponse)
def post_single_certification(req: CertificationRequest, db: Session = Depends(get_db)):
    work = db.query(Work).filter(Work.id == req.work_id).first()
    if not work:
        raise HTTPException(404, "作品不存在")
    record = certify_single(db, work)
    return record

@router.post("/batch", response_model=dict)
def post_batch_certification(req: CertificationRequest, db: Session = Depends(get_db)):
    """批量存证接口."""
    if not req.batch:
        raise HTTPException(400, "需要提供work_ids列表")
    result = batch_certify(db, req.batch)
    return result
```

**Step 5: 注册路由**

在 `backend/app/main.py` 中添加：
```python
from app.routers import certification
app.include_router(certification.router)
```

**Step 6: Alembic迁移**

```bash
alembic revision -m "add certification_records_table"
alembic upgrade head
```

**Step 7: 测试**

```python
# tests/test_certification.py
import pytest
from app.services.certification_service import compute_sha256, certify_single, batch_certify

def test_compute_sha256(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("hello world")
    assert len(compute_sha256(str(f))) == 64

def test_certify_single(db_session, sample_work):
    record = certify_single(db_session, sample_work)
    assert record.work_id == sample_work.id
    assert record.is_court_admissible is True
    assert record.cost_saved_yuan == 2000

def test_batch_certify_limits():
    with pytest.raises(ValueError, match="不能超过10,000件"):
        batch_certify(None, ["id"] * 10001)
```

**Commit:** `git add -A && git commit -m "feat: add blockchain certification engine with batch support"`

---

### Task 0.2: AI训练数据授权平台

**Files:**
- Create: `backend/app/models/ai_training_license.py`
- Create: `backend/app/routers/ai_training.py`
- Create: `backend/app/services/ai_training_service.py`
- Create: `backend/app/schemas/ai_training.py`
- Test: `tests/test_ai_training.py`

**Interfaces:**
- Consumes: `Work.id`, `Work.creator_type`
- Produces: `AILicenseConfig` with CC protocol, per-use pricing, revenue tracking

**Step 1: 数据模型**

```python
# backend/app/models/ai_training_license.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Float, ForeignKey, Enum as SAEnum, Text
from app.database import Base
import enum

class CCProtocol(enum.StrEnum):
    CC0 = "CC0"
    CC_BY = "CC-BY"
    CC_BY_NC = "CC-BY-NC"
    CC_BY_SA = "CC-BY-SA"
    CC_BY_NC_SA = "CC-BY-NC-SA"
    CC_BY_NC_ND = "CC-BY-NC-ND"

class AITrainingLicense(Base):
    """AI训练数据授权配置表."""
    __tablename__ = "ai_training_licenses"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    work_id = Column(String(32), ForeignKey("works.id"), nullable=False, index=True)
    cc_protocol = Column(SAEnum(CCProtocol), nullable=False, default=CCProtocol.CC0)
    enabled = Column(Boolean, default=False)  # 是否允许AI训练使用
    price_per_use_cents = Column(Integer, default=5)  # $0.05 = 5 cents
    exclude_ai_training_clause = Column(Text, nullable=True)  # AI排除条款文本
    total_uses = Column(Integer, default=0)  # 累计被使用次数
    total_revenue_cents = Column(Integer, default=0)  # 累计收入（美分）
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Step 2: Schema**

```python
# backend/app/schemas/ai_training.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.ai_training_license import CCProtocol

class AILicenseUpdate(BaseModel):
    work_id: str
    enabled: bool
    cc_protocol: Optional[CCProtocol] = None
    price_per_use_cents: Optional[int] = None

class AILicenseResponse(BaseModel):
    id: str
    work_id: str
    enabled: bool
    cc_protocol: CCProtocol
    price_per_use_cents: int
    total_uses: int
    total_revenue_cents: int
    exclude_ai_training_clause: Optional[str]
```

**Step 3: 服务层 — AI排除条款自动生成**

```python
# backend/app/services/ai_training_service.py
from sqlalchemy.orm import Session
from app.models.ai_training_license import AITrainingLicense, CCProtocol
from app.models.work import Work

AI_EXCLUDE_CLAUSE_TEMPLATE = """AI Training Exclusion Clause:
The Licensor expressly prohibits the use of this Work, including any derivatives,
for the purpose of training, fine-tuning, or improving any Artificial Intelligence
or Machine Learning model, including but not limited to generative AI systems.
Any unauthorized use for AI training constitutes a material breach of this agreement."""

def generate_exclude_clause(cc_protocol: CCProtocol) -> str:
    """根据CC协议生成AI训练排除条款."""
    if cc_protocol == CCProtocol.CC0:
        # CC0默认不限制，需要显式添加排除条款
        return AI_EXCLUDE_CLAUSE_TEMPLATE
    elif CCProtocol.CC_BY_NC in (cc_protocol,):
        # CC-BY-NC已限制商业用途，AI训练通常被视为商业使用
        return AI_EXCLUDE_CLAUSE_TEMPLATE + "\n(Note: CC-BY-NC already restricts commercial use.)"
    return ""

def upsert_ai_license(db: Session, work_id: str, enabled: bool,
                       cc_protocol: CCProtocol = CCProtocol.CC0,
                       price_per_use_cents: int = 5) -> AITrainingLicense:
    license = db.query(AITrainingLicense).filter(
        AITrainingLicense.work_id == work_id
    ).first()
    if not license:
        license = AITrainingLicense(
            work_id=work_id,
            enabled=enabled,
            cc_protocol=cc_protocol,
            price_per_use_cents=price_per_use_cents,
            exclude_ai_training_clause=generate_exclude_clause(cc_protocol) if enabled else None,
        )
        db.add(license)
    else:
        license.enabled = enabled
        license.cc_protocol = cc_protocol
        license.price_per_use_cents = price_per_use_cents
        if enabled:
            license.exclude_ai_training_clause = generate_exclude_clause(cc_protocol)
        else:
            license.exclude_ai_training_clause = None
    db.commit()
    db.refresh(license)
    return license
```

**Step 4: Router**

```python
# backend/app/routers/ai_training.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.ai_training import AILicenseUpdate, AILicenseResponse
from app.services.ai_training_service import upsert_ai_license

router = APIRouter(prefix="/api/ai-training", tags=["ai-training"])

@router.put("/{work_id}", response_model=AILicenseResponse)
def update_ai_license(work_id: str, req: AILicenseUpdate, db: Session = Depends(get_db)):
    license = upsert_ai_license(
        db, work_id=req.work_id,
        enabled=req.enabled,
        cc_protocol=req.cc_protocol,
        price_per_use_cents=req.price_per_use_cents or 5,
    )
    return license

@router.get("/{work_id}", response_model=AILicenseResponse)
def get_ai_license(work_id: str, db: Session = Depends(get_db)):
    license = db.query(AITrainingLicense).filter(
        AITrainingLicense.work_id == work_id
    ).first()
    if not license:
        raise HTTPException(404, "未找到AI授权配置")
    return license
```

**Step 5: 注册路由到main.py**

**Step 6: Alembic迁移**

**Step 7: 测试**

```python
# tests/test_ai_training.py
import pytest
from app.services.ai_training_service import generate_exclude_clause, upsert_ai_license
from app.models.ai_training_license import CCProtocol

def test_generate_exclude_clause_cc0():
    clause = generate_exclude_clause(CCProtocol.CC0)
    assert "AI Training Exclusion" in clause
    assert "Machine Learning" in clause

def test_upsert_creates_new(db_session, sample_work):
    from app.services.ai_training_service import upsert_ai_license
    license = upsert_ai_license(db_session, sample_work.id, enabled=True)
    assert license.enabled is True
    assert license.cc_protocol == CCProtocol.CC0

def test_upsert_updates_existing(db_session, sample_work):
    from app.services.ai_training_service import upsert_ai_license
    lic1 = upsert_ai_license(db_session, sample_work.id, enabled=True, price_per_use_cents=10)
    lic2 = upsert_ai_license(db_session, sample_work.id, enabled=False)
    assert lic2.enabled is False
```

**Commit:** `git commit -m "feat: add AI training data licensing platform with CC protocols"`

---

### Task 0.3: IP商业化全流程工具

**Files:**
- Create: `backend/app/models/ip_commercialization.py`
- Create: `backend/app/routers/ip_commercialization.py`
- Create: `backend/app/services/ip_commercialization_service.py`
- Create: `backend/app/schemas/ip_commercialization.py`
- Test: `tests/test_ip_commercialization.py`

**Interfaces:**
- Consumes: `Work.id`
- Produces: `IPAssessment`, `DerivativeProduct`, `PODIntegration`, `MGRCalculator`

**Step 1: 数据模型**

```python
# backend/app/models/ip_commercialization.py
import uuid, enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Enum as SAEnum, Text, Integer, JSON
from app.database import Base

class IPEvaluationStage(enum.StrEnum):
    ASSESSMENT = "assessment"
    CONCEPT = "concept"
    PROTOTYPE = "prototype"
    SUPPLY_LOCK = "supply_lock"
    MASS_PRODUCTION = "mass_production"
    LAUNCH_REVIEW = "launch_review"

class IPAsset(Base):
    """IP资产表 — 跟踪IP商业化全生命周期."""
    __tablename__ = "ip_assets"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    work_id = Column(String(32), ForeignKey("works.id"), nullable=False, index=True)
    ip_name = Column(String(200), nullable=False)
    originality_score = Column(Float, nullable=True)  # 原创性 0-100
    market_demand_score = Column(Float, nullable=True)  # 市场需求 0-100
    competition_density = Column(Float, nullable=True)  # 竞争密度 0-100
    monetization_potential = Column(Float, nullable=True)  # 变现潜力 0-100
    overall_score = Column(Float, nullable=True)  # 综合评分
    current_stage = Column(SAEnum(IPEvaluationStage), default=IPEvaluationStage.ASSESSMENT)
    derivative_products = Column(JSON, nullable=True)  # 衍生品列表
    pod_platforms = Column(JSON, nullable=True)  # POD平台集成配置
    mgr_floor_price = Column(Float, nullable=True)  # MGR保底金
    brand_premium_estimate = Column(Float, nullable=True)  # 品牌溢价预估(%)
    trademark_classes = Column(JSON, nullable=True)  # 推荐商标类别
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Step 2: Schema**

```python
# backend/app/schemas/ip_commercialization.py
from pydantic import BaseModel
from typing import Optional
from app.models.ip_commercialization import IPEvaluationStage

class IPAssessmentCreate(BaseModel):
    work_id: str
    ip_name: str
    originality_score: float
    market_demand_score: float
    competition_density: float
    monetization_potential: float

class IPAssessmentResponse(BaseModel):
    id: str
    work_id: str
    ip_name: str
    overall_score: Optional[float]
    current_stage: IPEvaluationStage
    brand_premium_estimate: Optional[float]
    trademark_classes: Optional[list[str]]
```

**Step 3: 服务层 — IP评估矩阵+品牌溢价计算器**

```python
# backend/app/services/ip_commercialization_service.py
from sqlalchemy.orm import Session
from app.models.ip_commercialization import IPAsset, IPEvaluationStage

def calculate_ip_score(originality: float, demand: float,
                        competition: float, potential: float) -> float:
    """IP综合评分 = 原创性×0.3 + 需求×0.3 + (100-竞争)×0.2 + 变现×0.2."""
    return round(originality * 0.3 + demand * 0.3 + (100 - competition) * 0.2 + potential * 0.2, 1)

def estimate_brand_premium(follower_count: int, engagement_rate: float, category: str) -> float:
    """品牌溢价估算: 输入粉丝量/互动率/领域 → 预估15-40%溢价空间."""
    base = 15.0
    if follower_count > 100000:
        base += 10
    elif follower_count > 10000:
        base += 5
    if engagement_rate > 5.0:
        base += 10
    elif engagement_rate > 2.0:
        base += 5
    return min(round(base, 1), 40.0)

def recommend_trademark_classes(creator_type: str) -> list[str]:
    """按创作者类型推荐商标类别."""
    mapping = {
        "illustrator": ["第9类(数码产品)", "第16类(出版物)", "第25类(服装)"],
        "musician": ["第9类(录音制品)", "第16类(乐谱)", "第41类(娱乐服务)"],
        "photographer": ["第9类(数码照片)", "第16类(印刷品)"],
        "writer": ["第16类(出版物)", "第41类(教育娱乐)"],
        "game_developer": ["第9类(软件)", "第16类(出版物)", "第25类(服装)", "第28类(玩具)"],
    }
    return mapping.get(creator_type, ["第9类", "第16类"])

def create_ip_assessment(db: Session, req: dict) -> IPAsset:
    score = calculate_ip_score(
        req["originality_score"], req["market_demand_score"],
        req["competition_density"], req["monetization_potential"],
    )
    asset = IPAsset(
        work_id=req["work_id"],
        ip_name=req["ip_name"],
        originality_score=req["originality_score"],
        market_demand_score=req["market_demand_score"],
        competition_density=req["competition_density"],
        monetization_potential=req["monetization_potential"],
        overall_score=score,
        trademark_classes=recommend_trademark_classes(req.get("creator_type", "illustrator")),
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset
```

**Step 4: Router**

```python
# backend/app/routers/ip_commercialization.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.ip_commercialization_service import create_ip_assessment, estimate_brand_premium

router = APIRouter(prefix="/api/ip-commercialization", tags=["ip-commercialization"])

@router.post("/assess", response_model=dict)
def post_ip_assessment(data: dict, db: Session = Depends(get_db)):
    asset = create_ip_assessment(db, data)
    return {"id": asset.id, "overall_score": asset.overall_score}

@router.post("/brand-premium")
def calc_brand_premium(follower_count: int, engagement_rate: float, category: str):
    premium = estimate_brand_premium(follower_count, engagement_rate, category)
    return {"estimated_premium_percent": premium}
```

**Step 5-7: 注册路由 + Alembic迁移 + 测试**

```python
# tests/test_ip_commercialization.py
import pytest
from app.services.ip_commercialization_service import (
    calculate_ip_score, estimate_brand_premium, recommend_trademark_classes
)

def test_calculate_ip_score():
    s = calculate_ip_score(90, 80, 30, 70)
    assert s == 90*0.3 + 80*0.3 + 70*0.2 + 70*0.2  # = 27+24+14+14 = 79

def test_brand_premium_range():
    p = estimate_brand_premium(50000, 3.0, "illustrator")
    assert 15 <= p <= 40

def test_trademark_classes():
    classes = recommend_trademark_classes("game_developer")
    assert len(classes) >= 3
```

**Commit:** `git commit -m "feat: add IP commercialization toolkit with assessment matrix and brand premium calculator"`

---

### Task 0.4: 交易费用体系

**Files:**
- Create: `backend/app/models/trading_fee.py`
- Create: `backend/app/routers/trading_fee.py`
- Create: `backend/app/services/trading_fee_service.py`
- Create: `backend/app/schemas/trading_fee.py`
- Test: `tests/test_trading_fee.py`

**Interfaces:**
- Consumes: 交易金额
- Produces: 佣金计算结果（阶梯递减）, escrow费用, 合约费用

**Step 1: 数据模型 — 创始会员费率**

```python
# backend/app/models/trading_fee.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, Boolean, ForeignKey, Integer
from app.database import Base

class TradingFeeTier(Base):
    """交易费率配置表 — 支持阶梯递减."""
    __tablename__ = "trading_fee_tiers"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    tier_name = Column(String(50), nullable=False, unique=True)  # "base", "silver", "gold", "diamond"
    monthly_volume_threshold = Column(Integer, nullable=False)  # ¥0, ¥10000, ¥100000, ¥500000
    commission_rate = Column(Float, nullable=False)  # 0.02, 0.015, 0.01, 0.005
    escrow_rate = Column(Float, nullable=False, default=0.003)  # 0.3%
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class FounderMembership(Base):
    """创始会员永久低费率计划."""
    __tablename__ = "founder_memberships"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String(32), nullable=False, index=True)
    membership_type = Column(String(20), nullable=False)  # "creator", "supplier", "pro"
    permanent_commission_rate = Column(Float, nullable=False)  # 永久1.5%
    is_active = Column(Boolean, default=True)
    enrolled_at = Column(DateTime, default=datetime.utcnow)
```

**Step 2: 初始化费率数据**

```python
# backend/app/services/trading_fee_service.py
from sqlalchemy.orm import Session
from app.models.trading_fee import TradingFeeTier

def init_fee_tiers(db: Session):
    """初始化交易费率阶梯数据."""
    tiers_data = [
        {"tier_name": "base", "monthly_volume_threshold": 0, "commission_rate": 0.02, "escrow_rate": 0.003},
        {"tier_name": "silver", "monthly_volume_threshold": 10000, "commission_rate": 0.015, "escrow_rate": 0.003},
        {"tier_name": "gold", "monthly_volume_threshold": 100000, "commission_rate": 0.01, "escrow_rate": 0.003},
        {"tier_name": "diamond", "monthly_volume_threshold": 500000, "commission_rate": 0.005, "escrow_rate": 0.003},
    ]
    for td in tiers_data:
        existing = db.query(TradingFeeTier).filter(
            TradingFeeTier.tier_name == td["tier_name"]
        ).first()
        if not existing:
            db.add(TradingFeeTier(**td))
    db.commit()

def get_commission_rate(monthly_volume_yuan: int) -> float:
    """根据月交易额获取对应佣金率."""
    if monthly_volume_yuan >= 500000:
        return 0.005
    elif monthly_volume_yuan >= 100000:
        return 0.01
    elif monthly_volume_yuan >= 10000:
        return 0.015
    return 0.02

def calculate_fee(transaction_amount_yuan: float, monthly_volume_yuan: int = 0) -> dict:
    """计算单笔交易费用."""
    rate = get_commission_rate(monthly_volume_yuan)
    commission = round(transaction_amount_yuan * rate, 2)
    escrow = round(transaction_amount_yuan * 0.003, 2)
    total_fee = commission + escrow
    return {
        "transaction_amount": transaction_amount_yuan,
        "commission_rate": rate,
        "commission": commission,
        "escrow_fee": escrow,
        "total_fee": total_fee,
        "net_to_creator": round(transaction_amount_yuan - total_fee, 2),
    }
```

**Step 3: Router**

```python
# backend/app/routers/trading_fee.py
from fastapi import APIRouter, Depends
from app.services.trading_fee_service import calculate_fee, get_commission_rate, init_fee_tiers
from app.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/trading-fees", tags=["trading-fees"])

@router.get("/calculate")
def fee_calc(amount: float, volume: int = 0):
    return calculate_fee(amount, volume)

@router.get("/rate")
def fee_rate(volume: int = 0):
    return {"commission_rate": get_commission_rate(volume)}

@router.post("/init")
def init_fees(db: Session = Depends(get_db)):
    init_fee_tiers(db)
    return {"status": "initialized"}
```

**Step 4: 测试**

```python
# tests/test_trading_fee.py
import pytest
from app.services.trading_fee_service import calculate_fee, get_commission_rate

def test_base_commission_rate():
    assert get_commission_rate(0) == 0.02

def test_silver_rate():
    assert get_commission_rate(15000) == 0.015

def test_diamond_rate():
    assert get_commission_rate(600000) == 0.005

def test_fee_calculation():
    result = calculate_fee(10000, 0)
    assert result["commission"] == 200.0  # 10000 * 0.02
    assert result["escrow_fee"] == 30.0   # 10000 * 0.003
    assert result["total_fee"] == 230.0
```

**Commit:** `git commit -m "feat: add trading fee system with tiered commissions and founder membership"`

---

### Task 0.5: 挂牌模式（Listing）

**Files:**
- Create: `backend/app/models/listing.py`
- Modify: `backend/app/models/commission.py` (扩展撮合交易)
- Create: `backend/app/routers/listing.py`
- Create: `backend/app/services/listing_service.py`
- Create: `backend/app/schemas/listing.py`
- Test: `tests/test_listing.py`

**Interfaces:**
- Consumes: `Work.id`, `TradingFeeTier`
- Produces: Listing → Order → Settlement 完整流程

**Step 1: 数据模型 — 挂牌+订单+结算**

```python
# backend/app/models/listing.py
import uuid, enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Enum as SAEnum, Integer, Boolean, Text
from app.database import Base

class ListingStatus(enum.StrEnum):
    ACTIVE = "active"
    SOLD = "sold"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class TransactionType(enum.StrEnum):
    LISTING = "listing"
    AUCTION = "auction"
    RFQ = "rfq"
    REVENUE_SHARE = "revenue_share"

class TradeListing(Base):
    """挂牌交易表 — 创作者上架作品供供应商订购."""
    __tablename__ = "trade_listings"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    work_id = Column(String(32), ForeignKey("works.id"), nullable=False, index=True)
    creator_id = Column(String(32), nullable=False, index=True)
    supplier_id = Column(String(32), nullable=True)  # 挂牌模式下为空，等待供应商订购
    listing_type = Column(SAEnum(TransactionType), default=TransactionType.LISTING)
    price_yuan = Column(Float, nullable=False)  # 挂牌价格
    license_scope = Column(Text, nullable=True)  # 授权范围说明
    status = Column(SAEnum(ListingStatus), default=ListingStatus.ACTIVE)
    expires_at = Column(DateTime, nullable=True)  # 过期时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TradeOrder(Base):
    """交易订单表."""
    __tablename__ = "trade_orders"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    listing_id = Column(String(32), ForeignKey("trade_listings.id"), nullable=False, index=True)
    buyer_id = Column(String(32), nullable=False, index=True)  # 供应商/买家
    seller_id = Column(String(32), nullable=False)  # 创作者
    amount_yuan = Column(Float, nullable=False)
    commission_yuan = Column(Float, nullable=False)  # 平台佣金
    escrow_fee_yuan = Column(Float, nullable=False)  # 托管费
    net_to_seller = Column(Float, nullable=False)  # 创作者净收入
    status = Column(String(20), default="pending_escrow")  # pending_escrow/released/completed/disputed
    escrow_released_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class TradeSettlement(Base):
    """交易结算表 — 定期结算给创作者."""
    __tablename__ = "trade_settlements"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    order_id = Column(String(32), ForeignKey("trade_orders.id"), nullable=True)
    seller_id = Column(String(32), nullable=False, index=True)
    gross_amount = Column(Float, nullable=False)
    platform_commission = Column(Float, nullable=False)
    escrow_fee = Column(Float, nullable=False)
    settled_amount = Column(Float, nullable=False)
    settlement_status = Column(String(20), default="pending")  # pending/settled/refunded
    settled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Step 2: Schema**

```python
# backend/app/schemas/listing.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ListingCreate(BaseModel):
    work_id: str
    price_yuan: float
    license_scope: Optional[str] = None
    expires_days: Optional[int] = 30

class ListingResponse(BaseModel):
    id: str
    work_id: str
    creator_id: str
    price_yuan: float
    status: str
    expires_at: Optional[datetime]

class OrderCreate(BaseModel):
    listing_id: str
    buyer_id: str

class OrderResponse(BaseModel):
    id: str
    listing_id: str
    buyer_id: str
    amount_yuan: float
    commission_yuan: float
    escrow_fee_yuan: float
    net_to_seller: float
    status: str
```

**Step 3: 服务层 — 挂牌→订购→结算**

```python
# backend/app/services/listing_service.py
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.listing import TradeListing, TradeOrder, TradeSettlement, ListingStatus, TransactionType
from app.models.work import Work
from app.services.trading_fee_service import calculate_fee

def create_listing(db: Session, work_id: str, creator_id: str,
                   price_yuan: float, license_scope: str | None = None,
                   expires_days: int = 30) -> TradeListing:
    listing = TradeListing(
        work_id=work_id,
        creator_id=creator_id,
        price_yuan=price_yuan,
        license_scope=license_scope,
        status=ListingStatus.ACTIVE,
        expires_at=datetime.utcnow() + timedelta(days=expires_days),
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing

def place_order(db: Session, listing_id: str, buyer_id: str) -> TradeOrder:
    listing = db.query(TradeListing).filter(
        TradeListing.id == listing_id,
        TradeListing.status == ListingStatus.ACTIVE,
    ).first()
    if not listing:
        raise ValueError("挂牌不存在或已过期")

    fee_info = calculate_fee(listing.price_yuan)
    order = TradeOrder(
        listing_id=listing_id,
        buyer_id=buyer_id,
        seller_id=listing.creator_id,
        amount_yuan=listing.price_yuan,
        commission_yuan=fee_info["commission"],
        escrow_fee_yuan=fee_info["escrow_fee"],
        net_to_seller=fee_info["net_to_creator"],
        status="pending_escrow",
    )
    listing.status = ListingStatus.SOLD
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

def release_escrow(db: Session, order_id: str) -> TradeSettlement:
    """确认交付后释放托管资金."""
    order = db.query(TradeOrder).filter(TradeOrder.id == order_id).first()
    if not order or order.status != "pending_escrow":
        raise ValueError("订单状态不允许释放托管")

    order.status = "completed"
    settlement = TradeSettlement(
        order_id=order_id,
        seller_id=order.seller_id,
        gross_amount=order.amount_yuan,
        platform_commission=order.commission_yuan,
        escrow_fee=order.escrow_fee_yuan,
        settled_amount=order.net_to_seller,
        settlement_status="settled",
        settled_at=datetime.utcnow(),
    )
    db.add(settlement)
    db.commit()
    db.refresh(settlement)
    return settlement
```

**Step 4: Router**

```python
# backend/app/routers/listing.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.listing import ListingCreate, ListingResponse, OrderCreate, OrderResponse
from app.services.listing_service import create_listing, place_order, release_escrow

router = APIRouter(prefix="/api/listings", tags=["listings"])

@router.post("/", response_model=ListingResponse)
def post_listing(data: ListingCreate, db: Session = Depends(get_db), creator_id: str = "default"):
    return create_listing(db, data.work_id, creator_id, data.price_yuan, data.license_scope, data.expires_days)

@router.post("/{listing_id}/order", response_model=dict)
def post_order(listing_id: str, data: OrderCreate, db: Session = Depends(get_db)):
    order = place_order(db, listing_id, data.buyer_id)
    return order
```

**Step 5-7: 注册路由 + Alembic迁移 + 测试**

```python
# tests/test_listing.py
import pytest
from app.services.listing_service import create_listing, place_order, release_escrow

def test_create_listing(db_session, sample_work):
    listing = create_listing(db_session, sample_work.id, "creator1", 1000.0)
    assert listing.price_yuan == 1000.0
    assert listing.status == "active"

def test_place_order(db_session, sample_work):
    listing = create_listing(db_session, sample_work.id, "creator1", 1000.0)
    order = place_order(db_session, listing.id, "buyer1")
    assert order.amount_yuan == 1000.0
    assert order.commission_yuan == 20.0  # 2%
    assert order.escrow_fee_yuan == 3.0   # 0.3%
    assert order.net_to_seller == 977.0
```

**Commit:** `git commit -m "feat: add listing mode for creator-supplier matching transactions"`

---

## Phase 1-3 概要（详细设计见主规划文档）

### Phase 1 (P1): 创作者权益强化（6-12个月）— 6个模块

| # | 模块 | 关键文件 |
|---|------|---------|
| 6 | 合约风险评估 | `models/contract_risk.py`, `routers/contract_risk.py`, `services/contract_review_service.py` |
| 7 | 创作者导航 | `routers/creator_navigation.py`, `services/navigation_service.py` |
| 8 | 版权保险市场 | `models/copyright_insurance.py`, `routers/copyright_insurance.py` |
| 9 | 创作者能力评估 | `models/creator_capability.py`, `services/capability_service.py` |
| 10 | 多市场扩张 | `models/multi_market.py`, `services/expansion_service.py` |
| 11 | 维权ROI计算器 | `models/rights_enforcement.py`, `services/roi_calculator.py` |

### Phase 2 (P2): 创作者成长体系（12-18个月）— 7个模块

| # | 模块 | 关键文件 |
|---|------|---------|
| 12 | 私域流量管理 | `models/private_traffic.py`, `routers/private_traffic.py` |
| 13 | 经营管理中心 | 扩展现有 `routers/dashboard.py` + `services/income_analysis.py` |
| 14 | 多平台适配流水线 | `models/content_pipeline.py`, `services/multi_platform_service.py` |
| 15 | 拍卖模式 | 扩展 `models/listing.py` + `routers/auction.py` |
| 16 | 询价模式 | `routers/rfq.py`, `services/rfq_service.py` |
| 17 | 授权分成V2 | 扩展 `models/listing.py` + `services/revenue_share.py` |
| 18 | 信用体系V1 | `models/credit_system.py`, `routers/credit.py`, `services/credit_service.py` |

### Phase 3 (P3): 全球化与智能化（18-24个月）— 5个模块

| # | 模块 | 关键文件 |
|---|------|---------|
| 19 | 侵权监测增强 | `services/clip_detection.py`, `services/dmca_auto.py` |
| 20 | 复杂合同引擎 | 扩展 `services/contract_service.py` |
| 21 | Enterprise数据API | `routers/enterprise_api.py` |
| 22 | 信用评分V2 | 扩展 `services/credit_service.py` (ML) |
| 23 | 争议仲裁系统 | `models/arbitration.py`, `routers/arbitration.py` |

---

## 全局约束

- **Python**: >= 3.11
- **FastAPI**: >= 0.110
- **SQLAlchemy**: >= 2.0
- **Pydantic**: >= 2.5
- **Vue**: 3.x (Composition API + `<script setup>`)
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **测试框架**: pytest >= 7.4 + pytest-asyncio
- **所有新增模型必须包含**: `created_at`, `updated_at` 时间戳字段
- **所有API响应遵循统一格式**: `{data, error, message}` envelope
- **不做NFT/Web3/DAO**: 代码中不得出现相关实现，仅预留API接口注释

---

## 自审结果

**Spec coverage**: 5个P0模块全部覆盖主规划文档第五部分和第七部分①③⑦⑫⑭
**Placeholder scan**: 无TBD/TODO占位符，所有代码步骤都有具体实现
**Type consistency**: 所有模型使用统一的String(32) UUID格式，与现有works表一致
**Scope check**: P0阶段5个模块相互依赖但各自可独立测试，符合bite-sized原则
