# [5] 内容分发中心 — 详细功能设计 v3

> **定位**: 创作者内容的多平台分发与推广中心。AI文案生成+图片处理+排期发布+影响力追踪。
> **最后更新**: 2026-06-12 (Stage 2修订: 平台列表补全、Onboarding平台预设、非插画平台标注)

---

## 一、v1 创作者类型支持声明

| 功能 | 插画师 v1 | 摄影师 | 视频 | 手工 | 音乐 | 文字 |
|------|-----------|--------|------|------|------|------|
| 社交媒体分发 | 完整支持 | 基础 | 基础 | 基础 | — | — |
| AI文案引擎 | 完整支持 | 规划中 | 规划中 | 规划中 | — | — |
| 图片处理 | 完整支持 | 规划中 | — | 规划中 | — | — |
| 排期发布 | 完整支持 | 规划中 | 规划中 | 规划中 | — | — |
| 影响力分析 | 完整支持 | 规划中 | 规划中 | 规划中 | — | — |
| 徽章生成 | 完整支持 | 规划中 | — | 规划中 | — | — |

---

## 二、功能架构

```
内容分发中心
├── 📱 发布推广 (核心Tab: 选内容→选平台→AI文案→图片处理→发布)
├── 🤖 AI文案引擎 (6种平台风格模板+Ollama/fallback生成)
├── 🖼️ 图片智能处理 (裁剪/水印/文字覆盖/尺寸适配)
├── 📅 排期发布 (定时发布+发布历史)
├── 📊 影响力分析 (各平台数据汇总+趋势图)
├── 🏷️ 原创认证徽章 (Verified徽章SVG生成+嵌入代码)
└── 📦 Feed导出 (JSON Product Feed+CSV，降级为子功能)
```

---

## 三、平台全集 (v1完整列表)

### 3.1 插画师核心平台 (v1完整支持)

| 平台 | 内容类型 | 格式规格 | 发布节奏 | v1状态 |
|------|----------|----------|----------|--------|
| 小红书 | 图片+文案 | 3:4竖图 1080×1440 | 工作日午间/晚间 | ✅ |
| 站酷 | 高清大图+设计理念 | 不限 | 工作日 | ✅ |
| 微博 | 短文+图片/视频 | 9宫格 1200×1200 | 晚间黄金时段 | ✅ |
| B站 | 视频+动态 | 16:9横屏 | 18:00-20:00 | ✅ |
| Instagram | 高清图+hashtags | 1:1 1080×1080 | 早晚通勤 | ✅ |
| 微信公众号 | 图文+排版 | 封面900×383 | 定时推送 | ✅ |

### 3.1.1 插画师可选平台 (基础发布可用)

| 平台 | 内容类型 | 格式规格 | v1状态 | 备注 |
|------|----------|----------|--------|------|
| 抖音 | 短视频 | 9:16竖屏 1080×1920 | 🔵 可选 | 非插画师主要分发渠道，基础支持 |
| YouTube | 长视频+Shorts | 16:9 / 9:16 | 🔵 可选 | 非插画师主要分发渠道，基础支持 |

### 3.2 其他类型平台 (v1标注"规划中")

| 平台 | 目标创作者 | 内容类型 | v1状态 |
|------|-----------|----------|--------|
| Spotify | 音乐 | 音频分发 | 🔵 规划中 |
| QQ音乐 | 音乐 | 音频分发 | 🔵 规划中 |
| 网易云音乐 | 音乐 | 音频分发 | 🔵 规划中 |
| Apple Music | 音乐 | 音频分发 | 🔵 规划中 |
| 起点中文网 | 文字 | 小说连载 | 🔵 规划中 |
| 晋江文学城 | 文字 | 小说/文学 | 🔵 规划中 |
| KDP (Amazon) | 文字 | 电子书出版 | 🔵 规划中 |
| Etsy | 手工 | 手工艺品 | 🔵 规划中 |

### 3.3 Onboarding 流程中的平台预设

在 Onboarding Wizard Step1 (选择创作者类型) 中，系统根据选择自动配置默认分发平台:

| 创作者类型 | 默认分发平台(前3) |
|-----------|-------------------|
| 插画师/AIGC艺术家 | 小红书、站酷、B站 |
| 摄影师(规划中) | 小红书、Instagram、微博 |
| 视频(规划中) | B站、抖音、YouTube |
| 手工(规划中) | 小红书、Etsy(规划中)、Instagram |
| 音乐(规划中) | B站、抖音、Spotify(规划中) |
| 文字(规划中) | 微信公众号、小红书、起点(规划中) |

