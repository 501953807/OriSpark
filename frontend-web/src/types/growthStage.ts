/** 创作者成长阶段类型定义 */

export interface StageInfo {
  key: string
  name_zh: string
  min_monthly_revenue: number
  max_monthly_revenue: number
  min_works: number
  min_certificates: number
  description_zh: string
  unlock_features: string[]
}

export interface GrowthTask {
  category: string
  title: string
  description?: string
  priority: number
}

export interface ProgressDashboard {
  current_stage: StageInfo
  progress_percent: number
  next_stage: StageInfo | null
  remaining_to_next: {
    monthly_revenue_gap: number
    works_needed: number
    certs_needed: number
  }
  completed_tasks: number
  total_tasks: number
  tasks: GrowthTask[]
}
