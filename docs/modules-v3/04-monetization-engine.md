# [4] 商业撮合平台 — 详细功能设计 v4

> **定位**: AI 时代的创作者商业撮合平台。连接创作者·供应商·工厂三方，纯工具平台，不碰交易和资金。v1聚焦插画师/AIGC艺术家，6条变现路径 × 100+产品品类。
> **最后更新**: 2026-06-23 (P2 全面重构: 四层架构 Design→Template→Listing→Publication, 规格校验阻断+修复建议, 兼容产品推荐, 产品详情页)

---

## 一、v1 创作者类型支持声明

| 变现路径 | 插画师 v1 | 摄影师 | 手工 | 音乐 | 文字 |
|---------|-----------|--------|------|------|------|
| 🖨️ POD渠道管理 | ✅ 完整 | 规划中 | 规划中 | — | — |
| 📱 数字产品 | 规划中 P2 | 规划中 | — | 规划中 | 规划中 |
| 🚀 众筹管理 | ✅ 完整 | 规划中 | 规划中 | 规划中 | 规划中 |
| 📜 IP授权 | ✅ 完整 | 规划中 | 规划中 | 规划中 | 规划中 |
| 👑 订阅/会员 | 🔵 规划中 P2 | — | — | 规划中 P2 | 规划中 P2 |
| 🤝 定制商单 | 规划中 P2 | 规划中 P2 | 规划中 P2 | 规划中 P2 | 规划中 P2 |

> **注**: v1 聚焦 4 条核心路径(POD/众筹/IP授权/收入追踪)。订阅会员和定制商单为 P2 规划功能。

---

## 一、核心概念：四层架构

```
Design File (作品/设计稿)
  ↓ 关联
Product Template (产品模板 — 物理规格定义)
  ↓ 组合
Listing (商品 — 设计稿 + 产品模板 + 定价)
  ↓ 分发
Publication (发布记录 — 商品在各平台的上线状态)
```

**各层职责：**

| 层级 | 实体 | 职责 | 类比 |
|------|------|------|------|
| 设计稿 | `works.id` | 原始创作文件（图片/视频/音频） | 一幅画 |
| 产品模板 | `product_templates` | 物理规格定义（尺寸/DPI/出血/材质） | T恤的印花区域规格 |
| 商品 | `design_listings` | 设计稿 × 产品模板 × 定价 | "我的画印在这件T恤上卖¥129" |
| 发布记录 | `publication_records` | 商品在各平台的上线状态 | "这件T恤已发布到Printful" |

**关键关系：**
- 一个 Design File → 多个 Listing（同一幅画印在不同产品上）
- 一个 Product Template → 多个 Listing（同一款T恤被不同设计使用）
- 一个 Listing → 多个 Publication（同一件商品发布到多个平台）
- 一个 Listing → 0或多个 Crowdfunding Reward
- 一个 Listing → 0或多个 IP License

## 二、用户场景

### 场景A：林山海(插画师)把《应龙》印在T恤上
```
林山海: "这幅《应龙》刚画完，想印在T恤上卖"
系统: 打开设计器 → 选作品《应龙》→ 选路径"POD渠道管理"→ 选品类"T恤"
系统: Canvas默认模式展示扁平叠加效果
      (如Printful API可用，Switch切换到照片级预览)
林山海: "放大一点，往下挪...黑色T恤也看看"
系统: 切换黑色底图，设计稿位置保持
林山海: "规格检查过了吗？"
系统: DPI 300 ✅ | 尺寸 4500×5400 ✅ | 色彩 sRGB ✅
      建议: 输出成品尺寸 12×16 inch @ 300 DPI
林山海: "成本多少？"
系统: 参考成本¥45，平台抽成估算¥12.9，建议售价¥99-199，利润¥41-141
林山海: "定价¥129，创建"
系统: 产品创建 → 效果图保存 → 列表出现"应龙T恤 ¥129"
```

### 场景B：林山海发起《山海经》系列众筹
```
林山海: "我想把《山海经》系列做成限定版画众筹"
系统: 进入众筹创建向导 → 选平台(摩点/Kickstarter) → 设目标金额
系统: AI建议目标 ¥80,000 (基于: 成本¥32,000 + 平台费¥6,400 + 物流¥8,000 + 缓冲¥10,000 + 预期利润¥23,600)
林山海: "设置三个档位"
系统: 早鸟版画 ¥199 × 限量100 → 全套8张签名版 ¥899 × 限量20 → 幕后故事电子版 ¥29
林山海: "上传项目封面和宣传图"
系统: 自动检测封面图规格(3000×2000px, ≥300DPI ✅)
林山海: "发布"
系统: 众筹项目创建 → 状态"筹备中" → 定时提醒"距离发布还有3天"
```

### 场景C：某公司将《麒麟》用于包装设计
```
采购方: "我想用你的《麒麟》做产品包装，需要商业扩展授权"
系统: 林山海收到授权询价通知 → 查看对方需求
林山海: "单次使用还是无限期？用在中国还是全球？"
采购方: "全球范围，1年期，单次商业用途"
系统: AI生成授权合约草案 → 推荐价格 ¥3,500 (基于作品价值+使用范围+期限)
林山海: "同意，发送合约"
系统: 生成PDF合约 → 双方电子签名 → 收款 → 授权记录归档
```

### 场景D：创作者发布设计需求，供应商接单
```
林山海: "我的《山海经》系列需要一套包装设计方案"
系统: 发布需求 → 填写技能要求(插画/包装)、预算、截止日
供应商A: 收到需求通知 → 查看需求 → 提交方案和报价 ¥2,000
系统: 通知林山海有新报价 → 展示供应商A作品集+样品
林山海: "方案不错，确认合作"
系统: 创建订单 → 供应商交付设计稿 → 林山海确认 → 付款给供应商(系统不碰资金，仅记录)
```

---

## 三、功能架构

