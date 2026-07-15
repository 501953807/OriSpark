# 商单工作流 (Commission Workflow) 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement task-by-task.
> **Cross-cutting feature:** Needed by ALL creator types (插画师/摄影师/视频/手工/音乐/文字)

**Goal:** 实现完整的约稿/商单管理系统，支持里程碑跟踪、收款记录、修改反馈、看板/日历视图
**Architecture:** 扩展现有 commission 后端路由 + 新建前端 Kanban/Detail/Calendar 组件
**Tech Stack:** FastAPI + SQLAlchemy (BE), Vue 3 + TypeScript + Pinia (FE)

## Global Constraints

- 所有 alert() 替换为 toast：`(window as any).$toast?.show('message', 'info')`
- 所有 async 函数必须有 try/catch
- 前端文件 <800 行，函数 <50 行
- 严格 immutability，禁止 mutation

---

## 后端实施

### Task 1: 扩展现有 Commission 模型

**Files:**
- `backend/app/models/commission.py` - 扩展现有模型 (添加里程碑、收款、修改记录关联)

**Interfaces:**
- Consumes: 现有 `CommissionProject` 模型
- Produces: 新增 `CommissionMilestone`, `CommissionPayment`, `CommissionRevision` 模型

**模型字段:**

```python
# CommissionMilestone
class CommissionMilestone(Base):
    __tablename__ = "commission_milestones"
    id = Column(String, primary_key=True)
    commission_id = Column(String, ForeignKey("commission_projects.id"), nullable=False)
    name = Column(String(200), nullable=False)
    status = Column(String(20), default="pending")  # pending|in_progress|completed|overdue
    due_date = Column(DateTime, nullable=True)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=current_timestamp)
    updated_at = Column(DateTime, default=current_timestamp, onupdate=current_timestamp)

# CommissionPayment
class CommissionPayment(Base):
    __tablename__ = "commission_payments"
    id = Column(String, primary_key=True)
    commission_id = Column(String, ForeignKey("commission_projects.id"), nullable=False)
    milestone_id = Column(String, ForeignKey("commission_milestones.id"), nullable=True)
    amount = Column(Numeric(10, 2), nullable=False)
    method = Column(String(50))  # bank_transfer|wechat|alipay|cash|check
    status = Column(String(20), default="pending")  # pending|received|partial|overdue
    paid_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=current_timestamp)

# CommissionRevision
class CommissionRevision(Base):
    __tablename__ = "commission_revisions"
    id = Column(String, primary_key=True)
    commission_id = Column(String, ForeignKey("commission_projects.id"), nullable=False)
    description = Column(Text, nullable=False)
    client_feedback = Column(Text, nullable=True)
    files = Column(JSON, nullable=True)  # uploaded file paths
    created_by = Column(String, nullable=False)  # 'artist' or 'client'
    created_at = Column(DateTime, default=current_timestamp)
```

- [ ] **Step 1:** 读取现有 `backend/app/models/commission.py` 了解当前模型结构
- [ ] **Step 2:** 添加上述三个新模型类
- [ ] **Step 3:** 在 `CommissionProject` 中添加 relationship 关联
- [ ] **Step 4:** 运行 `alembic revision --autogenerate -m "add commission workflow models"` 生成迁移
- [ ] **Step 5:** 运行 `alembic upgrade head` 应用迁移

### Task 2: 扩展 Commission API 路由

**Files:**
- `backend/app/routers/commission.py` - 扩展现有路由

**新增端点:**

