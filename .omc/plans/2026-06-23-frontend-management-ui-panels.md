# 前端管理 UI 面板 — 全面实施计划

## Context

后端 332 个 API 端点已全部实现，但多个管理功能缺少对应的前端 UI 面板。本计划将 6 个管理页面 + 导航集成全部落实到前端代码中。

**已有前端 API 函数（`system.ts`）：** 69 个，覆盖所有后端端点。
**缺失前端页面：** 6 个独立 View 组件。

---

## 需求摘要

| 序号 | 页面 | 路由 | 后端 API 端点数 | 核心功能 |
|------|------|------|----------------|----------|
| 1 | WatermarkPresetsView | `/app/settings/watermarks` | 6 | 水印预设 CRUD、类型切换、配置表单、预览、应用到作品 |
| 2 | MetadataTemplatesView | `/app/settings/templates` | 9 | 模板 CRUD、字段管理（增删改排序）、应用到作品 |
| 3 | WorkVariantsView | `/app/works/:id/variants` | 10 | 变体分组 CRUD、变体管理、7 种标准比例一键生成 |
| 4 | CullingView | `/app/works/cull` | 2 | 网格缩略图、评分/颜色标签、批量操作、过滤 |
| 5 | SubscriptionView | `/app/settings/subscriptions` | 7 | 订阅等级 CRUD、用户订阅管理、状态切换 |
| 6 | CommissionView | `/app/business/commissions` | 9 | 委托看板（拖拽）、委托 CRUD、状态流转 |

---

## 接受标准 (Acceptance Criteria)

1. **[AC-1]** 6 个新 View 组件均能独立访问，路由注册正确，404 不会出现
2. **[AC-2]** 每个页面的 CRUD 操作均调用真实后端 API，数据持久化到 SQLite
3. **[AC-3]** 侧边栏新增 6 个菜单项，图标使用 emoji，active 状态高亮正确
4. **[AC-4]** 顶部栏 pageTitles 映射包含 6 个新页面名称
5. **[AC-5]** 所有新组件遵循 `<script setup lang="ts">` + `<style scoped>` 模式
6. **[AC-6]** 使用 `var(--surface)`, `var(--border)`, `var(--accent)` 等 CSS 变量，不硬编码颜色
7. **[AC-7]** 无 console.log 语句，错误处理通过 toast 提示用户
8. **[AC-8]** 响应式布局：窄屏下表格/卡片自动堆叠
9. **[AC-9]** 编译通过：`vue-tsc --noEmit --skipLibCheck` 无新增错误

---

## 实施方案

### 文件变更清单

#### 新建文件 (6 个)

| 文件 | 行数预估 | 说明 |
|------|---------|------|
| `frontend/src/views/WatermarkPresetsView.vue` | ~350 | 水印预设管理 |
| `frontend/src/views/MetadataTemplatesView.vue` | ~350 | 元数据模板管理 |
| `frontend/src/views/WorkVariantsView.vue` | ~300 | 作品变体管理 |
| `frontend/src/views/CullingView.vue` | ~350 | 审片视图 |
| `frontend/src/views/SubscriptionView.vue` | ~300 | 订阅管理 |
| `frontend/src/views/CommissionView.vue` | ~350 | 委托看板 |

#### 修改文件 (3 个)

| 文件 | 变更 |
|------|------|
| `frontend/src/router/index.ts` | +6 路由注册 |
| `frontend/src/components/layout/AppSidebar.vue` | +6 菜单项 |
| `frontend/src/components/layout/AppTopbar.vue` | +6 pageTitles |

---

### Step 1: 水印预设管理页面

**路由：** `/app/settings/watermarks`
**组件：** `WatermarkPresetsView.vue`

**功能模块：**

1. **预设列表** — 表格展示所有水印预设（名称、类型、默认状态、创建时间）
2. **新建/编辑模态框** — 表单包含：
   - 名称、描述
   - 水印类型选择器（text / image / tiled）
   - 条件配置：
     - text: 文本内容、字体大小、颜色、位置 (corner/center/tile)
     - image: 图片上传、透明度、缩放比例
     - tiled: 网格间距、旋转角度、透明度
