/** 维权ROI计算器类型定义 */

export interface DecisionTreeResult {
  recommended_actions: Array<{
    action_key: string
    name_zh: string
    estimated_cost: [number, number]
    expected_duration_days: [number, number]
    win_rate: number
    note_zh?: string
  }>
  primary_recommendation: dict
  reasoning: string
}

export interface RoiPrediction {
  expected_cost: number
  expected_duration_days: number
  win_probability: number
  expected_compensation: number
  net_return: number
  roi_percent: number
  risk_level: 'low' | 'medium' | 'high'
}

export interface DefenseTier {
  id: string
  tier_key: string
  tier_name_zh: string
  monthly_cost_low?: number
  monthly_cost_high?: number
  annual_cost_low?: number
  annual_cost_high?: number
  features?: string[]
  description_zh?: string
  recommended_for?: string
}

export interface CaseReference {
  id: string
  infringement_type: string
  target_platform: string
  typical_cost_range_low?: number
  typical_cost_range_high?: number
  resolution_time_days_low?: number
  resolution_time_days_high?: number
  win_rate_percent?: number
  avg_compensation_yuan?: number
  roi_tier?: string
  description_zh?: string
}

export interface UserCasesSummary {
  cases: Array<{
    id: string
    infringement_type: string
    target_platform: string
    estimated_loss_yuan: number
    cost_yuan: number
    compensation_received_yuan: number
    outcome: string
    roi_percent?: number
    created_at: string
  }>
  summary: {
    total_cases: number
    successful_cases: number
    success_rate_percent: number
    total_cost: number
    total_compensation: number
    overall_roi_percent?: number
  }
}