```
商业撮合平台
├── 📊 变现仪表盘 (统计卡片+趋势图+分布图+最近产品+AI洞察)
├── 🎨 产品设计器 (7步向导: 选作品→路径→品类→效果→规格→定价→创建)
│   ├── Step 1: 选设计稿 (从作品库选择)
│   ├── Step 2: 选变现路径 (6条路径卡片)
│   ├── Step 3: 选产品品类 (60+品类，按材质/路径过滤)
│   ├── Step 4: 效果预览 (Canvas平面 → Printful照片级 → AI增强)
│   ├── Step 5: 规格校验 (DPI/尺寸/色彩/格式/透明度)
│   ├── Step 6: 智能定价 (成本计算 + 竞品分析 + AI建议)
│   └── Step 7: 创建产品 (表单 + 效果图 + 发布)
├── 📦 产品管理 (列表+筛选+CRUD+批量操作+数据看板)
├── 🚀 众筹管理 (项目CRUD+档位设计+进度追踪+状态流转+报表)
│   ├── 众筹创建向导
│   ├── 奖励档位设计 (模板库+自定义)
│   ├── 目标金额计算器 (成本/物流/平台费自动计算)
│   ├── 进度追踪 (资金/支持者/履约)
│   ├── 解锁目标 (Stretch Goals)
│   └── 报表导出 (CSV/PDF)
├── 📜 IP授权管理 (授权CRUD+类型/范围/期限/费用+到期提醒+合约模板)
│   ├── 授权类型 (单次/多次/商业扩展/买断)
│   ├── 授权范围 (用途/地域/期限/媒介)
│   ├── 智能定价 (基于作品价值×使用系数)
│   ├── 合约生成 (PDF + 电子签名)
│   └── 到期预警 (30天/7天/过期)
├── 🖨️ POD渠道管理 (创建→预览→规格校验→发布→URL记录→追踪)
│   ├── 平台连接器 (Printful/印鸽/Redbubble/Printify/Society6/Gelato)
│   ├── 一键跳转发布 (打开平台上传页)
│   ├── URL记录与校验
│   ├── 销售状态追踪 (手动/CSV导入)
│   └── 多平台对比 (同类目不同平台成本/定价/抽成对比)
├── 👑 订阅/会员 (规划中 P2: 创作者订阅/会员等级/独家内容)
├── 🤝 定制商单 (规划中 P2: Brief管理→方案→制作→交付→结算)
├── 🏭 按需制造 (规划中: 工厂管理+询价+样品+订单)
├── 📱 数字产品 (规划中: 文件上传+定价+下载链接+DRM)
├── 💰 收入追踪 (手动登记+CSV导入+自动汇总+利润计算+图表+AI分析)
├── 🛡️ 商业安全 (防抄袭水印+授权合约+使用追踪)
└── 🤖 AI商业助手 (定价建议+路径推荐+竞品分析+市场趋势)
```

---

## 四、商业撮合平台 — 三方协作架构 (新增)

### 4.1 核心概念：创作者·供应商·工厂 三方协作

商业撮合平台不只是让创作者自己卖东西，更是连接创作者、供应商、工厂的纯工具平台。

```
┌──────────────────────────────────────────────────────────────┐
│                    商业撮合平台 (纯工具)                        │
│                                                              │
│  ┌──────────┐    需求发布    ┌──────────┐    报价接单    ┌──────────┐
│  │ 创作者    │ ───────────▶ │ 供应商    │ ───────────▶ │ 工厂      │
│  │ (设计稿)  │ ◀─────────── │ (设计/    │ ◀─────────── │ (生产)    │
│  │          │   设计确认    │  打样)     │   生产确认   │          │
│  └──────────┘              └──────────┘              └──────────┘
│       │                        │                        │
│       │   产品上架/分销        │   按需生产             │   发货交付
│       ▼                        ▼                        ▼
│  ┌──────────────────────────────────────────────────────────┐
│  │              终端消费者 (平台不碰交易和资金)                │
│  └──────────────────────────────────────────────────────────┘
└──────────────────────────────────────────────────────────────┘
```

**三方角色定义**：

| 角色 | 职责 | 系统功能 |
|------|------|---------|
| **创作者** | 提供设计稿、发布需求 | 作品管理、产品设计器、需求发布 |
| **供应商** | 提供设计服务、打样、中间环节 | 供应商入驻、报价管理、样品管理 |
| **工厂** | 生产、仓储、物流 | 工厂管理、询价、订单路由、质检 |

**平台中立原则**：系统只做信息撮合工具，不处理资金流转，不碰交易。

### 4.2 供应商角色扩展 (新增 v1)

v1 新增供应商角色，支持以下场景：
- 创作者找不到合适的设计师 → 发布需求，供应商接单
- 工厂需要设计 → 联系供应商提供设计稿
- 供应商提供打样服务 → 创作者确认样品后下单生产

**数据模型扩展**：