---

## 四、发布推广核心流程

```
Step1: 选择推广内容
  ○ 作品 (从[1]创意资产中心选择 ─ 作品图片+标题+描述)
  ○ 产品 (从[4]商业转化引擎选择 ─ 产品效果图+标题+价格)
  ○ 纯文案 (仅文字发布)

Step2: 选择目标平台
  □ 小红书  □ 微博  □ 站酷  □ B站  □ 抖音  □ Instagram  □ YouTube  □ 公众号
  [全选] [快速选择: 插画师套装(小红书+站酷+B站)]

Step3: AI文案生成
  系统根据内容+平台风格自动生成文案:
  ┌─────────────────────────────────────────┐
  │ 小红书风格:                               │
  │ 🐉 新作来啦！山海经系列第二弹——应龙！      │
  │                                          │
  │ 这次以大荒东经中的应龙为灵感，融合东方水墨  │
  │ 与现代数码技法，龙鳞部分用了金色高光...     │
  │ (字数: 387)                               │
  │ [重新生成] [编辑] [复制]                   │
  └─────────────────────────────────────────┘
  对每个选中平台分别生成对应风格的文案

Step4: 图片处理 (可选)
  ┌─────────────────────────────────────────┐
  │ 原始图片 (3000×4000)                     │
  │                                          │
  │ 处理后预览: 小红书规格 (1080×1440)        │
  │ [裁剪] [加水印: ©山海画师2026] [加文字]   │
  │ [调整亮度] [加滤镜]                       │
  │                                          │
  │ 生成各平台规格:                            │
  │ □ 小红书 1080×1440  □ 微博 1200×1200     │
  │ □ B站专栏封面 □ Instagram 1080×1080      │
  │ [一键生成所有规格]                         │
  └─────────────────────────────────────────┘

Step5: 预览与确认
  显示每个平台的最终内容预览(文案+图片+平台名称)
  [编辑] [重新生成] [确认]

Step6: 发布/排期
  ○ 立即发布
  ○ 排期发布: [2026-06-13] [20:00] (小红书)
              [2026-06-14] [10:00] (站酷)
  [确认发布/排期]
```

---

## 五、AI文案引擎

### 5.1 6种平台风格模板

| 平台 | 风格 | emoji | 语气 | 字数 | 模板示例 |
|------|------|-------|------|------|----------|
| 小红书 | 种草/分享 | 大量 | 口语化、亲切 | 150-500 | "🐉 新作来啦！这次带来的是..." |
| 站酷 | 专业/作品 | 无 | 专业化、设计师语 | 500-1000 | "山海经·应龙 | 创作过程与技术分解" |
| 微博 | 简洁/话题 | 适量 | 短平快、互动 | 140-280 | "新作限时上架！#山海经# #应龙#" |
| B站 | 活泼/互动 | 适量 | 年轻化、引导三连 | 300-800 | "一键三连！山海经系列新角色来啦~" |
| 抖音 | 短平快 | 适量 | 挑战体、引导关注 | 100-300 | "你最喜欢山海经哪只神兽？评论区告诉我👇" |
| Instagram | Bilingual | 大量 | 视觉化、hashtags | 100-200 | "New drop! 🐲✨ Shan Hai Jing - Ying Long..." |

### 5.2 生成方式

- 输入: 作品/产品信息(title+description+tags) + 目标平台
- 后端调用: 本地Ollama(优先) → 远端OpenAI兼容API(配置) → 本地模板(fallback)
- 输出: 平台适配的完整文案(含emoji、话题标签、行文风格)

### 5.3 AI生成内容标注

> **免责声明 #5**: AI文案生成结果底部标注: "此文案由AI辅助生成，建议根据平台规则标注'AI辅助'并人工审核后发布。"

### 5.4 内容输入来源

- 从作品: title + synopsis + tags + author_name + license_type
- 从产品: title + description + price + product_category + platform

---

## 六、图片智能处理

### 功能
- 按平台裁切: 自动匹配各平台推荐尺寸
- 水印叠加: 署名(attribution_text) + Verified徽章
- 文字覆盖: 添加标题/店铺链接/二维码
- 效果预览: 修改后实时预览

### 实现方式
- HTML5 Canvas 前端处理
- 下载处理后的图片

