/**
 * 本地开发 Mock API 中间件
 *
 * 通过 Vite plugin 在 dev server 中拦截请求，返回 mock 数据。
 * 生产构建时此文件不会被包含。
 */

import type { Plugin } from 'vite'
import { getMockResponse } from './api'

export function mockApiPlugin(): Plugin {
  return {
    name: 'vite-plugin-mock-api',
    enforce: 'pre',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        // 仅在开发模式且路径以 /api 开头时拦截
        if (!req.url?.startsWith('/api')) return next()

        const mockData = getMockResponse(req.url!)
        if (!mockData) return next()

        const body = JSON.stringify({ data: mockData, message: 'ok' })
        res.writeHead(200, {
          'Content-Type': 'application/json; charset=utf-8',
          'Access-Control-Allow-Origin': '*',
        })
        res.end(body)
      })
    },
  }
}
