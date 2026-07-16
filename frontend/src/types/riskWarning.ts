/** 风险预警类型定义 */

export interface TaxDeadline {
  id: string
  tax_type: string
  due_date: string
  amount_yuan?: number
  is_completed: boolean
  days_remaining: number
}

export interface BurnoutRisk {
  risk_level: 'low' | 'medium' | 'high'
  score: number
  factors: string[]
  recommendation: string
}

export interface HealthMetric {
  daily_work_hours: number
  works_created: number
  has_break_taken: boolean
  mood_score?: number
  recorded_date: string
}