| Method | Path | Description | Request Body | Response |
|--------|------|-------------|--------------|----------|
| GET | `/api/commissions/{id}/milestones` | 获取里程碑列表 | - | `Milestone[]` |
| POST | `/api/commissions/{id}/milestones` | 创建里程碑 | `{name, due_date, description, order_index}` | `Milestone` |
| PATCH | `/api/commissions/{id}/milestones/{mid}` | 更新里程碑 | `{status, due_date, ...}` | `Milestone` |
| DELETE | `/api/commissions/{id}/milestones/{mid}` | 删除里程碑 | - | `{success: true}` |
| GET | `/api/commissions/{id}/payments` | 获取收款记录 | - | `Payment[]` |
| POST | `/api/commissions/{id}/payments` | 记录收款 | `{amount, method, milestone_id, notes}` | `Payment` |
| PATCH | `/api/commissions/{id}/payments/{pid}` | 更新收款 | `{status, paid_at, ...}` | `Payment` |
| GET | `/api/commissions/{id}/revisions` | 获取修改记录 | - | `Revision[]` |
| POST | `/api/commissions/{id}/revisions` | 记录修改 | `{description, client_feedback, files}` | `Revision` |
| GET | `/api/commissions/{id}/timeline` | 获取完整时间线(里程碑+收款+修改) | - | `TimelineEvent[]` |
| GET | `/api/commissions/calendar` | 约稿日历 | `?from=YYYY-MM-DD&to=YYYY-MM-DD` | `{events: CalendarEvent[]}` |
| GET | `/api/commissions/dashboard` | 仪表盘统计 | - | `{active_count, pending_payment, monthly_revenue, avg_ticket}` |

- [ ] **Step 1:** 读取现有 `backend/app/routers/commission.py` 了解当前路由
- [ ] **Step 2:** 添加 milestones CRUD 端点
- [ ] **Step 3:** 添加 payments CRUD 端点
- [ ] **Step 4:** 添加 revisions CRUD 端点
- [ ] **Step 5:** 添加 timeline 聚合端点
- [ ] **Step 6:** 添加 calendar 端点
- [ ] **Step 7:** 添加 dashboard 统计端点
- [ ] **Step 8:** 添加对应的 schemas (`backend/app/schemas/commission.py`)
- [ ] **Step 9:** 集成测试所有新端点

### Task 3: 扩展 CommissionView 前端页面

**Files:**
- `frontend/src/views/CommissionView.vue` - 扩展现有页面
- `frontend/src/stores/useCommissionStore.ts` - 新建
- `frontend/src/api/commission.ts` - 新建

**Store 接口:**

```typescript
interface CommissionStore {
  commissions: CommissionProject[]
  milestones: Milestone[]
  payments: Payment[]
  revisions: Revision[]
  dashboard: DashboardStats
  loading: boolean
  
  fetchCommissions(filters?: CommissionFilters): Promise<void>
  fetchCommissionDetail(id: string): Promise<void>
  createMilestone(commissionId: string, data: CreateMilestoneDto): Promise<Milestone>
  updateMilestone(commissionId: string, milestoneId: string, data: UpdateMilestoneDto): Promise<Milestone>
  createPayment(commissionId: string, data: CreatePaymentDto): Promise<Payment>
  fetchCalendar(from: string, to: string): Promise<CalendarEvent[]>
  fetchDashboard(): Promise<DashboardStats>
}
```

**组件扩展:**
- 在现有 CommissionView 中添加"查看详情"按钮，跳转到 CommissionDetailView
- 添加"看板视图"切换按钮

- [ ] **Step 1:** 创建 `frontend/src/types/commission.ts` 类型定义
- [ ] **Step 2:** 创建 `frontend/src/api/commission.ts` API 客户端
- [ ] **Step 3:** 创建 `frontend/src/stores/useCommissionStore.ts` Pinia store
- [ ] **Step 4:** 扩展现有 `CommissionView.vue` 添加视图切换

### Task 4: 新建 CommissionDetailView

**Files:**
- `frontend/src/views/CommissionDetailView.vue` - 新建
- `frontend/src/components/commission/` - 新建目录
  - `MilestoneBoard.vue` - 里程碑进度条
  - `PaymentRecordPanel.vue` - 收款记录面板
  - `RevisionLogPanel.vue` - 修改记录面板
  - `CommissionTimeline.vue` - 时间线视图

**CommissionDetailView 组件规格:**

Props: `{ commissionId: string }`

