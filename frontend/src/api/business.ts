import apiClient from './client'

export const businessApi = {
  listRevenues: (params?: Record<string, any>) => apiClient.get('/revenues', { params }),
  addRevenue: (data: any) => apiClient.post('/revenues', data),
  updateRevenue: (id: string, data: any) => apiClient.patch(`/revenues/${id}`, data),
  deleteRevenue: (id: string) => apiClient.delete(`/revenues/${id}`),
  importRevenueCsv: (formData: FormData) => apiClient.post('/publish/revenue/import', formData),
  revenueSummary: (params?: Record<string, any>) => apiClient.get('/revenues/summary', { params }),
  listPartners: (params?: Record<string, any>) => apiClient.get('/supply/partners', { params }),
  addPartner: (data: any) => apiClient.post('/supply/partners', data),
  updatePartner: (id: string, data: any) => apiClient.patch(`/supply/partners/${id}`, data),
  deletePartner: (id: string) => apiClient.delete(`/supply/partners/${id}`),
  listOrders: (params?: Record<string, any>) => apiClient.get('/supply/orders', { params }),
  addOrder: (data: any) => apiClient.post('/supply/orders', data),
  updateOrderStatus: (id: string, data: any) => apiClient.patch(`/supply/orders/${id}/status`, data),
  listNotifications: (params?: Record<string, any>) => apiClient.get('/notifications', { params }),
  unreadCount: () => apiClient.get('/notifications/unread-count'),
  markRead: (id: string) => apiClient.patch(`/notifications/${id}/read`),
  markAllRead: () => apiClient.post('/notifications/read-all'),
  getDashboard: () => apiClient.get('/dashboard'),
}