> **注**: 后端 watermark_service.py 不在 v1 范围内。水印功能 v1 由前端 Canvas 实现(Pillow后端为P2)。详见 PM启动报告 P2-4。

---

## 七、排期发布

### 功能
- 发布内容清单: 内容+平台+时间+状态
- 排期CRUD
- 手动执行(浏览器打开平台发布页)

注: 由于各平台的反爬机制和OAuth限制，实际"自动发布"为标记状态+提供一键跳转到平台发布页，而非全自动Playwright脚本。

### API
- POST /api/publish/schedule — 创建排期
- GET /api/publish/schedules — 排期列表
- DELETE /api/publish/schedules/{id} — 取消排期

---

## 八、影响力分析

### 功能
- 手动录入各平台数据: 浏览量/点赞/评论/转发/收藏
- 汇总图表: 按平台(柱状图) + 按时间(折线图)
- 增长趋势分析
- v2 规划: 社交媒体数据自动汇总(平台API对接)

### API
- GET /api/publish/analytics — 汇总分析数据
- POST /api/publish/analytics — 录入平台数据

---

## 九、原创认证徽章

### 功能 (已实现，增强)
- SVG徽章生成(含QR码+作品信息)
- HTML嵌入代码
- Markdown嵌入代码
- 下载徽章图片(PNG/SVG)

### 数据来源
- 作品SHA-256 + 存证证书ID → [1]创意资产中心 + [2]权利保护中心

---

## 十、Feed导出 (子功能，降级)

已实现: JSON Product Feed + 平台选择 + CSV。保留，不作主要功能推广。

---

## 十一、API端点 (17个，以代码为准)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/publish/ai-description | AI生成文案 |
| GET | /api/publish/style-templates | 平台风格模板列表 |
| GET | /api/publish/products | 产品列表(供选择推广) |
| POST | /api/publish/schedule | 创建排期发布 |
| GET | /api/publish/schedules | 排期列表 |
| DELETE | /api/publish/schedules/{id} | 取消排期 |
| GET | /api/publish/contents | 发布内容列表 |
| POST | /api/publish/contents | 创建发布内容 |
| GET | /api/publish/analytics | 影响力汇总 |
| POST | /api/publish/analytics | 录入平台数据 |
| GET | /api/publish/verified-badge/{product_id} | 徽章生成 |
| GET | /api/publish/feed | Feed导出 |
| POST | /api/publish/products | 创建发布产品 |
| PATCH/DELETE | /api/publish/products/{id} | 发布产品更新/删除 |
| POST | /api/publish/publish-product | 发布到平台 |

---

## 十二、前端实现

### PublishView.vue Tab结构

| # | Tab | 内容 | v1状态 | 空状态 |
|---|-----|------|--------|--------|
| 1 | 📱 发布推广 | 6步向导: 选内容→选平台→AI文案→图片处理→预览→发布/排期 | ✅ | "选择作品或产品开始推广" |
| 2 | 🤖 AI文案 | 单独的AI文案工具(已有，增强风格选择) | ✅ | "选择内容和平台后生成文案" |
| 3 | 🏷️ 原创徽章 | Verified徽章生成+嵌入代码(已有) | ✅ | "选择已存证的作品生成徽章" |
| 4 | 📦 Feed导出 | JSON Feed+CSV(已有，降级) | ✅ | "选择产品后导出Feed" |
| 5 | 📊 影响力 | 数据录入+汇总图表(新增) | ✅ | "录入发布数据后查看影响力趋势" |

### 侧边栏+Topbar标签
- 页面标题: "分发推广中心"

---

## 十三、上下游数据流

| 输入数据 | 来源 | 用途 |
|----------|------|------|
| work.id+title+thumbnail+description+tags+rights | [1]创意资产中心 | 作品推广素材+文案输入 |
| product.id+效果图+title+price+description | [4]商业转化引擎 | 产品推广素材+文案输入 |
| certificate.id+hash | [2]权利保护中心 | 徽章数据 |

| 输出数据 | 目标 | 用途 |
|----------|------|------|
| 平台浏览量/点赞/评论数据 | [6]经营管理中心 | 影响力分析 |
| 发布内容统计 | [6]经营管理中心 | 内容产出统计 |

---

## 十四、预留功能设计 (v2/v3/v4)

