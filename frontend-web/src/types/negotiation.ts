export interface TradeNegotiation {
  id: string
  buyer_id: string
  seller_id: string
  listing_id?: string
  match_request_id?: string
  description?: string
  initial_price_yuan?: number
  current_offer_yuan?: number
  final_price_yuan?: number
  status: 'pending' | 'negotiating' | 'agreed' | 'completed' | 'cancelled'
  message_log?: string
  created_at?: string
  updated_at?: string
}
