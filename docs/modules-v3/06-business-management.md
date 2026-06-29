# [6] 经营管理中心 — 详细功能设计 v3

> **定位**: 创作者经营决策的数据中心。聚合来自所有业务模块的数据——收入追踪、合作伙伴管理、通知中心、数据分析看板。
> **最后更新**: 2026-06-12 (Stage 2修订: 空状态设计、收入CSV导入、Partner/Order模型确认)

---

## 一、功能架构

```
经营管理中心
├── 💰 收入追踪 (手动登记+CSV导入+自动汇总+利润计算+图表)
├── 👥 合作伙伴管理 (供应商/工厂/客户/授权方 — Partner模型已存在)
├── 📦 订单管理 (Order/OrderPayment模型已存在)
├── 🔔 通知中心 (存证完成/扫描结果/IP到期/订单状态)
├── 📊 数据分析看板 (收入趋势+产品分布+影响力+安全)
└── ⏰ 提醒管理 (IP续展/年费/授权到期)
```

---

## 二、空状态设计

按照 UX 设计规范的"空状态 = 下一步做什么"原则，经营管理中心各模块空状态设计:

### 2.1 各场景空状态

| 场景 | 图标 | 标题 | 描述 | 主CTA |
|------|------|------|------|-------|
| 空仪表盘(首页) | 🚀 | 开始你的创作之旅 | 导入第一件作品，开始管理你的创作资产 | 导入第一件作品 |
| 空收入 | 💰 | 收入数据将自动汇总 | 创建产品并在POD渠道上架后，收入记录会出现在这里 | 设计产品 / 探索变现 |
| 空合作伙伴 | 👥 | 暂无合作伙伴 | 添加工厂、供应商或客户信息 | 添加伙伴 |
| 空订单 | 📋 | 暂无订单记录 | 制造订单和POD订单将在这里汇总 | 创建产品 |
| 空通知 | 🔔 | 暂无通知 | 存证完成、侵权扫描结果等通知将显示在这里 | — |
| 搜索无结果 | 🔍 | 未找到匹配结果 | 尝试调整筛选条件 | 清除筛选 |

### 2.2 非财务软件化设计

**设计原则**: 温馨引导而非空白图表。每个空状态:
- 图标 + 标题 + 一行描述 + 主CTA按钮 + 可选副CTA
- 如果有提示列表，使用有序列表而非要点

---

## 三、收入追踪

### 3.1 功能
- 手动登记: 金额/渠道/日期/关联产品/备注
- 支持退款记录(负收入)
- 成本录入(关联产品)
- **CSV导入**: 支持支付宝/微信/POD平台导出格式
  - 自动识别列头映射(金额→amount, 日期→date, 备注→notes)
  - 预览导入数据，确认后批量录入
  - API: `POST /api/supply/revenues/import-csv`
- 自动汇总: GET /api/revenues/summary?group_by=month|channel|product|path
- 利润计算: 收入-成本
- ECharts图表: 按月趋势(折线图) + 按渠道(柱状图) + 按变现路径(饼图)

### 3.2 数据来源
- [4]商业转化引擎: product.price / product.cost / RevenueRecord
- 手动录入: 约稿收入、授权费、版税等非系统内产生的收入
- CSV导入: 支付宝账单导出、微信账单导出、POD平台销售报表

### 3.2.1 收入来源类型

收入录入表单包含"收入来源类型"字段 (required):
| 来源类型 | 说明 | 额外字段 |
|---------|------|---------|
| 约稿 | 商业约稿收入 (插画师第一大收入来源，约40%) | 约稿项目名、客户名称 |
| POD | POD渠道商品销售 | 关联产品 |
| 授权 | IP授权收入 | 关联合约 |
| 版税 | 出版/发行版税 | 出版方 |
| 其他 | 其他收入来源 | 备注 |

### 3.3 API
- GET /api/revenues — 收入列表(?page=&date_from=&date_to=&channel=&product_id=)
- POST /api/revenues — 添加收入(body: {amount,channel,date,product_id,notes})
- POST /api/revenues/import-csv — CSV导入
- PATCH/DELETE /api/revenues/{id}
- GET /api/revenues/summary — 汇总(?group_by=month|channel|path)

