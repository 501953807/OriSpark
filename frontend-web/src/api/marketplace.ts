import client from './client'

export interface NegotiationItem {
  id: string
  listing_id: string
  request_id: string
  seller_id: string
  buyer_id: string
  status: 'pending' | 'negotiating' | 'agreed' | 'completed' | 'cancelled'
  initial_ask_yuan: number
  last_offer_yuan: number
  agreed_price_yuan?: number
  message_log: string
  created_at: string
  updated_at: string
}

export interface OfferRequest {
  amount_yuan: number
  message?: string
}

export interface MatchScore {
  listing_id: string
  score: number
  score_breakdown: Record<string, number>
}

export interface BatchToggleStatusReq {
  ids: string[]
  status: string
}

export interface BatchUpdatePriceReq {
  ids: string[]
  asking_price_yuan: number
}

export interface BatchExpireReq {
  ids: string[]
}

export interface ListingSearchParams {
  category?: string
  creator_type?: string
  price_min_yuan?: number
  price_max_yuan?: number
  tags?: string
  sort_by?: string
  page?: number
  page_size?: number
}

export interface SettlementItem {
  id: string
  sale_id: string
  sale_price_yuan: number
  base_cost_yuan: number
  shipping_cost_yuan: number
  platform_fee_yuan: number
  net_profit_yuan: number
  platform: string
}

export interface Settlement {
  id: string
  period: string
  status: string
  total_sales_yuan: number
  creator_earnings_yuan: number
  confirmed_at?: string
  items: SettlementItem[]
}

export interface SalesStatistics {
  total_sales: number
  total_revenue_yuan: number
  total_profit_yuan: number
  avg_profit_per_sale_yuan: number
  by_platform: Record<string, { sales: number; revenue_yuan: number; profit_yuan: number }>
}

export interface CommissionBalance {
  available_yuan: number
  frozen_yuan: number
  total_earned_yuan: number
}

export interface WithdrawalRequest {
  id: string
  amount_yuan: number
  net_amount_yuan: number
  fee_yuan: number
  status: string
  method: string
  created_at: string
}

export interface MonthlyCommissionStats {
  monthly: Record<string, { total: number; record_count: number }>
  records: number
}

export interface YearlyCommissionStats {
  year: number
  total_commission: number
  record_count: number
}

export interface ExpiringLicense {
  id: string
  work_title: string
  end_date: string
  days_remaining: number
}

export interface ContractPreview {
  contract_text: string
}

export const negotiationApi = {
  create: (data: { listing_id: string; request_id: string }) =>
    client.post<{ data: NegotiationItem }>('/negotiations', data),

  list: (params?: { status?: string; page?: number; page_size?: number }) =>
    client.get<{ data: NegotiationItem[] }>('/negotiations', { params }),

  getById: (id: string) =>
    client.get<{ data: NegotiationItem }>(`/negotiations/${id}`),

  submitOffer: (id: string, data: OfferRequest) =>
    client.post<{ data: NegotiationItem }>(`/negotiations/${id}/offer`, data),

  acceptOffer: (id: string) =>
    client.patch<{ data: NegotiationItem }>(`/negotiations/${id}/accept`),

  complete: (id: string) =>
    client.post<{ data: NegotiationItem }>(`/negotiations/${id}/complete`),

  cancel: (id: string) =>
    client.patch<{ data: NegotiationItem }>(`/negotiations/${id}/cancel`),
}

export const matchmakingApi = {
  autoMatch: (requestId: string) =>
    client.post<{ data: { matches: any[] } }>(`/matchmaking/auto-match/${requestId}`),

  getMatchScore: (params: { listing_id?: string; request_id?: string }) =>
    client.get<{ data: MatchScore[] }>('/matchmaking/match-score', { params }),
}

export const listingBatchApi = {
  toggleStatus: (data: BatchToggleStatusReq) =>
    client.post<{ data: { updated: number } }>('/listings/batch-toggle-status', data),

  updatePrice: (data: BatchUpdatePriceReq) =>
    client.post<{ data: { updated: number } }>('/listings/batch-update-price', data),

  expire: (data: BatchExpireReq) =>
    client.post<{ data: { expired: number } }>('/listings/batch-expire', data),

  search: (params: ListingSearchParams) =>
    client.get<{ data: any[] }>('/listings/search', { params }),
}

export const podSettlementApi = {
  myListings: () =>
    client.get<{ data: any[] }>('/pod-profit/my-settlements'),

  generate: (period: string) =>
    client.post<{ data: { id: string; period: string; status: string } }>('/pod-profit/settlements/generate', null, { params: { period } }),

  confirm: (id: string) =>
    client.post<{ data: { id: string; status: string } }>(`/pod-profit/settlements/${id}/confirm`),

  getSalesStatistics: (params?: { start_date?: string; end_date?: string }) =>
    client.get<{ data: SalesStatistics }>('/pod-profit/sales/statistics', { params }),
}

export const commissionApi = {
  getBalance: () =>
    client.get<{ data: CommissionBalance }>('/commission/balance'),

  withdraw: (data: { amount_yuan: number; method?: string; account_info?: Record<string, unknown> }) =>
    client.post<{ data: { id: string; amount_yuan: number; net_amount_yuan: number; status: string } }>('/commission/withdraw', data),

  getWithdrawals: (params?: { status?: string; limit?: number }) =>
    client.get<{ data: WithdrawalRequest[] }>('/commission/withdrawals', { params }),

  getMonthlyStats: (year?: number) =>
    client.get<{ data: MonthlyCommissionStats }>('/commission/statistics/monthly', { params: { year } }),

  getYearlyStats: (year?: number) =>
    client.get<{ data: YearlyCommissionStats }>('/commission/statistics/yearly', { params: { year } }),
}

export const ipCommercializationApi = {
  getContract: (licenseId: string) =>
    client.get<{ data: ContractPreview }>(`/ip-commercialization/licenses/${licenseId}/contract`),

  getExpiringSoon: (days?: number) =>
    client.get<{ data: { licenses: ExpiringLicense[] } }>('/ip-commercialization/expiring-soon', { params: { days } }),

  renewLicense: (licenseId: string, newEndDate: string) =>
    client.post<{ data: { id: string; end_date: string } }>(`/ip-commercialization/licenses/${licenseId}/renew`, null, { params: { new_end_date: newEndDate } }),
}

export const tradingFeeApi = {
  getConfig: () =>
    client.get<{ data: Record<string, unknown> }>('/trading-fees/config'),

  updateConfig: (configId: string, data: Record<string, unknown>) =>
    client.put<{ data: unknown }>(`/trading-fees/config/${configId}`, data),
}