```sql
-- 扩展 partners 表
ALTER TABLE partners ADD COLUMN partner_role TEXT DEFAULT 'client';
-- 'supplier' / 'factory' / 'client' / 'licensee'

-- 新增：供应商档案表
CREATE TABLE IF NOT EXISTS supplier_profiles (
    id TEXT PRIMARY KEY,
    partner_id TEXT NOT NULL REFERENCES partners(id),
    specialties JSON,              -- ['illustration', 'packaging', '3d_render']
    portfolio_urls JSON,           -- ['behance.net/xxx', ...]
    sample_gallery JSON,           -- [{'name': 'T恤印花', 'image': 'data/xxx.jpg'}, ...]
    lead_time_days INTEGER,        -- 平均交付周期
    min_order_quantity INTEGER,    -- 最小起订量
    certification TEXT,            -- 资质认证
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 新增：需求发布表
CREATE TABLE IF NOT EXISTS design_requests (
    id TEXT PRIMARY KEY,
    creator_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    required_skills JSON,          -- ['illustration', 'packaging_design']
    budget_min FLOAT,
    budget_max FLOAT,
    deadline DATE,
    status TEXT DEFAULT 'open',    -- 'open' / 'in_negotiation' / 'awarded' / 'closed'
    awarded_to TEXT REFERENCES supplier_profiles(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 新增：询价表
CREATE TABLE IF NOT EXISTS inquiries (
    id TEXT PRIMARY KEY,
    design_request_id TEXT REFERENCES design_requests(id),
    factory_id TEXT REFERENCES partners(id),
    product_template_id TEXT,
    quantity INTEGER,
    material TEXT,
    special_requirements TEXT,
    quoted_price FLOAT,
    quote_deadline DATE,
    status TEXT DEFAULT 'pending', -- 'pending' / 'quoted' / 'accepted' / 'rejected'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 4.3 前端组件 (新增)

| 组件 | Props | 说明 |
|------|-------|------|
| `SupplierMarketplace.vue` | — | 供应商市场：浏览供应商档案 + 作品集 + 报价 |
| `DesignRequestForm.vue` | `{ creatorId: string }` | 发布设计需求表单 |
| `InquiryWizard.vue` | `{ designRequestId: string }` | 询价向导：选工厂→选产品→填数量→提交 |

### 补充前端组件规格

**SupplierMarketplace.vue** — 供应商市场

Props: `{}`

```
┌────────────────────────────────────────────────────────┐
│ 🔗 供应商市场                                          │
├────────────────────────────────────────────────────────┤
│ 搜索: [设计师/供应商 ______] [技能: [插画 ▼]] [筛选▼]  │
│                                                        │
│ ┌────────────────────────────────────────────────────┐ │
│ │ 🏆 设计师A                                         │ │
│ │ 专长: 插画 / 包装设计 / 3D渲染                     │ │
│ │ 评分: ★★★★☆ (4.5/5)  交付周期: 5天                │ │
│ │ 作品集: [样图1] [样图2] [样图3] [查看更多→]       │ │
│ │ 报价范围: ¥500-¥3000/项目                          │ │
│ │ [查看档案] [发布需求]                              │ │
│ ├────────────────────────────────────────────────────┤ │
│ │ 🏆 设计师B                                         │ │
│ │ 专长: UI设计 / 品牌设计                            │ │
│ │ 评分: ★★★★★ (4.8/5)  交付周期: 3天                │ │
│ │ 作品集: [样图1] [样图2] [样图3] [查看更多→]       │ │
│ │ 报价范围: ¥1000-¥5000/项目                         │ │
│ │ [查看档案] [发布需求]                              │ │
│ └────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
```

Events: `@view-profile(partnerId)`, `@post-request(partnerId)`

**DesignRequestForm.vue** — 发布设计需求表单

Props: `{ creatorId: string }`

Steps:
1. **需求描述** — 标题 + 详细描述 + 参考图上传
2. **技能要求** — 多选: 插画/包装设计/3D渲染/UI设计/品牌设计
3. **预算范围** — 最小值/最大值 + 货币
4. **截止时间** — 日期选择器 + 提醒
5. **确认发布** — 预览 + 发布

```
┌────────────────────────────────────────────────────────┐
│ 📝 发布设计需求 (Step 1/5)                              │
├────────────────────────────────────────────────────────┤
│ 需求标题: [《山海经》系列包装设计需求 ___]              │
│ 详细描述:                                              │
│ ┌────────────────────────────────────────────────────┐ │
│ │ 需要一位有经验的包装设计师，为我们的《山海经》      │ │
│ │ 系列插画设计一套产品包装。                          │ │
│ │                                                     │ │
│ │ 要求:                                               │ │
│ │ - 中国传统风格                                      │ │
│ │ - 适用于茶叶礼盒                                    │ │
│ │ - 需提供源文件和成品文件                            │ │
│ └────────────────────────────────────────────────────┘ │
│ 参考图: [📎 上传参考图] (已选 2 张)                     │
│                                                        │
│ [上一步] [下一步: 技能要求]                             │
└────────────────────────────────────────────────────────┘
```

Events: `@next(stepData)`, `@prev`, `@cancel`, `@submit(success)`

**InquiryWizard.vue** — 询价向导

Props: `{ designRequestId: string }`

Steps:
1. **选择工厂** — 工厂列表（按评分/交期/价格排序）
2. **选择产品** — 关联的产品模板/设计稿
3. **填写数量** — MOQ 检查 + 数量输入
4. **特殊要求** — 材质/工艺/包装备注
5. **确认提交** — 预览询价单 + 提交

```
┌────────────────────────────────────────────────────────┐
│ 🔎 询价 (Step 1/5: 选择工厂)                            │
├────────────────────────────────────────────────────────┤
│ 推荐工厂 (按匹配度排序):                                │
│ ┌────────────────────────────────────────────────────┐ │
│ │ 🏭 华艺包装 (匹配度 95%)                            │ │
│ │ 资质: ISO9001 | 材质: 纸制品 | 交期: 7天           │ │
│ │ MOQ: 100件 | 价格范围: ¥5-¥15/件                   │ │
│ │ ○ 选择此工厂                                       │ │
│ ├────────────────────────────────────────────────────┤ │
│ │ 🏭 精美印刷 (匹配度 88%)                            │ │
│ │ 资质: ISO14001 | 材质: 综合 | 交期: 5天            │ │
│ │ MOQ: 50件 | 价格范围: ¥8-¥20/件                    │ │
│ │ ○ 选择此工厂                                       │ │
│ └────────────────────────────────────────────────────┘ │
│                                                        │
│ [上一步] [下一步: 选择产品]                             │
└────────────────────────────────────────────────────────┘
```

Events: `@select-factory(factoryId)`, `@next(stepData)`, `@prev`, `@submit(inquiryData)`

**CreatorTierBadges.vue** — 创作者等级徽章

Props: `{ tier: 'novice' | 'pro' | 'master', salesCount: number, rating: number }`

```
┌────────────────────────────────────────────────────┐
│ 🏅 创作者等级                                       │
│                                                    │
│ 当前等级: [Pro 专业创作者]                          │
│ 经验值: ████████░░ 750/1000 XP                     │
│                                                    │
│ 升级进度:                                           │
│ • 完成 5 个产品 → ✅ (5/5)                         │
│ • 月均收入 ¥2000+ → ✅ (¥3500)                     │
│ • 好评率 90%+ → ✅ (95%)                           │
│                                                    │
│ 升到 Master 后可享受:                               │
│ • 更低平台手续费                                    │
│ • 优先推荐曝光                                      │
│ • 专属客服通道                                      │
└────────────────────────────────────────────────────┘
```

---

## 五、产品设计器 7步向导 (增强版)

**向导UI规范** (遵循UX规范4.3):
- **步骤指示器**: 顶部水平步骤条，显示7步名称+编号，已完成步骤可点击回退
- **草稿保存**: 当前步骤数据自动存入 Pinia store (`useProductDesignerStore`)，页面刷新/关闭后恢复
- **关闭确认**: 关闭向导时弹出Modal "确认离开？当前设计草稿已自动保存"
- **加载状态**: Printful API 调用时显示蓝色 Spinner + "正在生成照片级预览..."
- **错误降级**: Printful API 失败时自动降级到 Canvas 平面预览 + Toast "照片级预览暂不可用，已切换至平面预览"
- **智能推荐**: 每步底部显示 AI 推荐按钮，提供个性化建议

### Step1: 选设计稿
- 从[1]创意资产中心作品库获取，网格展示缩略图+标题+尺寸+版权状态
- v1按图片类型自动筛选（插画师默认显示图片）
- 搜索+类型筛选+版权状态筛选，选中高亮
- **新增**: 显示作品存证状态(Verified Badge)，已存证作品优先推荐

### Step2: 选变现路径
6条路径卡片 (v1非插画路径标注"规划中"):

| 路径 | v1状态 | 适合 | 特点 |
|------|--------|------|------|
| 🖨️ POD渠道管理 | ✅ | 插画/摄影 | 零库存，手动上架+链接追踪 |
| 📱 数字产品 | 🔵规划中 | — | 零物流，壁纸/素材/预设 |
| 🚀 众筹 | ✅ | 插画 | 验证需求，系列盲盒/限定版画 |
| 📜 IP授权 | ✅ | 插画 | 持续收入，角色/图案授权 |
| 👑 订阅/会员 | 🔵规划中 | — | 稳定现金流，粉丝经济 |
| 🤝 定制商单 | 🔵规划中 | — | 高单价，一对一沟通 |
| 🏭 供应商市场 | **✅ (新增)** | 全类型 | 创作者·供应商·工厂三方撮合 |

### Step3: 选产品品类
100+品类按材质分类（纸质印刷/纺织服装/硬质家居/数字产品/手工精品），按Step2路径过滤。每个品类显示: 图标+名称+参考成本+建议售价+POD平台+适用变现路径标签

### Step4: 效果预览 — 三层方案

#### 方案A: Canvas 扁平叠加 (默认)
- HTML5 Canvas: 产品模板底图 + 设计稿叠加
- 拖拽调整位置 / 滚轮缩放(0.5x-3x) / 颜色切换
- 预设模板: T恤(白/黑/灰)、卫衣、帆布袋、马克杯、手机壳、海报、贴纸
- 导出: Canvas.toDataURL() → Blob

**UI标注**: "平面效果预览，非真实产品照片"

#### 方案B: Printful Mockup API (增强 P1)
- 接入 Printful Mockup Generator API
- 返回照片级产品效果图 (JPEG)
- API 不可用时自动降级到方案A
- 用户可切换: [平面预览] | [照片级预览(Printful)]

#### 方案C: AI 增强预览 (P1.5)
- 调用 Ollama/ComfyUI 生成产品场景化预览
- 支持多种风格: realistic/minimal/cartoon/studio
- 生成文字描述 + PIL 占位图

### Step5: 规格校验 (增强版 — P2)

**校验结果处理策略：**

| 结果 | 前端行为 | 用户操作 |
|------|---------|---------|
| pass | 绿色横幅，放行 | 直接进入 Step 6 |
| warning | 黄色横幅，显示 N 项警告 | 可继续，不影响创建 |
| error | 红色横幅，阻断 | 显示 SpecRemediationPanel，必须勾选覆盖才能继续 |

**SpecRemediationPanel 内容：**

```
┌──────────────────────────────────────────────────────────┐
│ ❌ 规格校验未通过 (3 项错误)                                │
│                                                          │
│ ✅ 以下产品可以使用此设计稿:                                │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐                      │
│ │ 贴纸     │ │ 明信片   │ │ 书签     │                     │
│ │ 匹配度 95%│ │ 匹配度 88%│ │ 匹配度 82%│                    │
│ │ 需要 ≥76x76px│ │ 需要 ≥148x105px│ │ 需要 ≥50x148px│           │
│ └─────────┘ └─────────┘ └─────────┘                      │
│                                                          │
│ 🔧 修复建议:                                               │
│ 📐 尺寸: 当前 50x50px → 需要 1771x590px (需放大 35x)       │
│ 🔍 DPI: 当前 未知 → 需要 ≥200 DPI                         │
│ 🎨 色彩: 当前 JPG → 需要 PNG (保留透明)                    │
│                                                          │
│ ☑ 我已知晓规格不达标，仍要创建此商品    [确认继续]           │
└──────────────────────────────────────────────────────────┘
```

**API 支持：**
- `POST /supply/spec-validate` — 校验单个品类（响应中增加 `compatible_categories` 字段）
- `POST /supply/spec-validate-compat` — 给定设计稿规格，返回所有兼容产品排名
- `POST /supply/spec-validate-remediation` — 返回具体修复建议（尺寸/DPI/格式/色彩）

### Step6: 智能定价 (增强版)

**定价公式**:
```
成本价 = 品类基础成本 + 平台抽成(按平台费率%) + 物流成本
建议售价 = 成本价 × (1 + 目标利润率%)
AI推荐售价 = f(成本价, 竞品均价, 作品价值评分, 目标市场购买力)
```

**竞品分析** (P2.5新增):
- 自动搜索同类目热门产品价格区间
- 基于作品存证等级/粉丝数/历史销量给出溢价系数
- 显示"低于均价/合理/高于均价"标签

**定价计算器交互**:
```
┌──────────────────────────────────────────────┐
│  智能定价引擎                                 │
│                                              │
│  品类基础成本: ¥45 (T恤, Gildan 5000)         │
│  平台抽成:     ¥12.9 (Printful, 约10%)        │
│  物流成本:     ¥8.0 (国内快递)                │
│  ──────────────────────────────               │
│  总成本:       ¥65.9                          │
│                                              │
│  竞品均价:     ¥89 - ¥159                     │
│  作品价值评分: ★★★★☆ (存证+粉丝500+)          │
│                                              │
│  AI建议售价:   ¥119 - ¥169                    │
│  预估利润率:   81% - 157%                     │
│                                              │
│  自定义售价:   [¥129    ]                     │
│  预估利润:     ¥63.1 / 件                     │
│  利润率:       96%                            │
│                                              │
│  💡 提示: 早鸟价可设 ¥99 吸引首批支持者        │
└──────────────────────────────────────────────┘
```

### Step7: 创建产品
表单: 标题/描述/渠道/可见性/定价 → 效果图上传 → POST /api/supply/products
→ 后续可选跳转到 POD渠道管理 Step

---

## 五、POD渠道管理 (增强版)

### 5.1 能力边界诚实声明

> **POD渠道管理** 提供产品创建→预览→规格校验→选平台→一键跳转→手动上架→记录商品URL→追踪状态。**v1不支持**: 自动同步库存、自动同步订单、API级全自动上架、平台间自动同步。

### 5.2 完整工作流 (增强)

```
[产品设计完成]
  → 选择目标POD平台 (Printful / Redbubble / Printify / 印鸽 / Society6 / Gelato)
  → 系统展示: 平台规格要求 / 设计稿适配检查结果
  → 系统提供: 一键跳转按钮 → 打开平台上传页面
  → 用户手动: 上传设计稿、填写信息、发布
  → 用户回到系统: 粘贴平台商品URL
  → 系统校验URL格式有效性 → Toast "商品链接已记录 ✅"
  → 系统自动: 记录平台URL、创建监控记录
  → 如72小时后未粘贴URL → 推送提醒通知 "您的[产品名]尚未记录平台链接"
  → 定期: 提示用户更新销售状态 (手动/CSV导入)
  → 系统提供CSV导入模板: 兼容 Printful/Redbubble 等平台导出格式
  → [P2] 自动同步: 通过平台API定期拉取销售和订单数据