---

## 四、合作伙伴管理

### 4.1 数据模型确认

Partner 模型已在 `app/models/supply.py` 中实现，包含字段:
- `name`, `company_name`, `type`, `contact_person`, `phone`(AES加密), `email`
- `address`, `website`, `categories`, `product_categories`, `material_capabilities`
- `moq_per_category`, `typical_lead_time_days`, `price_range`, `moq`
- `rating`, `tags`, `status`, `notes`
- 关联: `PartnerQualification` (资质证书)

### 4.2 合作伙伴类型

| 类型 | 说明 | 适用模块 |
|------|------|----------|
| 供应商/工厂 | 提供制造服务 | [4]按需制造 |
| POD平台 | Printful/印鸽等 | [4]POD渠道管理 |
| 授权方/客户 | 购买授权的对象 | [4]IP授权 |
| 约稿客户 | 委托创作的客户 | [1]创意资产中心 |

### 4.3 功能
- 添加/编辑/删除
- 分类筛选
- 基本信息: 名称/类型/联系方式/备注
- 工厂额外字段: 产品类型/材质能力/MOQ/交期/评分(已有Partner模型)
- 客户额外字段: 合作历史/总交易额

### 4.4 API
- GET/POST /api/partners
- PATCH/DELETE /api/partners/{id}

---

## 五、订单管理

### 5.1 数据模型确认

Order 和 OrderPayment 模型已在 `app/models/supply.py` 中实现:

**Order** 字段:
- `order_number`, `order_type`, `partner_id`, `campaign_id`, `product_id`
- `product_name`, `product_category`, `quantity`, `specifications`, `design_file_path`
- `unit_price`, `total_amount`, `deposit_percent`, `deposit_paid`, `balance_due`, `shipping_cost`
- `status` (pending→confirmed→in_production→shipped→completed→cancelled)
- `expected_date`, `actual_date`, `sample_requested/received/approved`
- `shipping_method`, `tracking_number`, `notes`

**OrderPayment** 字段:
- `order_id`, `amount`, `payment_type`(deposit/progress/balance/other), `payment_date`, `notes`

### 5.2 功能
- 订单列表: 按状态/类型/合作伙伴筛选
- 创建订单: 关联合作伙伴/产品/众筹项目
- 更新状态: 待确认→生产中→已发货→已完成
- 付款记录: 定金/进度款/尾款/其他
- 样品管理: 请求→收到→审批

### 5.3 API
- GET/POST /api/supply/orders
- PATCH /api/supply/orders/{id}/status
- POST /api/supply/orders/{id}/sample

---

## 六、通知中心

### 6.1 通知类型与触发源

| 通知类型 | 触发模块 | 触发条件 | 渠道 |
|----------|---------|----------|------|
| 存证完成 | [2]权益保护中心 | 平台返回存证成功 | WebSocket+系统内 |
| 证书就绪 | [2]权益保护中心 | PDF证书生成完成 | WebSocket+系统内 |
| 侵权扫描结果 | [2]权益保护中心 | 定时扫描有新结果 | WebSocket+系统内 |
| 维权行动状态变更 | [2]权益保护中心 | 投诉提交/受理/解决 | WebSocket+系统内 |
| 风险预警触发 | [2]权益保护中心 | 创作前风险预警 | WebSocket+系统内 |
| IP续展到期 | [3]IP登记工作站 | 商标/专利续展日期前30天/7天 | 系统内 |
| 年费到期 | [3]IP登记工作站 | 专利年费到期前30天 | 系统内 |
| 授权到期 | [4]商业撮合平台 | 授权期限到期前30天 | 系统内 |
| 订单状态变更 | [4]商业撮合平台 | 订单状态变化 | 系统内 |
| 众筹里程碑 | [4]商业撮合平台 | 达到目标50%/100% | 系统内 |
| 产品规格校验结果 | [4]商业撮合平台 | DPI/尺寸/色彩不达标 | 系统内 |
| 批量导入完成 | [1]创意资产中心 | 批量导入任务结束(含成功/失败统计) | 系统内 |
| 批量存证完成 | [2]权益保护中心 | 批量存证任务结束 | 系统内 |