Layout:
```
┌─────────────────────────────────────────────┐
│ ← 返回  |  商单: {title}                    │
├─────────────────────────────────────────────┤
│ [看板] [列表] [时间线] [日历]               │
├─────────────────────────────────────────────┤
│                                             │
│  客户信息: {name, contact, company}         │
│  金额: ¥{total}  |  已收: ¥{paid}          │
│  进度: ████████░░ 80%                      │
│                                             │
│  ── 里程碑 ───────────────────────────────  │
│  ☑ 需求确认 (2026-07-01)                  │
│  ☑ 初稿交付 (2026-07-10)                  │
│  ◐ 修改中 (2026-07-15)  ← 当前            │
│  ☐ 尾款结算 (2026-07-20)                  │
│                                             │
│  ── 收款记录 ─────────────────────────────  │
│  │ 日期       │ 金额   │ 方式   │ 状态    │ │
│  │ 2026-07-01 │ ¥3000  │ 微信   │ 已收    │ │
│  │ 2026-07-15 │ ¥3000  │ 银行   │ 待收    │ │
│                                             │
│  ── 修改记录 ─────────────────────────────  │
│  [+ 添加修改记录]                           │
│                                             │
└─────────────────────────────────────────────┘
```

- [ ] **Step 1:** 创建 `CommissionDetailView.vue` 骨架
- [ ] **Step 2:** 实现 `MilestoneBoard.vue` 组件
- [ ] **Step 3:** 实现 `PaymentRecordPanel.vue` 组件
- [ ] **Step 4:** 实现 `RevisionLogPanel.vue` 组件
- [ ] **Step 5:** 实现 `CommissionTimeline.vue` 组件
- [ ] **Step 6:** 添加路由配置 `frontend/src/router/index.ts`

### Task 5: 实现看板视图 (CommissionKanban)

**Files:**
- `frontend/src/components/commission/CommissionKanban.vue` - 新建

**功能:**
- 5列布局: 询价 → 已确认 → 制作中 → 交付 → 已结款
- 每列显示该状态的商单卡片
- 点击卡片拖拽到另一列更新状态
- 卡片显示: 客户名、金额、截止日期、倒计时

**拖拽状态机:**
```
询价 → 已确认: 需要 deposit_received=true
已确认 → 制作中: 需要 milestone_created=true
制作中 → 交付: 需要 final_delivery=true
交付 → 已结款: 需要 all_payments_received=true
```

- [ ] **Step 1:** 实现 Kanban 列布局组件
- [ ] **Step 2:** 实现商单卡片组件
- [ ] **Step 3:** 实现拖拽功能 (Vue Draggable 或原生 drag-and-drop API)
- [ ] **Step 4:** 实现状态更新 API 调用
- [ ] **Step 5:** 添加验证规则 (不能跳过状态)

### Task 6: 实现日历视图

**Files:**
- `frontend/src/components/commission/CommissionCalendar.vue` - 新建

**功能:**
- 月历视图，标记截止日和里程碑日
- 点击日期显示当日事件
- 支持从/到日期范围筛选

- [ ] **Step 1:** 集成日历组件 (使用 v-calendar 或自实现)
- [ ] **Step 2:** 加载日历事件数据
- [ ] **Step 3:** 实现事件标记和点击交互

---

## 测试计划

### 后端测试
- [ ] 里程碑 CRUD 单元测试
- [ ] 收款记录 CRUD 单元测试
- [ ] 修改记录 CRUD 单元测试
- [ ] 时间线聚合端点集成测试
- [ ] 日历端点测试 (日期范围筛选)
- [ ] 仪表盘统计测试

### 前端测试
- [ ] CommissionDetailView 渲染测试
- [ ] MilestoneBoard 拖拽测试
- [ ] PaymentRecordPanel 添加/编辑测试
- [ ] CommissionKanban 状态转换测试
- [ ] CommissionCalendar 事件显示测试

---

## Commit 策略

1. `feat: add commission milestone/payment/revision models` — 后端数据层
2. `feat: add commission workflow API endpoints` — 后端路由
3. `feat: add commission store and API client` — 前端数据层
4. `feat: add commission detail view with milestone board` — 前端视图
5. `feat: add kanban view for commission management` — 看板
6. `feat: add calendar view for commission deadlines` — 日历
