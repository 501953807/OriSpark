import client from './client'
import type { RiskCheckRequest } from '@/types/risk_warning'

export interface BatchCheckItem {
  work_id?: string
  prompt?: string
  work_title?: string
  model_name?: string
  reference_images?: string[]
}

export interface BatchCheckResult {
  work_id: string | null
  warnings: any[]
  warning_count: number
  status: 'ok' | 'error'
  error?: string
}

export const riskWarningApi = {
  check(data: RiskCheckRequest) {
    return client.post('/risk-warning/check', data)
  },
  batchCheck(items: BatchCheckItem[], userId: string = 'local') {
    return client.post('/risk-warning/batch-check', { items, user_id: userId })
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