### 6.2 通知渠道
- WebSocket实时推送: 页面顶部通知条
- 系统内通知列表: NotificationPanel下拉
- 邮件通知(配置SMTP后启用，P2)
- 微信模板消息(P2 规划，需企业微信/公众号接入)

### 6.3 通知数据结构
```
notifications: id, user_id, type, title, content, is_read, related_id, related_type, created_at
```

### 6.4 API
- GET /api/notifications — 通知列表(?page=&unread_only=)
- GET /api/notifications/unread-count — 未读数
- PATCH /api/notifications/{id}/read — 标记已读
- POST /api/notifications/read-all — 全部已读

---

## 七、数据分析看板

### 7.1 功能
- 聚合来自各模块的数据:
  - 收入: [4]RevenueRecord + [6]RevenueRecord(手动)
  - 作品: [1]works.total
  - 产品: [4]products.total
  - 存证: [2]notary_records.total
  - 侵权: [2]monitor_results.infringing_count
  - **维权**: [2]enforcement_actions.total/success_rate/avg_duration (新增)
  - **预警**: [2]risk_warnings.total/high_severity_count (新增)
- 看板布局:
  ```
  ┌──────────┬──────────┬──────────┬──────────┐
  │ 总收入    │ 作品数    │ 产品数    │ 存证数    │
  ├──────────┴──────────┼──────────┴──────────┤
  │ 收入趋势(6个月)      │ 作品按类型饼图       │
  ├─────────────────────┼─────────────────────┤
  │ 收入按渠道           │ 侵权趋势             │
  └─────────────────────┴─────────────────────┘
  ```

---

## 八、数据来源汇总

| 数据 | 源模块 | 表 |
|------|--------|-----|
| 作品数 | [1]创意资产中心 | works(count) |
| 存证数 | [2]权益保护中心 | notary_records(count) |
| 侵权数 | [2]权益保护中心 | monitor_results(count) |
| 维权统计 | [2]权益保护中心 | enforcement_actions(count/success_rate) (新增) |
| 风险预警 | [2]权益保护中心 | risk_warnings(count) (新增) |
| 产品数 | [4]商业撮合平台 | products(count) |
| 订单数 | [4]商业撮合平台 | orders(count) |
| 收入 | [4]商业撮合平台 + [6]手动 | revenue_records |
| 影响力 | [5]内容分发中心 | analytics数据 |
| 通知 | [6]经营管理中心 | notifications |

---

## 九、前端实现

### 页面入口
DashboardView.vue — 首页仪表盘:
- **空状态**: 🚀 "开始你的创作之旅 — 导入第一件作品"
- 有数据后: 统计卡片 + 收入趋势 + 作品分布 + 通知列表
- 风格: 温馨创作者工作室，非企业财务软件

### 收入管理
- 收入列表: 手动添加 + CSV导入按钮 + 批量操作
- 汇总图表: 按月/渠道/路径
- CSV导入向导: 上传→列映射→预览→确认导入

### 通知面板
NotificationPanel.vue (已有)，增强:
- 分类筛选
- 通知详情展开
- 跳转到关联页面(如点击"存证完成"跳转到存证记录)

---

## 十、上下游数据流

| 输入 | 来源 |
|------|------|
| 全模块聚合数据 | [1][2][3][4][5] |

| 输出 | 目标 |
|------|------|
| 通知推送 | 前端NotificationPanel |
| 趋势图表 | 前端DashboardView |

---

## 十一、预留功能设计 (v2/v3/v4)

> **设计原则**: v1经营管理中心聚焦插画师的收入追踪+合作伙伴+订单+通知+分析。其他创作者的专属经营管理需求在此完整设计。v1预留数据模型/API路由/组件骨架，v2-v4按版本实现。
> **关联文档**: `docs/agent-evaluation-report.md` 中林山海(约稿)周巧手(工厂+质检)的需求驱动设计。

---

### 11.1 约稿管理 (v2)

#### 11.1.1 commission_projects 表 + 里程碑 + 支付条款

- **目标版本**: v2 | **目标创作者**: 插画师/摄影师(约稿占插画师40%收入，评估报告林山海核心缺失)

**功能说明**: 完整商业约稿项目管理——从客户需求到交付结款。当前系统完全没有约稿功能。

