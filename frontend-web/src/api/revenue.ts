import client from './client'
import type { RevenueSummaryResponse, DiversityIndexResponse, RevenueRecord } from '@/types/revenue'

export const revenueApi = {
  getSummary(userId: string, months = 12) {
    return client.get(`/revenue/summary/${userId}`, { params: { months } })
  },
  getDiversity(userId: string, months = 12) {
    return client.get(`/revenue/diversity/${userId}`, { params: { months } })
  },
  addRecord(data: Partial<RevenueRecord>) {
    return client.post('/revenue/records', data)
  },
  exportRecords(params: { start_date?: string; end_date?: string; format?: 'csv' | 'json' } = {}) {
    return client.get('/revenue/records/export', { params })
  },
}