```

### 5.3 各平台对接状态

| 平台 | API对接 | 手动上架 | v1状态 | 佣金率 | 优势 |
|------|---------|---------|--------|--------|------|
| Printful | 产品目录API(读) + Mockup API(P1) | URL记录 | ✅ | ~$0 (按件计费) | 质量稳定，全球仓 |
| Printify | 无API | URL记录 | ✅ | ~$0 (按件计费) | 价格更低 |
| Redbubble | 无API | URL记录 | ✅ | 15-20% | 自带流量 |
| Society6 | 无API | URL记录 | ✅ | 10% | 艺术调性 |
| 印鸽 | 如有开放API同Printful | URL记录 | ✅ | 10-15% | 国内物流 |
| Gelato | 如有API评估接入 | URL记录 | ✅ | ~$0 (按件计费) | 100+国家本地打印 |

### 5.4 多平台对比工具 (P2新增)

选择品类后，系统自动展示各平台对比:
```
┌────────────┬──────────┬──────────┬──────────┬──────────┐
│   指标      │ Printful │ Printify │ Redbubble│   印鸽   │
├────────────┼──────────┼──────────┼──────────┼──────────┤
│ 基础成本    │  ¥45.00  │  ¥38.00  │  ¥42.00  │  ¥35.00  │
│ 物流(国内)  │  ¥12.00  │  ¥10.00  │   —      │   ¥6.00  │
│ 平台抽成    │   0%     │   0%     │  15-20%  │  10-15%  │
│ 建议售价    │  ¥99-159 │ ¥89-149  │ ¥69-119  │ ¥59-109  │
│ 预估利润/件 │  ¥42-101 │ ¥41-101  │ ¥30-70   │ ¥18-68   │
│ 自带流量    │   ❌     │   ❌     │   ✅     │   ❌     │
│ 全球覆盖    │   ✅     │   ✅     │   ✅     │   ❌     │
└────────────┴──────────┴──────────┴──────────┴──────────┘
```

---

## 六、众筹管理 (增强版)

### 6.1 数据模型 (增强)

```sql
campaigns:
  id, title, description, platform(modian/kickstarter/indiegogo/patreon),
  goal_amount, currency, raised_amount, backer_count,
  reward_tiers(JSON: [{name, price, description, limit, sold, shipping_cost, estimated_delivery}]),
  stretch_goals(JSON: [{threshold, unlock_description}]),
  launch_date, end_date, estimated_delivery_date, actual_delivery_date,
  status(draft→launching→funded/successful→fulfilling→completed),
  related_product_ids, related_work_ids,
  media_assets(JSON: [{type, url, caption}]),  -- 封面图/宣传视频/进度更新图
  marketing_url,  -- 外部推广链接
  created_at, updated_at
