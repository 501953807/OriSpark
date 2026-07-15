# 手工艺人完整支持 (Craftsman v3b) 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement task-by-task.
> **Version:** v3b | **Target Creator:** 手工艺人

**Goal:** 实现工厂对接、询价单、样品跟踪、质检报告、原料库存、生产批次、Etsy API 对接
**Architecture:** 扩展现有 factory/quality_inspection 模型 + 新建手工艺人视图
**Tech Stack:** FastAPI + SQLAlchemy (BE), Vue 3 + TypeScript + Pinia (FE)

## Global Constraints

- 所有 alert() 替换为 toast
- 所有 async 函数必须有 try/catch
- 前端文件 <800 行，函数 <50 行
- 严格 immutability

---

## Task 1: 手工艺人数据模型

**Files:**
- `backend/app/models/crafts.py` - 新建(从 reserved_crafts.py 迁移)
- `backend/app/schemas/crafts.py` - 新建
- `backend/app/routers/factory.py` - 扩展现有路由

**核心模型:**

```python
# RFQ (Request for Quotation) 询价单
class RFQRequest(Base):
    __tablename__ = "rfq_requests"
    id = Column(String, primary_key=True)
    creator_id = Column(String, nullable=False)
    product_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    material_specs = Column(JSON, nullable=True)  # 材料规格
    quantity = Column(Integer, nullable=False)
    target_price = Column(Numeric(10, 2), nullable=True)
    deadline = Column(DateTime, nullable=True)
    status = Column(String(20), default="draft")  # draft|sent|quoting|awarded|cancelled
    sent_to = Column(JSON, nullable=True)  # [{factory_id, sent_at, responded_at}]
    awarded_to = Column(String, nullable=True)  # factory_id
    created_at = Column(DateTime, default=current_timestamp)

# Factory Quote 工厂报价
class FactoryQuote(Base):
    __tablename__ = "factory_quotes"
    id = Column(String, primary_key=True)
    rfq_id = Column(String, ForeignKey("rfq_requests.id"), nullable=False)
    factory_id = Column(String, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    lead_time_days = Column(Integer, nullable=True)  # 交货周期
    min_order = Column(Integer, default=1)
    notes = Column(Text, nullable=True)
    status = Column(String(20), default="active")  # active|expired|accepted
    created_at = Column(DateTime, default=current_timestamp)

# Sample 样品
class Sample(Base):
    __tablename__ = "samples"
    id = Column(String, primary_key=True)
    order_id = Column(String, nullable=False)
    rfq_id = Column(String, nullable=True)
    version = Column(Integer, default=1)  # 第几版样品
    approval_status = Column(String(20), default="pending")  # pending|approved|rejected|revision_needed
    photos = Column(JSON, nullable=True)  # 样品照片路径
    revision_notes = Column(Text, nullable=True)  # 修改意见
    created_at = Column(DateTime, default=current_timestamp)

# Quality Report 质检报告
class QualityReport(Base):
    __tablename__ = "quality_reports"
    id = Column(String, primary_key=True)
    batch_id = Column(String, nullable=False)
    inspector = Column(String(100), nullable=True)  # 检验员
    aql_standard = Column(String(20), default="AQL 2.5")  # AQL标准
    total_checked = Column(Integer, nullable=False)
    passed = Column(Integer, nullable=False)
    failed = Column(Integer, nullable=False)
    defect_types = Column(JSON, nullable=True)  # [{"type": "color_shift", "count": 2}]
    result = Column(String(20))  # pass|fail|conditional
    photos = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=current_timestamp)

# Material Inventory 原料库存
class MaterialInventory(Base):
    __tablename__ = "material_inventory"
    id = Column(String, primary_key=True)
    creator_id = Column(String, nullable=False)
    name = Column(String(200), nullable=False)
    category = Column(String(50))  # fabric/wood/metal/clay/thread/accessory
    unit = Column(String(20))  # kg/m/pcs/liter
    quantity = Column(Numeric(10, 2), default=0)
    min_quantity = Column(Numeric(10, 2), default=0)  # 最低库存预警
    unit_cost = Column(Numeric(10, 2), nullable=True)
    supplier = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=current_timestamp)

# Production Batch 生产批次
class ProductionBatch(Base):
    __tablename__ = "production_batches"
    id = Column(String, primary_key=True)
    order_id = Column(String, nullable=False)
    batch_number = Column(String(50), unique=True, nullable=False)
    product_name = Column(String(200), nullable=False)
    quantity_planned = Column(Integer, nullable=False)
    quantity_completed = Column(Integer, default=0)
    status = Column(String(20), default="planning")  # planning|producing|quality_check|completed|shipped
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=current_timestamp)
```