> **设计原则**: v1分发中心聚焦插画师8个平台分发+AI文案+图片处理+排期发布。其他4类创作者的专属分发平台在此完整设计。v1预留平台列表/API路由/组件骨架，v2-v4按版本实现。
> **关联文档**: `docs/agent-evaluation-report.md` 中陈摄影(图库平台)周巧手(Etsy)苏旋律(音乐平台)文墨(写作平台)的需求驱动设计。

---

### 14.1 摄影分发平台 (v2)

#### 14.1.1 500px / 图虫 / Shutterstock 平台规格与批量上传

- **目标版本**: v2 | **目标创作者**: 摄影师

**平台规格**:

| 平台 | 定位 | 内容类型 | 格式要求 | API状态 | v2适配器 |
|------|------|----------|----------|---------|---------|
| 500px | 摄影师社区+市场 | 高分辨率摄影 | JPEG/TIFF, 3000px长边, ≤50MB | 受限API | FiveHundredPxGateway |
| 图虫 | 国内最大摄影社区 | 摄影/图文 | JPEG, 长边≥1920px, ≤20MB | 无公开API | TuchongGateway (手动+URL记录) |
| Shutterstock | 全球最大图库 | 商业摄影/矢量图 | JPEG/DNG, 15-50MB, 4MP+ | Contributor API | ShutterstockGateway |
| Getty Images | 顶级图库 | 高端商业摄影 | JPEG/TIFF, 高分辨率 | Contributor API | GettyGateway |

**图库分发工作流**:

```
选作品(从[1]创意资产中心) → 选目标图库平台
  → 检查平台格式要求(尺寸/DPI/色彩空间)
  → 规格校验结果:
    ✅ 500px 满足 3000px长边 ≥ 1920px
    ✅ Shutterstock 满足 4MP 分辨率要求
    ⚠️ Getty Images: 建议提供更大的JPEG (当前800×600不满足)
  → 设置关键词(tag→图库关键词映射)
  → 选择图库类目
  → 一键提交上传(有API的通过API，无API的提供"手动上传指引")
  → 记录上传结果(成功/审核中/拒绝/原因)
  → 追踪销售数据(API自动同步 + CSV手动导入)
```

**API端点设计**:

| 方法 | 路径 | 说明 | 版本 |
|------|------|------|------|
| GET | /api/publish/stock-platforms | 图库平台列表+规格要求 | v2 |
| POST | /api/publish/stock/upload | 上传作品到图库(body: {work_ids, platform, keywords, categories}) | v2 |
| GET | /api/publish/stock/upload-status/{task_id} | 上传任务状态 | v2 |
| GET | /api/publish/stock/uploads | 上传历史(?platform=&status=) | v2 |
| POST | /api/publish/stock/validate | 规格预检(body: {work_id, platform}) | v2 |
| GET | /api/publish/stock/sales | 图库销售数据汇总 | v2 |

**前端组件**:
- **StockPublishWizard.vue** (v2): Props: `{ workIds[] }` — 图库上传向导: 选作品→选平台→规格预检→关键词→类目→确认上传
- **StockSpecCheck.vue** (v2): Props: `{ workId, platform }` — 规格预检结果展示组件: 通过/警告/阻止 三级标识
- **StockUploadHistory.vue** (v2): Props: `{}` — 图库上传历史列表+审核状态

**v1集成点**:
- [5]分发平台列表 — v1已预留500px/图虫/Shutterstock(当前标注"规划中")
- [1]作品列表批量操作 — v1预留"发布到图库"操作入口
- [4]图库销售渠道(stock_channels表) — v1预留，与分发中心数据联动

> **标注**: v1分发中心平台列表已预留500px/图虫/Shutterstock。[1]批量操作预留"发布到图库"。完整图库分发集成交付v2实现。

---

### 14.2 手工分发平台 (v3)

#### 14.2.1 Etsy API网关设计 + Listing管理

- **目标版本**: v3 | **目标创作者**: 手工艺人

**Etsy API网关设计**:

```
app/gateway/etsy.py — EtsyGateway 类 (v3实现):

class EtsyGateway:
    API_BASE = "https://openapi.etsy.com/v3"
    
    # 核心方法
    create_listing(product_data, images[]) → listing_id
    update_listing(listing_id, product_data) → listing
    get_listing(listing_id) → listing_detail
    delete_listing(listing_id) → bool
    get_orders(shop_id, filters?) → orders[]
    get_inventory(listing_id) → inventory
    update_inventory(listing_id, quantity) → inventory
    get_messages(shop_id) → messages[]
    send_message(buyer_id, text) → message
    get_shipping_profiles() → profiles[]
    calculate_shipping(listing_id, destination) → cost
    get_reviews(listing_id) → reviews[]
    
    # 认证
    auth_type = "OAuth 2.0"  # Etsy uses OAuth 2.0
    required_scopes = ["listings_r", "listings_w", "listings_d",
                       "shops_r", "transactions_r", "listings_r"]
```

