# OriStudio Frontend-Web - 启动指南

## 正确启动命令

```bash
cd /path/to/OriSpark/frontend-web
npm run dev
```

默认端口 `5174`，Vite 配置读取 `FRONTEND_PORT` 环境变量。

## 代理配置

Vite 自动代理 `/api` 请求到后端：
- 后端端口由 `BACKEND_PORT` 环境变量决定，默认 `8001`
- WebSocket 路径 `/ws` 也自动代理

`.env`（项目根目录可选）：
```
BACKEND_PORT=8001
FRONTEND_PORT=5174
```

## 启动失败排查

| 错误 | 原因 | 解决 |
|------|------|------|
| `EADDRINUSE: address already in use :::5174` | 端口被占用 | 改端口：`FRONTEND_PORT=5175 npm run dev`，或 `lsof -i :5174` 查占用 |
| API 请求 404/Connection refused | 后端未启动或端口不对 | 确认后端在 `8001` 运行；检查代理配置 |
| TypeScript 类型错误 | 类型定义不匹配 | `npm run build` 查看详细错误 |
| Three.js SSR 报错（Nuxt） | 静态 import 在服务端崩溃 | 使用动态 `await import('three')` 在 `onMounted` 中加载 |

## 依赖安装

首次克隆或依赖变更后：
```bash
npm install
```