3. **预览** — 点击"预览"按钮调用 `previewWatermark` API，展示水印效果
4. **应用到作品** — 下拉选择作品，调用 `applyWatermark` API
5. **删除** — 二次确认后删除

**API 调用：**
```typescript
import { systemApi } from '@/api/system'
systemApi.watermarkPresets(params)
systemApi.createWatermarkPreset(data)
systemApi.updateWatermarkPreset(id, data)
systemApi.deleteWatermarkPreset(id)
systemApi.applyWatermark(workId, presetId)
systemApi.previewWatermark(config, imagePath)
```

**布局结构：**
```
┌─────────────────────────────────────────────┐
│  水印预设管理                    [+ 新建预设] │
├─────────────────────────────────────────────┤
│  类型: [全部▼]  默认: [全部▼]  [刷新]        │
├─────────────────────────────────────────────┤
│  名称    │ 类型  │ 默认 │ 操作              │
│  ────────┼───────┼──────┼──────────────────  │
│  角落水印 │ text │ ✓   │ [预览][编辑][删除]  │
│  平铺水印 │ tile │      │ [预览][编辑][删除]  │
└─────────────────────────────────────────────┘
```

---

### Step 2: 元数据模板管理页面

**路由：** `/app/settings/templates`
**组件：** `MetadataTemplatesView.vue`

**功能模块：**

1. **模板列表** — 卡片/表格展示所有模板（名称、字段数、默认状态）
2. **新建/编辑模板** — 表单：名称、描述、是否默认
3. **字段管理** — 点击模板展开字段列表：
   - 字段 Key、Label、类型（text/number/date/select/multiline）
   - 必填开关、默认值、选项列表（select 类型）
   - 增删排序字段
4. **应用到作品** — 选择作品后调用 `applyTemplate` API

**API 调用：**
```typescript
systemApi.metadataTemplates(params)
systemApi.createMetadataTemplate(data)
systemApi.updateMetadataTemplate(id, data)
systemApi.deleteMetadataTemplate(id)
systemApi.templateFields(id)
systemApi.addTemplateField(templateId, data)
systemApi.updateTemplateField(templateId, fieldId, data)
systemApi.deleteTemplateField(templateId, fieldId)
systemApi.applyTemplate(templateId, workId)
```

**布局结构：**
```
┌─────────────────────────────────────────────┐
│  元数据模板管理                    [+ 新建模板] │
├─────────────────────────────────────────────┤
│  [IPTC Core ▼]  [EXIF Camera ▼]  [CC ▼]     │
├─────────────────────────────────────────────┤
│  模板: IPTC Core (5 个字段)  [编辑] [应用]   │
│  ──────────────────────────────────────────  │
│  Key       │ Label    │ 类型    │ 必填       │
│  title     │ 标题     │ text    │ ✓          │
│  creator   │ 创作者   │ text    │ ✓          │
│  copyright │ 版权     │ text    │            │
│  keywords  │ 关键词   │ multiline│            │
│  date      │ 日期     │ date    │            │
│  [+ 添加字段]                                │
└─────────────────────────────────────────────┘
```

---

### Step 3: 作品变体管理页面

**路由：** `/app/works/:id/variants`
**组件：** `WorkVariantsView.vue`

**功能模块：**

1. **变体分组列表** — 展示该作品的所有变体分组
2. **新建分组** — 名称、描述
3. **分组内变体管理** — 每个变体：名称、宽高比、尺寸、排序
4. **一键生成** — 选择分组，自动生成 7 种标准比例（1:1, 4:5, 9:16, 16:9, 2:3, 3:2, 21:9）
5. **删除分组/变体**