```

### 6.2 奖励档位设计 (增强)

**模板库** (已实现于后端):
- 基础三档: 早鸟支持 → 标准档 → 豪华档
- POD预定模式: 单品档 → 组合档 → 全套档
- 数字产品模式: 基础包 → 完整包 → 终身会员
- 粉丝建设模式: 关注者 → 支持者 → 赞助者 (Patreon风格)
- 解锁目标模式: 标准支持 → 收藏版 → 终极版

**定价策略建议** (AI驱动):
- 早鸟价: 标准价 70-85%
- 限时限量: 前N名享受特别价
- 捆绑优惠: 多档位组合折扣
- Shipping-aware: 不同地区差异化运费

### 6.3 目标金额计算器 (增强)

```
输入:
  - 档位列表 (名称, 价格, 预估支持者数)
  - 制造成本 (单件)
  - 物流成本 (单件, 按地区)
  - 平台费率 (%)
  - 支付处理费 (%)
  - 缓冲比例 (%)

输出:
  - 预估总收入
  - 平台费用
  - 总成本 (制造+物流+平台费)
  - 盈亏平衡点
  - 建议目标金额 (含缓冲)
  - 预期净利润
```

### 6.4 进度追踪 (增强)

- 资金进度: 进度条 + 百分比 + 距目标差额
- 支持者数: 实时计数
- 档位售罄: 自动标记"售罄"标签
- 解锁目标: 可视化展示进度
- 履约进度: 每个支持者的订单状态追踪

### 6.5 状态流转

```
draft (草稿)
  → launching (进行中) ← 可回退到 draft
    → funded (达成目标) ← 可回退到 launching
      → successful (成功结束)
    → failed (未达成目标)
  → fulfilling (履行中) ← funded 后进入
    → completed (已完成) ← fulfilling 后进入
```

---

## 七、IP授权管理 (增强版)

### 7.1 数据模型 (增强)

```sql
licenses:
  id, work_id(FK),
  license_type(single_use/multi_use/commercial_extended/buyout/custom),
  platform,  -- creative_fabrica/creative_market/gumroad/envato/custom
  allowed_uses(JSON),  -- [personal, commercial, resale, modification, print_limit:N]
  restrictions(JSON),  -- [no_resale, attribution_required, geographic_limit, term_limit]
  scope: {
    usage_type: string,       -- personal/commercial/resale/modify
    geographic_scope: string, -- local/national/global
    duration: string,         -- 1year/perpetual/limited
    medium: string,           -- digital/print/web/social_merchandise
    print_run_limit: int,     -- 印刷数量限制
    revenue_cap: decimal,     -- 收益上限
  },
  price, currency,
  platform_listing_id, platform_listing_url,
  contract_template(JSON),  -- 合约模板
  contract_signed BOOLEAN,  -- 是否已签署
  contract_signed_at DATETIME,
  contract_party_name VARCHAR(200),  -- 被授权方
  contract_party_email VARCHAR(200),
  sales_count, total_revenue,
  status(active/expired/revoked/pending),
  created_at, updated_at
```

### 7.2 授权类型详解

| 类型 | 英文 | 价格区间 | 适用场景 | 限制 |
|------|------|---------|---------|------|
| 单次使用 | Single Use | ¥35-350 | 个人项目/社交媒体 | 仅限1次使用，不可转售 |
| 多次使用 | Multi-Use | ¥350-3,500 | 商业营销/多项目 | 可在多个项目中使用 |
| 商业扩展 | Commercial Extended | ¥700-7,000 | 转售产品/ merchandise | 可用于转售商品 |
| 买断 | Buyout | ¥7,000+ | 独家使用权转让 | 创作者放弃部分权利 |
| 自定义 | Custom | 面议 | 企业级授权 | 按需求定制 |

### 7.3 智能定价引擎

```
授权价格 = 基础价格 × 使用范围系数 × 地域系数 × 期限系数 × 媒介系数

系数参考:
  使用范围: personal=1.0, commercial=2.5, resale=5.0, buyout=20.0
  地域: local=1.0, national=1.5, global=2.0
  期限: 1year=1.0, 3years=1.5, perpetual=2.5
  媒介: digital=1.0, print=1.3, merchandise=2.0, broadcast=3.0
```

### 7.4 合约生成 (P2新增)

- 自动生成标准授权合约PDF
- 支持电子签名 (对接第三方签名服务)
- 合约模板库: 单次使用/多次使用/商业扩展/买断
- 合约到期提醒: 30天/7天/过期

### 7.5 到期提醒

- 到期前30天: 邮件通知创作者
- 到期前7天: 站内通知 + 邮件
- 过期后: 标记为 expired，通知双方

---

## 八、变现仪表盘 (增强版)

### 8.1 布局

```
┌─────────────────────────────────────────────────────────────────┐
│  📊 变现仪表盘                                                   │
├─────────────────────────────────────────────────────────────────┤
│  [总收入]  [总产品]  [总订单]  [活跃渠道]  [本月收入]  [ROI]     │  ← 6个StatCard
│                                                                  │
│  ┌─────────────────────┐  ┌─────────────────────┐               │
│  │  📈 月收入趋势       │  │  🥧 按路径分布       │               │
│  │  (ECharts折线图)     │  │  (ECharts饼图)       │               │
│  └─────────────────────┘  └─────────────────────┘               │
│                                                                  │
│  ┌─────────────────────┐  ┌─────────────────────┐               │
│  │  📊 按平台收入       │  │  🏆 Top 10 产品      │               │
│  │  (ECharts柱状图)     │  │  (列表+收入排序)      │               │
│  └─────────────────────┘  └─────────────────────┘               │
│                                                                  │
│  ┌─────────────────────────────────────────────────┐             │
│  │  🤖 AI 商业洞察                                   │             │
│  │  "你的POD产品平均利润率82%，高于行业均值65%。"    │             │
│  │  "建议尝试IP授权路径，你的《山海经》系列估值¥2000+"│             │
│  │  "Redbubble自带流量，建议将30%产品上架到该平台"   │             │
│  └─────────────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 AI商业洞察 (P2新增)

基于创作者的数据，AI自动分析并生成:
- 利润率分析 (vs 行业基准)
- 路径优化建议 (哪些路径表现好，哪些需要改进)
- 定价建议 (基于历史销售数据)
- 市场趋势 (哪些品类/风格受欢迎)
- 风险预警 (授权即将到期、众筹履约延迟等)

---

## 九、产品管理 (增强版 — P2 重构)