- [ ] **Step 1:** 读取 `backend/app/models/reserved_crafts.py` 了解预留结构
- [ ] **Step 2:** 创建 `backend/app/models/crafts.py` 完整模型
- [ ] **Step 3:** 创建 Alembic 迁移并应用
- [ ] **Step 4:** 创建 schemas
- [ ] **Step 5:** 扩展 factory.py 路由

## Task 2: 手工艺人前端

**Files:**
- `frontend/src/views/CraftsmanView.vue` - 新建
- `frontend/src/components/crafts/` - 新建目录
- `frontend/src/stores/useCraftsStore.ts` - 新建
- `frontend/src/api/factory.ts` - 新建

**手工艺人专属过程阶段:**
```
设计草图 → 材料准备 → 打样 → 客户确认 → 批量生产 → 质检 → 包装 → 发货
```

**Layout:**
```
┌─────────────────────────────────────────────┐
│ 手工艺人工作台                                │
├─────────────────────────────────────────────┤
│ 🏭 询价单: 3  |  📦 生产中: 2               │
│ 🔍 样品: 5件  |  📊 库存预警: 1项            │
│ 💰 本月产值: ¥8,900                         │
├─────────────────────────────────────────────┤
│ [询价] [样品] [质检] [库存] [批次]          │
├─────────────────────────────────────────────┤
│                                             │
│  ── 询价单列表 ────────────────────────────  │
│  │ 产品      │ 数量 │ 报价 │ 工厂 │ 状态   │ │
│  │ 陶瓷杯    │ 100  │ ¥35  │ A厂 │ 待确认 │ │
│  │ 皮钱包    │ 50   │ ¥120 │ B厂 │ 已下单 │ │
│                                             │
└─────────────────────────────────────────────┘
```

- [ ] **Step 1:** 创建 CraftsmanView.vue 骨架
- [ ] **Step 2:** 创建 useCraftsStore.ts
- [ ] **Step 3:** 创建 api/factory.ts
- [ ] **Step 4:** 创建类型定义 frontend/src/types/crafts.ts

## Task 3: 手工艺人子组件

**Files:**
- `frontend/src/components/crafts/RFQManager.vue` - 新建
- `frontend/src/components/crafts/SampleTracker.vue` - 新建
- `frontend/src/components/crafts/QualityReportPanel.vue` - 新建
- `frontend/src/components/crafts/InventoryPanel.vue` - 新建
- `frontend/src/components/crafts/ProductionBatchPanel.vue` - 新建

**RFQManager.vue:**
- 询价单列表 + 创建表单
- 工厂报价对比表
- 发送询价 → 等待报价 → 选择工厂 状态流转

**SampleTracker.vue:**
- 样品列表 + 版本管理
- 照片预览 (支持多图)
- 审批操作 (通过/驳回/需修改)

**QualityReportPanel.vue:**
- AQL标准选择
- 检查项目清单
- 缺陷类型标记 + 照片上传
- 结果判断 (pass/fail/conditional)

**InventoryPanel.vue:**
- 原料库存列表
- 低库存预警高亮
- 入库/出库操作

**ProductionBatchPanel.vue:**
- 批次列表 + 进度条
- 状态流转 (planning → producing → quality_check → completed → shipped)
- 质检报告关联

- [ ] **Step 1:** 实现 RFQManager.vue
- [ ] **Step 2:** 实现 SampleTracker.vue
- [ ] **Step 3:** 实现 QualityReportPanel.vue
- [ ] **Step 4:** 实现 InventoryPanel.vue
- [ ] **Step 5:** 实现 ProductionBatchPanel.vue

## Task 4: Etsy API 对接

**Files:**
- `backend/app/services/etsy_service.py` - 新建
- `backend/app/routers/supply.py` - 扩展

**功能:**
- OAuth2 授权流程
- 商品同步 (OriStudio → Etsy 店铺)
- 订单同步 (Etsy → OriStudio)
- 库存同步

- [ ] **Step 1:** 实现 Etsy OAuth2 客户端
- [ ] **Step 2:** 实现商品列表/创建/更新 API
- [ ] **Step 3:** 实现订单拉取
- [ ] **Step 4:** 实现库存同步

---

## 测试计划

- [ ] RFQ 状态机测试
- [ ] 样品审批流程测试
- [ ] 质检报告 AQL 计算测试
- [ ] 库存预警测试
- [ ] Etsy OAuth 流程测试
- [ ] 前后端联调测试
