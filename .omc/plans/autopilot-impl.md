# UX/UI 重设计实施计划

> **日期**: 2026-06-13 | **状态**: Phase 1 完成 → Phase 2 执行

## Phase 1: 菜单+路由重构 (立即)

### T1.1: 重写侧边栏菜单结构
**文件**: `frontend/src/components/layout/AppSidebar.vue`
- 合并 "存证确权" + "侵权监测" → "权利保护"
- 重命名 "产品数据" → "内容分发"
- 新增 "📈 经营管理" → `/app/business`
- 新增 "📂 项目分组" → `/app/projects` (修复孤儿页面)
- 新分组: 概览 | 核心业务 | 经营 | 设置

### T1.2: 修改路由表
**文件**: `frontend/src/router/index.ts`
- 新增 `/app/business` → `BusinessView.vue`
- 保留 `/app/projects` (已存在)

### T1.3: 修改 Topbar 标题
**文件**: `frontend/src/components/layout/AppTopbar.vue`
- 补全 `business: '经营管理'`, `projects: '项目分组'`
- 统一 sidebar 和 topbar 命名

## Phase 2: 经营管理中心 (第3-4天)

### T2.1: 新建 BusinessView.vue
**文件**: `frontend/src/views/BusinessView.vue` (NEW)
- 聚合仪表盘: 4 StatCards (总收入/本月收入/产品数/合作伙伴)
- 5 Tabs: 收入 | 合作伙伴 | 订单 | 通知 | 分析
- 收入Tab: 手动登记+CSV导入+ECharts图表
- 合作伙伴Tab: Partner CRUD+类型筛选
- 订单Tab: Order CRUD+状态流转
- 通知Tab: 分类筛选+关联跳转

### T2.2: 新建 store + API layer
**文件**: `frontend/src/stores/useBusinessStore.ts` (NEW)
**文件**: `frontend/src/api/business.ts` (NEW)

### T2.3: 从 SupplyView 移除收入/合作伙伴Tab
**文件**: `frontend/src/views/SupplyView.vue`
- 移除 "变现仪表盘"(收入)、"工厂"、"订单" Tab
- 这些功能迁移到 BusinessView

### T2.4: Dashboard 增强
**文件**: `frontend/src/views/DashboardView.vue`
- 增加业务总览卡片
- 空状态增加CTA

## Phase 3: IP登记交互重设计 (第5-6天)

### T3.1: 重写 IprView.vue
**文件**: `frontend/src/views/IprView.vue`
- 免责声明: Modal → Banner (首次acceptance)
- 操作区: IP类型选择器 → 辖区Tab切换 → 指引卡片
- 指引卡片: 折叠面板 (材料/流程/费用)
- 智能助手整合
- 我的登记记录+CRUD

### T3.2: 新建IPR组件
- `components/ipr/IpTypeSelector.vue` (NEW)
- `components/ipr/JurisdictionGuide.vue` (NEW)
- `components/ipr/SmartAssistant.vue` (NEW)

### T3.3: CNIPA律师审核步骤
- 导出材料前:选项A/B/C选择器
- 后端验证 lawyer_consulted 字段

## Phase 4: 业务链打通 (第7-8天)

### T4.1: 新建业务流指示器
**文件**: `frontend/src/components/layout/BusinessChainBar.vue` (NEW)
- 所有核心页面顶部显示: 作品→存证→IP→变现→分发→经营
- 已完成步骤打勾, 点击跳转

### T4.2: 跨模块快捷跳转
- 作品详情页: "去存证" / "去变现" 按钮
- 存证完成: "去IP登记" 链接

### T4.3: 全流程测试
- 上传作品 → 存证 → IP登记 → 产品设计 → 分发 → 收入 端到端