### 9.1 概念澄清

P2 起，"产品管理" = "商品管理 (Listing Management)"。

**设计器 (Wizard)** 是"创建"入口，**产品管理 (Listings)** 是"管理"入口，两者最终汇聚到 **产品详情页**。

### 9.2 导航结构

```
商业撮合平台 (/app/supply)
├── 📊 仪表盘 (Dashboard)
├── 📦 我的产品 (Listings) ← 核心入口
│   ├── 产品列表 (grid + list, 按路径/材质/平台/状态筛选)
│   └── 产品详情页 (/app/supply/listings/:id)
│       ├── 设计稿预览 + 基本信息
│       ├── 变现路径子 Tab:
│       │   ├── 🖨️ POD发布 (publication_records)
│       │   ├── 🚀 众筹档位 (campaigns)
│       │   ├── 📜 IP授权 (licenses)
│       │   ├── 💰 收入追踪 (revenue_records)
│       │   └── 📋 相关订单 (orders)
│       └── 操作: 编辑 / 删除 / 复制为新商品
├── 🎨 设计转产品 (Wizard)
├── 🏗️ 产品库 (Templates Browser)
├── 🏭 工厂与合作伙伴
├── 📋 订单管理
└── 🤖 AI顾问
```

### 9.3 产品详情页

每个商品详情页展示该商品在所有变现路径下的状态：

```
┌─────────────────────────────────────────────────────────────┐
│  📦 商品详情: 《山海经·应龙》T恤                              │
│  [编辑] [删除] [复制为新商品]                                 │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────────────────────────────┐  │
│  │ 设计稿预览   │  │ 基本信息                               │  │
│  │             │  │ 标题: 山海经·应龙 T恤                   │  │
│  │             │  │ 价格: ¥129  成本: ¥66  利润: ¥63 (48%) │  │
│  └─────────────┘  │ 模板: T恤/短袖 (cat_textile_tshirt)    │  │
│                   │ 规格: DPI 300 ✅ 尺寸 4500x5400 ✅     │  │
│                   └──────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  [🖨️ POD发布] [🚀 众筹] [📜 IP授权] [💰 收入] [📋 订单]      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🖨️ POD发布:                                                │
│  Printful:  应龙T恤-黑色-M    ✅ 已发布                     │
│  Redbubble: 应龙T恤           ⏳ 待发布   [一键跳转发布]       │
│                                                             │
│  🚀 众筹:                                                   │
│  摩点: 《山海经》系列限定版画众筹                             │
│  档位: 早鸟版画 ¥199 × 100  | 全套签名版 ¥899 × 20           │
│  进度: ¥48,000 / ¥80,000 (60%)                              │
│                                                             │
│  📜 IP授权:                                                 │
│  商业扩展授权 - XX公司     ¥3,500                            │
│  范围: 全球  期限: 1年  媒介: 包装  状态: 已签约              │
│                                                             │
│  💰 收入:                                                   │
│  2026-06  ¥2,450  |  2026-05  ¥1,890  |  累计: ¥12,340      │
│                                                             │
│  📋 订单:                                                   │
│  ORD-0615-001  Printful  应龙T恤-黑色-M  ¥129  ✅            │
│  ORD-0610-003  摩点众筹  山海经早鸟版画  ¥199  📦            │
└─────────────────────────────────────────────────────────────┘
```

### 9.4 产品卡片

```vue
<ListingCard>
  <img :src="mockup_image_path" />
  <Title>山海经·应龙 T恤</Title>
  <Price>¥129</Price>
  <Profit>利润 ¥63 (48%)</Profit>
  <Tag>POD</Tag> <Tag>纺织</Tag> <Tag>Printful</Tag>
  <Status active />
  <Actions>
    <Edit /> <Duplicate /> <Publish /> <View />
  </Actions>
</ListingCard>
```

### 9.5 批量操作

- **复制为新商品** — 同一设计稿 → 应用到不同产品模板（快速多品类上架）
- **批量切换状态** — 上架/下架
- **批量修改价格** — 统一调整
- **批量导出数据** — CSV/PDF

---

## 十、收入追踪 (增强版)

### 10.1 数据模型

```sql
revenue_records:
  id, product_id(FK), platform, amount, currency,
  date, order_count,
  source(manual/csv_import/auto_sync),
  refund_amount, platform_fee, net_revenue,
  monetization_path,  -- pod/digital/crowdfunding/licensing/subscription/commission
  notes,
  created_at
```

### 10.2 收入录入方式

1. **手动登记**: 填写金额/渠道/日期/产品
2. **CSV导入**: 支付宝/微信/POD平台导出格式
3. **[P2] 自动同步**: 通过平台API定期拉取销售数据

### 10.3 利润计算

```
单笔利润 = 售价 - 成本 - 平台费 - 支付处理费 - 物流费 - 退款
总利润 = Σ(单笔利润)
ROI = 总利润 / 总投入 × 100%
```

### 10.4 图表展示

- 按月/渠道/产品/路径的聚合视图
- 收入趋势折线图
- 渠道分布饼图
- 产品表现排行榜

---

## 十一、商业安全模块

### 11.1 防抄袭水印 (P2新增)

- 产品预览图自动添加半透明水印 (创作者名字 + "© OriStudio")
- 水印位置/透明度可调
- 已授权买家可获得无水印高清版本
- 支持隐形水印 (steganography) 用于溯源

### 11.2 授权合约管理

- 标准合约模板库
- 自动生成PDF合约
- 电子签名支持
- 合约存档和检索

### 11.3 使用追踪

- 记录每次授权的使用方信息
- 监控作品在网络上的使用情况 (对接[3]侵权监测中心)
- 发现未经授权使用时自动告警

---

## 十二、AI商业助手

### 12.1 功能

1. **路径推荐**: 基于作品类型/风格/质量，推荐最适合的变现路径
2. **定价建议**: 基于竞品分析 + 作品价值评分，给出价格区间
3. **市场趋势**: 分析热门品类/风格/平台，提供市场洞察
4. **优化建议**: 基于历史数据，优化产品描述/标签/定价策略

### 12.2 数据源

- 内部: 创作者作品库 + 历史销售数据
- 外部: 平台公开价格数据 (Printful/Redbubble等)
- AI: Ollama/ComfyUI 生成分析报告

---

## 十三、API端点

### P2 新增端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/supply/listings` | 商品列表 (分页+筛选) |
| `POST` | `/supply/listings` | 创建商品 (DesignListing) |
| `GET` | `/supply/listings/{id}` | 商品详情 (含关联POD/众筹/IP/收入/订单) |
| `PATCH` | `/supply/listings/{id}` | 更新商品信息 |
| `DELETE` | `/supply/listings/{id}` | 软删除商品 |
| `POST` | `/supply/spec-validate-compat` | 兼容产品推荐 |
| `POST` | `/supply/spec-validate-remediation` | 修复建议 |

### 现有端点增强

| 方法 | 路径 | 变更 |
|------|------|------|
| `POST` | `/supply/spec-validate` | 响应增加 `compatible_categories` 字段 |
| `GET` | `/supply/products` | 保留 (向后兼容，逐步废弃) |
| `POST` | `/supply/products` | 保留 (向后兼容，逐步废弃) |

