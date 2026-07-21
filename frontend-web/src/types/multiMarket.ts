/** 多市场扩展类型定义 */

export interface MarketInfo {
  market_code: string
  name_zh: string
  name_en: string
  total_creators?: number
  revenue_median_yuan?: number
  avg_rpm_yuan?: number
  growth_rate_yoy?: number
  is_open_to_foreign_creators: boolean
  copyright_protection_level: string
  language_barrier: 'low' | 'medium' | 'high'
}

export interface GeoArbitrageResult {
  current_total_monthly: number
  projected_with_targets: Record<string, number>
  total_projected_monthly: number
  increase_percent: number
  recommended_markets: string[]
}

export interface ExpansionPhase {
  phase_key: string
  phase_name_zh: string
  duration_months: number
  key_actions: string[]
  milestones: string[]
}

export interface TaxGuide {
  source_market: string
  target_market: string
  withholding_tax_rate?: number
  tax_treaty_reduction?: number
  recommended_entity?: string
  required_forms?: string[]
  description_zh?: string
}