**API 调用：**
```typescript
systemApi.variantGroups(workId)
systemApi.variantGroupDetail(groupId)
systemApi.createVariantGroup(data)
systemApi.updateVariantGroup(id, data)
systemApi.deleteVariantGroup(id)
systemApi.groupVariants(groupId)
systemApi.addVariant(groupId, data)
systemApi.updateVariant(groupId, variantId, data)
systemApi.deleteVariant(groupId, variantId)
systemApi.generateVariants(workId, groupId)
```

**布局结构：**
```
┌─────────────────────────────────────────────┐
│  作品变体管理                        [+ 新分组] │
├─────────────────────────────────────────────┤
│  ┌─ 社交媒体适配 ────────────────────────┐   │
│  │ 正方形 1:1  │  480×480               │   │
│  │ 故事 9:16   │  540×960               │   │
│  │ 封面 16:9   │  1280×720              │   │
│  │ [+ 添加变体]  [一键生成]  [编辑] [删除]│   │
│  └───────────────────────────────────────┘   │
│  ┌─ 印刷出版 ────────────────────────────┐   │
│  │ A4  210×297mm  │  印刷规格             │   │
│  │ [+ 添加变体]  [一键生成]  [编辑] [删除]│   │
│  └───────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

---

### Step 4: 审片视图 (Culling)

**路由：** `/app/works/cull`
**组件：** `CullingView.vue`

**功能模块：**

1. **网格缩略图** — 瀑布流/网格展示作品缩略图
2. **过滤栏** — 按 cull_status (pending/keep/reject)、rating (1-5)、color_label 过滤
3. **评分操作** — 鼠标悬停显示评分按钮 (1-5⭐)
4. **颜色标签** — 悬停显示红/黄/绿/蓝标签
5. **批量操作** — 多选后批量设置 cull_status、rating、color_label
6. **键盘导航** — 左右箭头切换、数字键评分、A=keep、R=reject

**API 调用：**
```typescript
systemApi.batchCull(workIds, action)
systemApi.cullWork(workId, action)
// list_works 支持过滤: ?cull_status=pending&rating=5&color_label=red
```

**布局结构：**
```
┌─────────────────────────────────────────────┐
│  审片模式                          [筛选▼]   │
├─────────────────────────────────────────────┤
│  状态: [全部▼]  评分: [全部▼]  颜色: [全部▼] │
│  [全选] [保留✓] [淘汰✗] [选中标记⭐]          │
├─────────────────────────────────────────────┤
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐        │
│  │ IMG_01│ │ IMG_02│ │ IMG_03│ │ IMG_04│       │
│  │ ⭐⭐⭐⭐│ │ ⭐⭐⭐ │ │ ⭐⭐⭐⭐⭐│ │ ⭐⭐  │       │
│  │ 绿色  │ │ 黄色  │ │ 红色  │ │ 蓝色  │       │
│  └──────┘ └──────┘ └──────┘ └──────┘        │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐        │
│  │ IMG_05│ │ IMG_06│ │ IMG_07│ │ IMG_08│       │
│  └──────┘ └──────┘ └──────┘ └──────┘        │
└─────────────────────────────────────────────┘
```

---

### Step 5: 订阅管理页面

**路由：** `/app/settings/subscriptions`
**组件：** `SubscriptionView.vue`

**功能模块：**

1. **订阅等级列表** — 表格展示（名称、价格、周期、功能数、订阅人数、状态）
2. **新建/编辑等级** — 表单：名称、描述、价格、货币、周期、功能列表、状态
3. **用户订阅列表** — 切换查看订阅用户（用户ID、等级、状态、订阅时间、过期时间）
4. **状态切换** — 激活/停用等级、取消用户订阅

**API 调用：**
```typescript
systemApi.subscriptions() // 注意：backend 路由是 /subscription/tiers
systemApi.subscribe(data)
systemApi.cancelSubscription(data)
// 需要补充: systemApi.listTiers, systemApi.createTier, systemApi.updateTier, systemApi.deleteTier
// 以及 systemApi.listSubscribers
```

**注意：** 前端 `system.ts` 中订阅相关 API 尚未添加，需要在 `system.ts` 中补充。后端路由路径为 `/subscription/*` 而非 `/system/*`。

**布局结构：**
```
┌─────────────────────────────────────────────┐
│  订阅管理                                    │
├─────────────────────────────────────────────┤
│  [订阅等级]  [订阅用户]                      │
├─────────────────────────────────────────────┤
│  ┌─ 免费版 ──────────────────────────────┐   │
│  │ ¥0/月  │ 5 功能 │ 0 订阅者 │ [编辑]   │   │
│  │ 基础存证、基础扫描                     │   │
│  └───────────────────────────────────────┘   │
│  ┌─ 专业版 ──────────────────────────────┐   │
│  │ ¥29/月  │ 20 功能 │ 15 订阅者 │ [编辑] │   │
│  │ 完整存证、高级扫描、批量导出             │   │
│  └───────────────────────────────────────┘   │
│  [+ 新建等级]                                 │
└─────────────────────────────────────────────┘
```

---

### Step 6: 委托看板 (Commission Kanban)

**路由：** `/app/business/commissions`
**组件：** `CommissionView.vue`

**功能模块：**

1. **看板视图** — 按状态分列（待接单/进行中/待审核/已完成/已取消）
2. **委托卡片** — 显示：客户名、作品名、金额、截止日期、优先级
3. **拖拽排序** — 卡片在不同列之间拖拽改变状态
4. **新建委托** — 弹窗表单
5. **查看详情** — 点击卡片查看完整信息

**API 调用：**
```typescript
// 后端路由: commission.py 9 个端点
// 前端 system.ts 中尚未添加，需要补充
```

**注意：** 后端 commission 端点在 `routers/commission.py`，前端 API 尚未添加到 `system.ts`。需要补充。

**布局结构：**
```
┌──────────────────────────────────────────────────────────────┐
│  委托看板                                       [+ 新建委托]  │
├────────────────┬───────────────┬──────────────┬───────────────┤
│  待接单 (3)    │  进行中 (2)   │  待审核 (1)  │  已完成 (5)   │
├────────────────┼───────────────┼──────────────┼───────────────┤
│ ┌────────────┐ │ ┌───────────┐ │ ┌──────────┐ │               │
│ │ Logo 设计   │ │ │ 画册排版  │ │ │ 视频剪辑 │ │               │
│ │ 张三 │ ¥2000│ │ 李四 │ ¥5000│ │ 王五 │ ¥3k│ │               │
│ │ 截止: 6/25  │ │ │ 截止: 6/28│ │ │ 截止: 6/22│ │               │
│ │ 🔴 紧急     │ │ │ 🟡 普通   │ │ │ 🔴 紧急  │ │               │
│ └────────────┘ │ └───────────┘ │ └──────────┘ │               │
│ ┌────────────┐ │               │               │               │
│ │ 摄影后期   │ │               │               │               │
│ │ 赵六 │ ¥1500│ │               │               │               │
│ └────────────┘ │               │               │               │
└────────────────┴───────────────┴──────────────┴───────────────┘
```

---

### Step 7: 前端 API 补充

在 `frontend/src/api/system.ts` 中补充以下 API 函数：

```typescript
// ─── Subscription (补充) ───
subscriptionTiers: (isActive?: boolean) =>
  client.get('/subscription/tiers', { params: isActive !== undefined ? { is_active: isActive } : {} }),

createSubscriptionTier: (data: any) =>
  client.post('/subscription/tiers', data),

updateSubscriptionTier: (tierId: string, data: any) =>
  client.patch(`/subscription/tiers/${tierId}`, data),

deleteSubscriptionTier: (tierId: string) =>
  client.delete(`/subscription/tiers/${tierId}`),

subscriptionSubscribers: (params?: { user_id?: string; status?: string }) =>
  client.get('/subscription/subscribers', { params }),

subscribe: (data: { user_id: string; tier_id: string }) =>
  client.post('/subscription/subscribe', data),

cancelSubscription: (data: { user_id: string }) =>
  client.post('/subscription/cancel', data),

// ─── Commission (补充) ───
commissions: (params?: any) =>
  client.get('/commissions', { params }),

createCommission: (data: any) =>
  client.post('/commissions', data),

updateCommission: (id: string, data: any) =>
  client.patch(`/commissions/${id}`, data),

deleteCommission: (id: string) =>
  client.delete(`/commissions/${id}`),

commissionDetail: (id: string) =>
  client.get(`/commissions/${id}`),

// ... 其他 commission 端点
```

---

### Step 8: 路由注册

在 `frontend/src/router/index.ts` 中添加 6 个新路由：

```typescript
// 在 /app children 数组中添加:
{ path: 'settings/watermarks', name: 'watermarks', component: () => import('@/views/WatermarkPresetsView.vue') },
{ path: 'settings/templates', name: 'metadata-templates', component: () => import('@/views/MetadataTemplatesView.vue') },
{ path: 'works/:id/variants', name: 'work-variants', component: () => import('@/views/WorkVariantsView.vue') },
{ path: 'works/cull', name: 'culling', component: () => import('@/views/CullingView.vue') },
{ path: 'settings/subscriptions', name: 'subscriptions', component: () => import('@/views/SubscriptionView.vue') },
{ path: 'business/commissions', name: 'commissions', component: () => import('@/views/CommissionView.vue') },
```

---

### Step 9: 侧边栏导航

在 `AppSidebar.vue` 中新增菜单项：

**"经营管理" 分区新增：**
- `📊` 审片视图 → `/app/works/cull`
- `📋` 委托看板 → `/app/business/commissions`

**"设置" 分区新增：**
- `🖊️` 水印预设 → `/app/settings/watermarks`
- `📄` 模板管理 → `/app/settings/templates`
- `🔄` 订阅管理 → `/app/settings/subscriptions`

**"创意资产" 子菜单（works 下的展开项）：**
- `📐` 作品变体 → `/app/works/:id/variants` (动态显示，需在路由守卫或计算属性中判断)

---

### Step 10: 顶部栏标题映射

在 `AppTopbar.vue` 的 `pageTitles` 中添加：

```typescript
const pageTitles: Record<string, string> = {
  // ... existing ...
  watermarks: '水印预设管理',
  'metadata-templates': '模板管理',
  'work-variants': '作品变体',
  culling: '审片视图',
  subscriptions: '订阅管理',
  commissions: '委托看板',
}
```

---

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| Commission API 前端未注册 | 委托看板无法工作 | Step 7 优先补充 API 函数 |
| Subscription API 前端未注册 | 订阅管理无法工作 | Step 7 优先补充 API 函数 |
| 变体路由含动态参数 `:id` | 可能与 works 路由冲突 | 将 variants 路由放在 works 路由之后 |
| 大文件导致编译慢 | 开发体验下降 | 每个组件控制在 350 行以内，抽取子组件 |
| 拖拽功能兼容性 | 看板交互可能失效 | 使用原生 HTML5 Drag & Drop API，不引入第三方库 |

---

## 实施顺序

1. **Step 7:** 补充前端 API 函数（system.ts）— 前置依赖
2. **Step 8:** 路由注册 — 确保新页面可访问
3. **Step 9:** 侧边栏导航 — 确保菜单可见
4. **Step 10:** 顶部栏标题 — 确保面包屑正确
5. **Step 1-6:** 6 个 View 组件开发（可并行）

---

## 验证方案

1. **导航完整性：** 侧边栏 6 个新菜单项均可点击并跳转到正确页面
2. **API 连通性：** 每个页面的 CRUD 操作均能成功调用后端并返回数据
3. **路由优先级：** 访问 `/app/works/xxx/variants` 时正确匹配变体页面而非作品详情
4. **无新增编译错误：** `vue-tsc --noEmit --skipLibCheck` 对比修改前无新增错误
5. **响应式：** 在 768px 和 375px 宽度下布局正常
6. **暗色模式：** 切换 dark/light 后所有元素颜色正确
