import client from './client'

export const notaryApi = {
  platforms: () =>
    client.get('/notary/platforms'),

  list: (params?: any) =>
    client.get('/notary/records', { params }),

  create: (data: { work_id: string; platform: string; notes?: string }) =>
    client.post('/notary/records', data),

  get: (id: string) =>
    client.get(`/notary/records/${id}`),

  confirm: (id: string, data?: { transaction_hash?: string; block_height?: string; platform_url?: string }) =>
    client.post(`/notary/records/${id}/confirm`, data || {}),

  batch: (workIds: string[], platform: string) =>
    client.post('/notary/batch', { work_ids: workIds, platform }),

  certificate: (id: string) =>
    client.get(`/notary/certificates/${id}`),

  generateC2PA: (workId: string) =>
    client.post(`/notary/c2pa/${workId}/generate`),

  verifyC2PA: (workId: string) =>
    client.get(`/notary/verify/c2pa/${workId}`),
}
