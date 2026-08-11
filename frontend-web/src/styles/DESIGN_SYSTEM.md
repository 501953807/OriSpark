# OriStudio 设计系统 — 组件复用指南

## 文件结构

```
frontend-web/src/styles/
├── design-tokens.css   ← 全局 CSS 变量（颜色/字体/间距/圆角/阴影/动效）
├── themes.css          ← 三套主题预设（data-theme 切换）
├── components.css      ← 公共组件样式（按钮/卡片/表格/弹窗/表单/标签/分页）
├── layout.css          ← 布局系统（侧边栏/顶部栏/业务链/全局布局）
├── main.css            ← 入口（import 以上全部）+ 工具类
├── transitions.css     ← Vue 过渡动画
└── a11y.css            ← 无障碍（focus/skip-link/reduced-motion）
```

## 核心设计基准

### 颜色变量（在 `design-tokens.css` + `themes.css` 中定义）

| 变量 | 用途 |
|------|------|
| `--bg` | 页面背景 |
| `--bg-subtle` | 次级背景 |
| `--surface` | 卡片/面板背景 |
| `--surface-2` | 次级卡片背景 |
| `--surface-hover` | hover 状态背景 |
| `--fg` | 主文字颜色 |
| `--fg-subtle` | 次级文字 |
| `--muted` | 次要/禁用文字 |
| `--muted-dim` | 更淡的文字 |
| `--border` | 边框色 |
| `--border-strong` | 强调边框 |
| `--accent` | 品牌主色（按钮/链接/高亮） |
| `--accent-dim` | 品牌色的半透明版本（背景/阴影） |
| `--accent-fg` | 品牌色上的文字（通常为白色） |
| `--sidebar-bg` | 侧边栏背景（浅色） |
| `--sidebar-fg` | 侧边栏文字 |
| `--sidebar-fg-dim` | 侧边栏次要文字 |
| `--sidebar-active` | 侧边栏激活态背景 |
| `--success` / `--warning` / `--danger` / `--info` | 语义色 |
| `--grad1` / `--grad2` / `--grad3` | 渐变起始/中间/结束色 |

### 主题切换

在 `<html>` 上设置 `data-theme` 属性：

```ts
// Pinia store
import { useAppStore } from '@/stores/useAppStore'
const appStore = useAppStore()
appStore.setTheme('cold-white')  // 'cold-white' | 'warm-gray' | 'deep-blue'
```

顶部栏内置颜色色块主题切换器（`AppTopbar.vue`），点击色块可预览并切换主题。

### 配色方案

所有主题均使用 OKLCH 色彩空间，支持 Indigo/Materio 风格：

| 主题 | 主色调 | 侧边栏 | 适用场景 |
|------|--------|--------|----------|
| `cold-white` | 冷白 + 蓝紫 accent (oklch(54% 0.16 280)) | 白色 | 默认商务风 |
| `warm-gray` | 暖灰 + 琥珀 accent (oklch(54% 0.14 40)) | 暖白 | 温和阅读 |
| `deep-blue` | 深蓝 + 亮紫 accent (oklch(65% 0.13 280)) | 深蓝 | 夜间模式 |

渐变变量 (`--grad1`, `--grad2`, `--grad3`) 随主题自动切换，用于 Logo、头像、图表等渐变元素。

### 间距系统（4档）

| 变量 | 值 | 场景 |
|------|------|------|
| `--space-1` | 8px | 内边距、小间距 |
| `--space-2` | 16px | 组件间距、行间距 |
| `--space-3` | 24px | 区块间距 |
| `--space-4` | 32px | 页面分区间距 |

### 圆角

| 变量 | 值 |
|------|------|
| `--radius-sm` | 6px |
| `--radius` | 8px |
| `--radius-lg` | 12px |
| `--radius-xl` | 16px |
| `--radius-full` | 9999px |

### 字体

| 变量 | 字体 | 用途 |
|------|------|------|
| `--font-display` | Noto Serif SC, PingFang SC | 标题 |
| `--font-body` | Noto Sans SC, PingFang SC | 正文 |
| `--font-mono` | JetBrains Mono, Fira Code | 代码/数据 |

## 公共组件用法

### 按钮

```html
<button class="btn btn-primary">主要操作</button>
<button class="btn btn-secondary">次要操作</button>
<button class="btn btn-ghost">幽灵按钮</button>
<button class="btn btn-danger">危险操作</button>

<!-- 尺寸 -->
<button class="btn btn-primary btn-sm">小按钮</button>
<button class="btn btn-primary btn-xs">极小按钮</button>
<button class="btn btn-primary btn-lg">大按钮</button>
<button class="btn btn-primary btn-full">全宽按钮</button>
```

### 卡片

```html
<div class="card">内容区域</div>
<div class="card card-hover">悬停有上浮效果</div>
```

### 数据表格

```html
<table class="data-table">
  <thead>
    <tr>
      <th class="table-header">列名</th>
      <th class="table-header">数值</th>
    </tr>
  </thead>
  <tbody>
    <tr class="table-row">
      <td class="table-cell">数据 A</td>
      <td class="table-cell">100</td>
    </tr>
  </tbody>
</table>
<!-- 斑马纹 -->
<table class="data-table table-striped">
```

### 弹窗 Modal

```html
<div class="modal-overlay" @click.self="show = false">
  <div class="modal-card">
    <div class="modal-header">
      <h3>弹窗标题</h3>
      <button class="modal-close-btn" @click="show = false">×</button>
    </div>
    <div class="modal-body">内容区域</div>
    <div class="modal-footer">
      <button class="btn btn-secondary" @click="show = false">取消</button>
      <button class="btn btn-primary">确认</button>
    </div>
  </div>
</div>
```