**Etsy Listing管理数据模型**:

```sql
-- v1预留
CREATE TABLE etsy_listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    physical_product_id INTEGER REFERENCES physical_products(id),
    etsy_listing_id VARCHAR(50),  -- Etsy返回的listing ID
    etsy_shop_id VARCHAR(50),
    title VARCHAR(140) NOT NULL,  -- Etsy标题最长140字符
    description TEXT NOT NULL,
    
    -- 价格
    price DECIMAL(10,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    quantity INTEGER DEFAULT 1,  -- 库存数量
    
    -- 分类
    etsy_category_id INTEGER,
    etsy_category_path VARCHAR(500),
    tags JSON,  -- Etsy最多13个标签
    -- ["handmade", "ceramic", "teacup", "japanese", ...]
    materials JSON,  -- 材料标签
    
    -- 物流
    shipping_profile_id VARCHAR(50),
    processing_time_days INTEGER,  -- 制作周期
    ships_from_country VARCHAR(2) DEFAULT 'CN',
    shipping_cost DECIMAL(10,2),
    free_shipping BOOLEAN DEFAULT FALSE,
    
    -- 变体(如尺寸/颜色选项)
    variations JSON,
    -- [{"name": "Size", "options": ["Small", "Medium", "Large"], "prices": [29, 39, 49]}]
    
    -- 图片
    image_order JSON,  -- 图片排序
    
    -- 状态
    status VARCHAR(20) DEFAULT 'draft',  -- draft/active/inactive/sold_out
    etsy_status VARCHAR(20),  -- Etsy侧状态: active/inactive/expired
    listed_at DATETIME,
    last_synced_at DATETIME,
    
    -- 统计
    views_count INTEGER DEFAULT 0,
    favorites_count INTEGER DEFAULT 0,
    sales_count INTEGER DEFAULT 0,
    revenue DECIMAL(10,2) DEFAULT 0.00,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Etsy订单同步
CREATE TABLE etsy_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER REFERENCES etsy_listings(id),
    etsy_order_id VARCHAR(50) NOT NULL UNIQUE,
    buyer_name VARCHAR(200),
    buyer_country VARCHAR(2),
    order_total DECIMAL(10,2),
    shipping_cost DECIMAL(10,2),
    tax DECIMAL(10,2),
    order_date DATE,
    shipping_deadline DATE,
    status VARCHAR(30),  -- paid/shipped/completed/cancelled
    tracking_number VARCHAR(100),
    notes TEXT,
    synced_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_etsy_listings_status ON etsy_listings(status);
CREATE INDEX idx_etsy_orders_listing ON etsy_orders(listing_id);
```

**API端点设计**:

| 方法 | 路径 | 说明 | 版本 |
|------|------|------|------|
| POST | /api/etsy/connect | OAuth连接Etsy (redirect) | v3 |
| GET | /api/etsy/callback | OAuth回调处理 | v3 |
| GET | /api/etsy/shops | 关联的Etsy店铺列表 | v3 |
| GET | /api/etsy/listings | Listing列表 (?status=&shop_id=) | v3 |
| POST | /api/etsy/listings | 创建Listing (body: {physical_product_id, title, description, price, ...}) | v3 |
| PATCH | /api/etsy/listings/{id} | 更新Listing | v3 |
| DELETE | /api/etsy/listings/{id} | 删除/下架Listing | v3 |
| POST | /api/etsy/listings/{id}/publish | 发布到Etsy | v3 |
| POST | /api/etsy/listings/{id}/sync | 同步Etsy数据(状态/销量/浏览) | v3 |
| GET | /api/etsy/orders | 订单列表 | v3 |
| POST | /api/etsy/orders/sync | 同步订单 | v3 |
| GET | /api/etsy/dashboard | Etsy仪表盘(销售额/浏览/收藏趋势) | v3 |