**数据模型**:

```sql
-- v1预留
CREATE TABLE commission_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    client_name VARCHAR(200) NOT NULL,
    client_contact VARCHAR(200),  -- 客户联系方式
    client_platform VARCHAR(100),  -- 客户来源平台(微博/米画师/站酷等)
    project_title VARCHAR(500) NOT NULL,
    commission_type VARCHAR(50),  -- illustration/character_design/cover_art/concept_art/portrait/brand_illustration/other
    
    -- 需求与规格
    brief_text TEXT,  -- 客户需求描述
    reference_images JSON,  -- 参考图路径
    -- [{"path": "ref/ref_1.jpg", "note": "风格参考"}, ...]
    specifications JSON,  -- 规格要求
    -- {"size": "A3", "dpi": 300, "color_mode": "CMYK", "format": ["PSD", "JPG"], "style": "水墨风"}

    -- 关联作品
    related_work_ids JSON,  -- 关联的作品ID(交付物)

    -- 里程碑
    milestones JSON,
    -- [
    --   {"name": "草图确认", "due_date": "2026-06-15", "status": "completed", "completed_at": "2026-06-14", "payment_percent": 30},
    --   {"name": "线稿确认", "due_date": "2026-06-20", "status": "in_progress", "payment_percent": 30},
    --   {"name": "终稿交付", "due_date": "2026-06-25", "status": "pending", "payment_percent": 40}
    -- ]

    -- 费用
    total_amount DECIMAL(10,2) NOT NULL,  -- 总金额
    payment_terms VARCHAR(200),  -- 支付条款 e.g., "30%预付+30%线稿+40%终稿"
    paid_amount DECIMAL(10,2) DEFAULT 0.00,  -- 已付金额
    unpaid_amount DECIMAL(10,2),  -- 未付金额(自动计算)
    currency VARCHAR(10) DEFAULT 'CNY',
    payment_records JSON,  -- 支付记录
    -- [{"date": "2026-06-10", "amount": 1500, "method": "微信", "milestone": "预付"}]

    -- 状态
    status VARCHAR(30) DEFAULT 'inquiry',  
    -- inquiry(询价) → negotiation(议价) → confirmed(确认) → in_progress(制作中)
    -- → revision(修改) → delivered(交付) → settled(已结款) → completed(完成) → cancelled(取消)
    
    -- 时间线
    inquiry_date DATE,  -- 询价日期
    confirmed_date DATE,  -- 确认日期
    deadline DATE,  -- 最终截止日期
    delivered_at DATETIME,
    settled_at DATETIME,

    -- 修改记录
    revision_count INTEGER DEFAULT 0,  -- 修改次数
    revision_limit INTEGER DEFAULT 3,  -- 修改次数上限(合同约定)
    revision_notes JSON,  -- 修改记录

    -- 沟通
    communication_log JSON,  -- 沟通记录摘要
    contract_url VARCHAR(500),  -- 合同链接

    is_rush_job BOOLEAN DEFAULT FALSE,  -- 是否加急
    rush_fee DECIMAL(10,2),  -- 加急费

    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_commission_status ON commission_projects(status);
CREATE INDEX idx_commission_deadline ON commission_projects(deadline);
```

**API端点设计**:

| 方法 | 路径 | 说明 | 版本 |
|------|------|------|------|
| GET | /api/commissions | 约稿列表(?status=&client=&date_from=&date_to=) | v2 |
| POST | /api/commissions | 创建约稿项目 | v2 |
| GET | /api/commissions/{id} | 约稿详情(含里程碑+支付+修改+时间线) | v2 |
| PATCH | /api/commissions/{id} | 更新约稿(body: {status, milestones, payment_records, ...}) | v2 |
| DELETE | /api/commissions/{id} | 删除约稿(仅草稿/询价阶段) | v2 |
| POST | /api/commissions/{id}/milestones | 更新里程碑状态(body: {milestone_name, status}) | v2 |
| POST | /api/commissions/{id}/payments | 记录收款(body: {amount, method, milestone}) | v2 |
| POST | /api/commissions/{id}/revisions | 记录修改(body: {description, client_feedback}) | v2 |
| GET | /api/commissions/dashboard | 约稿仪表盘(进行中/待收款/本月收入/平均客单价) | v2 |
| GET | /api/commissions/calendar | 约稿日历(截止日+里程碑日) | v2 |

