import client from './client'

export interface CreditImprovementSuggestion {
  priority: 'high' | 'medium' | 'low'
  title: string
  description: string
  action: string
}

export interface CreditImprovementResponse {
  user_id: string
  current_score: number | null
  tier: string | null
  transaction_count: number
  successful_transactions: number
  dispute_count: number
  recent_30_days: number
  recent_7_days: number
  suggestions: CreditImprovementSuggestion[]
}

export const creditApi = {
  getRating(userId: string) {
    return client.get<{ data: any }>(`/credit/rating/${userId}`)
  },
  getBehaviors(userId: string, limit: number = 50) {
    return client.get<{ data: any[] }>(`/credit/behaviors/${userId}`, { params: { limit } })
  },
  recordBehavior(data: { behavior_type: string; score_delta?: number; related_transaction_id?: string; description?: string }) {
    return client.post('/credit/behavior', data)
  },
  getImprovementSuggestions(userId: string) {
    return client.get<{ data: CreditImprovementResponse }>(`/credit/improvement-suggestions/${userId}`)
  },
}
