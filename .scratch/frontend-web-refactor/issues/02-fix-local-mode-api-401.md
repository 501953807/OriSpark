# 02 — 修复本地模式假 token 导致 API 全部 401

**What to build:** 本地开发模式下，用户应能正常看到数据，而非所有页面显示空状态。

**Blocked by:** None — can start immediately（可与 01 并行）

**Status:** ready-for-agent

## 根因

`router/index.ts` 路由守卫在 `requiresAuth` 页面自动生成假 token：

```typescript
// 当前代码（问题所在）
const fakeToken = 'local-' + Date.now()
auth.token = fakeToken
auth.user = { id: 'local', username: '创作者', email: 'local@oristudio', role: '本地用户', participant_roles: [], participant_role_names: [], creator_type: 'illustrator' }
```

进入 `/app` 后，所有 API 调用携带此假 token，后端 401，错误被静默吞掉，页面显示空。

## 方案：本地模式 mock API 拦截

**方案 A（推荐）：Vite Mock API 模式**
- 在 Vite 开发服务器中添加 API mock 拦截
- 检测到本地 token（`local-` 前缀）时，从后端种子数据或前端 mock 数据返回响应
- 生产构建时 mock 不生效

**方案 B：后端本地免登录模式**
- 后端 `/api/auth/local-login` 端点，返回真实 token 和预填充数据的用户
- 前端路由守卫改为调用此端点获取真实 token

**方案 C（最简）：前端 mock 数据**
- 在关键 store（`useWorkStore`、`useDashboardStore`）中，API 失败时 fallback 到本地 mock 数据
- 保持 API 结构不变，仅改善空数据体验

## 接受标准

- [ ] 本地模式（跳过登录）进入 `/app` 后，工作台 Dashboard 显示有效数据（非空）
- [ ] 作品列表、统计卡片、收入图表等组件均能正常渲染
- [ ] 选择方案并实现（在描述中注明）
- [ ] 不影响真实登录流程（JWT 验证正常）
- [ ] 生产模式下 API 行为不变
