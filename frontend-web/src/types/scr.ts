export interface SCRScore {
  id: string
  user_id: string
  overall_score: number
  rating_level: 'starter' | 'bronze' | 'silver' | 'gold'
  fulfillment_count: number
  default_count: number
  late_review_count: number
  complaint_count: number
  cleared_count: number
  avg_response_hours: number
  created_at?: string
  updated_at?: string
}

export interface SCRAuditLog {
  id: string
  user_id: string
  score_delta: number
  reason: string
  related_transaction_id?: string
  description?: string
  created_at?: string
}

export interface LeaderboardEntry {
  user_id: string
  overall_score: number
  rating_level: string
  fulfillment_count: number
  default_count: number
}