**前端组件**:
- **CommissionKanban.vue** (v2): Props: `{}` — 约稿看板视图: 询价→已确认→制作中→交付→已结款 各列+拖拽更新状态
- **CommissionDetail.vue** (v2): Props: `{ commissionId }` — 约稿详情: 客户信息+需求+里程碑进度条+付款进度+修改记录+时间线
- **CommissionForm.vue** (v2): Props: `{ commission? }` — 约稿创建/编辑表单
- **CommissionCalendar.vue** (v2): Props: `{ commissions[] }` — 约稿日历组件(截止日+里程碑日标记)
- **CommissionDashboard.vue** (v2): Props: `{}` — 约稿仪表盘(统计卡片+趋势图)

**v1集成点**:
- [6]收入追踪 — v1已预留"约稿"收入来源类型(3.2.1节)，约稿项目→收入记录关联
- [6]Partner表 — v1已有，客户可作为Partner类型管理
- [1]作品管理 — 约稿交付物可关联到作品库

> **标注**: v1 commission_projects表已预留。收入来源枚举已预留"约稿"类型。完整约稿项目管理系统待v2实现。

---

### 11.2 手工工厂对接 (v3)

#### 11.2.1 询价单 + 样品管理 + 质量检验报告

- **目标版本**: v3 | **目标创作者**: 手工艺人

**功能说明**: 手工艺人对接工厂(或自我生产)的管理系统——询价→样品确认→批量生产时的进度追踪+质量检验。评估报告中周巧手指出完全缺失。

**数据模型**:

```sql
-- v1预留

-- 询价单 (RFQ - Request for Quotation)
CREATE TABLE rfq_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    partner_id INTEGER REFERENCES partners(id),  -- 目标工厂
    rfq_number VARCHAR(50) NOT NULL UNIQUE,  -- 询价单号
    product_description TEXT NOT NULL,  -- 产品描述
    quantity INTEGER NOT NULL,
    unit VARCHAR(20),  -- pcs/set/dozen
    specifications JSON,  -- 规格详情
    -- {"material": "陶瓷瓷泥", "finish": "亚光釉", "color": "青花蓝", "dimensions": "20×20×15cm"}
    design_files JSON,  -- 设计图/参考图
    target_unit_price DECIMAL(10,2),  -- 目标单价
    total_budget DECIMAL(10,2),  -- 总预算
    deadline DATE,
    status VARCHAR(20) DEFAULT 'draft',  -- draft/sent/quoted/negotiating/confirmed/rejected
    responses JSON,  -- 工厂报价响应
    -- [{"partner_id": 5, "quoted_price": 45, "lead_time_days": 14, "moq": 100, "responded_at": "..."}]
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 样品管理 (增强已有的Order.sample_*字段)
CREATE TABLE samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER REFERENCES orders(id),
    rfq_id INTEGER REFERENCES rfq_requests(id),
    sample_number VARCHAR(50),  -- 样品编号
    sample_type VARCHAR(30),  -- initial/production/revised/final
    requested_at DATETIME,
    received_at DATETIME,
    photo_paths JSON,  -- 样品照片
    test_results JSON,  -- 测试结果
    -- {"durability": "pass", "color_match": "85%", "size_accuracy": "+-2mm"}
    approval_status VARCHAR(20) DEFAULT 'pending',  -- pending/approved/rejected/revision_needed
    approval_notes TEXT,
    revision_requests JSON,  -- 修改要求
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 质量检验报告
CREATE TABLE quality_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER REFERENCES orders(id),
    batch_id INTEGER REFERENCES production_batches(id),
    report_number VARCHAR(50) NOT NULL UNIQUE,
    inspection_date DATE NOT NULL,
    inspector VARCHAR(100),
    inspection_type VARCHAR(30),  -- inline/final/pre_shipment/third_party
    
    -- 抽样信息
    total_quantity INTEGER NOT NULL,
    sample_size INTEGER NOT NULL,
    accept_level VARCHAR(10) DEFAULT 'AQL 2.5',  -- 验收标准
    accept_point INTEGER,  -- 可接受的缺陷数上限
    actual_defects INTEGER,  -- 实际缺陷数
    
    -- 检查项目
    check_items JSON,
    -- [{"item": "尺寸", "standard": "20±0.5cm", "result": "pass", "actual": "19.8-20.2"},
    --  {"item": "釉面", "standard": "无气泡", "result": "fail", "defects": 3, "details": "底部有气泡"}]
    
    -- 结果
    result VARCHAR(20) NOT NULL,  -- pass/conditional_pass/fail
    defect_summary TEXT,  -- 缺陷汇总
    defect_photos JSON,  -- 缺陷照片
    corrective_actions TEXT,  -- 纠正措施要求
    factory_response TEXT,  -- 工厂回复
    
    report_file_path VARCHAR(500),  -- 原始检验报告文件
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_samples_order ON samples(order_id);
CREATE INDEX idx_quality_reports_order ON quality_reports(order_id);
CREATE INDEX idx_quality_reports_batch ON quality_reports(batch_id);
```

