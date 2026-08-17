import client from './client'
import type { TradeNegotiation } from '@/types/negotiation'

export const negotiationApi = {
  list: (params?: { status?: string; party?: string }) =>
    client.get<{ data: TradeNegotiation[] }>('/negotiations', { params }),
  getById: (id: string) =>
    client.get<{ data: TradeNegotiation }>(`/negotiations/${id}`),
  create: (data: { buyer_id: string; seller_id: string; listing_id?: string; description?: string; initial_price_yuan?: number }) =>
    client.post<{ data: TradeNegotiation }>('/negotiations', data),
  submitOffer: (id: string, data: { amount_yuan: number; message?: string }) =>
    client.post<{ data: TradeNegotiation }>(`/negotiations/${id}/offer`, data),
  acceptOffer: (id: string) =>
    client.patch<{ data: TradeNegotiation }>(`/negotiations/${id}/accept`),
  complete: (id: string) =>
    client.post<{ data: TradeNegotiation }>(`/negotiations/${id}/complete`),
  cancel: (id: string, reason?: string) =>
    client.patch<{ data: TradeNegotiation }>(`/negotiations/${id}/cancel`, null, { params: { reason } }),
}