---

## 十四、前端实现 (P2 重构)

### 新组件结构

```
frontend/src/
├── views/
│   ├── SupplyView.vue              # 仪表盘 + 向导 + 顾问 (精简)
│   ├── ListingListView.vue         # 商品列表页 (P2 新)
│   ├── ListingDetailView.vue       # 商品详情页 (P2 新)
│   └── TemplateBrowserView.vue     # 产品库浏览 (P2 新)
├── components/
│   ├── monetization/
│   │   ├── SpecRemediationPanel.vue   # 规格修复建议面板 (P2 新)
│   │   ├── ListingCard.vue            # 商品卡片 (P2 新)
│   │   ├── MonetizationTabs.vue       # 变现路径子Tab (P2 新)
│   │   ├── PublicationPanel.vue       # POD发布管理 (P2 新)
│   │   ├── CampaignPanel.vue          # 众筹关联管理 (P2 新)
│   │   └── LicensePanel.vue           # IP授权关联管理 (P2 新)
│   └── work/                        # 创意资产组件 (不变)
├── composables/
│   └── useProductDesigner.ts        # 设计向导状态管理 (P2 新)
├── api/
│   └── supply.ts                    # 新增 listings/compat/remediation API
└── types/
    └── supply.ts                    # 新增 Listing/Compatibility 类型
```

### 关键组件说明

- **SpecRemediationPanel.vue**: 在 Step 4 校验失败时展示兼容产品推荐、修复建议、覆盖选项
- **ListingDetailView.vue**: 商品详情页，含设计稿预览 + 基本信息 + 变现路径子Tab
- **MonetizationTabs.vue**: 商品详情页内的子Tab导航 (POD/众筹/IP/收入/订单)

---

## 十五、上下游数据流

| 输入数据 | 来源 | 用途 |
|----------|------|------|
| work.id+title+thumbnail+file_path+rights | [1]创意资产中心 | 设计器选作品 |
| certificate.id+qr_code | [2]权利保护中心 | Verified徽章/作品价值评分 |
| ipr.registration | [3]IP登记工作站 | 授权基础 |
| monitor.results | [3]侵权监测中心 | 使用追踪/告警 |

| 输出数据 | 目标 | 用途 |
|----------|------|------|
| product.id+效果图+title+price | [5]内容分发中心 | 推广素材 |
| product+price+cost+channel | [6]经营管理中心 | 收入关联 |
| license.contract | [2]权利保护中心 | 存证记录 |
| campaign.data | [5]内容分发中心 | 众筹推广 |

---

## 十六、预留功能设计 (v2/v3/v4)

> **设计原则**: v1变现引擎聚焦插画师/AIGC艺术家的4条核心路径(POD/众筹/IP授权/收入追踪)。其他2条路径(订阅会员/定制商单)和全创作者类型支持在此完整设计。v1预留数据模型/API路由/组件骨架，v2-v4按版本实现。

---

### 16.1 订阅/会员体系 (v2)

#### 16.1.1 创作者订阅模式

- **目标版本**: v2 | **目标创作者**: 插画师/音乐人/文字作者
- **定位**: 创作者建立稳定现金流，粉丝按月付费获得独家内容

**功能设计**:

| 功能 | 说明 | 参考 |
|------|------|------|
| 会员等级 | 3-5级 (关注/支持/赞助/核心) | Patreon |
| 月度订阅费 | 每级设定月费 | Ko-fi Memberships |
| 独家内容 | 高级会员可见/可下载 | OnlyFans |
| 早期访问 | 新作品优先看 | Substack |
| 社区权限 | 专属Discord/论坛 | Discord Communities |
| 定制权益 | 1v1沟通/定制内容 | Patreon Exclusive |

**数据模型**:
```sql
CREATE TABLE subscription_tiers (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name VARCHAR(100),
    description TEXT,
    monthly_price DECIMAL(10,2),
    max_members INTEGER,  -- NULL=无上限
    perks JSON,  -- [{"name": "早期访问", "enabled": true}, ...]
    content_access_level VARCHAR(20),  -- none/basic/premium/all
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE subscription_subscribers (
    id INTEGER PRIMARY KEY,
    tier_id INTEGER NOT NULL REFERENCES subscription_tiers(id),
    subscriber_user_id INTEGER,
    status VARCHAR(20),  -- active/past_due/canceled/expired
    current_period_start DATE,
    current_period_end DATE,
    canceled_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**v1集成点**:
- 变现路径Step2预留"订阅/会员"路径卡片
- subscription_tiers / subscription_subscribers表预留
- [6]收入追踪预留"订阅"收入来源类型

---

### 16.2 定制商单工作流 (v2)

#### 16.2.1 Brief→Proposal→Production→Delivery→Settlement

- **目标版本**: v2 | **目标创作者**: 全类型
- **定位**: 管理客户定制需求的全生命周期

**5阶段状态机**:
```
brief_received(收到需求)
  → proposal_submitted(提交方案)
    → accepted(方案通过)
      → production(制作中)
        → delivered(交付)
          → settled(已结算) / rejected(被拒)