**API端点设计**:

| 方法 | 路径 | 说明 | 版本 |
|------|------|------|------|
| GET | /api/production/rfqs | 询价单列表(?status=) | v3 |
| POST | /api/production/rfqs | 创建询价单 | v3 |
| GET | /api/production/rfqs/{id} | 询价单详情 | v3 |
| PATCH | /api/production/rfqs/{id} | 更新询价单(含工厂响应) | v3 |
| POST | /api/production/rfqs/{id}/send | 发送询价到工厂 | v3 |
| GET | /api/production/samples | 样品列表(?order_id=&approval_status=) | v3 |
| POST | /api/production/samples | 创建样品记录 | v3 |
| PATCH | /api/production/samples/{id} | 更新样品(审批/修改要求) | v3 |
| POST | /api/production/samples/{id}/photos | 上传样品照片 | v3 |
| GET | /api/production/quality-reports | 质检报告列表 | v3 |
| POST | /api/production/quality-reports | 创建质检报告 | v3 |
| GET | /api/production/quality-reports/{id} | 质检报告详情 | v3 |
| GET | /api/production/quality-stats | 质量统计(通过率/缺陷趋势/常见缺陷) | v3 |

**前端组件**:
- **RFQManager.vue** (v3): Props: `{}` — 询价单列表+创建/编辑表单
- **RFQDetail.vue** (v3): Props: `{ rfqId }` — 询价详情: 产品描述+工厂报价对比表+状态时间线
- **SampleTracker.vue** (v3): Props: `{ orderId }` — 样品跟踪: 样品列表+状态标签+照片预览+审批操作
- **QualityReportForm.vue** (v3): Props: `{ orderId?, batchId? }` — 质检表单: AQL标准选择+检查项目清单+结果判断+缺陷照片上传
- **QualityReportDetail.vue** (v3): Props: `{ reportId }` — 质检报告详情: 检查项目结果表+缺陷照片+结果标签+纠正措施

**v1集成点**:
- [6]Partner表 — v1已有(合作伙伴→工厂管理)
- [6]Order表 — v1已有(订单→样品+质检关联)
- [4]production_batches表 — v1预留(批次→质检关联)
- rfq_requests / samples / quality_reports表 — v1预留

> **标注**: v1 rfq_requests/samples/quality_reports三张表已预留。Partner/Order模型已有。完整工厂对接管理待v3实现。

---

## 十二、补充前端组件规格 (v2-v3 约稿/工厂对接)

### 12.1 约稿管理 v2 组件

**CommissionKanban.vue** — 约稿看板

Props: `{ commissions: Commission[] }`

```
┌────────────────────────────────────────────────────────┐
│ 📋 约稿看板                                             │
├────────────────────────────────────────────────────────┤
│ 询价     │ 已确认     │ 制作中     │ 交付     │ 已结款  │
│ ──────── │ ──────── │ ──────── │ ──────── │ ──────── │
│          │ [项目A]   │ [项目B]   │          │ [项目C]  │
│ [项目D]  │ [项目E]   │ [项目F]   │ [项目G]  │          │
│          │            │          │          │          │
│          │            │ [拖拽]   │          │          │
└────────────────────────────────────────────────────────┘
```