**前端组件**:
- **EtsyConnectView.vue** (v3): Props: `{}` — OAuth授权引导页面
- **EtsyListingEditor.vue** (v3): Props: `{ physicalProduct? }` — Etsy Listing编辑: 标题(140字符计数)+描述+价格+标签(13个限制)+材料+物流设置+变体+图片排序
- **EtsyDashboard.vue** (v3): Props: `{}` — Etsy销售仪表盘: 销售额+浏览量+收藏+订单+趋势图

**v1集成点**:
- [5]分发平台列表 — v1已预留Etsy(当前标注"规划中")
- etsy_listings / etsy_orders表 — v1预留
- [4]physical_products表 — 手工产品→Etsy listing映射
- [6]收入追踪 — v1预留"Etsy销售"收入来源类型

> **标注**: v1分发中心平台列表已预留Etsy。etsy_listings/etsy_orders表已预留。完整Etsy API集成交付v3实现。

---

### 14.3 音乐分发平台 (v4)

#### 14.3.1 Spotify / QQ音乐 / 网易云 / Apple Music 平台规格与分发流程

- **目标版本**: v4 | **目标创作者**: 音乐人

**平台规格汇总**:

| 平台 | 内容类型 | 格式要求 | 分发方式 | v4适配器 |
|------|----------|----------|----------|---------|
| Spotify | 音频流媒 | WAV/FLAC, 16/24bit, 44.1/48/96kHz | DistroKid/TuneCore聚合 | SpotifyGateway(读取数据) |
| QQ音乐 | 音频流媒+下载 | WAV/FLAC, 16/24bit, 44.1kHz+ | 开放平台(音乐人) | QQMusicGateway(URL记录+手动) |
| 网易云音乐 | 音频流媒+社区 | WAV/FLAC, 16bit, 44.1kHz+ | 云音乐人平台 | NeteaseGateway(URL记录+手动) |
| Apple Music | 音频流媒 | WAV/FLAC, 24bit, 44.1kHz+ | DistroKid/TuneCore聚合 | AppleMusicGateway(读取数据) |
| 抖音(音乐) | 短视频配乐 | MP3/WAV | 抖音音乐人 | DouyinMusicGateway |
| Bandcamp | 独立音乐销售 | WAV/FLAC/MP3 | 直接上传API | BandcampGateway |
| SoundCloud | 音乐分享社区 | WAV/FLAC/MP3 | 直接上传API | SoundCloudGateway |

**音乐分发工作流**:

```
[发行准备]
  选择作品(Album/Single/EP) → 从[1]创意资产中心选择音频文件
  确认元数据: ISRC码分配、封面3000×3000、曲目排序
  选择发行聚合平台: DistroKid / TuneCore / CD Baby / Amuse / LANDR
    (选择后跳转到聚合平台完成实际分发)
         │
         ▼
[发行提交]
  在发行聚合平台的Web端完成:
  上传音频文件 + 封面 + 元数据 + 选择分销商店 → 提交
         │
         ▼
[状态追踪]
  系统通过各平台API读取(非写入)分发状态:
  - Spotify: Spotify for Artists API → 流媒数据/播放列表/听众画像
  - Apple Music: Apple Music for Artists API → 播放数据
  - QQ音乐: 音乐人后台数据 → CSV导入
  - 网易云: 音乐人后台数据 → CSV导入
         │
         ▼
[数据汇总]
  [6]经营管理中心 → 收入+流媒数据汇总
```

**API端点设计**:

| 方法 | 路径 | 说明 | 版本 |
|------|------|------|------|
| GET | /api/publish/music-platforms | 音乐平台列表+格式要求 | v4 |
| GET | /api/publish/music/release-status | 发行作品在各平台的状态(?work_id/album_id) | v4 |
| POST | /api/publish/music/import-data | 导入平台数据(CSV/手动)(body: {platform, data}) | v4 |
| GET | /api/publish/music/stats | 流媒数据汇总(?platform=&date_from=&date_to=) | v4 |
| GET | /api/publish/music/playlists | 各平台播放列表收录情况 | v4 |

**前端组件**:
- **MusicDistroDashboard.vue** (v4): Props: `{}` — 音乐分发仪表盘: 各平台发行状态+流媒数据+播放列表收录
- **MusicStatsImport.vue** (v4): Props: `{ platform }` — 各平台数据CSV导入向导
- **ReleaseTracker.vue** (v4): Props: `{ releaseId }` — 发行状态追踪: 提交→审核→上架时间线

**v1集成点**:
- [5]分发平台列表 — v1已预留Spotify/QQ音乐/网易云/Apple Music(当前标注"规划中")
- [4]distribution_releases表 — v1预留(发行→平台数据同步)
- [1]albums/album_tracks表 — v1预留(发行内容组织)

