# 前端全面实施计划 — TS 修复 + 管理 UI + OAuth + 平台 + C2PA

## Context

后端 332 个 API 端点已全部实现，但前端存在多处问题需要修复和新功能需要开发。本计划覆盖 6 大类工作，全部落地到代码中。

---

## 需求摘要

| 类别 | 工作量 | 依赖 | 优先级 |
|------|--------|------|--------|
| A. 修复 17 个 TS 预存错误 | 小 (~30min) | 无 | P0 |
| B. 前端管理 UI 面板 (6 个页面) | 大 (~4h) | A 先过 | P1 |
| C. 补充前端 API (订阅/委托/平台) | 小 (~20min) | 无 | P1 |
| D. OAuth 前端集成 (Google/微信/抖音) | 中 (~1h) | C 先过 | P2 |
| E. 外部平台配置界面 (Printful/Redbubble 等) | 中 (~1h) | C 先过 | P2 |
| F. C2PA 前端存证入口 | 小 (~30min) | 无 | P2 |

---

## 接受标准

1. **[AC-1]** `vue-tsc --noEmit --skipLibCheck` 无新增 TS 错误（原有 17 个全部修复）
2. **[AC-2]** 6 个管理页面均可独立访问，CRUD 操作均调用真实后端 API
3. **[AC-3]** 侧边栏新增菜单项均可点击跳转，active 状态高亮正确
4. **[AC-4]** OAuth 绑定/解绑在设置页可用，显示真实绑定状态
5. **[AC-5]** 外部平台配置页可保存 API key 到系统设置
6. **[AC-6]** C2PA 存证入口在作品详情页可用，可生成/验证 manifest
7. **[AC-7]** 所有新组件遵循 `<script setup lang="ts">` + `<style scoped>` 模式
8. **[AC-8]** 使用 CSS 变量，不硬编码颜色值
9. **[AC-9]** 无 console.log 语句

---

## 实施方案

### 阶段 A: 修复 17 个 TS 预存错误

#### A1. CampaignPanel.vue (line 117)
**问题：** `defineProps<Props>()` 返回值未赋值给 `props` 变量
**修复：** 将 `defineProps<Props>()` 改为 `const props = defineProps<Props>()`

#### A2. LicensePanel.vue (line 126)
**问题：** 同上
**修复：** `const props = defineProps<Props>()`

#### A3. LicensePanel.vue (line 25)
**问题：** `lic.partyName` 不存在于接口中，实际字段是 `contract_party_name`
**修复：** 改为 `lic.contract_party_name || lic.license_party_name || '未填写'`

#### A4. ListingCard.vue (line 65)
**问题：** `defineProps<Props>()` 未赋值
**修复：** `const props = defineProps<Props>()`

#### A5. OrderPanel.vue (line ~110)
**问题：** 完全没有 `defineProps` 声明，但使用了 `props.listingId`
**修复：** 添加 `interface Props { listingId: string }` 和 `const props = defineProps<Props>()`

#### A6. PublicationPanel.vue (line 89)
**问题：** `defineProps<Props>()` 未赋值
**修复：** `const props = defineProps<Props>()`

#### A7. SpecRemediationPanel.vue (line 65)
**问题：** `acknowledged` ref 在模板中使用但未声明
**修复：** 在 script setup 中添加 `const acknowledged = ref(false)`

#### A8. DashboardView.vue (line 91, 119)
**问题：** `reactive` 被使用但未从 vue 导入
**修复：** `import { onMounted, reactive } from 'vue'`

#### A9. ListingDetailView.vue (line 57)
**问题：** `listing.monetization_path` 可能是 null，传给需要 string 的 `pathLabel`
**修复：** `pathLabel(listing.monetization_path || '')`

#### A10. ListingListView.vue (line 89)
**问题：** 同上
**修复：** `pathLabel(l.monetization_path || '')`

#### A11. PublishView.vue (line 321)
**问题：** 传递了 `:analytics` prop，但 RevenueCharts 只接受 `:revenues`
**修复：** `:revenues="analyticsData"`

#### A12. SettingsView.vue (line 317, 333)
**问题：** `currentPassword` 在模板中使用但未声明
**修复：** 添加 `const currentPassword = ref('')`

#### A13. SettingsView.vue (line 386)
**问题：** `revokeSession` 函数未定义
**修复：** 添加 `async function revokeSession(id: string)` 并在 onMounted 中调用 loadSessions