```

**数据模型**:
```sql
CREATE TABLE commission_orders (
    id INTEGER PRIMARY KEY,
    creator_id INTEGER NOT NULL,
    client_name VARCHAR(200),
    client_email VARCHAR(200),
    title VARCHAR(500) NOT NULL,
    brief_text TEXT,  -- 客户需求原文
    brief_attachments JSON,
    budget_min DECIMAL(10,2),
    budget_max DECIMAL(10,2),
    final_price DECIMAL(10,2),
    
    status VARCHAR(30) DEFAULT 'brief_received',
    -- brief_received / proposal_submitted / accepted / production / delivered / settled / rejected / cancelled
    
    proposal_deadline DATE,
    delivery_deadline DATE,
    
    revision_count INTEGER DEFAULT 0,
    max_revisions INTEGER DEFAULT 2,  -- 包含几次免费修改
    
    related_work_ids JSON,
    contract_url VARCHAR(500),
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE commission_messages (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES commission_orders(id) ON DELETE CASCADE,
    sender VARCHAR(100),  -- client / creator / system
    message_text TEXT,
    attachments JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**v1集成点**:
- 变现路径Step2预留"定制商单"入口
- commission_orders / commission_messages表预留

---

### 16.3 摄影师专属变现路径 (v2)

#### 16.3.1 图库销售渠道

对接主流图库平台: Shutterstock / Alamy / Getty / 500px / 图虫

**核心功能**:
- 批量上传 + 关键词管理 + 类目选择
- 销售数据追踪 (Royalty-Free vs Rights-Managed)
- CSV导入销售报表
- AI关键词推荐 (基于图像内容)

> 详见原设计文档 15.1.1 节 (数据模型/API/前端组件不变)

#### 16.3.2 数字预设包

摄影师将 Lightroom 预设 / PS 动作 / LUT 打包为 ZIP 数字产品销售。

> 详见原设计文档 15.1.2 节 (不变)

#### 16.3.3 艺术微喷

专业照片打印，支持纸张类型/装裱选项/尺寸矩阵。

> 详见原设计文档 15.1.3 节 (不变)

---

### 16.4 视频创作者专属变现路径 (v3)

#### 16.4.1 品牌商单工作流

品牌Brief→提案→脚本→制作→反馈→交付→结算

> 详见原设计文档 15.2.1 节 (不变)

#### 16.4.2 平台激励追踪

追踪各视频平台的创作者激励收入

> 详见原设计文档 15.2.2 节 (不变)

#### 16.4.3 周边衍生品管理

IP角色的周边衍生品(手办/公仔/徽章)

> 详见原设计文档 15.2.3 节 (不变)

---

### 16.5 手工艺人专属变现路径 (v3)

#### 16.5.1 物理原件产品模型

作品是物理实体，照片是衍生记录

> 详见原设计文档 15.3.1 节 (不变)

#### 16.5.2 原料库存管理

粘土/釉料/木材等原料库存

> 详见原设计文档 15.3.2 节 (不变)

#### 16.5.3 生产批次管理

从投料到产出的全流程追踪

> 详见原设计文档 15.3.3 节 (不变)

#### 16.5.4 质检分级

A/B/C级质量检验

> 详见原设计文档 15.3.4 节 (不变)

---

### 16.6 音乐创作者专属变现路径 (v4)

#### 16.6.1 音乐发行管理

对接 DistroKid/TuneCore 等发行聚合器

> 详见原设计文档 15.4.1 节 (不变)

#### 16.6.2 采样授权管理

追踪采样素材的授权状态

> 详见原设计文档 15.4.2 节 (不变)

---

### 16.7 文字创作者专属变现路径 (v4)

#### 16.7.1 电子书产品管理

Pandoc格式转换 + ISBN管理 + 多渠道发布

> 详见原设计文档 15.5.1 节 (不变)

#### 16.7.2 有声书制作管理

配音演员/录音棚/分章节音频管理

> 详见原设计文档 15.5.2 节 (不变)

#### 16.7.3 KDP/起点/晋江对接

主流电子书和网文发布平台对接

> 详见原设计文档 15.5.3 节 (不变)

---

## 十七、多语言多币种支持 (P2新增)

### 17.1 币种

- 默认 CNY
- 支持 USD, EUR, GBP, JPY
- 实时汇率换算 (对接外汇API)

### 17.2 语言

- 产品描述/标题支持中英文双语
- 平台发布时自动翻译 (AI辅助)
- 授权合约支持中英双语

### 17.3 国际化定价策略

- 不同市场差异化定价
- 基于购买力平价(PPP)调整
- 显示"当地等效价格"参考

---

## 十八、创作者分级权益体系 (P2新增)

基于创作者的累计收入/作品数量/存证数量/粉丝数，自动划分等级:

| 等级 | 条件 | 权益 |
|------|------|------|
| 🌱 新手 | 注册即自动 | 基础功能，所有路径可用 |
| 🌿 成长 | 累计收入≥¥1000 或 作品≥20 | 优先AI推荐，高级定价工具 |
| 🌳 专业 | 累计收入≥¥10000 或 存证≥50 | 自定义合约模板，批量操作 |
| 🏆 大师 | 累计收入≥¥100000 | 专属客户经理，API直连POD平台 |

---

## 十九、文件清单 (P2 重构)

### 新建文件 (10)
| 文件 | 用途 |
|------|------|
| `backend/app/models/listings.py` | DesignListing + Compatibility 数据模型 |
| `backend/app/services/compatibility.py` | 兼容产品推荐 + 修复建议 (已合并到 spec_checker.py) |
| `backend/app/routers/listings.py` | 商品CRUD + 兼容推荐 API (已合并到 supply.py) |
| `frontend/src/views/ListingListView.vue` | 商品列表页 |
| `frontend/src/views/ListingDetailView.vue` | 商品详情页 |
| `frontend/src/views/TemplateBrowserView.vue` | 产品库浏览 |
| `frontend/src/components/monetization/SpecRemediationPanel.vue` | 规格校验修复面板 ✅ |
| `frontend/src/components/monetization/ListingCard.vue` | 商品卡片 |
| `frontend/src/components/monetization/MonetizationTabs.vue` | 变现路径子Tab |
| `frontend/src/composables/useProductDesigner.ts` | 设计向导状态管理 |

### 修改文件 (12)
| 文件 | 变更 |
|------|------|
| `backend/app/models/publish.py` | ProductPublishing 添加 listing_id FK ✅ |
| `backend/app/models/monetization.py` | Campaign/License 添加 listing_id FK ✅ |
| `backend/app/models/supply.py` | Order 添加 listing_id FK ✅ |
| `backend/app/models/listings.py` | 新建: DesignListing + Compatibility ✅ |
| `backend/app/services/spec_checker.py` | 添加 get_compatible_templates() + compute_remediation_suggestions() ✅ |
| `backend/app/routers/supply.py` | 新增 listings CRUD + spec-validate-compat + spec-validate-remediation ✅ |
| `frontend/src/views/SupplyView.vue` | 规格校验阻断 + 修复建议 + 创建后跳转 ✅ |
| `frontend/src/api/supply.ts` | 新增 listings/compat/remediation API ✅ |
| `frontend/src/types/supply.ts` | 新增 Listing, Compatibility 类型 ✅ |
| `docs/modules-v3/04-monetization-engine.md` | 更新架构描述 ✅ |

### 待实施 (Phase 3-5)
| 文件 | 用途 |
|------|------|
| `frontend/src/views/ListingListView.vue` | 商品列表页 |
| `frontend/src/views/ListingDetailView.vue` | 商品详情页 |
| `frontend/src/views/TemplateBrowserView.vue` | 产品库浏览 |
| `frontend/src/components/monetization/ListingCard.vue` | 商品卡片 |
| `frontend/src/components/monetization/MonetizationTabs.vue` | 变现路径子Tab |
| `frontend/src/router/index.ts` | 新增路由 |
| 文件 | 用途 | 版本 |
|------|------|------|
| `subscription_tiers` 表 | 会员等级管理 | v2 |
| `subscription_subscribers` 表 | 订阅者管理 | v2 |
| `commission_orders` 表 | 定制商单管理 | v2 |
| `stock_channels` 表 | 图库渠道 | v2 |
| `stock_uploads` 表 | 图库上传 | v2 |
| `stock_sales` 表 | 图库销售 | v2 |
| `digital_downloads` 表 | 数字产品下载 | v2 |
| `fine_art_print_configs` 表 | 艺术微喷配置 | v2 |
| `brand_campaigns` 表 | 品牌商单 | v3 |
| `platform_earnings` 表 | 平台激励 | v3 |
| `physical_products` 表 | 物理产品 | v3 |
| `materials_inventory` 表 | 原料库存 | v3 |
| `production_batches` 表 | 生产批次 | v3 |
| `quality_inspections` 表 | 质检分级 | v3 |
| `distribution_releases` 表 | 音乐发行 | v4 |
| `sample_clearances` 表 | 采样授权 | v4 |
| `ebook_products` 表 | 电子书产品 | v4 |
| `audiobook_productions` 表 | 有声书制作 | v4 |
