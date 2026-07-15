# Phase 2+3 测试报告整改实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成测试报告中所有 P2 和 P3 问题的整改，使系统达到内部试用标准。

**Architecture:** 基于 Vue 3 + TypeScript + Vite + Pinia 的前端单页应用。P2/P3 问题大部分已有基础实现，本次重点是补齐缺失的交互细节、文案说明和状态反馈。

**Tech Stack:** Vue 3 (Composition API), TypeScript, Vite, Pinia, vue-router, CSS variables (OKLCH), scoped CSS

## Global Constraints

- 所有修改遵循 `docs/DESIGN.md` 和 `docs/modules-v3/` 模块设计文档
- 模块命名一致：权益保护/商业撮合/内容分发等
- 代码风格遵循 `.claude/rules/common/coding-style.md`（不可变性、KISS、DRY、YAGNI）
- 文件组织：MANY SMALL FILES > FEW LARGE FILES，单文件不超过 800 行
- 不使用 `any`，使用 `unknown` + 类型收窄
- 无 `console.log` 语句
- 不新建文档文件，所有变更必须是代码实现

---

## 审计结论

经过代码审计，测试报告中 24 项问题的实际状态如下：

| 类别 | 问题数 | 状态 |
|------|--------|------|
| P0 致命 (1项) | 1 | ✅ 一期已完成 |
| P1 严重 (9项) | 9 | ✅ 一期已完成 |
| P2 一般 (8项) | 8 | ✅ 全部已实现（含智能助手/费用计算器/回收站/项目分组） |
| P3 轻微 (6项) | 6 | ⚠️ 部分已实现，需补齐交互细节 |

### 本次需处理的 P3 任务 (4项)

1. Task 1: 侧边栏折叠按钮 hover 临时展开（折叠态悬停展开）
2. Task 2: 侧边栏菜单 hover 气泡说明（角标释义）
3. Task 3: 业务链步骤序号显示
4. Task 4: 免责声明弹窗 "本次登录不再提示" 选项

### 已实现的 P2/P3 项（无需修改）

- ✅ 面包屑导航（Breadcrumb.vue 已实现，覆盖 21 个路由）
- ✅ 侧边栏持久化（localStorage `oristudio-sidebar-collapsed`）
- ✅ 深色模式持久化 + 系统跟随（localStorage `oristudio-theme`）
- ✅ 深色模式按钮 hover 提示（已有 `:title` + `aria-label`）
- ✅ 回收站规则说明（RecycleBinView.vue 已有 30 天保留说明）
- ✅ 项目分组规则说明（ProjectsView.vue 已有分组用途说明）
- ✅ 智能助手预填面板（IprView.vue assistant tab 已有完整 wizard + 作品选择 + 预填按钮 + 结果展示）
- ✅ 费用计算器（IprView.vue calculator tab 已有 IP 类型/辖区/分类选择 + 计算按钮 + 结果明细）

---

### Task 1: 侧边栏折叠态 hover 临时展开

**Files:**
- Modify: `frontend/src/components/layout/AppSidebar.vue` (template + script + style)

**Interfaces:**
- Consumes: `appStore.sidebarCollapsed`
- Produces: 折叠状态下鼠标悬停侧边栏边缘时临时展开到完整宽度，鼠标离开后恢复折叠

**Details:**
1. 在 `<aside>` 上监听 `mouseenter`/`mouseleave`，当处于折叠态时添加临时展开 class
2. CSS: `.sidebar.collapsed.hover-expand { width: var(--sidebar-w); }`
3. transition 保持 0.3s ease 平滑过渡

```vue
<!-- Template: add mouseenter/leave handlers -->
<aside :class="['sidebar', { collapsed: isCollapsed, 'mobile-visible': mobileVisible, 'hover-expand': isCollapsed && isHovering }]" ...>

<!-- Add ref -->
const isHovering = ref(false)

<!-- Add handlers -->
@mouseenter="isHovering = true"
@mouseleave="isHovering = false"
```

```css
/* Add to .sidebar.collapsed */
.sidebar.collapsed.hover-expand {
  width: var(--sidebar-w);
}
```

