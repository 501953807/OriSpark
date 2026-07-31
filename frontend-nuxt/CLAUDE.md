# OriStudio Frontend-Nuxt - 启动指南

## 正确启动命令

```bash
cd /path/to/OriSpark/frontend-nuxt
npm run dev
```

默认端口 `3000`（Nuxt 标准端口）。

## 代理配置

Nuxt 通过 `nuxt.config.ts` 配置代理，同样读取 `BACKEND_PORT` 环境变量（默认 `8001`）。

## 启动失败排查

| 错误 | 原因 | 解决 |
|------|------|------|
| `Cannot find module 'three'` | 缺少依赖 | `npm install three` |
| `Three.js SSR crash` | 静态 import 在服务端执行 | 改为动态 `await import('three')` 在 `onMounted` 中加载 |
| `SyntaxError: Unexpected token =>` | Vue 组合式 API 语法错误 | 检查 `onMounted => {` → 应为 `onMounted(() => {` |
| `EADDRINUSE` | 端口被占用 | 改端口：`PORT=3001 npm run dev` |

## 常见组件修复

以下组件在 2026-07-31 已修复 `onMounted` 语法问题：
- `app/components/DynamicWaveFill.vue`
- `app/components/GalleryCard.vue`
- `app/components/StatCounter.vue`
- `app/components/ThreeScene.vue`

修复模式：`onMounted => {` → `onMounted(() => {`

## 依赖安装

首次克隆或依赖变更后：
```bash
npm install
```