#### A14. SupplyView.vue (line 1037)
**问题：** 空字符串 `''` 作为对象键查找失败
**修复：** `{ below: '低于均价', reasonable: '合理区间', above: '高于均价' }[pos || 'reasonable']`

#### A15. SupplyView.vue (line 1056)
**问题：** `dashboard` 变量未声明
**修复：** 使用 `dashboardStore` 或从现有 `monetizationPaths` 获取数据

#### A16. SupplyView.vue (line 1162)
**问题：** `compat.data.data?.compatible_templates` 双重嵌套访问错误
**修复：** `compat?.data?.compatible_templates || []`

#### A17. MediaPlayer.vue (line 4)
**问题：** `crossorigin` 属性类型不匹配
**修复：** `:crossorigin="''"`

---

### 阶段 C: 补充前端 API 函数

在 `frontend/src/api/system.ts` 末尾追加：

```typescript
// ─── Subscription Tiers ───
subscriptionTiers: (isActive?: boolean) =>
  client.get('/subscription/tiers', { params: isActive !== undefined ? { is_active: isActive } : {} }),
createSubscriptionTier: (data: any) => client.post('/subscription/tiers', data),
updateSubscriptionTier: (id: string, data: any) => client.patch(`/subscription/tiers/${id}`, data),
deleteSubscriptionTier: (id: string) => client.delete(`/subscription/tiers/${id}`),
subscriptionSubscribers: (params?: any) => client.get('/subscription/subscribers', { params }),
subscribe: (data: { user_id: string; tier_id: string }) => client.post('/subscription/subscribe', data),
cancelSubscription: (data: { user_id: string }) => client.post('/subscription/cancel', data),

// ─── Commission ───
commissions: (params?: { user_id?: string; status?: string }) =>
  client.get('/commission/projects', { params }),
createCommission: (data: any) => client.post('/commission/projects', data),
updateCommission: (id: string, data: any) => client.put(`/commission/projects/${id}`, data),
deleteCommission: (id: string) => client.delete(`/commission/projects/${id}`),
commissionOrders: (projectId: string, params?: { status?: string }) =>
  client.get(`/commission/projects/${projectId}/orders`, { params }),
createCommissionOrder: (projectId: string, data: { order_type: string; amount: number }) =>
  client.post(`/commission/projects/${projectId}/orders`, data),
commissionMessages: (projectId: string) =>
  client.get(`/commission/projects/${projectId}/messages`),
createCommissionMessage: (projectId: string, data: { sender_id: string; content: string }) =>
  client.post(`/commission/projects/${projectId}/messages`, data),

// ─── C2PA ───
generateC2PA: (workId: string) =>
  client.post(`/notary/c2pa/${workId}/generate`),
verifyC2PA: (workId: string) =>
  client.get(`/notary/verify/c2pa/${workId}`),

// ─── Platform Config ───
platformConfig: () =>
  client.get('/system/platform-config'),
updatePlatformConfig: (data: any) =>
  client.patch('/system/platform-config', data),
```

同时需要补充 `backend/app/models/__init__.py` 中的 commission 模型导出：
- 添加 `CommissionProject, CommissionOrder, CommissionMessage` 到 `__all__`

---

### 阶段 B: 前端管理 UI 面板 (6 个页面)

#### 页面 1: WatermarkPresetsView.vue
**路由：** `/app/settings/watermarks`
**功能：** 水印预设 CRUD + 预览 + 应用
**布局：** 卡片列表 + 模态框编辑
**文件：** `frontend/src/views/WatermarkPresetsView.vue` (~350 行)

#### 页面 2: MetadataTemplatesView.vue
**路由：** `/app/settings/templates`
**功能：** 模板 CRUD + 字段管理 + 应用到作品
**布局：** 左侧模板列表 + 右侧字段编辑器
**文件：** `frontend/src/views/MetadataTemplatesView.vue` (~350 行)

#### 页面 3: WorkVariantsView.vue
**路由：** `/app/works/:id/variants`
**功能：** 变体分组 CRUD + 变体管理 + 7 种比例生成
**布局：** 分组卡片 + 变体表格
**文件：** `frontend/src/views/WorkVariantsView.vue` (~300 行)

#### 页面 4: CullingView.vue
**路由：** `/app/works/cull`
**功能：** 网格缩略图 + 评分/颜色标签 + 批量操作
**布局：** 瀑布流网格 + 工具栏
**文件：** `frontend/src/views/CullingView.vue` (~350 行)

