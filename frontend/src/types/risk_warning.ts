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
