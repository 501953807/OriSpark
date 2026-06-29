# OriStudio — 设计系统文档

## 项目概述

**OriStudio** 是一个个人创作者全链路助手工具，在个人电脑上运行的桌面应用（B/S 架构），帮助独立创作者完成：
作品管理 → 存证确权 → 侵权监测 → IP 登记 → 供应链协作 → 发布变现 的全流程闭环。

## 设计文件清单

| 文件 | 用途 | 说明 |
|------|------|------|
| `index.html` | 原型导航首页 | 卡片式入口，链接到各个原型页面 |
| `landing.html` | 产品营销首页 | 响应式 Landing Page，含 Hero/Feature/Proof/CTA |
| `app.html` | 应用工作台 (Dashboard) | 完整 SP 应用交互原型：侧边栏导航、6大模块切换、作品管理、统计数据、导入/编辑/删除作品、弹窗、拖拽上传 |
| `onboarding.html` | 新手指引 | 5 步交互式 Onboarding 引导，支持键盘导航、进度动画 |
| `login.html` | 登录注册 | 完整认证流程：登录/注册/忘记密码/2FA 验证码、社交登录、表单校验动画 |
| `settings.html` | 设置中心 | 个人资料、API 密钥配置、通知偏好、安全隐私、数据备份 |
| `integrations.html` | 第三方对接中心 | 存证平台（版权家/蚂蚁链/至信链）、侵权监测、电商发布、AI 模型连接 |
| `mq7tc56m-OriStudio-完整建设方案.html` | 完整建设方案 | 系统设计说明书（22张表、13个API、开发路线图） |
| `mq7tc56p-OriStudio-功能架构图.html` | 功能架构图 | SVG 架构图 |
| `mq7tc56p-OriStudio-技术架构图.html` | 技术架构图 | SVG 分层技术架构 |

## 设计令牌 (Design Tokens)

```css
:root {
  --bg:      oklch(98% 0.004 240);   /* 页面背景 */
  --surface: oklch(100% 0 0);       /* 卡片/面板背景 */
  --fg:      oklch(20% 0.02 240);   /* 主文字 */
  --muted:   oklch(50% 0.018 240);  /* 次要文字 */
  --border:  oklch(90% 0.006 240);  /* 边框 */
  --accent:  oklch(56% 0.12 170);   /* 主色调 (teal-green) */
  --accent2: oklch(62% 0.16 280);   /* 辅色调 (purple) */
  --grad1:   oklch(56% 0.12 170);   /* 渐变起点 */
  --grad2:   oklch(62% 0.16 260);   /* 渐变终点 (blue) */

  --font-display: 'Söhne', 'Avenir Next', system-ui, sans-serif;
  --font-body: system-ui, 'SF Pro Text', sans-serif;

  --radius-sm: 8px;
  --radius: 14px;
  --radius-lg: 20px;
  --radius-xl: 28px;
}
```

## 视觉方向

**Human / Approachable** (Airbnb / Duolingo 系统)：
- 干净的浅色背景 + 产品主导的色彩系统
- 宽松圆角 (14-28px) + 清晰层级
- 柔和阴影代替硬边框
- 主色调 teal-green + 蓝紫渐变强调

## 组件规范

### 按钮
- 主按钮: `background: linear-gradient(135deg, var(--grad1), var(--grad2))` + 白色文字 + 阴影
- 次级按钮: 白色背景 + `1px solid var(--border)`
- 幽灵按钮: 透明 + hover 时浅灰背景

### 卡片
- `background: var(--surface)` + `border: 1px solid var(--border)` + `border-radius: var(--radius-lg)`
- Hover: `transform: translateY(-2~6px)` + `box-shadow: 0 8px 32px oklch(0 0 0 / 0.07)`

### 面板 (Panel)
- 带 header/footer 的结构化容器
- border 分隔线

### 弹窗 (Modal)
- 半透明遮罩 + 居中卡片 + scale 动画入场
- 点击遮罩关闭

## 响应式断点

| 断点 | 行为 |
|------|------|
| >1024px | 完整布局，侧边栏+双栏面板 |
| 768-1024px | 2列统计，单栏面板 |
| 480-768px | 隐藏侧边栏（汉堡菜单），1-2列 |
| 360-480px | 单列，紧凑间距 |
| <360px | 最小化，保持可用性 |

## 交互模式

1. **页面切换**: Hash-based 模块切换 (`#works`, `#notary`, `#monitor`...)
2. **Toast 通知**: 底部居中/右侧浮动，2秒自动消失
3. **表单校验**: 实时错误提示 + shake 动画
4. **文件导入**: 模态框 + 拖拽区域 + 文件列表预览
5. **编辑面板**: 右侧滑出抽屉面板
6. **确认删除**: `confirm()` 对话框 + fade-out 动画
7. **进度模拟**: 分步进度条动画（发布流程）

## 技术方案（供编码参考）

- **前端**: Vue 3 + Naive UI 组件库
- **后端**: FastAPI (Python) + Uvicorn
- **数据库**: SQLite (22张核心表)
- **打包**: PyInstaller / Electron
- **AI**: Ollama 本地 LLM + 可选云端 API
- **存证**: 版权家 / 蚂蚁链 / 至信链 HTTP API + 用户扫码支付
- **监测**: 百度识图 / Google Vision API
- **发布**: Playwright 浏览器自动化 + OAuth

## 数据库核心表

```
works, work_versions, work_tags, projects
notary_records, certificates
monitor_tasks, monitor_results, evidence_packages
ip_registrations, trademark_classes
partners, orders, order_payments, order_communications, reminders
products, product_publishings, verified_marks, revenue_records
system_settings, audit_logs, backup_records
```