> **标注**: v1分发中心平台列表已预留4个音乐平台。distribution_releases表已预留。完整音乐分发数据追踪待v4实现。

---

### 14.4 写作分发平台 (v4)

#### 14.4.1 起点 / 晋江 / KDP / 知乎 / 微信公众号 平台规格与格式要求

- **目标版本**: v4 | **目标创作者**: 文字作者

**平台规格**:

| 平台 | 内容类型 | 格式要求 | 发布方式 | v4适配器 |
|------|----------|----------|----------|---------|
| 起点中文网 | 网络小说连载 | 在线编辑器/Word导入 | 作者后台 | QidianGateway(URL记录+手动) |
| 晋江文学城 | 网络文学 | 在线编辑器/Rich Text | 作者后台 | JjwxcGateway(URL记录+手动) |
| KDP (Amazon) | 电子书出版 | EPUB/DOCX, 封面2560×1600 | KDP Publishing(受限) | KdpGateway(API辅助) |
| 知乎 | 深度文章/专栏 | 富文本/Markdown | 内容API | ZhihuGateway(API发布) |
| 微信公众号 | 图文/付费阅读 | 排版编辑器 | 素材管理API | WechatArticleGateway(API发布) |
| 豆瓣阅读 | 电子书/征文 | EPUB/DOCX | 作者后台 | DoubanReadGateway |
| 番茄小说 | 网络小说 | 在线编辑器 | 作者后台 | FanqieGateway |

**章节→平台格式转换**:

| 目标平台 | 输入格式 | 转换方式 | 说明 |
|----------|----------|----------|------|
| 起点/晋江 | 纯文本/Markdown | 章节拼接+格式清洗 | 在线编辑器粘贴 |
| KDP | EPUB | Pandoc管道 (章节合并→EPUB导出) | 含封面+目录+元数据 |
| 知乎 | Markdown | 原生支持 | 保留加粗/标题/图片 |
| 微信公众号 | 富文本HTML | Markdown→HTML转换 | 保留格式+图片 |

**写作发布工作流**:

```
[发布准备]
  从[1]创意资产中心选择文字作品
  确认: 章节结构完整 / 封面设计 / 权利细分配置
         │
         ▼
[选择目标平台]
  □ 起点中文网 □ 晋江 □ KDP □ 知乎 □ 公众号 □ 豆瓣阅读 □ 番茄
         │
         ▼
[格式准备]
  - 有API平台: 系统自动生成适配格式+KDP上传EPUB
  - 无API平台: 系统提供"手动发布指引"+格式化复制按钮
         │
         ▼
[发布执行]
  有API: 一键提交(知乎文章发布/公众号图文发布/KDP草稿上传)
  无API: 一键跳转+格式化复制+手动粘贴发布+URL回填
         │
         ▼
[追踪]
  各平台数据: API读取(知乎/KDP) + CSV导入(起点/晋江) + 手动录入
  [6]经营管理中心 → 各平台阅读/订阅/收藏/收入汇总
```

**API端点设计**:

| 方法 | 路径 | 说明 | 版本 |
|------|------|------|------|
| GET | /api/publish/writing-platforms | 写作平台列表+格式要求 | v4 |
| POST | /api/publish/writing/prepare | 准备发布内容(body: {work_id, platforms[]}) | v4 |
| POST | /api/publish/writing/publish | 执行发布(body: {work_id, platform}) | v4 |
| POST | /api/publish/writing/format | 生成平台格式(body: {work_id, platform}) | v4 |
| GET | /api/publish/writing/stats | 各平台发布数据汇总 | v4 |

**前端组件**:
- **WritingPublishWizard.vue** (v4): Props: `{ workId }` — 写作发布向导: 选平台→格式预览→确认发布
- **PlatformFormatPreview.vue** (v4): Props: `{ format: string, content: string }` — 各平台格式预览(显示转换后的内容/格式)
- **WritingStatsDashboard.vue** (v4): Props: `{}` — 各平台阅读/订阅/收藏数据汇总

### 补充前端组件规格 (v2-v4 平台适配器)

**StockUploadHistory.vue** (v2)
Props: `{}`