- 拖拽卡片更新状态
- 每张卡片显示: 项目名称 + 客户名 + 截止日期 + 金额
- 逾期项目红色边框

**CommissionForm.vue** — 约稿创建/编辑表单

Props: `{ commission?: Commission }`

Steps:
1. **客户信息** — 选择已有客户/新建客户
2. **需求描述** — 标题 + 详细描述 + 参考图
3. **里程碑** — 添加里程碑(草图→线稿→上色→终稿) + 日期
4. **付款条款** — 定金比例 + 进度款 + 尾款
5. **确认** — 预览 + 创建

**CommissionCalendar.vue** — 约稿日历

Props: `{ commissions: Commission[] }`

- 月视图日历，标记截止日和里程碑日
- 截止日红色高亮，里程碑日黄色标记
- 点击日期显示当日事件列表

**CommissionDetail.vue** — 约稿详情

Props: `{ commissionId: string }`

```
┌────────────────────────────────────────────────────────┐
│ 📋 约稿: 《应龙》商业插画                               │
├────────────────────────────────────────────────────────┤
│ 客户: 张三 (XX文化公司)                                 │
│ 状态: [🟡 制作中]                                       │
│ 金额: ¥5,000 | 已付: ¥2,000 | 待付: ¥3,000             │
│                                                        │
│ 里程碑进度:                                             │
│ ● 草图 ✅ 6/1  ───○ 线稿 🟡 6/5 ───○ 上色 ○ 6/10 ───○ 终稿 ○ 6/15
│                                                        │
│ 修改记录:                                               │
│ [6/3] 客户反馈: 龙角需要更尖锐 → 已修改                 │
│ [6/7] 客户反馈: 背景颜色偏暗 → 已修改                   │
│                                                        │
│ [上传交付文件] [发起收款] [记录修改]                    │
└────────────────────────────────────────────────────────┘
```

**CommissionDashboard.vue** — 约稿仪表盘

Props: `{}`

- 统计卡片: 进行中/待收款/本月收入/平均客单价
- 收入趋势图 (月度)
- 逾期约稿列表 (红色警告)

### 12.2 工厂对接 v3 组件

**RFQManager.vue** — 询价单管理

Props: `{}`

- 询价单列表: 产品 + 工厂 + 数量 + 报价 + 状态
- 筛选: 状态(待报价/已报价/已接受/已拒绝) + 工厂
- "新建询价" 按钮 → 打开 RFQDetail

**RFQDetail.vue** — 询价详情

Props: `{ rfqId: string }`

```
┌────────────────────────────────────────────────────────┐
│ 📦 询价: T恤印花 × 华艺包装                             │
├────────────────────────────────────────────────────────┤
│ 产品: 《应龙》T恤设计                                  │
│ 数量: 500件                                            │
│ 材质: 纯棉 180g                                       │
│                                                        │
│ 报价对比:                                               │
│ ┌────────────┬────────┬──────┬───────┬───────────────┐ │
│ │ 工厂       │ 单价   │ 交期 │ MOQ   │ 状态          │ │
│ ├────────────┼────────┼──────┼───────┼───────────────┤ │
│ │ 华艺包装   │ ¥35/件 │ 7天  │ 100   │ ✅ 已接受     │ │
│ │ 精美印刷   │ ¥42/件 │ 5天  │ 50    │ ⏳ 待回复     │ │
│ │ 鑫达制造   │ ¥28/件 │ 10天 │ 500   │ ❌ 超出MOQ    │ │
│ └────────────┴────────┴──────┴───────┴───────────────┘ │
│                                                        │
│ [接受报价] [拒绝] [要求修改]                             │
└────────────────────────────────────────────────────────┘
```

**SampleTracker.vue** — 样品跟踪

Props: `{ orderId: string }`

