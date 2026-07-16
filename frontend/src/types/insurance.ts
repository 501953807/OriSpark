/** 版权保险市场类型定义 */

export interface InsuranceProduct {
  id: string
  product_key: string
  category: string
  tier: 'basic' | 'advanced' | 'pro'
  name_zh: string
  annual_min_yuan: number
  annual_max_yuan: number
  coverage_description?: string
  max_coverage_yuan?: number
  is_active: boolean
}

export interface InsuranceEstimateRequest {
  creator_type: string
  work_count: number
  risk_level: 'low' | 'medium' | 'high'
  categories: string[]
}

export interface InsuranceEstimateResponse {
  recommended_products: Array<{
    tier: string
    estimated_premium: number
    products: InsuranceProduct[]
  }>
  estimated_annual_premium: number
  tier: string
}

export interface InsurancePolicy {
  id: string
  user_id: string
  product_id: string
  product_name: string
  status: 'pending' | 'active' | 'expired' | 'cancelled' | 'claiming'
  annual_premium_yuan: number
  start_date: string
  end_date: string
  policy_number?: string
}

export interface InsuranceClaim {
  id: string
  policy_id: string
  claim_type: string
  description?: string
  evidence_urls?: string[]
  claimed_amount_yuan?: number
  status: 'submitted' | 'under_review' | 'approved' | 'denied' | 'paid'
  resolution?: string
  created_at: string
  resolved_at?: string
}

export interface InsuranceProvider {
  id: string
  name_zh: string
  name_en?: string
  license_no?: string
  contact_email?: string
  is_active: boolean
}