```
┌────────────────────────────────────────────────────────┐
│ 📤 图库上传历史                                        │
├────────────────────────────────────────────────────────┤
│ 筛选: [全部状态 ▼] [平台: [全部 ▼]] [日期范围: ▼]      │
│                                                        │
│ ┌────────────────────────────────────────────────────┐ │
│ │ [缩略图] 风景照片_001.jpg                           │ │
│ │ 平台: 500px | 状态: ✅ 已接受 | 2026-06-20         │ │
│ │ 价格: ¥15/次 | 下载: 23次 | 收入: ¥345             │ │
│ └────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────┐ │
│ │ [缩略图] 城市夜景.jpg                               │ │
│ │ 平台: 图虫 | 状态: ⏳ 审核中 | 2026-06-22           │ │
│ └────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────┐ │
│ │ [缩略图] 人像_003.jpg                               │ │
│ │ 平台: 500px | 状态: ❌ 被拒 (规格不符) | 2026-06-18│ │
│ └────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
```

**EtsyConnectView.vue** (v3)
Props: `{}`

- OAuth 授权引导页面
- 步骤 1: 显示 Etsy Seller 登录按钮
- 步骤 2: 授权成功后显示店铺信息 + 已同步商品列表
- 步骤 3: 断开连接按钮

**EtsyListingEditor.vue** (v3)
Props: `{ physicalProduct: boolean }`

- 标题输入 (140 字符计数器，实时显示剩余字符)
- 描述 textarea
- 价格输入 + 成本输入
- 标签输入 (13 个限制，实时显示已用数量)
- 材料输入
- 物流设置 (重量/尺寸/发货地)
- 变体管理 (颜色/尺寸)
- 图片排序 (拖拽调整)

**EtsyDashboard.vue** (v3)
Props: `{}`

- 销售总额 + 订单数 + 浏览量 + 收藏数 统计卡片
- 销售额趋势折线图 (7天/30天/90天)
- 热销商品排行列表
- 近期订单列表

**MusicDistroDashboard.vue** (v4)
Props: `{}`

- 各平台发行状态卡片 (Spotify/Apple Music/网易云/QQ音乐...)
- 状态标签: 待审核/已上架/审核失败
- 流媒体数据汇总: 总播放量/月听众/收入
- 播放列表收录列表

**ReleaseTracker.vue** (v4)
Props: `{ releaseId: string }`

```
┌────────────────────────────────────────────────────────┐
│ 🎵 发行追踪: 《山海经·应龙》EP                          │
├────────────────────────────────────────────────────────┤
│ 时间线:                                                │
│ ● 2026-06-01 提交发行                                   │
│   └── Spotify: 已提交                                  │
│   └── Apple Music: 已提交                              │
│                                                        │
│ ○ 2026-06-05 审核中                                    │
│                                                        │
│ ○ 2026-06-10 上架                                      │
│                                                        │
│ ── 各平台状态 ──                                        │
│ Spotify:     ⏳ 审核中 (提交: 06-01)                    │
│ Apple Music: ⏳ 审核中 (提交: 06-01)                    │
│ 网易云音乐:  ✅ 已上架 (06-03)  播放: 1,234            │
│ QQ音乐:      ✅ 已上架 (06-03)  播放: 856              │
└────────────────────────────────────────────────────────┘
```

**WritingPublishWizard.vue** (v4) — 补充规格
Props: `{ workId: string }`

Steps:
1. **选择平台** — 起点/晋江/KDP/微信公众号 卡片选择
2. **格式预览** — 显示转换后的内容格式
3. **元数据填写** — 书名/作者/简介/标签/分类
4. **确认发布** — 预览 + 发布按钮

Events: `@next(stepData)`, `@prev`, `@submit(success)`

**PlatformFormatPreview.vue** (v4)
Props: `{ format: string, content: string }`

- 实时预览各平台格式要求
- 格式不符时红色高亮提示
- 支持切换预览模式 (HTML/纯文本/Markdown)

**WritingStatsDashboard.vue** (v4)
Props: `{}`

- 各平台阅读/订阅/收藏数据汇总表格
- 趋势折线图 (日/周/月)
- 热门章节排行
- 读者评论摘要

**v1集成点**:
- [5]分发平台列表 — v1已预留起点/晋江/KDP/知乎/公众号(当前标注"规划中")
- [1]chapters表 — v1预留(章节结构→发布内容来源)
- [1]export_formats — v1预留(格式转换记录)

> **标注**: v1分发中心平台列表已预留5个写作平台。chapters/export_formats表已预留。完整写作分发适配器待v4实现。
