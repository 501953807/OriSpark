import apiClient from './client'

export const businessApi = {
  // Revenue
  listRevenues: (params?: Record<string, any>) => apiClient.get('/api/revenues', { params }),
  addRevenue: (data: any) => apiClient.post('/api/revenues', data),
  updateRevenue: (id: string, data: any) => apiClient.patch(`/api/revenues/${id}`, data),
  deleteRevenue: (id: string) => apiClient.delete(`/api/revenues/${id}`),
  importRevenueCsv: (formData: FormData) => apiClient.post('/api/publish/revenue/import', formData),
  revenueSummary: (params?: Record<string, any>) => apiClient.get('/api/revenues/summary', { params }),

  // Partners
  listPartners: (params?: Record<string, any>) => apiClient.get('/api/supply/partners', { params }),
  addPartner: (data: any) => apiClient.post('/api/supply/partners', data),
  updatePartner: (id: string, data: any) => apiClient.patch(`/api/supply/partners/${id}`, data),
  deletePartner: (id: string) => apiClient.delete(`/api/supply/partners/${id}`),

  // Orders
  listOrders: (params?: Record<string, any>) => apiClient.get('/api/supply/orders', { params }),
  addOrder: (data: any) => apiClient.post('/api/supply/orders', data),
  updateOrderStatus: (id: string, data: any) => apiClient.patch(`/api/supply/orders/${id}/status`, data),

  // Notifications
  listNotifications: (params?: Record<string, any>) => apiClient.get('/api/notifications', { params }),
  unreadCount: () => apiClient.get('/api/notifications/unread-count'),
  markRead: (id: string) => apiClient.patch(`/api/notifications/${id}/read`),
  markAllRead: () => apiClient.post('/api/notifications/read-all'),

  // Dashboard
  getDashboard: () => apiClient.get('/api/dashboard'),
}