- [ ] **Step 1: 添加折叠态 hover 临时展开功能**
  - 在 `<aside>` 上添加 `@mouseenter`/`@mouseleave` 事件绑定
  - 添加 `isHovering` ref 控制 hover-expand class
  - 仅在 `isCollapsed && isHovering` 时应用 hover-expand
  - CSS 添加 `.sidebar.collapsed.hover-expand { width: var(--sidebar-w); }`
  - 修改文件: `frontend/src/components/layout/AppSidebar.vue`

- [ ] **Step 2: 验证构建**
  - Run: `npx vue-tsc --noEmit`
  - Expected: 零错误

---

### Task 2: 侧边栏菜单 hover 气泡说明 + 角标释义

**Files:**
- Modify: `frontend/src/components/layout/AppSidebar.vue:14-90` (all router-links)

**Interfaces:**
- Consumes: 无
- Produces: 每个菜单项增加 `:title` 属性作为 hover 说明

**Details:**
为每个侧边栏菜单项添加 `title` 属性，用户 hover 时浏览器原生显示说明文字：

```vue
<!-- 概览 -->
<router-link to="/app" :title="'工作台：系统概览与数据统计'" ...>

<!-- 创意资产 -->
<router-link to="/app/works" :title="'创意资产：原创作品素材存储仓库，IP运营起始入口'" ...>

<!-- IP登记 -->
<router-link to="/app/ipr" :title="'IP登记：版权确权、商标注册、外观设计专利申请'" ...>

<!-- 权利保护 -->
<router-link to="/app/rights" :title="'权利保护：侵权监测、维权投诉、证据存证'" ...>

<!-- 内容分发 -->
<router-link to="/app/publish" :title="'内容分发：多平台内容发布与管理'" ...>

<!-- 商业转化 -->
<router-link to="/app/supply" :title="'商业转化：授权变现、交易撮合、合同管理'" ...>

<!-- 经营数据 -->
<router-link to="/app/business" :title="'经营数据：业务收入统计与数据分析'" ...>

<!-- 回收站 -->
<router-link to="/app/recycle" :title="'回收站：已删除作品的临时存放区，保留30天'" ...>

<!-- 项目分组 -->
<router-link to="/app/projects" :title="'项目分组：按系列/客户/年份组织作品'" ...>

<!-- 审片视图 -->
<router-link to="/app/works/cull" :title="'审片视图：作品批量筛选与审核'" ...>

<!-- 委托看板 -->
<router-link to="/app/business/commissions" :title="'委托看板：客户委托任务管理'" ...>

<!-- 偏好设置 -->
<router-link to="/app/settings" :title="'偏好设置：主题、语言、通知等系统配置'" ...>

<!-- 第三方对接 -->
<router-link to="/app/integrations" :title="'第三方对接：连接外部平台与服务'" ...>

<!-- 水印预设 -->
<router-link to="/app/settings/watermarks" :title="'水印预设：自定义图片/视频水印样式'" ...>

<!-- 模板管理 -->
<router-link to="/app/settings/templates" :title="'模板管理：合同/协议模板管理'" ...>

<!-- 订阅管理 -->
<router-link to="/app/settings/subscriptions" :title="'订阅管理：查看和升级会员订阅'" ...>
```

- [ ] **Step 1: 为所有侧边栏菜单项添加 hover title 属性**
  - 修改 `AppSidebar.vue` 中所有 `<router-link>` 标签
  - 每个添加 `:title` 属性，值为中文说明文案
  - 修改文件: `frontend/src/components/layout/AppSidebar.vue`

- [ ] **Step 2: 验证构建**
  - Run: `npx vue-tsc --noEmit`
  - Expected: 零错误

---

### Task 3: 业务链步骤序号显示

**Files:**
- Modify: `frontend/src/components/layout/BusinessChainBar.vue`

**Interfaces:**
- Consumes: 现有 `steps` computed, `v-for="(step, idx) in steps"`
- Produces: 每个步骤显示序号圆形徽章 (1/2/3/4/5/6)

**Details:**
在 `.chain-step` 内添加序号徽章，根据步骤状态变色：

