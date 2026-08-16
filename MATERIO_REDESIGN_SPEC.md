# Materio Style Redesign — OriStudio frontend-web 全面对齐方案

**日期**: 2026-08-16
**分支**: feat/materio-style-redesign
**参照站**: https://demos.themeselection.com/materio-vuetify-vuejs-admin-template/demo-2/
**目标**: 将 frontend-web 全局风格对齐 Materio Demo-2 Vuetify Admin Template

---

## 一、问题诊断

### 1.1 核心根因

项目同时存在**两套设计令牌系统**且均不完整：

| 系统 | 文件 | 主色 | 间距步进 | 状态 |
|------|------|------|---------|------|
| Hope UI (旧) | `design-tokens.css` | #3A57E8 | 8px | 仍在被多处引用 |
| Materio (新) | `materio-tokens.css` | #5585FF | 4px | 部分生效，未全面覆盖 |

两套 token 冲突导致颜色、间距、圆角等视觉属性在页面间不一致。

### 1.2 具体问题清单

| # | 问题 | 影响范围 | 严重度 |
|---|------|---------|--------|
| P1 | 双 Token 系统冲突，主色不一致 | 全站 | 高 |
| P2 | 侧边栏激活指示条为直角，非 Materio 圆角样式 | MaterioLayout | 高 |
| P3 | 侧边栏分组折叠使用 display toggle，无过渡动画 | MaterioLayout | 高 |
| P4 | 顶部栏缺少垂直导航 Pills（Materio demo-2 特征） | MaterioLayout | 中 |
| P5 | MInput 使用原生 input，无浮动标签 | 所有表单页面 | 高 |
| P6 | MBtn 无涟漪效果，点击反馈弱 | 全站 | 中 |
| P7 | MTable 无斑马纹行、排序箭头无过渡 | 数据列表页面 | 中 |
| P8 | MCard hover 动效不够丝滑 | 全站 | 低 |
| P9 | 登录页左侧装饰区过于简陋 | LoginView | 中 |
| P10 | 动效 timing 不统一（部分用 ease，部分用 cubic-bezier） | 全站 | 中 |
| P11 | 旧布局组件未清理（AppLayout/AppSidebar/DynamicSidebar/CreatorSidebar） | 目录冗余 | 低 |
| P12 | 无 MTabs/MSelect 组件，各页面自实现风格不一 | 多页面 | 高 |

### 1.3 参照站关键视觉特征（demo-2）

- **主色**: #5585FF (primary), #2A52B0 (darken-2)
- **侧边栏**: 白色、256px、分组折叠+箭头旋转、左侧圆角竖条激活指示、底部用户卡片
- **顶部栏**: 白色 sticky、垂直导航 Pills（Dashboards/Sales等）、圆角搜索框、Material Icons
- **卡片**: 圆角 12px、柔和阴影 elevation-1、hover 微上移 2px
- **按钮**: 4px 圆角、elevated/flat/outlined/text/tonal 五种变体、涟漪
- **输入框**: Filled 风格（背景 #F4F5FA）、浮动标签、底部边框线 focus 时变蓝
- **表格**: 表头浅灰背景 #F6F7FB、斑马纹行交替、悬停高亮
- **Tabs**: 下划线指示器（sliding indicator）、transition 250ms
- **字体**: Inter + Source Han Sans SC
- **阴影**: `0 0.125rem 0.25rem rgba(46,38,61,0.16)` 等 Material 层级
- **动效**: `cubic-bezier(0.4, 0, 0.2, 1)` Material standard easing

---

## 二、分阶段改造方案

### 阶段一：设计令牌统一（Token Unification）

**目标**: 建立单一 Materio 风格的 token 源，消除冲突

**变更文件**:
- `frontend-web/src/styles/materio-tokens.css` — 扩充完整 token 集
- `frontend-web/src/styles/design-tokens.css` — 标记废弃或迁移引用
- `frontend-web/src/styles/themes.css` — 移除与 materio-tokens 冲突的定义

