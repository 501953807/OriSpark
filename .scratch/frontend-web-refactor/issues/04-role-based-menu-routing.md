# 04 — 9 种角色登录后动态菜单处理

**What to build:** 完成 onboarding 后，系统根据用户的 participant_role 正确渲染对应角色的侧边栏菜单。

**Blocked by:** 02（本地模式 API 修复，否则无法测试非 creator 角色）

**Status:** ready-for-agent

## 现状分析

### 后端 ✅
- `auth_service.py`：`complete_onboarding` 正确存储 `participant_roles`
- `/api/auth/me`：返回 `participant_roles` 和 `participant_role_names`
- `role_permission_service.py`：定义了 9 角色权限矩阵

### 前端部分完成
- `types/roles.ts`：`PARTICIPANT_ROLES` 定义了 9 角色及各自的 `sidebarItems`
- `DynamicSidebar.vue`：已有 `hasNonCreatorRole` / `roleInfo` 计算属性
- 非创作者角色渲染逻辑已存在

### 关键 Bug
路由守卫中本地模式强制 set `participant_roles: []`，导致所有本地用户都是 creator。

## 改动

### router/index.ts
- 本地模式不再强制 `participant_roles: []`
- 从 localStorage 读取保存的 role（`oristudio-participant-role`）

### DynamicSidebar.vue
- 验证非创作者角色的菜单渲染逻辑正确
- 确保 role badge 正确显示在侧边栏顶部

### 添加角色切换调试入口（开发模式）
- 在设置页或顶部栏添加开发工具入口
- 允许在 9 种角色间切换，快速验证各角色菜单
- 生产模式自动隐藏此功能

## 接受标准

- [ ] 以 `operator` 角色登录后，侧边栏显示：合约市场、多市场扩展、交易谈判、能力评估、信用提升、偏好设置
- [ ] 以 `legal_rep` 角色登录后，侧边栏显示：合约市场、合同风险评估、交易谈判、风控中心、偏好设置
- [ ] 以 `platform` 角色登录后，侧边栏显示完整平台管理菜单
- [ ] 以 `creator` 角色登录后，显示原有创作者菜单
- [ ] 本地模式支持通过设置或调试入口切换到不同角色
- [ ] 角色切换后菜单即时更新，无需刷新页面
