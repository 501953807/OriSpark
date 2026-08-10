export interface PlatformStats {
  total_creators: number
  total_works: number
  total_contracts: number
  active_contracts: number
  monthly_transaction_volume: number
  avg_split_rate: number
}

export interface CreatorRankingItem {
  user_id: string
  username: string
  email: string
  creator_type?: string
  work_count: number
  total_transactions: number
  scr_score?: number
  rating_level?: string
}

export interface CategoryTrendItem {
  category: string
  work_count: number
  period: string
}

export interface IndustryReport {
  report_month: string
  generated_at: string
  summary: string
  total_creators: number
  total_works: number
  total_contracts: number
  transaction_volume: number
  top_categories: string[]
}
