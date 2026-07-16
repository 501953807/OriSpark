export type Severity = 'low' | 'medium' | 'high'

export interface RiskWarning {
  id: string
  warning_type: string
  severity: Severity
  title: string
  matched_entity: string | null
  confidence: number | null
  dismissed: boolean
  created_at: string | null
}

export interface RiskCheckRequest {
  user_id?: string
  work_id?: string | null
  prompt?: string | null
  reference_images?: string[] | null
  model_name?: string | null
  work_title?: string
}

export type SeverityColor = 'red' | 'orange' | 'yellow'

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
