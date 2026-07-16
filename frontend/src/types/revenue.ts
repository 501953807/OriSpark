export interface RevenueRecord {
  id: string
  user_id: string | null
  income_category: string
  amount: number
  currency: string
  platform: string | null
  source_description: string | null
  recorded_date: string | null
  is_verified: boolean
  created_at: string | null
}

export interface IncomeCategoryInfo {
  name: string
  color: string
  amount: number
  proportion: number
}

export interface DiversityIndexResponse {
  diversity_index: number
  total_sources: number
  warnings: string[]
  category_distribution: Record<string, IncomeCategoryInfo>
}

export interface RevenueSummaryResponse {
  user_id: string
  total_revenue: number
  currency: string
  months: number
  monthly_trend: Array<{ month: string; amount: number }>
  diversity: DiversityIndexResponse
}

export type IncomeCategoryKey =
  | 'ad_revenue'
  | 'sponsorship'
  | 'subscription'
  | 'tip'
  | 'ecommerce'
  | 'affiliate'
  | 'knowledge_payment'
  | 'ip_licensing'
