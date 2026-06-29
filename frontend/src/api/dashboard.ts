import client from './client'

export const dashboardApi = {
  stats: () =>
    client.get('/dashboard/stats'),

  recent: (limit?: number) =>
    client.get('/dashboard/recent', { params: { limit } }),
}