**具体动作**:
1. materio-tokens.css 补全缺失 token:
   - 补充 surface-2 (#EEF0F4)、surface-bright
   - 补充完整的 grey scale (50-900, 9级)
   - 补充 on-surface-variant
   - 补充 opacity 值 (hover: 0.04, activated: 0.16, focus: 0.1, disabled: 0.4)
2. design-tokens.css 中的 `--primary`, `--accent`, `--sidebar-*` 等与 materio-tokens 冲突的变量标记为废弃
3. themes.css 中的三套主题保留但重构为基于 materio-tokens 的变体
4. 全局搜索替换所有使用旧 token 的文件

**验收标准**:
- `grep --include="*.vue" --include="*.css" -r "design-tokens\| Hope UI\|hope-ui" frontend-web/src` 无产出
- 所有页面主色统一为 #5585FF

### 阶段二：布局与导航对齐（Layout & Navigation）

**目标**: MaterioLayout 精细化，对齐 demo-2 的侧边栏和顶部栏

**变更文件**:
- `frontend-web/src/layouts/MaterioLayout.vue` — 主要改造
- `frontend-web/src/styles/layout.css` — 清理或标记废弃

**具体动作**:

#### 2.1 侧边栏改进
- 激活项左侧竖条: 从 `border-left: 3px solid` 改为圆角矩形伪元素（`border-radius: 0 2px 2px 0`，`width: 3px`）
- 分组折叠动画: 从 `v-show` 直接切换改为 `max-height` transition（0 → N×item-height）
- Collapsed 状态: 添加 tooltip 悬停提示（使用 CSS `title` 属性或自定义 tooltip 组件）
- 用户卡片底部: 头像渐变色统一为 `linear-gradient(135deg, #5585FF, #2A52B0)`

#### 2.2 顶部栏改进
- 添加垂直导航 Pill 行（在 MaterioLayout 中，在 topbar 下方或替代当前 breadcrumb）
- 搜索框: 圆角 8px、背景 #F4F5FA、Material Icons 前缀 `search`
- 通知铃铛: 添加红点（绝对定位小圆点，右上角偏移）
- 用户菜单下拉: 添加过渡动画（opacity + translateY）

#### 2.3 动效统一
- 所有 transition 统一使用 `cubic-bezier(0.4, 0, 0.2, 1)`
- sidebar collapse: 250ms
- menu expand/collapse: 300ms
- card hover: 200ms

**验收标准**:
- 侧边栏折叠/展开动效丝滑（非突变）
- 激活菜单项有圆角左侧竖条
- 顶部栏有导航 Pills
- 所有动效使用统一 easing

### 阶段三：组件库升级（Component Library）

**目标**: M-* 组件对齐 Materio 交互细节

**变更文件**:
- `frontend-web/src/components/ui/MInput.vue` — 浮动标签 + Filled 风格
- `frontend-web/src/components/ui/MBtn.vue` — 涟漪效果
- `frontend-web/src/components/ui/MTable.vue` — 斑马纹 + 排序动画
- `frontend-web/src/components/ui/MCard.vue` — hover 动效优化
- `frontend-web/src/components/ui/MChip.vue` — Material 风格
- 新增 `frontend-web/src/components/ui/MTabs.vue`
- 新增 `frontend-web/src/components/ui/MSelect.vue`
- 新增 `frontend-web/src/components/ui/MField.vue`（通用字段容器，含浮动标签逻辑）

**具体动作**:

#### MInput — 浮动标签输入框
```
结构: <div class="m-field">
  <input class="m-field__input" ... />
  <label class="m-field__label">邮箱</label>
  <div class="m-field__line" />
</div>
```
- 默认背景: #F4F5FA（filled）
- Focus 时: label 上移 + 缩小 + 变 primary 色，底部线条变 primary
- 图标前缀/后缀支持
- 错误状态: 红色边框 + 错误提示文字

#### MBtn — 涟漪按钮
- 添加 ripple overlay（点击时从点击位置扩散的圆形渐变）
- 保持现有 variant/size 系统不变
- 涟漪颜色: white (elevated/flat), primary (outlined/text/tonal)

#### MTable — 斑马纹表格
- 偶数行背景: rgba(85, 133, 255, 0.03)
- 表头: background #F6F7FB, font-weight 600
- 排序图标: 上箭头/下箭头 SVG，transition 150ms
- 行悬停: rgba(85, 133, 255, 0.05)

#### MTabs — 下划线 Tabs
- 固定宽度 Tab 项
- 活动指示器: 蓝色下划线，通过 transform: translateX 滑动
- 支持 icon + label
- transition: 250ms cubic-bezier(0.4, 0, 0.2, 1)

#### MSelect — 浮动标签选择框
- 复用 MField 结构
- 自定义下拉选项（非原生 select）
- 支持多选 chip 显示

**验收标准**:
- MInput 有浮动标签效果
- MBtn 点击有涟漪扩散
- MTable 有斑马纹和排序动画
- MTabs 有滑动下划线指示器
- MSelect 有浮动标签 + 自定义下拉

### 阶段四：认证页面重构（Auth Pages）

**目标**: 登录/注册页对齐 Materio auth 风格

**变更文件**:
- `frontend-web/src/views/LoginView.vue`
- `frontend-web/src/views/VerifyView.vue`（如有注册）

**具体动作**:
- 左侧面板: 改为渐变背景（#5585FF → #2A52B0）+ 抽象几何图形
- 右侧面板: 使用 MInput 浮动标签组件替代原生 input
- OAuth 按钮: 对齐 Materio outlined button 风格
- 表单验证错误提示: 使用 MAlert 红色提示条

### 阶段五：视图页面清理（View Pages Cleanup）

**目标**: 逐步将各视图页面中的旧样式替换为 Materio 风格

**变更文件**: 涉及 20+ 个 View 文件

**策略**:
- 优先改造高频访问页面：DashboardView、WorksView、IprView、ContractMarketView
- 使用新的 M-* 组件替代内联样式
- 统一卡片间距：padding 24px（space-6），gap 16px（space-4）
- 确保所有页面使用 materio-tokens 而非旧 token

**不在本期范围内**：
- backend API 改动
- Electron 桌面端特定适配
- 微信小程序映射

---

## 三、实施顺序与依赖

```
阶段一 (Tokens) → 阶段二 (Layout) → 阶段三 (Components) → 阶段四 (Auth) → 阶段五 (Views)
     ↓                   ↓                    ↓                ↓            ↓
  可独立验证          可独立验证            可独立验证         可独立验证    最后执行
```

**每阶段完成后**:
1. 本地启动 `npm run dev`  (:5174)
2. 截图对比 Materio demo-2 对应页面
3. 确认无回归（功能正常）
4. commit 后进入下一阶段

---

## 四、关键 CSS 对照表

| 属性 | Materio demo-2 | 当前 OriStudio | 目标值 |
|------|---------------|---------------|--------|
| Primary | #5585FF | #3A57E8 / #5585FF 混用 | #5585FF |
| Sidebar width | 256px | 259px | 256px |
| Sidebar collapsed | 80px | 60px | 80px |
| Topbar height | 64px | 66px | 64px |
| Border radius sm | 6px | 4px | 6px |
| Border radius md | 10px | 8-10px 混用 | 10px |
| Border radius lg | 12px | 12px | 12px |
| Space unit | 4px base | 8px base | 4px base |
| Font size base | 15px (0.9375rem) | 14px | 15px |
| Shadow key color | rgba(46,38,61,...) | rgba(35,45,66,...) | rgba(46,38,61,...) |
| Transition | 250ms cubic-bezier(0.4,0,0.2,1) | 混合 | 统一 |
| Group header font | 0.75rem uppercase tracking 0.05em | 不一致 | 统一 |
| Active item indicator | 3px left bar, rounded | 3px left border | 圆角伪元素 |

---

## 五、风险提示

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 旧 token 残留导致部分页面样式异常 | 视觉不一致 | 阶段一完成前不做后续阶段 |
| MInput 浮动标签与现有表单兼容 | 需要逐一适配 | 先做 POC 验证，再批量替换 |
| MaterioLayout 修改影响 Electron 端 | 桌面端可能异常 | Electron 复用同一代码，需同步测试 |
| 视图页面改造引入回归 | 功能异常 | 每阶段独立测试，保留 git 快照 |
| 20+ 视图页面改造工作量大 | 周期长 | 按优先级分批，先高频后低频 |

---

## 六、验收标准

### 6.1 视觉验收
- [ ] 侧边栏与 Materio demo-2 截图对比，差异率 < 10%
- [ ] 顶部栏导航 Pills 存在且样式对齐
- [ ] 所有 M-* 组件在浏览器中展示效果对标 Materio 对应组件
- [ ] 登录页左右分栏布局对齐
- [ ] 动效在所有页面一致（easing + timing）

### 6.2 功能验收
- [ ] 侧边栏折叠/展开正常
- [ ] 分组折叠/展开正常
- [ ] 搜索功能正常
- [ ] 用户菜单下拉正常
- [ ] 所有路由跳转正常
- [ ] 表单提交正常
- [ ] 深色/浅色主题切换正常

### 6.3 代码验收
- [ ] `design-tokens.css` 不再被任何 .vue/.css 文件 import
- [ ] 所有 token 引用统一使用 materio-tokens.css
- [ ] 无 hardcoded 颜色值（使用 CSS variable）
- [ ] 无 console.log 遗留
- [ ] TypeScript 无编译错误