#### 页面 5: SubscriptionView.vue
**路由：** `/app/settings/subscriptions`
**功能：** 订阅等级 CRUD + 用户订阅管理
**布局：** 双 tab（等级/用户）+ 卡片展示
**文件：** `frontend/src/views/SubscriptionView.vue` (~300 行)

#### 页面 6: CommissionView.vue
**路由：** `/app/business/commissions`
**功能：** 委托看板（拖拽）+ 项目 CRUD + 消息
**布局：** 看板 5 列（待接单/进行中/待审核/已完成/已取消）
**文件：** `frontend/src/views/CommissionView.vue` (~400 行)

---

### 阶段 D: OAuth 前端集成

**改造：** `SettingsView.vue` 中"关联账号"tab

当前状态：3 个平台 (Google/微信/抖音) 的 `bound` 全部硬编码为 `false`，`bindProvider` 是 no-op。

**需要做的：**

1. 在 `onMounted` 中调用 `client.get('/auth/me')` 获取真实绑定状态
2. 更新 `providers` 数组的 `bound` 和 `account` 字段
3. 绑定按钮改为实际调用 `bindProvider(provider, data)`
4. 解绑按钮已经调用真实的 `systemApi.unbindProvider(provider)`

**后端需要同步改造：**
- `/auth/google/url` 返回真实 OAuth URL（当配置了 GOOGLE_CLIENT_ID 时）
- `/auth/wechat/qrcode` 返回真实二维码 URL
- `/auth/douyin/url` 返回真实 OAuth URL
- 如果未配置，返回带提示的配置页面链接

---

### 阶段 E: 外部平台配置界面

**改造：** `IntegrationsView.vue`

当前状态：所有 `connected` 硬编码为 `false`，`connectItem` 是 no-op toast。

**需要做的：**

1. 新增"平台配置"tab，列出所有有 gateway 骨架的平台：
   - Printful (POD) — 需要 PRINTFUL_API_KEY
   - Redbubble (POD) — 需要 REDBUBBLE_API_KEY
   - Spring (POD) — 需要 SPRING_API_KEY
   - Gelato (POD) — 需要 GELATO_API_KEY
   - Society6 (POD) — 需要 SOCIETY6_API_KEY
   - Zazzle (POD) — 需要 ZAZZLE_API_KEY

2. 每个平台显示配置表单（API Key 输入框 + 保存按钮 + 测试连接按钮）

3. 后端新增端点：
   - `PATCH /system/platform-config` — 保存平台配置到 system_settings
   - `GET /system/platform-config` — 获取平台配置状态（隐藏 key 值）

4. Gateway 文件已存在，只需确保 API key 从 system_settings 读取

**后端 gateway 文件清单（已存在）：**
- `gateway/printful.py` — Printful API
- `gateway/redbubble.py` — Redbubble API
- `gateway/spring.py` — Spring API
- `gateway/gelato.py` — Gelato API
- `gateway/society6.py` — Society6 API
- `gateway/zazzle.py` — Zazzle API

---

### 阶段 F: C2PA 前端存证入口

**C2PA 后端已完整实现**（纯 Python，无需额外库）：
- `POST /notary/c2pa/{work_id}/generate` — 生成 manifest + ECDSA 签名
- `GET /notary/verify/c2pa/{work_id}` — 验证 manifest

**需要做的：**

1. 在 `WorkDetailView.vue` 的"存证记录"section 中：
   - 添加"生成 C2PA 凭证"按钮
   - 调用 `generateC2PA(workId)`
   - 显示生成结果（manifest hash、签名时间、公钥指纹）

2. 添加"验证 C2PA 凭证"按钮：
   - 调用 `verifyC2PA(workId)`
   - 显示验证报告（签名有效、时间戳、身份）

3. 前端 API 已在阶段 C 中补充

---

### 阶段 G: 路由 + 侧边栏 + 顶部栏集成