### 表单

```html
<div class="form-group">
  <label class="form-label">标签名称</label>
  <input class="form-input" v-model="value" placeholder="请输入" />
  <span class="form-hint">提示文字</span>
  <span class="form-error">错误信息</span>
</div>
<textarea class="form-textarea" v-model="text"></textarea>
<select class="form-select" v-model="val">
  <option value="a">选项 A</option>
  <option value="b">选项 B</option>
</select>
<!-- 错误状态 -->
<input class="form-input form-input-error" v-model="value" />
```

### 标签/徽章

```html
<span class="badge badge-default">默认</span>
<span class="badge badge-success">成功</span>
<span class="badge badge-warning">警告</span>
<span class="badge badge-danger">危险</span>
<span class="badge badge-info">信息</span>
<span class="badge badge-accent">强调</span>
```

### 标签页 Tabs

```html
<div class="tabs">
  <button :class="['tab', { active: active === 0 }]" @click="active = 0">标签一</button>
  <button :class="['tab', { active: active === 1 }]" @click="active = 1">标签二</button>
</div>
<div class="tab-content">
  <div v-if="active === 0">内容一</div>
  <div v-if="active === 1">内容二</div>
</div>
```

### 分页 Pagination

```html
<div class="pagination">
  <button class="page-btn" disabled>上一页</button>
  <button class="page-btn active">1</button>
  <button class="page-btn">2</button>
  <button class="page-btn">3</button>
  <button class="page-btn">下一页</button>
  <span class="page-info">共 100 条</span>
</div>
```

### 提示消息 Toast

```ts
// 全局 toast（通过 window.$toast 注入，见 EnhancedToast.vue）
;(window as any).$toast?.show('操作成功', 'success')
;(window as any).$toast?.show('操作失败', 'error')
;(window as any).$toast?.show('请稍候', 'info')
;(window as any).$toast?.show('注意警告', 'warning')
```

### 状态消息

```html
<div class="status-msg status-msg-success">操作成功</div>
<div class="status-msg status-msg-warning">请注意</div>
<div class="status-msg status-msg-error">发生错误</div>
<div class="status-msg status-msg-info">提示信息</div>
```

### 空状态

```html
<div class="empty-state">
  <div class="empty-state-icon">📭</div>
  <div class="empty-state-title">暂无数据</div>
  <div class="empty-state-desc">描述文字</div>
  <button class="btn btn-primary">执行操作</button>
</div>
```

### 骨架屏

```html
<div class="skeleton" style="height: 16px; width: 200px;"></div>
```

## 布局系统

### 整体布局

```html
<div class="app-root">
  <aside class="sidebar"><!-- 侧边栏 --></aside>
  <div class="main-content">
    <header class="topbar drag-region"><!-- 顶部栏 --></header>
    <nav class="chain-bar"><!-- 业务链栏 --></nav>
    <main class="page-content"><!-- 页面内容 --></main>
  </div>
</div>
```

### 栅格系统

```html
<div class="grid-12">
  <div class="grid-col-3">占 3 列</div>
  <div class="grid-col-6">占 6 列</div>
  <div class="grid-col-3">占 3 列</div>
</div>
```

### 统计卡片网格

```html
<div class="stat-grid">
  <div class="stat-card">
    <span class="stat-icon">📊</span>
    <div>
      <div class="stat-label">标签</div>
      <div class="stat-value">1,234</div>
      <div class="stat-change">↑ 12%</div>
    </div>
  </div>
</div>
```

### 通用工具类

```
.container    → max-width: 1440px, 居中
.flex / .flex-col / .items-center / .justify-between
.gap-1 / .gap-2 / .gap-3      → 间距
.mt-1 / .mt-2 / .mb-1 / .mb-2  → 外边距
.p-2 / .p-3                    → 内边距
.text-muted / .text-fg / .text-accent
.w-full / .h-full
.divider                       → 水平分割线
```

## Electron 适配说明

- Electron 使用 `frame: false` + `titleBarStyle: 'hidden'`（macOS）
- 顶部栏 `.topbar.drag-region` 启用 `-webkit-app-region: drag`
- 顶部栏内所有可交互元素自动标记 `.topbar.drag-region .btn` 等排除拖拽
- 窗口控件（最小化/最大化/关闭）通过 `window.oristudio` IPC API 调用：
  ```ts
  await (window as any).oristudio.minimize()
  await (window as any).oristudio.maximize()
  await (window as any).oristudio.close()
  ```
- 双端样式完全同源：sidebar 白色背景 + 阴影分隔，与网页端一致

## 禁止事项

1. ❌ 直接在组件中写硬编码颜色值 — 使用 CSS 变量
2. ❌ 在组件中定义自己的间距值 — 使用 `--space-*` 变量
3. ❌ 创建与现有设计不一致的组件样式 — 优先复用已有类
4. ❌ 在 `.vue` 文件的 `<style scoped>` 中使用固定的 oklch/hex 颜色 — 使用变量
5. ❌ 忽略 `data-theme` 属性切换 — 确保所有样式通过变量控制
6. ❌ 使用旧主题色值（如 oklch(52% 0.15 260)）— 使用新的 Indigo 色值

## 新增组件检查清单

新建组件前确认：
- [ ] 颜色全部使用 CSS 变量（`var(--xxx)`）
- [ ] 间距使用 `--space-*` 变量或工具类
- [ ] 圆角使用 `--radius-*` 变量
- [ ] 阴影使用 `--shadow-*` 变量
- [ ] 过渡动画使用 `--transition-*` 变量
- [ ] 不引入新的第三方 UI 库
- [ ] 遵循 4 档间距梯度
