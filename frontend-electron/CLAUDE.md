# OriStudio Electron Desktop App

## 实现说明

### 架构

- 使用 `vite-plugin-electron` + `vite-plugin-electron-renderer` 管理构建流程
- 主进程 (`src/main/index.ts`) 和预加载脚本 (`src/main/preload.ts`) 分别打包到 `dist/electron/`
- 渲染进程复用 `frontend-web/` 全部代码，输出到 `dist/web/`
- 通过 `contextBridge` 暴露安全的 IPC API：`window.oristudio`

### 动效系统

运动系统完全由 `frontend-web/src/stores/motion.ts` 驱动，Electron 层无需额外代码：
- 沉浸等级 / 粒子系统 / 帧率监控 — 全在 Vue renderer 中运行
- `prefers-reduced-motion` 通过 `initMotionPreferences()` 自动检测
- Three.js 粒子场景 (`ThreeScene.vue`) 依赖 `webgl: true` 设置

### 全局快捷键

注册了两组快捷键（`globalShortcut`）：
- **F11** — 切换全屏（对应沉浸式模式）
- **Cmd/Ctrl+Shift+M** — 同上（跨平台兼容）

快捷键事件通过 IPC 发送到渲染进程，应用层自行处理动效切换逻辑。

### IPC 接口清单

| Channel | Type | 说明 |
|---------|------|------|
| `app:toggle-fullscreen` | invoke | 切换全屏，返回新状态 |
| `app:get-fullscreen` | invoke | 查询当前全屏状态 |
| `app:minimize` | invoke | 最小化窗口 |
| `app:maximize` | invoke | 最大化/还原窗口 |
| `app:close` | invoke | 关闭窗口 |
| `app:get-screen-info` | invoke | 获取屏幕分辨率和缩放比 |
| `app:shortcut` | send/on | 全局快捷键 -> 渲染进程 |
| `app:shortcut-reply` | event | 反向通道（目前保留） |

### 开发流程

```bash
# 首次安装
npm install

# 开发模式（热重载）
npm run dev
# 启动 http://localhost:5175，自动打开 Electron 窗口

# 生产构建
npm run build
# 输出到 dist/web/ + dist/electron/

# 打包为桌面应用
npm run make
# 生成 macOS .dmg/.zip / Windows .exe / Linux .AppImage
```
