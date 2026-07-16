import { request } from '@/api/client'
import type { ProgressDashboard } from '@/types/growthStage'

export function getDashboard() {
  return request.get('/growth-stages/dashboard').then(res => res.data as ProgressDashboard)
}

export function updateMetrics(data: {
  monthly_revenue_yuan: number
  total_works: number
  total_certificates: number
  credit_score: number
}) {
  return request.put('/growth-stages/update', data).then(res => res.data)
}

export function completeTask(taskId: string) {
  return request.patch(`/growth-stages/tasks/${taskId}/complete`).then(res => res.data)
}
