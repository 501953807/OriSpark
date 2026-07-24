export interface Work {
  id: string
  title: string
  description: string
  category: string
  tags: string[]
  thumbnail: string | null
  creator_name: string
  is_featured: boolean
  created_at: string | null
}

export interface Contract {
  id: string
  title: string
  description: string
  contract_type: string
  total_amount: number
  currency: string
  status: string
  scope_usage: string
  scope_geography: string
  created_at: string | null
}

export interface DashboardStats {
  total_works: number
  total_contracts: number
  total_listings: number
  total_users: number
  active_contracts: number
  monthly_transaction_volume: number
}

export interface MarketTrend {
  period: string
  value: number
  label: string
}

export interface CaseStudy {
  id: string
  title: string
  summary: string
  category: string
  cover_image: string | null
  created_at: string | null
}

export interface Opportunity {
  id: string
  title: string
  description: string
  type: string
  created_by: string
  created_at: string | null
}

export interface PublicNotification {
  id: string
  title: string
  body: string
  type: string
  created_at: string | null
}

