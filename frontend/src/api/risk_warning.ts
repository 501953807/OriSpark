import client from './client'
import type { RiskCheckRequest } from '@/types/risk_warning'

export const riskWarningApi = {
  check(data: RiskCheckRequest) {
    return client.post('/risk-warning/check', data)
  },
  getAll(params?: { dismissed?: boolean; severity?: string }) {
    return client.get('/risk-warning', { params })
  },
  getByWork(workId: string) {
    return client.get(`/risk-warning/work/${workId}`)
  },
  dismiss(warningId: string) {
    return client.patch(`/risk-warning/${warningId}/dismiss`)
  },
}
