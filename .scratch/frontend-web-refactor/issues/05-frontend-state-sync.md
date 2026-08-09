# 05 — 前端多 store 数据同步机制

**What to build:** 建立全局数据一致性机制，确保跨模块的数据变更能正确同步，消除状态不一致。

**Blocked by:** 02（本地模式数据正常加载后才能验证同步机制）

**Status:** ready-for-agent

## 现状分析

### 当前架构
```
frontend-web/
  stores/
    useWorkStore.ts         → /api/works/*
    useBusinessStore.ts     → /api/business/*
    useContractMarketStore.ts → /api/contract-market/*
    useIllustratorStore.ts  → /api/illustrator/*
    usePhotographerStore.ts → /api/photographer/*
    useMusicianStore.ts     → /api/musician/*
    useDashboardStore.ts    → /api/dashboard/*
    useAppStore.ts          → 主题/侧边栏/统计计数（全局）
    ... (约 20+ 个独立 store)
```

### 问题
1. 各 store 独立 fetch，缺少全局状态协调
2. `useAppStore.workCount` 由 `useDashboardStore.fetchStats()` 手动同步，其他 store 变更后不会自动更新
3. 无全局事件总线，store 之间无法感知对方数据变更
4. 后端已统一（单一 API + 单一数据库），问题在前端状态管理

## 改动方案

### 方案：Pinia 插件 + 事件总线

1. **创建 `useGlobalEvents.ts`**：跨 store 事件总线
   ```typescript
   // 定义事件类型
   export type GlobalEvents = {
     'work:created': { workId: string }
     'work:deleted': { workId: string }
     'work:updated': { workId: string }
     'contract:signed': { contractId: string }
     // ...
   }
   ```

2. **修改关键 store**：在数据变更时 dispatch 事件
   - `useWorkStore`：create/delete/update 时 emit `work:*` 事件
   - `useContractMarketStore`：sign 合约时 emit `contract:signed` 事件

3. **修改 `useAppStore`**：监听事件自动更新全局统计
   - 监听 `work:created/deleted/updated` → 更新 `workCount`
   - 监听 `contract:signed` → 更新合约计数
   - 监听侵权相关事件 → 更新 `alertCount`

### 不引入额外依赖
- 使用 Vue 3 内置 `EventBus` 模式（ref + watch）
- 不引入 pinia-plugin-persistedstate（除非有其他需求）

## 接受标准

- [ ] 创建作品后，侧边栏作品数量 badge 自动更新
- [ ] 删除作品后，badge 数量自动减少
- [ ] 存证作品后，存证数量 badge 自动更新
- [ ] 触发侵权告警后，告警数量 badge 自动更新
- [ ] 无重复数据请求（避免同一数据被多个 store 重复 fetch）
- [ ] 单元测试覆盖事件总线基本功能