```vue
<!-- Inside .chain-step router-link -->
<span class="step-num">{{ idx + 1 }}</span>
<span class="step-icon">{{ step.done ? '✅' : step.icon }}</span>
<span class="step-label">{{ step.label }}</span>
```

```css
.step-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  font-size: 0.65rem;
  font-weight: 700;
  background: var(--border);
  color: var(--muted);
  flex-shrink: 0;
}
.chain-step.active .step-num {
  background: rgba(255,255,255,0.3);
  color: #fff;
}
.chain-step.done .step-num {
  background: var(--accent);
  color: #fff;
}
```

- [ ] **Step 1: 业务链步骤增加序号显示**
  - 在 `BusinessChainBar.vue` 的 `.chain-step` 内添加 `<span class="step-num">{{ idx + 1 }}</span>`
  - 添加 `.step-num` CSS 样式（默认灰色、active 白色半透明、done 绿色）
  - 修改文件: `frontend/src/components/layout/BusinessChainBar.vue`

- [ ] **Step 2: 验证构建**
  - Run: `npx vue-tsc --noEmit`
  - Expected: 零错误

---

### Task 4: 免责声明弹窗增加"本次登录不再提示"

**Files:**
- Modify: `frontend/src/views/IprView.vue` (disclaimer modal + script)

**Interfaces:**
- Consumes: `disclaimersAccepted` ref, `acceptDisclaimers()` function, `localStorage`
- Produces: 弹窗底部增加 checkbox，勾选后 localStorage 写入 `ipr_disclaimer_accepted = 'true'` 且会话内不再弹出

**Details:**
当前 IprView.vue 的免责声明弹窗没有"不再提示"选项，每次进入都弹出。

1. 在 disclaimer modal footer 中添加 checkbox：

```vue
<!-- Replace lines 20-22 -->
<div class="disclaimer-footer">
  <label class="disclaimer-checkbox-label">
    <input type="checkbox" v-model="dismissDisclaimers" />
    <span>本次登录不再提示</span>
  </label>
  <button class="btn btn-primary btn-lg" @click="acceptDisclaimers">
    我已阅读并同意
  </button>
</div>
```

2. 添加 `dismissDisclaimers` ref 并修改 `acceptDisclaimers`：

```typescript
const dismissDisclaimers = ref(false)

function acceptDisclaimers() {
  // Always persist to localStorage
  localStorage.setItem('ipr_disclaimer_accepted', 'true')

  // If checkbox is checked, also accept via API
  if (dismissDisclaimers.value) {
    // POST to /api/system/disclaimers/accept
  }

  // Close modal
  disclaimersAccepted.value = false
  dismissDisclaimers.value = false
}
```

3. 添加 checkbox 样式：

```css
.disclaimer-checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: var(--muted);
  cursor: pointer;
  margin-bottom: 12px;
}
.disclaimer-checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
}
```

- [ ] **Step 1: 免责声明弹窗增加 checkbox**
  - 在 `IprView.vue` disclaimer modal footer 添加 checkbox + label
  - 添加 `dismissDisclaimers` ref（初始 `ref(false)`）
  - 修改 `acceptDisclaimers` 函数：始终写 localStorage，checkbox 勾选时也调 API
  - 添加 `.disclaimer-checkbox-label` CSS 样式
  - 修改文件: `frontend/src/views/IprView.vue`

- [ ] **Step 2: 验证构建**
  - Run: `npx vue-tsc --noEmit`
  - Expected: 零错误

---

## 执行顺序

4 个 Task 互相独立，可并行执行。每个 Task 完成后验证构建。

## 验证清单

- [ ] `npx vue-tsc --noEmit` 零错误
- [ ] `npx vite build` 成功
- [ ] 侧边栏折叠态 hover 临时展开
- [ ] 侧边栏菜单 hover 有说明气泡
- [ ] 业务链步骤有数字序号
- [ ] 免责声明弹窗有"不再提示"选项
- [ ] 智能助手/费用计算器 UI 确认完整（已实现）
- [ ] 回收站/项目分组说明文案确认（已实现）
