import client from './client'

export const publishApi = {
  // Products
  products: (params?: any) =>
    client.get('/publish/products', { params }),

  createProduct: (data: any) =>
    client.post('/publish/products', data),

  generateDescription: (id: string, data?: { style?: string; language?: string }) =>
    client.post(`/publish/products/${id}/describe`, data || {}),

  exportCsv: (id: string, platform: string = 'taobao') =>
    client.get(`/publish/export/${id}`, { params: { platform } }),

  platforms: () =>
    client.get('/publish/platforms'),

  publish: (id: string, platform: string) =>
    client.post(`/publish/publish/${id}`, null, { params: { platform } }),

  // AI Description styles (P1.6.1)
  describeStyles: () =>
    client.get('/publish/describe/styles'),

  // Verified Badge (P1.6.3)
  generateVerifiedBadge: (id: string) =>
    client.post(`/publish/products/${id}/verified-badge`),

  getVerifiedEmbed: (id: string) =>
    client.get(`/publish/verified-mark/${id}/embed`),

  // JSON Feed (P1.6.5-P1.6.7)
  getFeed: (params?: any) =>
    client.get('/publish/feed', { params }),

  getFeedSchema: () =>
    client.get('/publish/feed/schema'),

  getFeedPlatforms: () =>
    client.get('/publish/feed/platforms'),

  exportFeed: (platform: string = 'universal', category?: string) =>
    client.get('/publish/feed/export', { params: { platform, category } }),

  // Revenue (P1.6.9-P1.6.11)
  revenue: (params?: any) =>
    client.get('/publish/revenue', { params }),

  addRevenue: (data: any) =>
    client.post('/publish/revenue', data),

  revenueSummary: (period: string = 'month') =>
    client.get('/publish/revenue/summary', { params: { period } }),

  importRevenue: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return client.post('/publish/revenue/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  // MCP Feed formats (P2.6.5)
  exportFeedWangdiantong: (category?: string) =>
    client.get('/publish/feed/export', { params: { platform: 'wangdiantong', category } }),

  exportFeedJushuitan: (category?: string) =>
    client.get('/publish/feed/export', { params: { platform: 'jushuitan', category } }),

  // ─── Content Distribution Center (P2) ───
  // Schedules
  createSchedule: (data: any) =>
    client.post('/publish/schedule', data),

  listSchedules: () =>
    client.get('/publish/schedules'),

  deleteSchedule: (id: string) =>
    client.delete(`/publish/schedules/${id}`),

  // Contents
  listContents: () =>
    client.get('/publish/contents'),

  createContent: (data: any) =>
    client.post('/publish/contents', data),

  // Analytics
  listAnalytics: (params?: any) =>
    client.get('/publish/analytics', { params }),

  addAnalytics: (data: any) =>
    client.post('/publish/analytics', data),
}