#### G1. 路由注册 (`router/index.ts`)
在 `/app` children 中添加 6 个新路由：
```typescript
{ path: 'settings/watermarks', name: 'watermarks', component: () => import('@/views/WatermarkPresetsView.vue') },
{ path: 'settings/templates', name: 'metadata-templates', component: () => import('@/views/MetadataTemplatesView.vue') },
{ path: 'works/:id/variants', name: 'work-variants', component: () => import('@/views/WorkVariantsView.vue') },
{ path: 'works/cull', name: 'culling', component: () => import('@/views/CullingView.vue') },
{ path: 'settings/subscriptions', name: 'subscriptions', component: () => import('@/views/SubscriptionView.vue') },
{ path: 'business/commissions', name: 'commissions', component: () => import('@/views/CommissionView.vue') },
```

#### G2. 侧边栏新增菜单 (`AppSidebar.vue`)
在"经营管理"分区新增：
- `🔍` 审片视图 → `/app/works/cull`
- `📋` 委托看板 → `/app/business/commissions`

在"设置"分区新增：
- `🖊️` 水印预设 → `/app/settings/watermarks`
- `📄` 模板管理 → `/app/settings/templates`
- `💎` 订阅管理 → `/app/settings/subscriptions`

#### G3. 顶部栏标题映射 (`AppTopbar.vue`)
```typescript
watermarks: '水印预设管理',
'metadata-templates': '模板管理',
'work-variants': '作品变体',
culling: '审片视图',
subscriptions: '订阅管理',
commissions: '委托看板',
```

---

## 文件变更清单

### 新建文件 (6 个)

| 文件 | 行数 | 说明 |
|------|------|------|
| `views/WatermarkPresetsView.vue` | ~350 | 水印预设管理 |
| `views/MetadataTemplatesView.vue` | ~350 | 元数据模板管理 |
| `views/WorkVariantsView.vue` | ~300 | 作品变体管理 |
| `views/CullingView.vue` | ~350 | 审片视图 |
| `views/SubscriptionView.vue` | ~300 | 订阅管理 |
| `views/CommissionView.vue` | ~400 | 委托看板 |

### 修改文件 (约 20 个)

| 文件 | 变更 |
|------|------|
| `api/system.ts` | +25 个新 API 函数 |
| `api/notary.ts` | +2 个 C2PA 函数 |
| `router/index.ts` | +6 个路由 |
| `components/layout/AppSidebar.vue` | +6 个菜单项 |
| `components/layout/AppTopbar.vue` | +6 个标题 |
| `components/monetization/CampaignPanel.vue` | TS 修复 |
| `components/monetization/LicensePanel.vue` | TS 修复 x2 |
| `components/monetization/ListingCard.vue` | TS 修复 |
| `components/monetization/OrderPanel.vue` | TS 修复 |
| `components/monetization/PublicationPanel.vue` | TS 修复 |
| `components/monetization/SpecRemediationPanel.vue` | TS 修复 |
| `views/DashboardView.vue` | TS 修复 |
| `views/ListingDetailView.vue` | TS 修复 |
| `views/ListingListView.vue` | TS 修复 |
| `views/PublishView.vue` | TS 修复 |
| `views/SettingsView.vue` | TS 修复 + OAuth 集成 |
| `views/IntegrationsView.vue` | 平台配置界面 |
| `views/WorkDetailView.vue` | C2PA 入口 |
| `models/__init__.py` | +3 commission 模型导出 |

---

## 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| Commission 模型未导出到 __init__ | Alembic 可能不识别 | 先修模型导出，再跑迁移 |
| 6 个新页面代码量大 | 单次执行容易出错 | 分 3 批执行：TS 修复 → 管理页面 → OAuth/平台/C2PA |
| C2PA 需要作品文件路径 | 可能找不到文件 | 加 null guard 和错误提示 |
| 平台配置保存后需要重启 | 运行时读取 settings | 用 settings store 热加载 |

---

## 实施顺序

1. **批次 1 (A):** 修复 17 个 TS 错误 — 确保编译通过
2. **批次 2 (C):** 补充前端 API + 模型导出 — 为后续提供依赖
3. **批次 3 (B):** 6 个管理页面开发 — 核心新功能
4. **批次 4 (G):** 路由 + 导航集成 — 让新页面可访问
5. **批次 5 (D+E+F):** OAuth + 平台配置 + C2PA — 增强功能

## 验证方案

1. `vue-tsc --noEmit --skipLibCheck` 无错误
2. 6 个新页面均可从侧边栏点击访问
3. 每个管理页面的 CRUD 操作调用真实后端
4. OAuth 绑定/解绑显示真实状态
5. 平台配置保存后 gateway 可读取
6. C2PA 生成/验证端点返回正确数据
