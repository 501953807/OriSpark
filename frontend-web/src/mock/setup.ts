/**
 * Vite 开发服务器 Mock API 中间件
 *
 * 在开发模式下拦截常见 API 请求，返回 mock 数据。
 * 生产构建时此文件不会被包含（通过 import.meta.env.DEV 控制）。
 */

import { getMockResponse } from './api'

export function setupMockMiddleware(): void {
  // This is called from vite.config.ts in dev mode
  if (!import.meta.env?.DEV) return

  // The actual interception happens via Vite's configureServer hook
  // This file is imported only in dev to avoid production bundle bloat
}