```
┌────────────────────────────────────────────────────────┐
│ 🧪 样品跟踪: 订单 #ORD-2026-001                         │
├────────────────────────────────────────────────────────┤
│ 样品列表:                                               │
│ ┌────────────────────────────────────────────────────┐ │
│ │ 样品 #1 — 2026-06-15                              │ │
│ │ 状态: [✅ 已批准]                                  │ │
│ │ 照片: [缩略图1] [缩略图2] [缩略图3]               │ │
│ │ 工厂备注: 颜色略有偏差，已调整                      │ │
│ │ [查看详情] [要求修改]                              │ │
│ ├────────────────────────────────────────────────────┤ │
│ │ 样品 #2 — 2026-06-20 (大货样品)                    │ │
│ │ 状态: [⏳ 待寄出]                                  │ │
│ │ 预计寄出: 2026-06-25                              │ │
│ └────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
```

**QualityReportForm.vue** — 质检表单

Props: `{ orderId?: string, batchId?: string }`

```
┌────────────────────────────────────────────────────────┐
│ 🔍 质检报告创建                                         │
├────────────────────────────────────────────────────────┤
│ AQL 标准: [AQL 2.5 ▼]                                  │
│ 检查项目:                                              │
│ ☑ 颜色偏差 (标准: ΔE < 3)  → [通过] [不通过]          │
│ ☑ 尺寸误差 (标准: ±2cm)    → [通过] [不通过]          │
│ ☑ 缝线质量 (标准: 无脱线)  → [通过] [不通过]          │
│ ☑ 印花清晰度 (标准: 无模糊) → [通过] [不通过]          │
│ ☑ 包装完整性 (标准: 无损)   → [通过] [不通过]          │
│                                                        │
│ 缺陷照片: [📎 上传]                                    │
│ 备注: _______________________________________________  │
│                                                        │
│ [生成报告] [保存草稿]                                   │
└────────────────────────────────────────────────────────┘
```

**QualityReportDetail.vue** — 质检报告详情

Props: `{ reportId: string }`

- 检查项目结果表格
- 缺陷照片展示
- 结果标签 (PASS/FAIL/MARGINAL)
- 纠正措施记录

### 12.3 核心 v1 组件补齐

**PartnerManagement.vue** — 合作伙伴管理

Props: `{}`

```
┌────────────────────────────────────────────────────────┐
│ 👥 合作伙伴管理                                         │
├────────────────────────────────────────────────────────┤
│ 搜索: [合作伙伴 ______] [类型: [全部 ▼]] [筛选▼]       │
│                                                        │
│ ┌────────────────────────────────────────────────────┐ │
│ │ 🏭 华艺包装             [编辑] [删除]              │ │
│ │ 类型: 工厂 | 评分: ★★★★☆ | 材质: 纸制品            │ │
│ │ 联系人: 李经理 | 电话: ***-****-5678               │ │
│ │ 合作订单: 3 | 总交易额: ¥15,000                     │ │
│ ├────────────────────────────────────────────────────┤ │
│ │ 📦 印鸽POD              [编辑] [删除]              │ │
│ │ 类型: POD平台 | 评分: ★★★★★ | 品类: 全品类        │ │
│ │ 合作订单: 12 | 总交易额: ¥45,000                    │ │
│ └────────────────────────────────────────────────────┘ │
│                                                        │
│ [+ 添加合作伙伴]                                        │
└────────────────────────────────────────────────────────┘
```

**OrderManagement.vue** — 订单管理

Props: `{}`

```
┌────────────────────────────────────────────────────────┐
│ 📦 订单管理                                             │
├────────────────────────────────────────────────────────┤
│ 筛选: [全部状态 ▼] [类型: [全部 ▼]] [伙伴: [全部 ▼]]   │
│                                                        │
│ ┌────────────────────────────────────────────────────┐ │
│ │ #ORD-2026-001        [🟡 生产中]                    │ │
│ │ 华艺包装 | T恤印花 × 500件                          │ │
│ │ 金额: ¥17,500 | 定金: ¥5,250 ✅ | 尾款: ¥12,250    │ │
│ │ 期望: 6/20 | 实际: —                                │ │
│ │ [查看详情] [更新状态] [记录付款]                    │ │
│ ├────────────────────────────────────────────────────┤ │
│ │ #ORD-2026-002        [🟢 已完成]                   │ │
│ │ 印鸽POD | 马克杯 × 200件                           │ │
│ │ 金额: ¥6,000 | 已付清 ✅                            │ │
│ │ 完成: 6/15                                        │ │
│ │ [查看详情] [评价]                                  │ │
│ └────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
```
