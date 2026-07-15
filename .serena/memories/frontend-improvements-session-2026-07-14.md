---
name: frontend-improvements-session-2026-07-14
description: 记录本次会话修复的所有前端 bug 和修改的文件
metadata:
  type: project
---

# 本次会话修复的 Bug 清单

## 已修复的 Bug

### 1. ErrorBoundary 组件缺失
- **问题**: App.vue 使用了 `<error-boundary>` 但未注册
- **修复**: 创建 `frontend/src/components/common/ErrorBoundary.vue`，更新 App.vue 导入使用

### 2. 作品详情页一直"加载中..."
- **问题**: `loadWork()` 从不设置 `loading.value = false`
- **修复**: 添加 try/finally 确保关闭 loading
- **文件**: `frontend/src/views/WorkDetailView.vue`

### 3. 作品列表缩略图不显示
- **问题**: LazyImage 组件的 IntersectionObserver 查找 `[data-lazy-src]` 元素但模板没设这个属性
- **修复**: 简化 LazyImage，直接加载图片，placeholder 作为过渡效果
- **文件**: `frontend/src/components/common/LazyImage.vue`

### 4. 作品详情页预览图片不显示
- **问题**: 预览用了 `work.file_path`（本地文件系统绝对路径），浏览器无法访问
- **修复**: 改用 `work.file_url`（API 路径）
- **文件**: `frontend/src/views/WorkDetailView.vue`

### 5. API 请求路径重复 `/api/api/...` 导致 404
- **问题**: businessApi baseURL 已是 `/api`，路径又多了一层 `/api`
- **修复**: 去掉 API 文件里的冗余 `/api` 前缀
- **文件**: `frontend/src/api/business.ts`

### 6. 缩略图 404 (`/api/files//Users/...`)
- **问题**: SupplyView.vue 用绝对路径 `thumbnail_path` 拼接 URL
- **修复**: 改用 API 路径 `thumbnail_url`
- **文件**: `frontend/src/views/SupplyView.vue`

### 7. 侧边栏"作品管理"菜单重复
- **问题**: routes 数组已含 `'works'`，下方硬编码又加了一次
- **修复**: 删除硬编码的重复项
- **文件**: `frontend/src/components/layout/DynamicSidebar.vue`

### 8. 侧边栏"权利保护"/"经营管理"重复
- **问题**: `typeInfo.routes` 已包含 rights/monitor/supply/business，硬编码共享区又添加了相同路由
- **修复**: 新增 `hasSharedRoute()` 函数，当路由已在 routes 中时跳过硬编码项
- **文件**: `frontend/src/components/layout/DynamicSidebar.vue`

## 端口配置统一
- 前端: 5174
- 后端: 8001
- 文件: `.env`, `frontend/vite.config.ts`, `backend/app/config.py`, `start.sh`, `backend/Dockerfile`

## 后端启动修复
- schemas/__init__.py 导入别名修复
- 文件: `backend/app/schemas/__init__.py`

## 待处理/可能的问题
- TypeScript 编译已通过
- 需要重启前端和后端服务使修改生效
- 其他创作者类型（摄影师/视频/手工艺/音乐人/文字作者）的 routes 只有自身一个，硬编码共享区对他们仍然有效
